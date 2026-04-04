# Implementación: Importar Unidades Funcionales (UF) vía Excel/CSV

Eres un Senior Fullstack Developer. Tu objetivo es implementar la importación masiva de Unidades Funcionales (UF) subiendo un Excel (.xlsx) o un CSV desde el Frontend de una aplicación React/Tauri hacia un backend FastAPI. 

## Reglas Acordadas
- **Formatos:** Se debe soportar tanto `.csv` como `.xlsx`. (Puedes usar `papaparse` para CSV y `xlsx` / SheetJS para Excel. Ya están instalados en el frontend).
- **Validación Frontend:** Antes de enviar el JSON al backend, el frontend debe sumar todos los `Coef_A` del archivo. Si no da 100 o 1 (dentro de un margen de error por redondeo, ej. 0.99 a 1.01), debe saltar una advertencia fuerte pero permitir continuar, o bloquearlo si prefieres, pero debe avisar.
- **Lógica de Sobreescritura (Upsert):** Si el listado de Excel tiene una unidad que ya está cargada (exactamente mismo nombre de "unidad", ej: "1A"), **no debe pisarla si es identica**, pero si cambiaron datos (propietario, coeficientes) sí debe **actualizarla (update)**. Si hay unidades en el Excel que no existen, debe **agregarlas (insert)**. Las unidades creadas a mano que NO estén en el Excel NO DEBEN ser borradas (solo "agrega y actualiza" lo que llega en el archivo).

---

## Tareas (Paso a Paso)

### Paso 1: Schema en FastAPI
1. Revisa `api/schemas.py` y asegúrate de que exista `UnidadBatchIn`.
```python
class UnidadBatchIn(BaseModel):
    unidades: List[UnidadCreate]
```
*(Nota: Ya agregué esto en un paso previo, pero confírmalo).*

### Paso 2: Endpoint Upsert en FastAPI
1. Abre `api/routers/consorcios.py`.
2. Crea el endpoint `POST /consorcios/{cid}/unidades/batch`.
3. Al recibir la lista de unidades, haz lo siguiente:
   - Trae todas las unidades existentes del consorcio (`SELECT * FROM unidades WHERE consorcio_id=?`).
   - Crea un diccionario local indexado por el campo `unidad` (ej. `dict["1A"] = row`).
   - Itera las unidades del Excel (`UnidadBatchIn`):
     - Si la unidad EXISTE en el diccionario temporal: haz un `UPDATE` en la tabla modificando `piso`, `dpto`, `propietario`, `inquilino`, `coef_a`, `coef_b`, `coef_c`, `email`.
     - Si la unidad NO EXISTE: haz un `INSERT`.
   - Recuerda devolver al final `{"ok": True, "message": "Importación exitosa"}`.

### Paso 3: Frontend - Componente de Importación
1. Abre `frontend/src/pages/Consorcios.tsx`.
2. Agrega al header del módulo (al lado del botón *Nueva Unidad*) un botón "Importar Padrón" (usa el ícono `UploadCloud` de Lucide).
3. Este botón debe abrir un Modal (Dialog de Shadcn) que incluya un Área de Dropzone (`react-dropzone`).
4. **Lógica de Manejo de Archivos:**
   - Si el archivo termina en `.csv`, léeselo con `Papa.parse`.
   - Si termina en `.xlsx`, léeselo con `xlsx` (`read` y `utils.sheet_to_json`).
   - Adapta los headers del Excel a un JSON compatible con `UnidadCreate` (`unidad`, `piso`, `coef_a`, etc).
     **¡IMPORTANTE (Mapeo Flexible)!:** Los usuarios de Excel suelen modificar o escribir los headers de formas impredecibles ("Depto", "Dpto.", "Coef A", "Coef_a", "Unidad"). Tu lógica de parseo DEBE normalizar los headers (ej. convirtiendo todo a minúsculas, quitando espacios y puntos) y usar un mapeo flexible. Si asumes que el string del Excel será perfecto, el parser generará un objeto lleno de `undefined` y fallará. Asegurate de hacer código a prueba de clientes.
5. **Validación:** Suma todos los `coef_a`. Tira un `alert()` o toast de error si la suma está muy desfasada.
6. Manda la lista con un `await api.post('/api/consorcios/${cid}/unidades/batch', { unidades: parsedArray })`.
7. Si fue exitoso, cierra el Modal y fuerza el `refetchU()` para repintar la grilla.

**[INSTRUCCIÓN PARA CLAUDE]**: No me des todo el código de una sola vez. Mostrame primero tu código propuesto para el Endpoint de FastAPI (Paso 2), comprobemos la lógica de Update/Insert. Cuando te lo apruebe, armamos la interfaz en React (Paso 3).
