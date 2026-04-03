"""Router: Reportes PDF"""
import sqlite3
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from decimal import Decimal, ROUND_HALF_UP
from fpdf import FPDF
from api.database import get_db

router = APIRouter(tags=["Reportes"])


def _boletas_dir() -> Path:
    folder = Path.home() / "Documents" / "Expensas" / "Boletas"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _save_pdf(pdf_bytes: bytes, filename: str) -> str:
    path = _boletas_dir() / filename
    path.write_bytes(pdf_bytes)
    return str(path)


# -- helpers ------------------------------------------------------------------

def _tf(val):
    if val is None or val == "": return 0.0
    try: return float(str(val).replace(",", ".").replace("$", "").replace(" ", "").strip())
    except: return 0.0

def _m(val) -> float:
    return float(Decimal(str(round(float(val), 10))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def _fmt(val) -> str:
    try: f = float(val)
    except: return "0,00"
    s = f"{f:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def _pa_of(k: str) -> str:
    y, m = int(k[:4]), int(k[5:])
    m -= 1
    if m == 0: m, y = 12, y - 1
    return f"{y}-{m:02d}"

def _vto(periodo: str, dia_vto: int) -> str:
    y, m = int(periodo[:4]), int(periodo[5:])
    m_v = m + 1 if m < 12 else 1
    y_v = y if m < 12 else y + 1
    return f"{dia_vto}/{m_v}/{y_v}"

def _get_cfg(db, key: str, default: str = "") -> str:
    try:
        row = db.execute("SELECT valor FROM configuracion WHERE clave=?", (key,)).fetchone()
        return row["valor"] if row and row["valor"] else default
    except:
        return default


# -- landscape page headers ---------------------------------------------------

def _hdr_admin_L(pdf: FPDF):
    y0 = pdf.get_y()
    pdf.rect(10, y0, 277, 14)
    pdf.set_xy(12, y0 + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(150, 5, "Administracion de Consorcios   Jorge Eduardo Da Ros", ln=True)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(150, 5, "San Lorenzo 2657   Dpto 6   (1651) San Andres,  Bs As")
    pdf.set_xy(190, y0 + 7)
    pdf.cell(20, 5, "Celular")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(30, 5, "11 36636072", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(20, 5, "Movistar", align="R", ln=True)
    pdf.set_y(y0 + 18)

def _hdr_page_L(pdf: FPDF, titulo: str, periodo: str, vto: str, nombre: str, direccion: str):
    _hdr_admin_L(pdf)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(150, 7, f"CONSORCIO DE PROPIETARIOS {nombre}  {direccion}".upper(), border=1)
    pdf.cell(87, 7, "", border=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(40, 7, f"Vto ..... {vto}", border=1, align="C", ln=True)
    pdf.ln(3)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(70, 7, titulo)
    pdf.set_fill_color(255, 242, 204)
    pdf.cell(25, 7, periodo, border=1, fill=True, align="C", ln=True)
    pdf.ln(3)

# -- PDF GENERAL (3 pages, landscape) ----------------------------------------

def _pdf_general(consorcio: dict, unis: list, gastos: list, pagos_ant: dict, pagos_act: dict, periodo: str, cat_names: dict) -> bytes:
    rh = 6
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=8)
    nom  = consorcio.get("nombre", "")
    dire = consorcio.get("direccion", "")
    dia_vto     = int(consorcio.get("dia_vto") or 10)
    reserva_pct = _tf(consorcio.get("reserva_pct", 0.0))
    vto = _vto(periodo, dia_vto)
    tot_a = sum(_tf(g["monto"]) for g in gastos if g["categoria"] == "A")
    tot_b = sum(_tf(g["monto"]) for g in gastos if g["categoria"] == "B")
    tot_c = sum(_tf(g["monto"]) for g in gastos if g["categoria"] == "C")

    # Pagina 1: Liquidacion de Gastos
    pdf.add_page()
    _hdr_page_L(pdf, "Liquidacion de Gastos Expensas", periodo, vto, nom, dire)
    w = [27, 200, 50]
    pdf.set_x(10); pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(230, 230, 230)
    pdf.cell(w[0], rh, "Cat.", border=1, fill=True, align="C")
    pdf.cell(w[1], rh, "Descripcion del Gasto", border=1, fill=True, align="C")
    pdf.cell(w[2], rh, "Monto", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    cur_cat = None; sub = 0.0
    for g in sorted(gastos, key=lambda x: x["categoria"] or ""):
        cat = g["categoria"] or ""; m_g = _tf(g["monto"])
        if cat != cur_cat:
            if cur_cat is not None:
                pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
                lbl = f"Subtotal {cur_cat} - {cat_names.get(cur_cat, cur_cat)}"
                pdf.cell(w[0] + w[1], rh, lbl, border=1, align="R")
                pdf.cell(w[2], rh, _fmt(sub), border=1, align="R", ln=True)
                pdf.set_font("Helvetica", "", 9)
            cur_cat = cat; sub = 0.0
        sub += m_g
        desc = str(g.get("descripcion") or "")
        pdf.set_x(10)
        pdf.cell(w[0], rh, cat, border=1, align="C")
        pdf.cell(w[1], rh, "  " + desc, border=1)
        pdf.cell(w[2], rh, _fmt(m_g), border=1, align="R", ln=True)
    if cur_cat is not None:
        pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w[0] + w[1], rh, f"Subtotal Categoria {cur_cat}", border=1, align="R")
        pdf.cell(w[2], rh, _fmt(sub), border=1, align="R", ln=True)
    pdf.ln(2); pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w[0] + w[1], rh, "TOTAL GENERAL DE GASTOS", border=1, align="R")
    pdf.set_fill_color(255, 255, 0)
    pdf.cell(w[2], rh, _fmt(tot_a + tot_b + tot_c), border=1, fill=True, align="R", ln=True)

    # Pagina 2: Prorrateo
    pdf.add_page()
    _hdr_page_L(pdf, "Prorrateo de gastos expensas", periodo, vto, nom, dire)
    w1 = [13, 13, 14, 63, 19, 23, 23, 27, 27, 27, 28]
    pdf.set_x(10); pdf.set_fill_color(230, 230, 230); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(sum(w1[:4]), rh, "", border=0)
    pdf.cell(w1[4],  rh, "Locales",       border=1, fill=True, align="C")
    pdf.cell(w1[5],  rh, "Fuerza motriz", border=1, fill=True, align="C")
    pdf.cell(w1[6],  rh, "Exp con todos", border=1, fill=True, align="C")
    pdf.cell(w1[7],  rh, "A",             border=1, fill=True, align="C")
    pdf.cell(w1[8],  rh, "B",             border=1, fill=True, align="C")
    pdf.cell(w1[9],  rh, "C",             border=1, fill=True, align="C")
    pdf.cell(w1[10], rh, "TOTAL",         border=1, fill=True, align="C", ln=True)
    pdf.set_x(10)
    for lbl, wi in zip(["Piso", "Dpto", "U.F.", "Nombre y Apellido"], w1[:4]):
        pdf.cell(wi, rh, lbl, border=1, fill=True, align="C")
    for lbl, wi in zip(["B", "C", "A", "A", "B", "C", "Expensas"], w1[4:]):
        pdf.cell(wi, rh, lbl, border=1, fill=True, align="C")
    pdf.ln()
    tc_a = tc_b = tc_c = ti_a = ti_b = ti_c = ti_ex = 0.0
    pdf.set_font("Helvetica", "", 9)
    for u in unis:
        ca, cb, cc = _tf(u["coef_a"]), _tf(u["coef_b"]), _tf(u["coef_c"])
        tc_a += ca; tc_b += cb; tc_c += cc
        ia = tot_a * ca / 100.0; ib = tot_b * cb / 100.0; ic = tot_c * cc / 100.0; ex = ia + ib + ic
        ti_a += ia; ti_b += ib; ti_c += ic; ti_ex += ex
        nombre_u = u.get("propietario") or u.get("inquilino") or ""
        pdf.set_x(10)
        pdf.cell(w1[0],  rh, u.get("piso", ""),   border=1, align="C")
        pdf.cell(w1[1],  rh, u.get("dpto", ""),   border=1, align="C")
        pdf.cell(w1[2],  rh, str(u["unidad"]),     border=1, align="C")
        pdf.cell(w1[3],  rh, " " + nombre_u[:32], border=1)
        pdf.cell(w1[4],  rh, _fmt(cb) + "%",      border=1, align="R")
        pdf.cell(w1[5],  rh, _fmt(cc) + "%",      border=1, align="R")
        pdf.cell(w1[6],  rh, _fmt(ca) + "%",      border=1, align="R")
        pdf.cell(w1[7],  rh, _fmt(ia),            border=1, align="R")
        pdf.cell(w1[8],  rh, _fmt(ib),            border=1, align="R")
        pdf.cell(w1[9],  rh, _fmt(ic),            border=1, align="R")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w1[10], rh, _fmt(ex),            border=1, align="R", ln=True)
        pdf.set_font("Helvetica", "", 9)
    pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(sum(w1[:4]), rh, "TOTALES",    border=1, align="R")
    pdf.cell(w1[4],  rh, _fmt(tc_b) + "%", border=1, align="R")
    pdf.cell(w1[5],  rh, _fmt(tc_c) + "%", border=1, align="R")
    pdf.cell(w1[6],  rh, _fmt(tc_a) + "%", border=1, align="R")
    pdf.cell(w1[7],  rh, _fmt(ti_a),       border=1, align="R")
    pdf.cell(w1[8],  rh, _fmt(ti_b),       border=1, align="R")
    pdf.cell(w1[9],  rh, _fmt(ti_c),       border=1, align="R")
    pdf.set_fill_color(255, 255, 0); pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w1[10], rh, _fmt(ti_ex),      border=1, fill=True, align="R", ln=True)

    # Pagina 3: Recaudacion y Expensas
    pdf.add_page()
    _hdr_page_L(pdf, "Recaudacion y expensas", periodo, vto, nom, dire)
    w2 = [13, 13, 14, 50, 24, 24, 18, 24, 26, 20, 18, 33]
    pdf.set_x(10); pdf.set_fill_color(230, 230, 230); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(sum(w2[:5]), rh, "", border=0)
    pdf.cell(w2[5] + w2[6], rh, "COBRANZA", border=1, fill=True, align="C")
    pdf.cell(sum(w2[7:]),   rh, "", border=0, ln=True)
    pdf.set_x(10)
    for lbl, wi in zip(["Piso","Dpto","U.F.","Nombre y Apellido","Saldo","Mes Ant","Telec / Vs","SALDO","Expensas","Reserva","Redondeo","TOTAL PAGO"], w2):
        pdf.cell(wi, rh, lbl, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    ts_a = ts_co = ts_tel = ts_sn = ts_ex = ts_re = ts_rd = ts_tot = 0.0
    for u in unis:
        uid = u["id"]
        ca, cb, cc = _tf(u["coef_a"]), _tf(u["coef_b"]), _tf(u["coef_c"])
        ex = tot_a * ca / 100.0 + tot_b * cb / 100.0 + tot_c * cc / 100.0
        pa = pagos_ant.get(uid, {}); pc = pagos_act.get(uid, {})
        saldo_ant = max(0.0, _tf(pa.get("monto_deuda", 0.0))) if pa else _tf(pc.get("saldo_inicial", 0.0))
        cobranza  = _tf(pc.get("monto_recibido", 0.0))
        telec     = _tf(pc.get("telec", 0.0))
        reserva   = _tf(pc.get("reserva", 0.0)) if pc else _m(ex * reserva_pct / 100.0)
        redondeo  = _tf(pc.get("redondeo", 0.0))
        saldo_neto  = max(0.0, saldo_ant - cobranza - telec)
        total_pagar = saldo_neto + ex + reserva + redondeo
        ts_a += saldo_ant; ts_co += cobranza; ts_tel += telec; ts_sn += saldo_neto
        ts_ex += ex; ts_re += reserva; ts_rd += redondeo; ts_tot += total_pagar
        nombre_u = u.get("propietario") or u.get("inquilino") or ""
        pdf.set_x(10)
        pdf.cell(w2[0],  rh, u.get("piso", ""),   border=1, align="C")
        pdf.cell(w2[1],  rh, u.get("dpto", ""),   border=1, align="C")
        pdf.cell(w2[2],  rh, str(u["unidad"]),    border=1, align="C")
        pdf.cell(w2[3],  rh, " " + nombre_u[:26], border=1)
        pdf.cell(w2[4],  rh, _fmt(saldo_ant),     border=1, align="R")
        pdf.cell(w2[5],  rh, _fmt(cobranza),      border=1, align="R")
        pdf.cell(w2[6],  rh, _fmt(telec),         border=1, align="R")
        if saldo_neto <= 0.01:
            pdf.set_fill_color(198, 224, 180)
            pdf.cell(w2[7], rh, _fmt(saldo_neto), border=1, fill=True, align="R")
        else:
            pdf.cell(w2[7], rh, _fmt(saldo_neto), border=1, align="R")
        pdf.cell(w2[8],  rh, _fmt(ex),        border=1, align="R")
        pdf.cell(w2[9],  rh, _fmt(reserva),   border=1, align="R")
        pdf.cell(w2[10], rh, _fmt(redondeo),  border=1, align="R")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w2[11], rh, _fmt(total_pagar), border=1, align="R", ln=True)
        pdf.set_font("Helvetica", "", 9)
    pdf.ln(2); pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(sum(w2[:4]), rh, "TOTALES",  border=1, align="R")
    pdf.cell(w2[4],  rh, _fmt(ts_a),      border=1, align="R")
    pdf.cell(w2[5],  rh, _fmt(ts_co),     border=1, align="R")
    pdf.cell(w2[6],  rh, _fmt(ts_tel),    border=1, align="R")
    pdf.cell(w2[7],  rh, _fmt(ts_sn),     border=1, align="R")
    pdf.cell(w2[8],  rh, _fmt(ts_ex),     border=1, align="R")
    pdf.cell(w2[9],  rh, _fmt(ts_re),     border=1, align="R")
    pdf.cell(w2[10], rh, _fmt(ts_rd),     border=1, align="R")
    pdf.set_fill_color(255, 255, 0); pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w2[11], rh, _fmt(ts_tot),    border=1, fill=True, align="R", ln=True)

    return bytes(pdf.output())

