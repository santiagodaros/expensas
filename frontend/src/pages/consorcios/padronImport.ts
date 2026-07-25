import { UnidadCreate } from "@/types/api";

const COMBINING_MARK_START = 0x0300;
const COMBINING_MARK_END = 0x036f;

export function normalizeHeader(h: string): string {
  let noDiacritics = "";
  for (const ch of h.toLowerCase().normalize("NFD")) {
    const code = ch.codePointAt(0) ?? 0;
    if (code >= COMBINING_MARK_START && code <= COMBINING_MARK_END) continue;
    noDiacritics += ch;
  }
  return noDiacritics.replace(/[\s._\-/]+/g, "");
}

export const HEADER_MAP: Record<string, keyof UnidadCreate> = {
  unidad: "unidad", nro: "unidad", numero: "unidad", numero_de_unidad: "unidad",
  piso: "piso",
  dpto: "dpto", depto: "dpto", departamento: "dpto",
  propietario: "propietario", prop: "propietario", dueno: "propietario", titular: "propietario",
  inquilino: "inquilino", inq: "inquilino", locatario: "inquilino",
  coefa: "coef_a", coef_a: "coef_a", coeficientea: "coef_a", coeficiente: "coef_a", coef: "coef_a",
  coefb: "coef_b", coef_b: "coef_b", coeficienteb: "coef_b",
  coefc: "coef_c", coef_c: "coef_c", coeficientec: "coef_c",
  email: "email", mail: "email", correo: "email", correoelectronico: "email",
  saldoinicial: "saldo_apertura", saldoapertura: "saldo_apertura", saldoarrastrado: "saldo_apertura",
};

export function parseRows(rawRows: Record<string, any>[]): UnidadCreate[] {
  const units = rawRows
    .filter((row) => Object.values(row).some((v) => v !== "" && v != null))
    .map((row) => {
      const mapped: Record<string, any> = {};
      for (const [key, val] of Object.entries(row)) {
        const norm = normalizeHeader(String(key));
        const field = HEADER_MAP[norm];
        if (field) mapped[field] = val;
      }
      const toNum = (v: any) => parseFloat(String(v ?? "0")) || 0;
      return {
        unidad: String(mapped.unidad ?? "").trim(),
        piso: String(mapped.piso ?? "").trim(),
        dpto: String(mapped.dpto ?? "").trim(),
        propietario: String(mapped.propietario ?? "").trim() || undefined,
        inquilino: String(mapped.inquilino ?? "").trim() || undefined,
        coef_a: toNum(mapped.coef_a),
        coef_b: toNum(mapped.coef_b),
        coef_c: toNum(mapped.coef_c),
        email: String(mapped.email ?? "").trim() || undefined,
        saldo_apertura: toNum(mapped.saldo_apertura),
      };
    })
    .filter((u) => u.unidad !== "");

  // Detectar escala: el sistema guarda en base 100 (porcentaje).
  // Si la suma de coef_a es ≈ 1, el Excel usa decimales → convertir multiplicando por 100.
  const sumA = units.reduce((acc, u) => acc + u.coef_a, 0);
  if (sumA > 0 && Math.abs(sumA - 1) < 0.1) {
    return units.map((u) => ({
      ...u,
      coef_a: parseFloat((u.coef_a * 100).toFixed(6)),
      coef_b: parseFloat((u.coef_b * 100).toFixed(6)),
      coef_c: parseFloat((u.coef_c * 100).toFixed(6)),
    }));
  }
  return units;
}
