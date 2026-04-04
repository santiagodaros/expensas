# Plan Detallado: Importar Padrón de Unidades (Excel/CSV)

**Fecha:** 2026-04-03  
**Estado actual:** Sin implementar (0/3 pasos completos)

---

## Diagnóstico del estado actual

| Componente | Estado | Detalle |
|---|---|---|
| `api/schemas.py` | ❌ Falta | `UnidadBatchIn` NO existe |
| `api/routers/consorcios.py` | ❌ Falta | Endpoint `/batch` NO existe |
| `frontend/src/pages/Consorcios.tsx` | ❌ Falta | Botón + Modal de importación NO existe |
| `frontend/src/types/api.ts` | ❌ Falta | Tipo `UnidadBatchIn` NO existe |

---

## Paso 1 — Schema en FastAPI (`api/schemas.py`)

**Archivo:** [api/schemas.py](api/schemas.py)  
**Dónde:** Agregar después del bloque `# ─── UNIDADES ───` (línea 46, después de `UnidadOut`)

```python
class UnidadBatchIn(BaseModel):
    unidades: List[UnidadCreate]
```

**También agregar a la respuesta del batch** (ya existe `MessageOut` con `ok` y `message`):

```python
class UnidadBatchOut(BaseModel):
    ok: bool
    message: str
    insertados: int
    actualizados: int
    sin_cambios: int
```

---

## Paso 2 — Endpoint Upsert en FastAPI (`api/routers/consorcios.py`)

**Archivo:** [api/routers/consorcios.py](api/routers/consorcios.py)  
**Dónde:** Agregar al final del bloque `# ─── UNIDADES ───`, después de `delete_unidad` (línea 105)

### 2.1 — Actualizar imports (línea 17)

Cambiar:
```python
from api.schemas import ConsorcioOut, ConsorcioCreate, UnidadOut, UnidadCreate, MessageOut
```
Por:
```python
from api.schemas import ConsorcioOut, ConsorcioCreate, UnidadOut, UnidadCreate, MessageOut, UnidadBatchIn, UnidadBatchOut
```

### 2.2 — Agregar el endpoint

```python
@router.post("/consorcios/{cid}/unidades/batch", response_model=UnidadBatchOut, status_code=200)
def batch_upsert_unidades(cid: int, body: UnidadBatchIn, db: sqlite3.Connection = Depends(get_db)):
    """
    Upsert masivo de unidades desde Excel/CSV.
    - INSERT si la unidad (por nombre) no existe en el consorcio.
    - UPDATE si existe y algún campo cambió.
    - SKIP si existe y los datos son idénticos.
    - NUNCA elimina unidades que no estén en el archivo.
    """
    # 1. Traer existentes e indexar por nombre de unidad (case-sensitive, tal como vienen)
    rows = db.execute(
        "SELECT * FROM unidades WHERE consorcio_id=?", (cid,)
    ).fetchall()
    existentes: dict[str, dict] = {row_to_dict(r)["unidad"]: row_to_dict(r) for r in rows}

    insertados = 0
    actualizados = 0
    sin_cambios = 0

    for u in body.unidades:
        if u.unidad in existentes:
            ex = existentes[u.unidad]
            # Comparar campos relevantes
            changed = (
                ex["piso"] != u.piso
                or ex["dpto"] != u.dpto
                or ex["propietario"] != u.propietario
                or ex["inquilino"] != u.inquilino
                or abs(ex["coef_a"] - u.coef_a) > 1e-6
                or abs(ex["coef_b"] - u.coef_b) > 1e-6
                or abs(ex["coef_c"] - u.coef_c) > 1e-6
                or ex["email"] != u.email
            )
            if changed:
                db.execute(
                    """UPDATE unidades
                       SET piso=?, dpto=?, propietario=?, inquilino=?,
                           coef_a=?, coef_b=?, coef_c=?, email=?
                       WHERE consorcio_id=? AND unidad=?""",
                    (u.piso, u.dpto, u.propietario, u.inquilino,
                     u.coef_a, u.coef_b, u.coef_c, u.email,
                     cid, u.unidad)
                )
                actualizados += 1
            else:
                sin_cambios += 1
        else:
            db.execute(
                """INSERT INTO unidades
                   (consorcio_id, unidad, piso, dpto, propietario, inquilino, coef_a, coef_b, coef_c, email)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cid, u.unidad, u.piso, u.dpto, u.propietario,
                 u.inquilino, u.coef_a, u.coef_b, u.coef_c, u.email)
            )
            insertados += 1

    return {
        "ok": True,
        "message": f"Importación completa: {insertados} nuevas, {actualizados} actualizadas, {sin_cambios} sin cambios.",
        "insertados": insertados,
        "actualizados": actualizados,
        "sin_cambios": sin_cambios,
    }
```

