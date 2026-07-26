"""Router: Dashboard - KPIs y graficos agregados"""
from fastapi import APIRouter, Depends, Query
import sqlite3
from datetime import datetime
from api.database import get_db
from api.schemas import DashboardOut, DashboardKPI, BarData, DeudorPendiente
from api.utils import load_pagos_periodo, apply_interes_mora

router = APIRouter(tags=["Dashboard"])

def _tf(val):
    if val is None or val == "": return 0.0
    try: return float(str(val).replace(",", ".").strip())
    except: return 0.0

_MESES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

def _last_n_periods(n=8):
    from datetime import datetime
    y, m = datetime.now().year, datetime.now().month
    result = []
    for _ in range(n):
        result.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0: m, y = 12, y - 1
    return list(reversed(result))

@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(
    consorcio: int = Query(...),
    periodo: str = Query(None),
    db: sqlite3.Connection = Depends(get_db),
):
    if not periodo:
        periodo = datetime.now().strftime("%Y-%m")
    per = periodo

    cons = db.execute("SELECT * FROM consorcios WHERE id=?", (consorcio,)).fetchone()
    if not cons: return DashboardOut(kpi=DashboardKPI(total_unidades=0,pagados=0,pendientes=0,pct_cobranza=0,v_recaudado=0,v_deuda=0), chart=[], deudores=[])
    cons = dict(cons); reserva_pct = _tf(cons.get("reserva_pct", 0.0)); dia_vto = int(cons.get("dia_vto") or 10)
    interes_pct = _tf(cons.get("interes_mora_pct", 0.0))

    unis = db.execute("SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (consorcio,)).fetchall()
    gs = db.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=?", (consorcio, per)).fetchall()
    uid_list = [u["id"] for u in unis]

    p_ant, p_act = load_pagos_periodo(db, consorcio, per)
    tot_a = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "A")
    tot_b = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "B")
    tot_c = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "C")

    kpi_mora = 0; kpi_pagados = 0; kpi_deuda = 0.0; kpi_rec = 0.0
    deudores_list = []

    for u in unis:
        uid = u["id"]; u_d = dict(u)
        ca, cb, cc = _tf(u_d.get("coef_a")), _tf(u_d.get("coef_b")), _tf(u_d.get("coef_c"))
        imp = tot_a*ca/100.0 + tot_b*cb/100.0 + tot_c*cc/100.0
        pa = p_ant.get(uid, {}); pc = p_act.get(uid, {})
        saldo_ant = apply_interes_mora(_tf(pa.get("monto_deuda", 0.0)), interes_pct) if pa else _tf(u_d.get("saldo_apertura", 0.0))
        monto_rec = _tf(pc.get("monto_recibido", 0.0)); telec = _tf(pc.get("telec", 0.0))
        imp_d = imp if imp > 0 else _tf(pc.get("imp_mes_override") or 0)
        reserva = _tf(pc.get("reserva", 0.0)) if pc else round(imp_d * reserva_pct / 100.0, 2)
        redondeo = _tf(pc.get("redondeo", 0.0))
        total_pagar = (saldo_ant - monto_rec - telec) + imp_d + reserva + redondeo
        pagado = bool(pc.get("pagado", 0)); en_mora = not pagado and total_pagar > 1.0
        if pagado: kpi_pagados += 1
        if monto_rec > 0: kpi_rec += monto_rec
        if en_mora:
            kpi_mora += 1; kpi_deuda += total_pagar
            nombre = str(u_d.get("propietario") or u_d.get("inquilino") or "-")
            deudores_list.append(DeudorPendiente(unidad_id=uid, unidad=str(u_d.get("unidad", "")),
                nombre=nombre, email=u_d.get("email"), total_pagar=round(total_pagar, 2), vence_dia=dia_vto))

    deudores_list.sort(key=lambda x: x.total_pagar, reverse=True)
    total_cobrable = kpi_rec + kpi_deuda
    pct = (kpi_rec / total_cobrable * 100) if total_cobrable > 0 else 0.0
    kpi = DashboardKPI(total_unidades=len(unis), pagados=kpi_pagados,
        pendientes=kpi_mora, pct_cobranza=round(pct, 1), v_recaudado=round(kpi_rec, 2), v_deuda=round(kpi_deuda, 2))

    # Chart: ultimos 8 periodos
    periodos = _last_n_periods(8)
    chart = []
    for p in periodos:
        if uid_list:
            ph = ",".join("?" * len(uid_list))
            p_rows = db.execute(f"SELECT SUM(monto_recibido) as rec FROM pagos WHERE periodo=? AND unidad_id IN ({ph})", [p] + uid_list).fetchone()
            ingresos = _tf(p_rows["rec"] if p_rows else 0)
        else:
            ingresos = 0.0
        g_rows = db.execute("SELECT SUM(monto) as tot FROM gastos WHERE consorcio_id=? AND periodo=?", (consorcio, p)).fetchone()
        egresos = _tf(g_rows["tot"] if g_rows else 0)
        y2, m2 = int(p[:4]), int(p[5:])
        label = f"{_MESES[m2]} {y2}"
        chart.append(BarData(periodo=p, label=label, ingresos=round(ingresos, 2), egresos=round(egresos, 2)))

    return DashboardOut(kpi=kpi, chart=chart, deudores=deudores_list[:10])
