"""Router: Finanzas"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import List
import sqlite3
import os
from pathlib import Path
from api.database import get_db, rows_to_list
from api.schemas import GastoOut, GastoCreate, GastoBatchIn, GastoUpdate, PagoRegistrar, PagosResumenOut, PagoUnitRow, MessageOut, GastoParticularOut, GastoParticularCreate, BatchMarcarPagados
from api.utils import safe_filename_part, safe_periodo, load_pagos_periodo, apply_interes_mora

from decimal import Decimal, ROUND_HALF_UP

router = APIRouter(tags=["Finanzas"])

_COMPROBANTES_MAX_BYTES = 15 * 1024 * 1024  # 15MB
_COMPROBANTES_ALLOWED_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def _comprobantes_base() -> Path:
    return Path.home() / "Documents" / "Expensas" / "Comprobantes"

def _tf(val):
    if val is None or val == "": return 0.0
    try: return float(str(val).replace(",", ".").replace("$", "").strip())
    except: return 0.0

def _m(val) -> float:
    """Round to 2 decimal places using ROUND_HALF_UP (banker-safe for money)."""
    return float(Decimal(str(round(float(val), 10))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

# GASTOS
@router.get("/finanzas/gastos", response_model=List[GastoOut])
def get_gastos(consorcio: int = Query(...), periodo: str = Query(...), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=? ORDER BY categoria, descripcion", (consorcio, periodo)).fetchall()
    return rows_to_list(rows)

@router.post("/finanzas/gastos", response_model=GastoOut, status_code=201)
def create_gasto(consorcio_id: int, periodo: str, body: GastoCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO gastos(consorcio_id,periodo,categoria,descripcion,monto,tipo,comprobante_path,proveedor_id) VALUES(?,?,?,?,?,?,?,?)",
        (consorcio_id, periodo, body.categoria, body.descripcion, body.monto, body.tipo, body.comprobante_path, body.proveedor_id)
    )
    row = db.execute("SELECT * FROM gastos WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.post("/finanzas/gastos/batch", response_model=MessageOut)
def batch_gastos(body: GastoBatchIn, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM gastos WHERE consorcio_id=? AND periodo=?", (body.consorcio_id, body.periodo))
    for g in body.gastos:
        db.execute("INSERT INTO gastos(consorcio_id,periodo,categoria,descripcion,monto,tipo,comprobante_path,proveedor_id) VALUES(?,?,?,?,?,?,?,?)",
                   (body.consorcio_id, body.periodo, g.categoria, g.descripcion, g.monto, g.tipo, g.comprobante_path, g.proveedor_id))
    return {"ok": True, "message": f"{len(body.gastos)} gastos guardados para {body.periodo}"}

@router.delete("/finanzas/gastos/{gid}", response_model=MessageOut)
def delete_gasto(gid: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM gastos WHERE id=?", (gid,))
    return {"ok": True, "message": f"Gasto {gid} eliminado"}

@router.put("/finanzas/gastos/{gid}", response_model=MessageOut)
def update_gasto(gid: int, body: GastoUpdate, db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE gastos SET categoria=?, descripcion=?, monto=?, tipo=?, proveedor_id=? WHERE id=?",
               (body.categoria, body.descripcion, body.monto, body.tipo, body.proveedor_id, gid))
    return {"ok": True, "message": f"Gasto {gid} actualizado"}


@router.post("/finanzas/gastos/{gid}/comprobante", response_model=MessageOut)
async def subir_comprobante(gid: int, file: UploadFile = File(...), db: sqlite3.Connection = Depends(get_db)):
    gasto = db.execute("SELECT consorcio_id, periodo FROM gastos WHERE id=?", (gid,)).fetchone()
    if not gasto:
        raise HTTPException(404, "Gasto no encontrado")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _COMPROBANTES_ALLOWED_EXT:
        raise HTTPException(400, "Tipo de archivo no permitido (solo PDF o imagen)")
    contents = await file.read()
    if len(contents) > _COMPROBANTES_MAX_BYTES:
        raise HTTPException(400, "El archivo supera el tamaño máximo permitido (15MB)")

    periodo = safe_periodo(gasto["periodo"])
    folder = _comprobantes_base() / str(gasto["consorcio_id"]) / periodo
    folder.mkdir(parents=True, exist_ok=True)
    filename = safe_filename_part(f"{gid}_{file.filename}")
    path = folder / filename
    path.write_bytes(contents)

    db.execute("UPDATE gastos SET comprobante_path=? WHERE id=?", (str(path), gid))
    return {"ok": True, "message": "Comprobante guardado"}


@router.get("/finanzas/gastos/{gid}/comprobante")
def abrir_comprobante(gid: int, db: sqlite3.Connection = Depends(get_db)):
    gasto = db.execute("SELECT comprobante_path FROM gastos WHERE id=?", (gid,)).fetchone()
    if not gasto or not gasto["comprobante_path"]:
        raise HTTPException(404, "Este gasto no tiene comprobante adjunto")
    path = gasto["comprobante_path"]
    if not os.path.isfile(path):
        raise HTTPException(404, "El archivo del comprobante ya no existe en disco")
    os.startfile(path)
    return {"ok": True}


# GASTOS PARTICULARES
@router.get("/finanzas/gastos_particulares", response_model=List[GastoParticularOut])
def get_gastos_particulares(consorcio: int = Query(...), periodo: str = Query(...), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM gastos_particulares WHERE consorcio_id=? AND periodo=? ORDER BY unidad_id, descripcion",
        (consorcio, periodo)
    ).fetchall()
    return rows_to_list(rows)

@router.post("/finanzas/gastos_particulares", response_model=GastoParticularOut, status_code=201)
def create_gasto_particular(consorcio_id: int, periodo: str, body: GastoParticularCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO gastos_particulares(consorcio_id,periodo,unidad_id,descripcion,monto) VALUES(?,?,?,?,?)",
        (consorcio_id, periodo, body.unidad_id, body.descripcion, body.monto)
    )
    row = db.execute("SELECT * FROM gastos_particulares WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)

@router.delete("/finanzas/gastos_particulares/{gid}", response_model=MessageOut)
def delete_gasto_particular(gid: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM gastos_particulares WHERE id=?", (gid,))
    return {"ok": True, "message": f"Gasto particular {gid} eliminado"}

@router.put("/finanzas/gastos_particulares/{gid}", response_model=MessageOut)
def update_gasto_particular(gid: int, body: GastoParticularCreate, db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE gastos_particulares SET unidad_id=?, descripcion=?, monto=? WHERE id=?",
               (body.unidad_id, body.descripcion, body.monto, gid))
    return {"ok": True, "message": f"Gasto particular {gid} actualizado"}

# PAGOS
@router.get("/finanzas/pagos", response_model=PagosResumenOut)
def get_pagos(consorcio: int = Query(...), periodo: str = Query(...), db: sqlite3.Connection = Depends(get_db)):
    cid = consorcio; per = periodo
    cons_row = db.execute("SELECT * FROM consorcios WHERE id=?", (cid,)).fetchone()
    if not cons_row: raise HTTPException(404, "Consorcio no encontrado")
    cons = dict(cons_row); reserva_pct = _tf(cons.get("reserva_pct", 0.0)); interes_pct = _tf(cons.get("interes_mora_pct", 0.0))
    unis = db.execute("SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (cid,)).fetchall()
    gs = db.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=?", (cid, per)).fetchall()
    p_ant, p_act = load_pagos_periodo(db, cid, per)
    tot_a = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "A")
    tot_b = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "B")
    tot_c = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "C")
    kpi_mora = 0; kpi_pagados = 0; kpi_deuda = 0.0; kpi_rec = 0.0
    result_units = []
    for u in unis:
        uid = u["id"]; u_d = dict(u)
        ca, cb, cc = _tf(u_d.get("coef_a")), _tf(u_d.get("coef_b")), _tf(u_d.get("coef_c"))
        imp_mes = tot_a*ca/100.0 + tot_b*cb/100.0 + tot_c*cc/100.0
        part = db.execute("SELECT COALESCE(SUM(monto),0) FROM gastos_particulares WHERE consorcio_id=? AND periodo=? AND unidad_id=?", (cid, per, uid)).fetchone()[0]
        imp_mes += _tf(part)
        pa = p_ant.get(uid, {}); pc = p_act.get(uid, {})
        # No se clampa a 0: un sobrepago real (monto_deuda negativo) debe
        # trasladarse como credito a favor del mes siguiente, no perderse.
        # Si todavia no hay ningun pago anterior registrado, se arranca desde
        # el saldo de apertura cargado en la unidad (deuda o credito previo
        # a empezar a usar el sistema). El interes por mora solo se aplica
        # sobre deuda que ya vino de un periodo anterior registrado, nunca
        # sobre el saldo de apertura de una unidad recien cargada.
        saldo_ant = apply_interes_mora(_tf(pa.get("monto_deuda", 0.0)), interes_pct) if pa else _tf(u_d.get("saldo_apertura", 0.0))
        monto_rec = _tf(pc.get("monto_recibido", 0.0)); telec = _tf(pc.get("telec", 0.0))
        imp_display = imp_mes if imp_mes > 0 else _tf(pc.get("imp_mes_override") or 0)
        reserva = _tf(pc.get("reserva", 0.0)) if pc else _m(imp_display * reserva_pct / 100.0)
        redondeo = _tf(pc.get("redondeo", 0.0))
        saldo_cobr = saldo_ant - monto_rec - telec
        total_pagar = saldo_cobr + imp_display + reserva + redondeo
        pagado = bool(pc.get("pagado", 0)); en_mora = not pagado and total_pagar > 1.0
        nombre = str(u_d.get("propietario") or u_d.get("inquilino") or "-")
        if pagado: kpi_pagados += 1
        if en_mora: kpi_mora += 1; kpi_deuda += total_pagar
        if monto_rec > 0: kpi_rec += monto_rec
        result_units.append(PagoUnitRow(
            unidad_id=uid, unidad=str(u_d.get("unidad", "")), piso=str(u_d.get("piso", "")),
            dpto=str(u_d.get("dpto", "")), nombre=nombre, email=u_d.get("email"),
            pagado=pagado, en_mora=en_mora, saldo_anterior=round(saldo_ant, 2),
            monto_recibido=round(monto_rec, 2), telec=round(telec, 2),
            imp_mes=_m(imp_display), reserva=_m(reserva),
            redondeo=_m(redondeo), total_pagar=_m(total_pagar)))
    total_cobrable = kpi_rec + kpi_deuda
    pct = (kpi_rec / total_cobrable * 100) if total_cobrable > 0 else 0.0
    return PagosResumenOut(periodo=per, consorcio_id=cid, unidades=result_units,
        kpi_mora=kpi_mora, kpi_pagados=kpi_pagados, kpi_total_deuda=round(kpi_deuda, 2),
        kpi_pct_cobranza=round(pct, 1), kpi_recaudado=round(kpi_rec, 2))

@router.post("/finanzas/pagos", response_model=MessageOut)
def registrar_pago(body: PagoRegistrar, db: sqlite3.Connection = Depends(get_db)):
    # Recalculate imp_mes server-side (same logic as get_pagos) to avoid client drift
    unidad = db.execute(
        "SELECT consorcio_id, coef_a, coef_b, coef_c FROM unidades WHERE id=?",
        (body.unidad_id,)
    ).fetchone()
    if unidad:
        gs = db.execute(
            "SELECT categoria, monto FROM gastos WHERE consorcio_id=? AND periodo=?",
            (unidad["consorcio_id"], body.periodo)
        ).fetchall()
        tot_a = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "A")
        tot_b = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "B")
        tot_c = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "C")
        ca = _tf(unidad["coef_a"]); cb = _tf(unidad["coef_b"]); cc = _tf(unidad["coef_c"])
        imp_mes_calc = tot_a * ca / 100.0 + tot_b * cb / 100.0 + tot_c * cc / 100.0
        part = db.execute("SELECT COALESCE(SUM(monto),0) FROM gastos_particulares WHERE consorcio_id=? AND periodo=? AND unidad_id=?", (unidad["consorcio_id"], body.periodo, body.unidad_id)).fetchone()[0]
        imp_mes_calc += _tf(part)
    else:
        imp_mes_calc = 0.0
    imp = imp_mes_calc if imp_mes_calc > 0 else (body.imp_mes_override or 0.0)
    deuda = body.saldo_inicial - body.monto_recibido - body.telec + imp + body.reserva + body.redondeo
    db.execute(
        "INSERT INTO pagos(unidad_id,periodo,pagado,monto_deuda,monto_recibido,telec,reserva,redondeo,saldo_inicial,imp_mes_override) "
        "VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(unidad_id,periodo) DO UPDATE SET "
        "pagado=excluded.pagado,monto_deuda=excluded.monto_deuda,monto_recibido=excluded.monto_recibido,"
        "telec=excluded.telec,reserva=excluded.reserva,redondeo=excluded.redondeo,"
        "saldo_inicial=excluded.saldo_inicial,imp_mes_override=excluded.imp_mes_override",
        (body.unidad_id, body.periodo, body.pagado, _m(deuda), body.monto_recibido,
         body.telec, body.reserva, body.redondeo, body.saldo_inicial, body.imp_mes_override))
    # No hace falta pre-sembrar el periodo siguiente: get_pagos() ya lee
    # monto_deuda de este período como saldo_anterior del que viene. El bloque
    # que existía acá escribía `deuda` en el monto_recibido del mes siguiente,
    # lo cual se cancelaba con ese mismo saldo_anterior (dejaba en $0 una deuda
    # real) y, para sobrepagos, invertía el signo y generaba una mora falsa.
    return {"ok": True, "message": "Pago registrado"}


@router.post("/finanzas/pagos/batch_marcar", response_model=MessageOut)
def batch_marcar_pagados(body: BatchMarcarPagados, db: sqlite3.Connection = Depends(get_db)):
    """Marca varias unidades como pagadas de una vez, cobrando exactamente lo
    que cada una debia (igual que abrir 'Registrar Pago' y confirmar el monto
    prellenado, pero para varias unidades en un solo click)."""
    resumen = get_pagos(consorcio=body.consorcio_id, periodo=body.periodo, db=db)
    filas = {u.unidad_id: u for u in resumen.unidades}
    marcados = 0
    for uid in body.unidad_ids:
        row = filas.get(uid)
        if not row:
            continue
        registrar_pago(PagoRegistrar(
            unidad_id=uid, periodo=body.periodo, pagado=1,
            monto_recibido=row.total_pagar if row.total_pagar > 0 else 0.0,
            telec=row.telec, reserva=row.reserva, redondeo=row.redondeo,
            saldo_inicial=row.saldo_anterior,
            imp_mes_override=row.imp_mes if row.imp_mes > 0 else None,
        ), db)
        marcados += 1
    return {"ok": True, "message": f"{marcados} unidades marcadas como pagadas"}