> **Gotcha crítico:** La comparación de strings puede fallar si Python guarda `None` y el Excel viene como `""`. La comparación `ex["propietario"] != u.propietario` necesita que ambos sean del mismo tipo. El schema `UnidadCreate` tiene `propietario: Optional[str] = None`, así que si el Excel manda `""` y la DB tiene `None`, va a hacer un UPDATE innecesario. Opciones:
> - Normalizar en el endpoint: `(u.propietario or None)` antes de comparar
> - O tolerarlo: hacer el UPDATE igual (es inofensivo, solo más trabajo)
> - **Recomendado:** normalizar con `(val or None)` en la comparación

---

## Paso 3 — Frontend (`frontend/src/pages/Consorcios.tsx`)

**Archivo:** [frontend/src/pages/Consorcios.tsx](frontend/src/pages/Consorcios.tsx)

### 3.1 — Actualizar imports

**Línea 12 — Agregar `UploadCloud` a lucide:**
```tsx
import { Building2, Plus, Pencil, Trash2, Users, ChevronRight, MapPin, Hash, UploadCloud } from "lucide-react";
```

**Agregar después de los imports de lucide:**
```tsx
import { useCallback, useState } from "react"; // ya hay useState, agregar useCallback
import { useDropzone } from "react-dropzone";
import Papa from "papaparse";
import * as XLSX from "xlsx";
import type { UnidadCreate } from "@/types/api";
```

> **Verificar antes de implementar:** Correr `cd frontend && npm ls papaparse xlsx react-dropzone` para confirmar que están instalados. Si no, instalar antes.

### 3.2 — Header normalization (lógica crítica)

Los usuarios de Excel escriben headers de mil formas distintas. Esta función normaliza y mapea:

```tsx
// Normaliza un header: lowercase, sin espacios, sin puntos, sin guiones bajos, sin acentos
function normalizeHeader(h: string): string {
  return h
    .toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // quitar acentos
    .replace(/[\s._\-/]+/g, ""); // quitar espacios, puntos, guiones, barras
}

// Mapeo flexible de headers normalizados → campo de UnidadCreate
const HEADER_MAP: Record<string, keyof UnidadCreate> = {
  // unidad
  "unidad": "unidad",
  "nro": "unidad",
  "numero": "unidad",
  "depto": "dpto",
  "departamento": "dpto",
  // piso
  "piso": "piso",
  // dpto
  "dpto": "dpto",
  // propietario
  "propietario": "propietario",
  "prop": "propietario",
  "dueno": "propietario",
  // inquilino
  "inquilino": "inquilino",
  "inq": "inquilino",
  "locatario": "inquilino",
  // coef_a
  "coefa": "coef_a",
  "coef_a": "coef_a",
  "coeficientea": "coef_a",
  "coeficiente": "coef_a",
  "coef": "coef_a",
  // coef_b
  "coefb": "coef_b",
  "coef_b": "coef_b",
  "coeficienteb": "coef_b",
  // coef_c
  "coefc": "coef_c",
  "coef_c": "coef_c",
  "coeficientec": "coef_c",
  // email
  "email": "email",
  "mail": "email",
  "correo": "email",
};
```

### 3.3 — Parser de filas a `UnidadCreate[]`

```tsx
function parseRows(rawRows: Record<string, any>[]): UnidadCreate[] {
  return rawRows
    .filter((row) => Object.values(row).some((v) => v !== "" && v != null))
    .map((row) => {
      // Mapear cada key del objeto a su campo canónico
      const mapped: Record<string, any> = {};
      for (const [key, val] of Object.entries(row)) {
        const norm = normalizeHeader(key);
        const field = HEADER_MAP[norm];
        if (field) mapped[field] = val;
      }

      // Normalizar coef_a: si viene como porcentaje (ej: 4.5 → 0.045 si >1)
      // OJO: la convención del sistema es decimal (0 a 1). Si el Excel tiene >1, dividir por 100.
      const toCoef = (v: any): number => {
        const n = parseFloat(String(v ?? "0")) || 0;
        return n > 1 ? n / 100 : n;
      };

      return {
        unidad: String(mapped.unidad ?? "").trim(),
        piso: String(mapped.piso ?? "").trim(),
        dpto: String(mapped.dpto ?? "").trim(),
        propietario: String(mapped.propietario ?? "").trim() || undefined,
        inquilino: String(mapped.inquilino ?? "").trim() || undefined,
        coef_a: toCoef(mapped.coef_a),
        coef_b: toCoef(mapped.coef_b),
        coef_c: toCoef(mapped.coef_c),
        email: String(mapped.email ?? "").trim() || undefined,
      };
    })
    .filter((u) => u.unidad !== ""); // descartar filas sin nombre de unidad
}
```