# -- PDF BOLETA INDIVIDUAL (1 page, portrait) ---------------------------------

def _pdf_boleta(consorcio: dict, u: dict, gastos: list, saldo_ant: float, cobranza: float, telec: float, reserva: float, redondeo: float, periodo: str, cat_names: dict) -> bytes:
    rh = 6; lm = 15; pw = 180
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False, margin=10)
    pdf.add_page()
    nom  = consorcio.get("nombre", "")
    dire = consorcio.get("direccion", "")
    dia_vto = int(consorcio.get("dia_vto") or 10)
    vto = _vto(periodo, dia_vto)
    ca, cb, cc = _tf(u["coef_a"]), _tf(u["coef_b"]), _tf(u["coef_c"])
    tot_a = sum(_tf(g["monto"]) for g in gastos if g["categoria"] == "A")
    tot_b = sum(_tf(g["monto"]) for g in gastos if g["categoria"] == "B")
    tot_c = sum(_tf(g["monto"]) for g in gastos if g["categoria"] == "C")
    imp_mes    = tot_a * ca / 100.0 + tot_b * cb / 100.0 + tot_c * cc / 100.0
    saldo_neto = max(0.0, saldo_ant - cobranza - telec)
    total_pagar = imp_mes + saldo_neto + reserva + redondeo
    nombre_u = u.get("propietario") or u.get("inquilino") or ""

    y0 = 10
    pdf.rect(lm, y0, pw, 13)
    pdf.set_xy(lm + 2, y0 + 1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(pw - 2, 5, "Administracion de Consorcios   Jorge Eduardo Da Ros", ln=True)
    pdf.set_x(lm + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(110, 5, "San Lorenzo 2657  Dpto 6  (1651) San Andres, Bs As")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(68, 5, "Cel: 11 36636072", align="R", ln=True)

    pdf.set_y(y0 + 17); pdf.set_x(lm)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(pw - 40, 7, "CONSORCIO: " + nom.upper(), border=1)
    pdf.cell(40, 7, "Vto: " + vto, border=1, align="C", ln=True)
    pdf.set_x(lm)
    pdf.cell(pw - 40, 7, dire.upper() if dire else "", border=1)
    pdf.cell(40, 7, periodo, border=1, align="C", ln=True)
    pdf.ln(3)

    pdf.set_x(lm); pdf.set_font("Helvetica", "B", 10)
    unit_str = "UNIDAD: " + str(u.get("unidad","")) + "   PISO: " + str(u.get("piso","")) + "   DPTO: " + str(u.get("dpto","")) + "   " + nombre_u[:40]
    pdf.cell(pw, 8, unit_str, border=1, ln=True)
    pdf.ln(4)

    pdf.set_x(lm); pdf.set_fill_color(230, 230, 230); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(18,  rh, "Cat.",                  border=1, fill=True, align="C")
    pdf.cell(117, rh, "Descripcion del Gasto", border=1, fill=True, align="C")
    pdf.cell(45,  rh, "Importe",               border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)

    for cat_key, coef in [("A", ca), ("B", cb), ("C", cc)]:
        cat_gs = [g for g in gastos if g["categoria"] == cat_key]
        if not cat_gs: continue
        sub_imp = 0.0
        for g in cat_gs:
            importe = _tf(g["monto"]) * coef / 100.0; sub_imp += importe
            gdesc = str(g.get("descripcion") or "")
            pdf.set_x(lm)
            pdf.cell(18,  rh, cat_key, border=1, align="C")
            pdf.cell(117, rh, "  " + gdesc[:52], border=1)
            pdf.cell(45,  rh, _fmt(importe), border=1, align="R", ln=True)
        cat_lbl = "  Subtotal " + cat_key + " - " + cat_names.get(cat_key, cat_key)
        pdf.set_x(lm); pdf.set_font("Helvetica", "B", 9)
        pdf.cell(135, rh, cat_lbl, border=1, align="R")
        pdf.cell(45,  rh, _fmt(sub_imp), border=1, align="R", ln=True)
        pdf.set_font("Helvetica", "", 9)

    pdf.ln(4)
    cw1, cw2 = 110, 70

    def _row(label, valor, bold=False, fill=False):
        pdf.set_x(lm)
        pdf.set_font("Helvetica", "B" if bold else "", 11 if bold else 10)
        if fill: pdf.set_fill_color(255, 255, 0)
        h = rh + (2 if bold else 0)
        pdf.cell(cw1, h, label, border=1, align="R", fill=fill)
        pdf.cell(cw2, h, "$ " + _fmt(valor), border=1, align="R", fill=fill, ln=True)

    _row("Expensas del Mes:", imp_mes)
    if saldo_ant  > 0.001: _row("Saldo Anterior:", saldo_ant)
    if cobranza   > 0.001: _row("Cobranza Recibida:", cobranza)
    if telec      > 0.001: _row("Telec / Vs:", telec)
    if saldo_ant  > 0.001 and (cobranza > 0.001 or telec > 0.001): _row("Saldo Neto:", saldo_neto)
    if reserva    > 0.001: _row("Reserva:", reserva)
    if abs(redondeo) > 0.001: _row("Redondeo:", redondeo)
    _row("TOTAL A PAGAR:", total_pagar, bold=True, fill=True)

    return bytes(pdf.output())

# -- data helpers -------------------------------------------------------------

def _load_pagos(db, cid: int, periodo: str):
    per_a    = _pa_of(periodo)
    uid_list = [u["id"] for u in db.execute("SELECT id FROM unidades WHERE consorcio_id=?", (cid,)).fetchall()]
    if not uid_list:
        return {}, {}
    ph   = ",".join("?" * len(uid_list))
    rows = db.execute(
        f"SELECT * FROM pagos WHERE periodo IN (?,?) AND unidad_id IN ({ph})",
        [per_a, periodo] + uid_list
    ).fetchall()
    p_ant = {p["unidad_id"]: dict(p) for p in rows if p["periodo"] == per_a}
    p_act = {p["unidad_id"]: dict(p) for p in rows if p["periodo"] == periodo}
    return p_ant, p_act


# -- endpoints ----------------------------------------------------------------

@router.get("/reportes/general/{consorcio_id}/{periodo}")
def reporte_general(consorcio_id: int, periodo: str, db: sqlite3.Connection = Depends(get_db)):
    import traceback
    cons = db.execute("SELECT * FROM consorcios WHERE id=?", (consorcio_id,)).fetchone()
    if not cons:
        raise HTTPException(404, "Consorcio no encontrado")
    unis   = db.execute("SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (consorcio_id,)).fetchall()
    gastos = db.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=? ORDER BY categoria, descripcion", (consorcio_id, periodo)).fetchall()
    pagos_ant, pagos_act = _load_pagos(db, consorcio_id, periodo)
    cat_names = {
        "A": _get_cfg(db, "nombre_cat_a", "Gastos Comunes"),
        "B": _get_cfg(db, "nombre_cat_b", "Fuerza Motriz"),
        "C": _get_cfg(db, "nombre_cat_c", "Locales"),
    }
    try:
        pdf_bytes = _pdf_general(
            dict(cons), [dict(u) for u in unis], [dict(g) for g in gastos],
            pagos_ant, pagos_act, periodo, cat_names
        )
        nom      = (cons["nombre"] or "consorcio").replace(" ", "_")
        filename = f"General_{nom}_{periodo}.pdf"
        path = _save_pdf(pdf_bytes, filename)
        return {"path": path, "filename": filename}
    except Exception as e:
        raise HTTPException(500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


@router.get("/reportes/boleta/{unidad_id}/{periodo}")
def reporte_boleta(unidad_id: int, periodo: str, db: sqlite3.Connection = Depends(get_db)):
    import traceback
    u = db.execute("SELECT * FROM unidades WHERE id=?", (unidad_id,)).fetchone()
    if not u:
        raise HTTPException(404, "Unidad no encontrada")
    cons   = db.execute("SELECT * FROM consorcios WHERE id=?", (u["consorcio_id"],)).fetchone()
    gastos = db.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=? ORDER BY categoria, descripcion", (u["consorcio_id"], periodo)).fetchall()
    pagos_ant, pagos_act = _load_pagos(db, u["consorcio_id"], periodo)
    pa = pagos_ant.get(unidad_id, {}); pc = pagos_act.get(unidad_id, {})
    saldo_ant = max(0.0, _tf(pa.get("monto_deuda", 0.0))) if pa else _tf(pc.get("saldo_inicial", 0.0))
    cobranza  = _tf(pc.get("monto_recibido", 0.0))
    telec     = _tf(pc.get("telec", 0.0))
    reserva   = _tf(pc.get("reserva", 0.0))
    redondeo  = _tf(pc.get("redondeo", 0.0))
    cat_names = {
        "A": _get_cfg(db, "nombre_cat_a", "Gastos Comunes"),
        "B": _get_cfg(db, "nombre_cat_b", "Fuerza Motriz"),
        "C": _get_cfg(db, "nombre_cat_c", "Locales"),
    }
    try:
        pdf_bytes = _pdf_boleta(
            dict(cons), dict(u), [dict(g) for g in gastos],
            saldo_ant, cobranza, telec, reserva, redondeo, periodo, cat_names
        )
        nombre_u = (u.get("propietario") or u.get("inquilino") or "UF" + str(u["unidad"])).replace(" ", "_")
        filename = f"UF{u['unidad']}_{nombre_u}_{periodo}.pdf"
        path = _save_pdf(pdf_bytes, filename)
        return {"path": path, "filename": filename}
    except Exception as e:
        raise HTTPException(500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
