"""Router: Finanzas"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
import sqlite3
from api.database import get_db, rows_to_list, row_to_dict
from api.schemas import GastoOut, GastoCreate, GastoBatchIn, GastoUpdate, PagoRegistrar, PagosResumenOut, PagoUnitRow, MessageOut, GastoParticularOut, GastoParticularCreate

from decimal import Decimal, ROUND_HALF_UP

router = APIRouter(tags=["Finanzas"])

def _tf(val):
    if val is None or val == "": return 0.0
    try: return float(str(val).replace(",", ".").replace("$", "").strip())
    except: return 0.0

def _m(val) -> float:
    """Round to 2 decimal places using ROUND_HALF_UP (banker-safe for money)."""
    return float(Decimal(str(round(float(val), 10))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def _pa_of(k):
    y, m = int(k[:4]), int(k[5:])
    m -= 1
    if m == 0: m, y = 12, y - 1
    return f"{y}-{m:02d}"

def _pn_of(k):
    y, m = int(k[:4]), int(k[5:])
    m += 1
    if m == 13: m, y = 1, y + 1
    return f"{y}-{m:02d}"

# GASTOS
@router.get("/finanzas/gastos", response_model=List[GastoOut])
def get_gastos(consorcio: int = Query(...), periodo: str = Query(...), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=? ORDER BY categoria, descripcion", (consorcio, periodo)).fetchall()
    return rows_to_list(rows)

@router.post("/finanzas/gastos", response_model=GastoOut, status_code=201)
def create_gasto(consorcio_id: int, periodo: str, body: GastoCreate, db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute(
        "INSERT INTO gastos(consorcio_id,periodo,categoria,descripcion,monto,tipo,comprobante_path) VALUES(?,?,?,?,?,?,?)",
        (consorcio_id, periodo, body.categoria, body.descripcion, body.monto, body.tipo, body.comprobante_path)
    )
    row = db.execute("SELECT * FROM gastos WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.post("/finanzas/gastos/batch", response_model=MessageOut)
def batch_gastos(body: GastoBatchIn, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM gastos WHERE consorcio_id=? AND periodo=?", (body.consorcio_id, body.periodo))
    for g in body.gastos:
        db.execute("INSERT INTO gastos(consorcio_id,periodo,categoria,descripcion,monto,tipo,comprobante_path) VALUES(?,?,?,?,?,?,?)",
                   (body.consorcio_id, body.periodo, g.categoria, g.descripcion, g.monto, g.tipo, g.comprobante_path))
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
    cid = consorcio; per = periodo; per_a = _pa_of(per)
    cons_row = db.execute("SELECT * FROM consorcios WHERE id=?", (cid,)).fetchone()
    if not cons_row: raise HTTPException(404, "Consorcio no encontrado")
    cons = dict(cons_row); reserva_pct = _tf(cons.get("reserva_pct", 0.0))
    unis = db.execute("SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (cid,)).fetchall()
    gs = db.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=?", (cid, per)).fetchall()
    uid_list = [u["id"] for u in unis]
    if uid_list:
        ph = ",".join("?" * len(uid_list))
        pagos_rows = db.execute(f"SELECT * FROM pagos WHERE periodo IN (?,?) AND unidad_id IN ({ph})", [per_a, per] + uid_list).fetchall()
    else:
        pagos_rows = []
    p_ant = {p["unidad_id"]: dict(p) for p in pagos_rows if p["periodo"] == per_a}
    p_act = {p["unidad_id"]: dict(p) for p in pagos_rows if p["periodo"] == per}
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
        saldo_ant = max(0.0, _tf(pa.get("monto_deuda", 0.0))) if pa else _tf(pc.get("saldo_inicial", 0.0))
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
    if body.pagado:
        per_n = _pn_of(body.periodo)
        db.execute("INSERT INTO pagos(unidad_id,periodo,monto_recibido) VALUES(?,?,?) ON CONFLICT(unidad_id,periodo) DO UPDATE SET monto_recibido=excluded.monto_recibido",
                   (body.unidad_id, per_n, _m(deuda)))
    return {"ok": True, "message": "Pago registrado"}