> **Gotcha del coef:** El plan dice "si no da 100 o 1". Esto implica que el Excel puede tener coeficientes como `4.5` (porcentaje) o `0.045` (decimal). La función `toCoef` maneja ambos casos: si el valor es > 1, lo divide por 100.

### 3.4 — Componente `ImportarPadronDialog`

Agregar ANTES de `ConsorciosPage` (después de `UnidadDialog`):

```tsx
function ImportarPadronDialog({
  consorcioId,
  onClose,
  onSaved,
}: {
  consorcioId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [parsed, setParsed] = useState<UnidadCreate[] | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [coefSum, setCoefSum] = useState<number>(0);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<{ insertados: number; actualizados: number; sin_cambios: number } | null>(null);

  const processFile = useCallback((file: File) => {
    setFileName(file.name);
    setParsed(null);
    setResult(null);

    const handleRows = (rawRows: Record<string, any>[]) => {
      const units = parseRows(rawRows);
      const sum = units.reduce((acc, u) => acc + u.coef_a, 0);
      setParsed(units);
      setCoefSum(sum);
    };

    if (file.name.endsWith(".csv")) {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (res) => handleRows(res.data as Record<string, any>[]),
      });
    } else {
      const reader = new FileReader();
      reader.onload = (e) => {
        const wb = XLSX.read(e.target?.result, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json<Record<string, any>>(ws, { defval: "" });
        handleRows(rows);
      };
      reader.readAsArrayBuffer(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "text/csv": [".csv"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"] },
    maxFiles: 1,
    onDrop: (accepted) => { if (accepted[0]) processFile(accepted[0]); },
  });

  // Validación: suma de coef_a debe ser ≈ 1 (decimal) o ≈ 100 (porcentaje)
  // Como ya normalizamos a decimal, validamos contra 1
  const coefOk = Math.abs(coefSum - 1) < 0.02; // tolerancia del 2%
  const coefWarning = parsed && parsed.length > 0 && !coefOk;

  const handleImport = async () => {
    if (!parsed || parsed.length === 0) return;
    setImporting(true);
    try {
      const res = await api.post(`/api/consorcios/${consorcioId}/unidades/batch`, { unidades: parsed });
      const data = res.data as { insertados: number; actualizados: number; sin_cambios: number; message: string };
      setResult({ insertados: data.insertados, actualizados: data.actualizados, sin_cambios: data.sin_cambios });
      toast.success(data.message);
      onSaved();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? err?.message ?? "Error al importar");
    } finally {
      setImporting(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent style={{ backgroundColor: "var(--color-surface)", borderColor: "var(--color-border)", color: "var(--color-text)", maxWidth: 500 }}>
        <DialogHeader>
          <DialogTitle style={{ color: "var(--color-text)" }}>Importar Padrón</DialogTitle>
        </DialogHeader>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className="rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors"
          style={{
            borderColor: isDragActive ? "var(--color-accent)" : "var(--color-border)",
            backgroundColor: isDragActive ? "rgba(59,130,246,0.05)" : "var(--color-surface2)",
          }}
        >
          <input {...getInputProps()} />
          <UploadCloud size={32} className="mx-auto mb-3" style={{ color: "var(--color-text2)" }} />
          {fileName ? (
            <p className="text-sm font-medium" style={{ color: "var(--color-text)" }}>{fileName}</p>
          ) : (
            <>
              <p className="text-sm" style={{ color: "var(--color-text)" }}>
                {isDragActive ? "Soltá el archivo acá" : "Arrastrá o hacé click para seleccionar"}
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--color-text2)" }}>Soporta .csv y .xlsx</p>
            </>
          )}
        </div>

        {/* Preview y validación */}
        {parsed && (
          <div className="flex flex-col gap-2 text-xs">
            <div className="flex items-center justify-between px-1">
              <span style={{ color: "var(--color-text2)" }}>{parsed.length} unidades detectadas</span>
              <span style={{ color: coefOk ? "var(--color-success, #22c55e)" : "var(--color-danger)" }}>
                Σ Coef A = {coefSum.toFixed(4)} {coefOk ? "✓" : "⚠ no suma 1"}
              </span>
            </div>
            {coefWarning && (
              <div className="rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: "rgba(234,179,8,0.1)", color: "#ca8a04" }}>
                ⚠ La suma de coeficientes A es {coefSum.toFixed(4)}, debería ser 1.0 (o 100%). Podés continuar igual, pero revisá el archivo.
              </div>
            )}
          </div>
        )}

        {result && (
          <div className="rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: "rgba(34,197,94,0.1)", color: "#16a34a" }}>
            ✅ {result.insertados} insertadas · {result.actualizados} actualizadas · {result.sin_cambios} sin cambios
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} style={{ color: "var(--color-text2)" }}>
            {result ? "Cerrar" : "Cancelar"}
          </Button>
          {!result && (
            <Button
              onClick={handleImport}
              disabled={!parsed || parsed.length === 0 || importing}
              style={{ backgroundColor: "rgba(59,130,246,0.15)", color: "var(--color-accent)", border: "1px solid rgba(59,130,246,0.3)" }}
            >
              {importing ? "Importando..." : `Importar ${parsed?.length ?? 0} unidades`}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### 3.5 — Agregar estado e integración en `ConsorciosPage`

**En el estado del componente** (cerca de línea 141, junto a los otros estados):
```tsx
const [importDialog, setImportDialog] = useState(false);
```

**En el header de la panel de unidades** (línea 259, junto al botón "Nueva unidad"):
```tsx
<div className="flex items-center gap-2">
  <Button size="sm" onClick={() => setImportDialog(true)} className="h-7 px-3 text-xs gap-1"
    style={{ backgroundColor: "rgba(255,255,255,0.05)", color: "var(--color-text2)", border: "1px solid var(--color-border)" }}>
    <UploadCloud size={12} /> Importar Padrón
  </Button>
  <Button size="sm" onClick={() => setUnidadDialog({ open: true })} className="h-7 px-3 text-xs gap-1"
    style={{ backgroundColor: "rgba(59,130,246,0.15)", color: "var(--color-accent)", border: "1px solid rgba(59,130,246,0.3)" }}>
    <Plus size={12} /> Nueva unidad
  </Button>
