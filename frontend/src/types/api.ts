// ─── Consorcios ───────────────────────────────────────────────────────────────
export interface Consorcio {
  id: number;
  nombre: string;
  cuit?: string;
  direccion?: string;
  unidades: number;
  reserva_pct: number;
  dia_vto: number;
}

export interface ConsorcioCreate {
  nombre: string;
  cuit?: string;
  direccion?: string;
  unidades: number;
  reserva_pct: number;
  dia_vto: number;
}

// ─── Unidades ─────────────────────────────────────────────────────────────────
export interface Unidad {
  id: number;
  consorcio_id: number;
  unidad: string;
  piso: string;
  dpto: string;
  propietario?: string;
  inquilino?: string;
  coef_a: number;
  coef_b: number;
  coef_c: number;
  email?: string;
}

export interface UnidadCreate {
  unidad: string;
  piso: string;
  dpto: string;
  propietario?: string;
  inquilino?: string;
  coef_a: number;
  coef_b: number;
  coef_c: number;
  email?: string;
}

// ─── Gastos ───────────────────────────────────────────────────────────────────
export interface Gasto {
  id: number;
  consorcio_id: number;
  periodo: string;
  categoria: "A" | "B" | "C";
  descripcion: string;
  monto: number;
  comprobante_path?: string;
}

export interface GastoBatchItem {
  categoria: "A" | "B" | "C";
  descripcion: string;
  monto: number;
  comprobante_path?: string;
}

// ─── Pagos ────────────────────────────────────────────────────────────────────
export interface PagoUnitRow {
  unidad_id: number;
  unidad: string;
  piso: string;
  dpto: string;
  nombre: string;
  email?: string;
  pagado: boolean;
  en_mora: boolean;
  saldo_anterior: number;
  monto_recibido: number;
  telec: number;
  imp_mes: number;
  reserva: number;
  redondeo: number;
  total_pagar: number;
}

export interface PagosResumen {
  periodo: string;
  consorcio_id: number;
  unidades: PagoUnitRow[];
  kpi_mora: number;
  kpi_pagados: number;
  kpi_total_deuda: number;
  kpi_pct_cobranza: number;
  kpi_recaudado: number;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export interface BarData {
  periodo: string;
  label: string;
  ingresos: number;
  egresos: number;
}

export interface DeudorPendiente {
  unidad_id: number;
  unidad: string;
  nombre: string;
  email?: string;
  total_pagar: number;
  vence_dia: number;
}

export interface DashboardKPI {
  total_unidades: number;
  pagados: number;
  pendientes: number;
  pct_cobranza: number;
  v_recaudado: number;
  v_deuda: number;
}

export interface Dashboard {
  kpi: DashboardKPI;
  chart: BarData[];
  deudores: DeudorPendiente[];
}

// ─── Config ───────────────────────────────────────────────────────────────────
export interface Config {
  [key: string]: string;
}
