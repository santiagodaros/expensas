"""
Pydantic Schemas - Modelos de entrada/salida para la API REST.
"""
from pydantic import BaseModel
from typing import Optional, List


# ─── CONSORCIOS ────────────────────────────────────────────────────────────────

class ConsorcioBase(BaseModel):
    nombre: str
    cuit: Optional[str] = None
    direccion: Optional[str] = None
    unidades: int = 0
    reserva_pct: float = 0.0
    dia_vto: int = 10

class ConsorcioCreate(ConsorcioBase):
    pass

class ConsorcioOut(ConsorcioBase):
    id: int
    model_config = {"from_attributes": True}


# ─── UNIDADES ──────────────────────────────────────────────────────────────────

class UnidadBase(BaseModel):
    unidad: str
    piso: str = ""
    dpto: str = ""
    propietario: Optional[str] = None
    inquilino: Optional[str] = None
    coef_a: float = 0.0
    coef_b: float = 0.0
    coef_c: float = 0.0
    email: Optional[str] = None
    saldo_apertura: float = 0.0

class UnidadCreate(UnidadBase):
    pass

class UnidadOut(UnidadBase):
    id: int
    consorcio_id: int
    saldo_apertura_editable: bool = True
    model_config = {"from_attributes": True}

class UnidadBatchIn(BaseModel):
    unidades: List[UnidadCreate]

class UnidadBatchOut(BaseModel):
    ok: bool
    message: str
    insertados: int
    actualizados: int
    sin_cambios: int


# ─── GASTOS ────────────────────────────────────────────────────────────────────

class GastoBase(BaseModel):
    categoria: str  # A | B | C
    descripcion: str
    monto: float
    tipo: str = "ordinario"  # "ordinario" | "extraordinario"
    comprobante_path: Optional[str] = None
    proveedor_id: Optional[int] = None

class GastoCreate(GastoBase):
    pass

class GastoOut(GastoBase):
    id: int
    consorcio_id: int
    periodo: str
    model_config = {"from_attributes": True}

class GastoBatchIn(BaseModel):
    """Reemplaza TODOS los gastos del periodo con este listado."""
    consorcio_id: int
    periodo: str
    gastos: List[GastoCreate]

class GastoUpdate(BaseModel):
    categoria: str
    descripcion: str
    monto: float
    tipo: str = "ordinario"
    proveedor_id: Optional[int] = None


# ─── PROVEEDORES ───────────────────────────────────────────────────────────────

class ProveedorBase(BaseModel):
    razon_social: str
    cuit: Optional[str] = None
    domicilio: Optional[str] = None
    cat_afip: Optional[str] = None
    cbu: Optional[str] = None

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorOut(ProveedorBase):
    id: int
    consorcio_id: int
    model_config = {"from_attributes": True}

class ProveedorUpdate(ProveedorBase):
    pass

class CuentaCorrienteRow(BaseModel):
    proveedor_id: int
    razon_social: str
    total_gastos: float
    periodos: int


# ─── GASTOS PARTICULARES ───────────────────────────────────────────────────────

class GastoParticularBase(BaseModel):
    unidad_id: int
    descripcion: str
    monto: float

class GastoParticularCreate(GastoParticularBase):
    pass

class GastoParticularOut(GastoParticularBase):
    id: int
    consorcio_id: int
    periodo: str
    model_config = {"from_attributes": True}


# ─── PAGOS ─────────────────────────────────────────────────────────────────────

class BatchMarcarPagados(BaseModel):
    """Body para POST /api/finanzas/pagos/batch_marcar — marca varias unidades
    como pagadas de una vez, cobrando exactamente lo que cada una debía."""
    consorcio_id: int
    periodo: str
    unidad_ids: List[int]


class PagoRegistrar(BaseModel):
    """Body para POST /api/finanzas/pagos — registra/actualiza un pago de una unidad."""
    unidad_id: int
    periodo: str
    pagado: int = 0
    monto_recibido: float = 0.0
    telec: float = 0.0
    reserva: float = 0.0
    redondeo: float = 0.0
    saldo_inicial: float = 0.0
    imp_mes_override: Optional[float] = None


class PagoUnitRow(BaseModel):
    """Fila de Estado de Pagos para una unidad."""
    unidad_id: int
    unidad: str
    piso: str
    dpto: str
    nombre: str
    email: Optional[str] = None
    pagado: bool
    en_mora: bool
    saldo_anterior: float
    monto_recibido: float
    telec: float
    imp_mes: float
    reserva: float
    redondeo: float
    total_pagar: float


class PagosResumenOut(BaseModel):
    periodo: str
    consorcio_id: int
    unidades: List[PagoUnitRow]
    kpi_mora: int
    kpi_pagados: int
    kpi_total_deuda: float
    kpi_pct_cobranza: float
    kpi_recaudado: float


# ─── DASHBOARD ─────────────────────────────────────────────────────────────────

class DashboardKPI(BaseModel):
    total_unidades: int
    pagados: int
    pendientes: int
    pct_cobranza: float
    v_recaudado: float
    v_deuda: float

class BarData(BaseModel):
    periodo: str
    label: str      # "Jul 2024"
    ingresos: float
    egresos: float

class DeudorPendiente(BaseModel):
    unidad_id: int
    unidad: str
    nombre: str
    email: Optional[str] = None
    total_pagar: float
    vence_dia: int

class DashboardOut(BaseModel):
    kpi: DashboardKPI
    chart: List[BarData]
    deudores: List[DeudorPendiente]


# ─── CONFIG ────────────────────────────────────────────────────────────────────

class ConfigOut(BaseModel):
    nombre_cat_a: str = "Gastos Comunes"
    nombre_cat_b: str = "Fuerza Motriz"
    nombre_cat_c: str = "Locales"
    smtp_server: str = ""
    smtp_port: str = "587"
    smtp_user: str = ""

class ConfigUpdate(BaseModel):
    nombre_cat_a: Optional[str] = None
    nombre_cat_b: Optional[str] = None
    nombre_cat_c: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None


class BackupOut(BaseModel):
    ok: bool
    message: str
    path: str
    total_backups: int


class SmtpTestRequest(BaseModel):
    smtp_server: str
    smtp_port: str = "587"
    smtp_user: str
    smtp_pass: Optional[str] = None  # si se omite, se usa la guardada (para no reescribirla por un campo vacío)


# ─── SUELDOS ───────────────────────────────────────────────────────────────────

class SueldoBase(BaseModel):
    empleado: str
    concepto: str = "Encargado"
    sueldo_bruto: float = 0.0
    cargas_suterh: float = 0.0
    cargas_fateryh: float = 0.0
    otras_cargas: float = 0.0

class SueldoCreate(SueldoBase):
    pass

class SueldoOut(SueldoBase):
    id: int
    consorcio_id: int
    periodo: str
    total_gasto: float
    gasto_id: Optional[int] = None
    model_config = {"from_attributes": True}

class SueldoUpdate(SueldoBase):
    pass


# ─── MISC ──────────────────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    ok: bool
    message: str = ""