</div>
```

**Al final del JSX** (junto a los otros dialogs, línea 326):
```tsx
{importDialog && selected && (
  <ImportarPadronDialog
    consorcioId={selected.id}
    onClose={() => setImportDialog(false)}
    onSaved={() => { setImportDialog(false); refetchU(); }}
  />
)}
```

---

## Tipo en `frontend/src/types/api.ts`

Agregar después de `UnidadCreate` (línea 46):

```typescript
export interface UnidadBatchOut {
  ok: boolean;
  message: string;
  insertados: number;
  actualizados: number;
  sin_cambios: number;
}
```

---

## Orden de implementación recomendado

1. **Primero el backend** (Paso 1 → Paso 2): testear con `curl` o Swagger antes de tocar el frontend
2. **Luego el tipo** en `api.ts`
3. **Luego el frontend** (Paso 3): agregar funciones helper primero, luego el componente, luego la integración

---

## Gotchas importantes (no obvios)

| # | Problema | Solución |
|---|---|---|
| 1 | Headers del Excel impredecibles | Normalización con `normalizeHeader()` + `HEADER_MAP` |
| 2 | Coef como porcentaje vs decimal | `toCoef()` divide por 100 si el valor es > 1 |
| 3 | Strings vacíos vs `None` en DB | `String(val).trim() \|\| undefined` en el parser |
| 4 | Comparación `None` vs `""` en Python | Normalizar con `(val or None)` en el endpoint antes de comparar |
| 5 | Filas vacías en Excel | `filter` por `u.unidad !== ""` en el parser |
| 6 | `react-dropzone` + Tauri | El `tauriAdapter` ya maneja el POST correcto; el dropzone es local, no afecta |
| 7 | Nombres de unidades case-sensitive | La comparación es exacta (`"1A" != "1a"`). Decisión: mantener case-sensitive |

---

## Dependencias a verificar antes de implementar

```bash
cd frontend && npm ls papaparse xlsx react-dropzone
```

Si falta alguna:
```bash
npm install papaparse xlsx react-dropzone
npm install --save-dev @types/papaparse
```

---

## Criterio de aceptación

- [ ] Subir un `.xlsx` con 10 unidades → aparecen en la grilla
- [ ] Subir mismo `.xlsx` sin cambios → `sin_cambios: 10`, ninguna duplicada
- [ ] Subir `.xlsx` con 1 propietario cambiado → `actualizados: 1`, `sin_cambios: 9`
- [ ] Subir `.xlsx` con headers raros (`"Coef A"`, `"Dpto."`, `"Mail"`) → parsea correctamente
- [ ] Subir `.xlsx` con coef que no suma 1 → muestra warning pero permite continuar
- [ ] Unidades cargadas a mano (no en el Excel) → NO se borran
