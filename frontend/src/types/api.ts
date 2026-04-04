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

export interface UnidadBatchOut {
  ok: boolean;
  message: string;
  insertados: number;
  actualizados: number;
  sin_cambios: number;
}

// ─── Gastos ───────────────────────────────────────────────────────────────────
export interface Gasto {
  id: number;
  consorcio_id: number;
  periodo: string;
  categoria: "A" | "B" | "C";
  descripcion: string;
  monto: number;
  tipo?: string;  // "ordinario" | "extraordinario"
  comprobante_path?: string;
  proveedor_id?: number;
}

export interface GastoBatchItem {
  categoria: "A" | "B" | "C";
  descripcion: string;
  monto: number;
  tipo?: string;
  comprobante_path?: string;
  proveedor_id?: number;
}

// ─── Gastos Particulares ──────────────────────────────────────────────────────
export interface GastoParticular {
  id: number;
  consorcio_id: number;
  periodo: string;
  unidad_id: number;
  descripcion: string;
  monto: number;
}

export interface GastoParticularCreate {
  unidad_id: number;
  descripcion: string;
  monto: number;
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

// ─── Proveedores ──────────────────────────────────────────────────────────────
export interface Proveedor {
  id: number;
  consorcio_id: number;
  razon_social: string;
  cuit?: string;
  domicilio?: string;
  cat_afip?: string;
  cbu?: string;
}

export interface ProveedorCreate {
  razon_social: string;
  cuit?: string;
  domicilio?: string;
  cat_afip?: string;
  cbu?: string;
}

export interface CuentaCorrienteRow {
  proveedor_id: number;
  razon_social: string;
  total_gastos: number;
  periodos: number;
}

// ─── Sueldos ──────────────────────────────────────────────────────────────────
export interface Sueldo {
  id: number;
  consorcio_id: number;
  periodo: string;
  empleado: string;
  concepto: string;
  sueldo_bruto: number;
  cargas_suterh: number;
  cargas_fateryh: number;
  otras_cargas: number;
  total_gasto: number;
  gasto_id?: number;
}

export interface SueldoCreate {
  empleado: string;
  concepto: string;
  sueldo_bruto: number;
  cargas_suterh: number;
  cargas_fateryh: number;
  otras_cargas: number;
}

// ─── Config ───────────────────────────────────────────────────────────────────
export interface Config {
  nombre_cat_a: string;
  nombre_cat_b: string;
  nombre_cat_c: string;
  smtp_server: string;
  smtp_port: string;
  smtp_user: string;
}
