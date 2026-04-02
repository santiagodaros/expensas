"""
Gestor de Consorcios - PDF Generation Module
All PDF generation functions: consorcio, boletas, email.
"""
from fpdf import FPDF
from gestor.helpers import _tf, _fmt
from gestor.db import get_cfg

# ===== GENERACION DE PDF ESTILO EXCEL =====
def _encabezado_admin(pdf):
    y_start = pdf.get_y()
    pdf.rect(10, y_start, 277, 14)
    pdf.set_xy(12, y_start + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(150, 5, "Administracion de Consorcios   Jorge Eduardo Da Ros", align="L", ln=True)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(150, 5, "San Lorenzo 2657   Dpto 6   (1651) San Andres,  Bs As", align="L")
    pdf.set_xy(190, y_start + 7)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(20, 5, "Celular", align="L")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(30, 5, "11 36636072", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(20, 5, "Movistar", align="R", ln=True)
    pdf.set_y(y_start + 18)

def _encabezado_pagina(pdf, titulo, periodo, vto_date, nombre_cons, dir_cons):
    _encabezado_admin(pdf)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(150, 7, f"CONSORCIO DE PROPIETARIOS {nombre_cons}  {dir_cons}".upper(), border=1)
    pdf.cell(87, 7, "", border=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(40, 7, f"Vto ..... {vto_date}", border=1, align="C", ln=True)
    pdf.ln(3)
    pdf.set_x(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(70, 7, titulo, border=0)
    pdf.set_fill_color(255, 242, 204)
    pdf.cell(25, 7, periodo, border=1, fill=True, align="C", ln=True)
    pdf.ln(3)

def generar_pdf_consorcio(consorcio, unis, gastos_rows, pagos_map, deudas_map, cobranza_map, saldo_ini_map, telec_map, periodo, progress_cb=None):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=8)

    tot_a = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "A")
    tot_b = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "B")
    tot_c = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "C")

    _y, _m = int(periodo[:4]), int(periodo[5:])
    _m_vto = _m + 1 if _m < 12 else 1
    _y_vto = _y if _m < 12 else _y + 1
    _dia_vto = int(consorcio.get("dia_vto") or 10)
    vto_date = f"{_dia_vto}/{_m_vto}/{_y_vto}"
    nom_a = get_cfg("nombre_cat_a", "Gastos Comunes")
    nom_b = get_cfg("nombre_cat_b", "Fuerza Motriz")
    nom_c = get_cfg("nombre_cat_c", "Locales")
    _cat_names = {"A": nom_a, "B": nom_b, "C": nom_c}
    nombre_cons = consorcio.get("nombre", ""); dir_cons = consorcio.get("direccion", "")
    rh = 6

    # ---- PAGINA 1: LIQUIDACION DE GASTOS ----------------------------------
    pdf.add_page()
    _encabezado_pagina(pdf, "Liquidacion de Gastos Expensas", periodo, vto_date, nombre_cons, dir_cons)
    w_g = [27, 200, 50]
    pdf.set_x(10); pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(230, 230, 230)
    pdf.cell(w_g[0], rh, "Cat.", border=1, fill=True, align="C")
    pdf.cell(w_g[1], rh, "Descripcion del Gasto", border=1, fill=True, align="C")
    pdf.cell(w_g[2], rh, "Monto", border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    current_cat = None; sub = 0.0
    for g in sorted(gastos_rows, key=lambda x: x["categoria"] or ""):
        cat = g["categoria"] or ""; monto_gasto = _tf(g["monto"])
        if cat != current_cat:
            if current_cat is not None:
                pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
                pdf.cell(w_g[0]+w_g[1], rh, f"Subtotal {current_cat} - {_cat_names.get(current_cat, current_cat)}", border=1, align="R")
                pdf.cell(w_g[2], rh, _fmt(sub), border=1, align="R", ln=True)
                pdf.set_font("Helvetica", "", 9)
            current_cat = cat; sub = 0.0
        sub += monto_gasto
        pdf.set_x(10)
        pdf.cell(w_g[0], rh, cat, border=1, align="C")
        pdf.cell(w_g[1], rh, f"  {g.get('descripcion') or ''}", border=1, align="L")
        pdf.cell(w_g[2], rh, _fmt(monto_gasto), border=1, align="R", ln=True)
    if current_cat is not None:
        pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w_g[0]+w_g[1], rh, f"Subtotal Categoria {current_cat}", border=1, align="R")
        pdf.cell(w_g[2], rh, _fmt(sub), border=1, align="R", ln=True)
    pdf.ln(2); pdf.set_x(10)
    total_gastos = tot_a + tot_b + tot_c
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w_g[0]+w_g[1], rh, "TOTAL GENERAL DE GASTOS", border=1, align="R")
    pdf.set_fill_color(255, 255, 0)
    pdf.cell(w_g[2], rh, _fmt(total_gastos), border=1, fill=True, align="R", ln=True)

    # ---- PAGINA 2: PRORRATEO ----------------------------------------------
    pdf.add_page()
    _encabezado_pagina(pdf, "Prorrateo de gastos expensas", periodo, vto_date, nombre_cons, dir_cons)
    w1 = [13, 13, 14, 63, 19, 23, 23, 27, 27, 27, 28]
    pdf.set_x(10); pdf.set_fill_color(230, 230, 230); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w1[0]+w1[1]+w1[2]+w1[3], rh, "", border=0)
    pdf.cell(w1[4], rh, "Locales",       border=1, fill=True, align="C")
    pdf.cell(w1[5], rh, "Fuerza motriz", border=1, fill=True, align="C")
    pdf.cell(w1[6], rh, "Exp con todos", border=1, fill=True, align="C")
    pdf.cell(w1[7], rh, "A", border=1, fill=True, align="C")
    pdf.cell(w1[8], rh, "B", border=1, fill=True, align="C")
    pdf.cell(w1[9], rh, "C", border=1, fill=True, align="C")
    pdf.cell(w1[10],rh, "TOTAL", border=1, fill=True, align="C", ln=True)
    pdf.set_x(10)
    pdf.cell(w1[0], rh, "Piso",             border=1, fill=True, align="C")
    pdf.cell(w1[1], rh, "Dpto",             border=1, fill=True, align="C")
    pdf.cell(w1[2], rh, "U.F.",             border=1, fill=True, align="C")
    pdf.cell(w1[3], rh, "Nombre y Apellido",border=1, fill=True, align="C")
    pdf.cell(w1[4], rh, "B", border=1, fill=True, align="C")
    pdf.cell(w1[5], rh, "C", border=1, fill=True, align="C")
    pdf.cell(w1[6], rh, "A", border=1, fill=True, align="C")
    pdf.cell(w1[7], rh, "A", border=1, fill=True, align="C")
    pdf.cell(w1[8], rh, "B", border=1, fill=True, align="C")
    pdf.cell(w1[9], rh, "C", border=1, fill=True, align="C")
    pdf.cell(w1[10],rh, "Expensas", border=1, fill=True, align="C", ln=True)
    tot_ca = tot_cb = tot_cc = 0.0; tot_ia = tot_ib = tot_ic = tot_ex = 0.0
    pdf.set_font("Helvetica", "", 9)
    for u in unis:
        ca, cb, cc = _tf(u["coef_a"]), _tf(u["coef_b"]), _tf(u["coef_c"])
        tot_ca += ca; tot_cb += cb; tot_cc += cc
        ia = tot_a * ca / 100.0; ib = tot_b * cb / 100.0; ic = tot_c * cc / 100.0
        ex = ia + ib + ic
        tot_ia += ia; tot_ib += ib; tot_ic += ic; tot_ex += ex
        nom = u.get("propietario") or u.get("inquilino") or ""
        pdf.set_x(10)
        pdf.cell(w1[0], rh, u.get("piso", ""), border=1, align="C")
        pdf.cell(w1[1], rh, u.get("dpto", ""), border=1, align="C")
        pdf.cell(w1[2], rh, u["unidad"],        border=1, align="C")
        pdf.cell(w1[3], rh, f" {nom[:32]}",     border=1, align="L")
        pdf.cell(w1[4], rh, f"{_fmt(cb)}%", border=1, align="R")
        pdf.cell(w1[5], rh, f"{_fmt(cc)}%", border=1, align="R")
        pdf.cell(w1[6], rh, f"{_fmt(ca)}%", border=1, align="R")
        pdf.cell(w1[7], rh, _fmt(ia), border=1, align="R")
        pdf.cell(w1[8], rh, _fmt(ib), border=1, align="R")
        pdf.cell(w1[9], rh, _fmt(ic), border=1, align="R")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w1[10], rh, _fmt(ex), border=1, align="R", ln=True)
        pdf.set_font("Helvetica", "", 9)
    pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w1[0]+w1[1]+w1[2]+w1[3], rh, "TOTALES", border=1, align="R")
    pdf.cell(w1[4], rh, f"{_fmt(tot_cb)}%", border=1, align="R")
    pdf.cell(w1[5], rh, f"{_fmt(tot_cc)}%", border=1, align="R")
    pdf.cell(w1[6], rh, f"{_fmt(tot_ca)}%", border=1, align="R")
    pdf.cell(w1[7], rh, _fmt(tot_ia), border=1, align="R")
    pdf.cell(w1[8], rh, _fmt(tot_ib), border=1, align="R")
    pdf.cell(w1[9], rh, _fmt(tot_ic), border=1, align="R")
    pdf.set_fill_color(255, 255, 0); pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w1[10], rh, _fmt(tot_ex), border=1, fill=True, align="R", ln=True)

    # ---- PAGINA 3: ESTADO DE RECAUDACION ----------------------------------
    pdf.add_page()
    _encabezado_pagina(pdf, "Recaudacion y expensas", periodo, vto_date, nombre_cons, dir_cons)
    w2 = [13, 13, 14, 50, 24, 24, 18, 24, 26, 20, 18, 33]  # 277mm total
    pdf.set_x(10); pdf.set_fill_color(230, 230, 230); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w2[0]+w2[1]+w2[2]+w2[3]+w2[4], rh, "", border=0)
    pdf.cell(w2[5]+w2[6], rh, "COBRANZA", border=1, fill=True, align="C")
    pdf.cell(w2[7]+w2[8]+w2[9]+w2[10]+w2[11], rh, "", border=0, ln=True)
    pdf.set_x(10)
    pdf.cell(w2[0],  rh, "Piso",            border=1, fill=True, align="C")
    pdf.cell(w2[1],  rh, "Dpto",            border=1, fill=True, align="C")
    pdf.cell(w2[2],  rh, "U.F.",            border=1, fill=True, align="C")
    pdf.cell(w2[3],  rh, "Nombre y Apellido",border=1, fill=True, align="C")
    pdf.cell(w2[4],  rh, "Saldo",           border=1, fill=True, align="C")
    pdf.cell(w2[5],  rh, "Mes Ant",         border=1, fill=True, align="C")
    pdf.cell(w2[6],  rh, "Telec / Vs",      border=1, fill=True, align="C")
    pdf.cell(w2[7],  rh, "SALDO",           border=1, fill=True, align="C")
    pdf.cell(w2[8],  rh, "Expensas",        border=1, fill=True, align="C")
    pdf.cell(w2[9],  rh, "Reserva",         border=1, fill=True, align="C")
    pdf.cell(w2[10], rh, "Redondeo",        border=1, fill=True, align="C")
    pdf.cell(w2[11], rh, "TOTAL PAGO",      border=1, fill=True, align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    t_saldo_ant = t_cobranza = t_saldo_act = t_expensas = t_reserva = t_redondeo = t_total = 0.0
    for i_u, u in enumerate(unis):
        if progress_cb: progress_cb(i_u + 1, u.get("propietario") or u.get("inquilino") or f"UF{u['unidad']}")
        uid = u["id"]
        ca, cb, cc = _tf(u["coef_a"]), _tf(u["coef_b"]), _tf(u["coef_c"])
        ex = (tot_a * ca / 100.0) + (tot_b * cb / 100.0) + (tot_c * cc / 100.0)
        if ex == 0: ex = _tf(pagos_map.get(uid, {}).get("imp_mes_override") or 0)
        saldo_ant = _tf(deudas_map.get(uid, saldo_ini_map.get(uid, 0.0)))
        cobranza  = _tf(cobranza_map.get(uid, 0.0))
        telec     = _tf(telec_map.get(uid, 0.0))
        reserva   = _tf(pagos_map.get(uid, {}).get("reserva", 0.0))
        redondeo  = _tf(pagos_map.get(uid, {}).get("redondeo", 0.0))
        saldo_neto   = max(0.0, saldo_ant - cobranza - telec)
        total_pagar  = saldo_neto + ex + reserva + redondeo
        t_saldo_ant += saldo_ant; t_cobranza += cobranza; t_saldo_act += saldo_neto
        t_expensas += ex; t_reserva += reserva; t_redondeo += redondeo; t_total += total_pagar
        nom = u.get("propietario") or u.get("inquilino") or ""
        pdf.set_x(10)
        pdf.cell(w2[0],  rh, u.get("piso", ""),  border=1, align="C")
        pdf.cell(w2[1],  rh, u.get("dpto", ""),  border=1, align="C")
        pdf.cell(w2[2],  rh, u["unidad"],         border=1, align="C")
        pdf.cell(w2[3],  rh, f" {nom[:26]}",      border=1, align="L")
        pdf.cell(w2[4],  rh, _fmt(saldo_ant),     border=1, align="R")
        pdf.cell(w2[5],  rh, _fmt(cobranza),      border=1, align="R")
        pdf.cell(w2[6],  rh, _fmt(telec),         border=1, align="R")
        if saldo_neto <= 0.01:
            pdf.set_fill_color(198, 224, 180)
            pdf.cell(w2[7], rh, _fmt(saldo_neto), border=1, fill=True, align="R")
        else:
            pdf.cell(w2[7], rh, _fmt(saldo_neto), border=1, align="R")
        pdf.cell(w2[8],  rh, _fmt(ex),       border=1, align="R")
        pdf.cell(w2[9],  rh, _fmt(reserva),  border=1, align="R")
        pdf.cell(w2[10], rh, _fmt(redondeo), border=1, align="R")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w2[11], rh, _fmt(total_pagar), border=1, align="R", ln=True)
        pdf.set_font("Helvetica", "", 9)
    pdf.ln(2); pdf.set_x(10); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w2[0]+w2[1]+w2[2]+w2[3], rh, "TOTALES", border=1, align="R")
    pdf.cell(w2[4],  rh, _fmt(t_saldo_ant), border=1, align="R")
    pdf.cell(w2[5],  rh, _fmt(t_cobranza),  border=1, align="R")
    pdf.cell(w2[6],  rh, "0,00",            border=1, align="R")
    pdf.cell(w2[7],  rh, _fmt(t_saldo_act), border=1, align="R")
    pdf.cell(w2[8],  rh, _fmt(t_expensas),  border=1, align="R")
    pdf.cell(w2[9],  rh, _fmt(t_reserva),   border=1, align="R")
    pdf.cell(w2[10], rh, _fmt(t_redondeo),  border=1, align="R")
    pdf.set_fill_color(255, 255, 0); pdf.set_font("Helvetica", "B", 10)
    pdf.cell(w2[11], rh, _fmt(t_total), border=1, fill=True, align="R", ln=True)
    return pdf

# ===== BOLETA INDIVIDUAL POR UNIDAD (PORTRAIT A4) ==========================
def generar_pdf_boletas(consorcio, unis, gastos_rows, pagos_map, deudas_map, cobranza_map, saldo_ini_map, telec_map, periodo):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False, margin=10)

    tot_a = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "A")
    tot_b = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "B")
    tot_c = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "C")

    _y, _m = int(periodo[:4]), int(periodo[5:])
    _m_vto = _m + 1 if _m < 12 else 1
    _y_vto = _y if _m < 12 else _y + 1
    _dia_vto = int(consorcio.get("dia_vto") or 10)
    vto_date = f"{_dia_vto}/{_m_vto}/{_y_vto}"
    nom_a = get_cfg("nombre_cat_a", "Gastos Comunes")
    nom_b = get_cfg("nombre_cat_b", "Fuerza Motriz")
    nom_c = get_cfg("nombre_cat_c", "Locales")
    _cat_names_b = {"A": nom_a, "B": nom_b, "C": nom_c}
    nombre_cons = consorcio.get("nombre", "")
    dir_cons    = consorcio.get("direccion", "")
    lm = 15; pw = 180; rh = 6

    for u in unis:
        uid = u["id"]
        ca, cb, cc = _tf(u["coef_a"]), _tf(u["coef_b"]), _tf(u["coef_c"])
        imp_mes    = tot_a * ca / 100.0 + tot_b * cb / 100.0 + tot_c * cc / 100.0
        if imp_mes == 0: imp_mes = _tf(pagos_map.get(uid, {}).get("imp_mes_override") or 0)
        saldo_ant  = _tf(deudas_map.get(uid, saldo_ini_map.get(uid, 0.0)))
        cobranza   = _tf(cobranza_map.get(uid, 0.0))
        telec      = _tf(telec_map.get(uid, 0.0))
        saldo_neto = max(0.0, saldo_ant - cobranza - telec)
        reserva    = _tf(pagos_map.get(uid, {}).get("reserva", 0.0))
        redondeo   = _tf(pagos_map.get(uid, {}).get("redondeo", 0.0))
        total_pagar = imp_mes + saldo_neto + reserva + redondeo
        nom = u.get("propietario") or u.get("inquilino") or ""

        pdf.add_page()
        pdf.set_text_color(0, 0, 0)

        # Admin header
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

        # Consorcio header
        pdf.set_y(y0 + 17)
        pdf.set_x(lm)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(pw - 40, 7, f"CONSORCIO: {nombre_cons}".upper(), border=1)
        pdf.cell(40, 7, f"Vto: {vto_date}", border=1, align="C", ln=True)
        pdf.set_x(lm)
        pdf.cell(pw - 40, 7, dir_cons.upper() if dir_cons else "", border=1)
        pdf.cell(40, 7, periodo, border=1, align="C", ln=True)

        pdf.ln(3)

        # Unit info
        pdf.set_x(lm)
        pdf.set_font("Helvetica", "B", 10)
        unit_str = (f"UNIDAD: {u.get('unidad','')}   PISO: {u.get('piso','')}   "
                    f"DPTO: {u.get('dpto','')}   {nom[:40]}")
        pdf.cell(pw, 8, unit_str, border=1, ln=True)

        pdf.ln(4)

        # Expenses header
        pdf.set_x(lm)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(18, rh, "Cat.", border=1, fill=True, align="C")
        pdf.cell(117, rh, "Descripcion del Gasto", border=1, fill=True, align="C")
        pdf.cell(45, rh, "Importe", border=1, fill=True, align="C", ln=True)

        # Expenses rows by category
        pdf.set_font("Helvetica", "", 9)
        for cat_key, coef in [("A", ca), ("B", cb), ("C", cc)]:
            cat_gs = [g for g in gastos_rows if g["categoria"] == cat_key]
            if not cat_gs:
                continue
            sub_imp = 0.0
            for g in cat_gs:
                importe = _tf(g["monto"]) * coef / 100.0
                sub_imp += importe
                pdf.set_x(lm)
                pdf.cell(18, rh, cat_key, border=1, align="C")
                pdf.cell(117, rh, f"  {str(g.get('descripcion') or '')[:52]}", border=1, align="L")
                pdf.cell(45, rh, _fmt(importe), border=1, align="R", ln=True)
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(135, rh, f"  Subtotal {cat_key} - {_cat_names_b.get(cat_key, cat_key)}", border=1, align="R")
            pdf.cell(45, rh, _fmt(sub_imp), border=1, align="R", ln=True)
            pdf.set_font("Helvetica", "", 9)

        pdf.ln(4)

        # Totals
        cw1, cw2 = 110, 70

        def _tot_row(label, valor, bold=False, fill=False):
            pdf.set_x(lm)
            pdf.set_font("Helvetica", "B" if bold else "", 11 if bold else 10)
            if fill:
                pdf.set_fill_color(255, 255, 0)
            h_row = rh + (2 if bold else 0)
            pdf.cell(cw1, h_row, label, border=1, align="R", fill=fill)
            pdf.cell(cw2, h_row, f"$ {_fmt(valor)}", border=1, align="R", fill=fill, ln=True)

        _tot_row("Expensas del Mes:", imp_mes)
        if saldo_ant > 0.001:
            _tot_row("Saldo Anterior:", saldo_ant)
        if cobranza > 0.001:
            _tot_row("Cobranza Recibida:", cobranza)
        if telec > 0.001:
            _tot_row("Telec / Vs:", telec)
        if saldo_ant > 0.001 and (cobranza > 0.001 or telec > 0.001):
            _tot_row("Saldo Neto:", saldo_neto)
        if reserva > 0.001:
            _tot_row("Reserva:", reserva)
        if abs(redondeo) > 0.001:
            _tot_row("Redondeo:", redondeo)
        _tot_row("TOTAL A PAGAR:", total_pagar, bold=True, fill=True)

    return pdf

# ===== PDF COMPLETO PARA EMAIL (boleta + prorrateo + recaudacion) ===========
def generar_pdf_email_unidad(target_uid, consorcio, unis, gastos_rows, pagos_map,
                              deudas_map, cobranza_map, saldo_ini_map, telec_map, periodo):
    """PDF de 3 paginas: boleta individual (portrait) + prorrateo + recaudacion (landscape)."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False, margin=10)

    tot_a = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "A")
    tot_b = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "B")
    tot_c = sum(_tf(g["monto"]) for g in gastos_rows if g["categoria"] == "C")
    _y, _m = int(periodo[:4]), int(periodo[5:])
    _m_vto = _m + 1 if _m < 12 else 1
    _y_vto = _y if _m < 12 else _y + 1
    _dia_vto = int(consorcio.get("dia_vto") or 10)
    vto_date  = f"{_dia_vto}/{_m_vto}/{_y_vto}"
    nom_a = get_cfg("nombre_cat_a", "Gastos Comunes")
    nom_b = get_cfg("nombre_cat_b", "Fuerza Motriz")
    nom_c = get_cfg("nombre_cat_c", "Locales")
    _cn  = {"A": nom_a, "B": nom_b, "C": nom_c}
    nombre_cons = consorcio.get("nombre", ""); dir_cons = consorcio.get("direccion", "")
    lm = 15; pw = 267; rh = 6

    # ---- PAGINA 1: BOLETA INDIVIDUAL (landscape) ----------------------------
    u_list = [u for u in unis if u["id"] == target_uid]
    for u in u_list:
        uid = u["id"]
        ca, cb, cc = _tf(u["coef_a"]), _tf(u["coef_b"]), _tf(u["coef_c"])
        imp_mes    = tot_a*ca/100.0 + tot_b*cb/100.0 + tot_c*cc/100.0
        if imp_mes == 0: imp_mes = _tf(pagos_map.get(uid, {}).get("imp_mes_override") or 0)
        saldo_ant  = _tf(deudas_map.get(uid, saldo_ini_map.get(uid, 0.0)))
        cobranza   = _tf(cobranza_map.get(uid, 0.0))
        telec      = _tf(telec_map.get(uid, 0.0))
        saldo_neto = max(0.0, saldo_ant - cobranza - telec)
        reserva    = _tf(pagos_map.get(uid, {}).get("reserva", 0.0))
        redondeo   = _tf(pagos_map.get(uid, {}).get("redondeo", 0.0))
        total_pagar = imp_mes + saldo_neto + reserva + redondeo
        nom = u.get("propietario") or u.get("inquilino") or ""
        pdf.add_page(orientation="L")
        pdf.set_text_color(0, 0, 0)
        y0 = 10
        pdf.rect(lm, y0, pw, 13)
        pdf.set_xy(lm+2, y0+1); pdf.set_font("Helvetica","B",10)
        pdf.cell(pw-2, 5, "Administracion de Consorcios   Jorge Eduardo Da Ros", ln=True)
        pdf.set_x(lm+2); pdf.set_font("Helvetica","",9)
        pdf.cell(110, 5, "San Lorenzo 2657  Dpto 6  (1651) San Andres, Bs As")
        pdf.set_font("Helvetica","B",10); pdf.cell(68, 5, "Cel: 11 36636072", align="R", ln=True)
        pdf.set_y(y0+17); pdf.set_x(lm); pdf.set_font("Helvetica","B",10)
        pdf.cell(pw-40, 7, f"CONSORCIO: {nombre_cons}".upper(), border=1)
        pdf.cell(40, 7, f"Vto: {vto_date}", border=1, align="C", ln=True)
        pdf.set_x(lm); pdf.cell(pw-40, 7, dir_cons.upper() if dir_cons else "", border=1)
        pdf.cell(40, 7, periodo, border=1, align="C", ln=True)
        pdf.ln(3); pdf.set_x(lm); pdf.set_font("Helvetica","B",10)
        pdf.cell(pw, 8, f"UNIDAD: {u.get('unidad','')}   PISO: {u.get('piso','')}   DPTO: {u.get('dpto','')}   {nom[:40]}", border=1, ln=True)
        wcat, wdesc, wimp = 18, pw-63, 45
        pdf.ln(4); pdf.set_x(lm); pdf.set_fill_color(230,230,230); pdf.set_font("Helvetica","B",9)
        pdf.cell(wcat,  rh, "Cat.", border=1, fill=True, align="C")
        pdf.cell(wdesc, rh, "Descripcion del Gasto", border=1, fill=True, align="C")
        pdf.cell(wimp,  rh, "Importe", border=1, fill=True, align="C", ln=True)
        pdf.set_font("Helvetica","",9)
        for cat_key, coef in [("A",ca),("B",cb),("C",cc)]:
            cat_gs = [g for g in gastos_rows if g["categoria"] == cat_key]
            if not cat_gs: continue
            sub_imp = 0.0
            for g in cat_gs:
                importe = _tf(g["monto"]) * coef / 100.0; sub_imp += importe
                pdf.set_x(lm); pdf.cell(wcat, rh, cat_key, border=1, align="C")
                pdf.cell(wdesc, rh, f"  {str(g.get('descripcion') or '')[:80]}", border=1, align="L")
                pdf.cell(wimp,  rh, _fmt(importe), border=1, align="R", ln=True)
            pdf.set_x(lm); pdf.set_font("Helvetica","B",9)
            pdf.cell(wcat+wdesc, rh, f"  Subtotal {cat_key} - {_cn.get(cat_key,cat_key)}", border=1, align="R")
            pdf.cell(wimp, rh, _fmt(sub_imp), border=1, align="R", ln=True)
            pdf.set_font("Helvetica","",9)
        pdf.ln(4)
        cw1, cw2 = pw-70, 70
        def _tr(label, valor, bold=False, fill=False, _pdf=pdf):
            _pdf.set_x(lm); _pdf.set_font("Helvetica","B" if bold else "",11 if bold else 10)
            if fill: _pdf.set_fill_color(255,255,0)
            h_r = rh + (2 if bold else 0)
            _pdf.cell(cw1, h_r, label, border=1, align="R", fill=fill)
            _pdf.cell(cw2, h_r, f"$ {_fmt(valor)}", border=1, align="R", fill=fill, ln=True)
        _tr("Expensas del Mes:", imp_mes)
        if saldo_ant > 0.001: _tr("Saldo Anterior:", saldo_ant)
        if cobranza  > 0.001: _tr("Cobranza Recibida:", cobranza)
        if telec     > 0.001: _tr("Telec / Vs:", telec)
        if saldo_ant > 0.001 and (cobranza > 0.001 or telec > 0.001): _tr("Saldo Neto:", saldo_neto)
        if reserva   > 0.001: _tr("Reserva:", reserva)
        if abs(redondeo) > 0.001: _tr("Redondeo:", redondeo)
        _tr("TOTAL A PAGAR:", total_pagar, bold=True, fill=True)

    # ---- PAGINA 2: PRORRATEO (landscape) ------------------------------------
    pdf.add_page(orientation="L")
    _encabezado_pagina(pdf, "Prorrateo de gastos expensas", periodo, vto_date, nombre_cons, dir_cons)
    w1 = [13,13,14,63,19,23,23,27,27,27,28]
    pdf.set_x(10); pdf.set_fill_color(230,230,230); pdf.set_font("Helvetica","B",9)
    pdf.cell(w1[0]+w1[1]+w1[2]+w1[3], rh, "", border=0)
    pdf.cell(w1[4], rh, "Locales",       border=1, fill=True, align="C")
    pdf.cell(w1[5], rh, "Fuerza motriz", border=1, fill=True, align="C")
    pdf.cell(w1[6], rh, "Exp con todos", border=1, fill=True, align="C")
    pdf.cell(w1[7], rh, "A", border=1, fill=True, align="C")
    pdf.cell(w1[8], rh, "B", border=1, fill=True, align="C")
    pdf.cell(w1[9], rh, "C", border=1, fill=True, align="C")
    pdf.cell(w1[10],rh, "TOTAL", border=1, fill=True, align="C", ln=True)
    pdf.set_x(10)
    for lbl in ["Piso","Dpto","U.F.","Nombre y Apellido"]:
        pdf.cell(w1[["Piso","Dpto","U.F.","Nombre y Apellido"].index(lbl)], rh, lbl, border=1, fill=True, align="C")
    for lbl,wi in [("B",w1[4]),("C",w1[5]),("A",w1[6]),("A",w1[7]),("B",w1[8]),("C",w1[9]),("Expensas",w1[10])]:
        pdf.cell(wi, rh, lbl, border=1, fill=True, align="C")
    pdf.ln()
    tot_ca=tot_cb=tot_cc=tot_ia=tot_ib=tot_ic=tot_ex=0.0
    pdf.set_font("Helvetica","",9)
    for u in unis:
        ca,cb,cc = _tf(u["coef_a"]),_tf(u["coef_b"]),_tf(u["coef_c"])
        tot_ca+=ca; tot_cb+=cb; tot_cc+=cc
        ia=tot_a*ca/100.0; ib=tot_b*cb/100.0; ic=tot_c*cc/100.0; ex=ia+ib+ic
        tot_ia+=ia; tot_ib+=ib; tot_ic+=ic; tot_ex+=ex
        nom = u.get("propietario") or u.get("inquilino") or ""
        pdf.set_x(10)
        pdf.cell(w1[0],rh,u.get("piso",""),border=1,align="C")
        pdf.cell(w1[1],rh,u.get("dpto",""),border=1,align="C")
        pdf.cell(w1[2],rh,u["unidad"],      border=1,align="C")
        pdf.cell(w1[3],rh,f" {nom[:32]}",   border=1,align="L")
        pdf.cell(w1[4],rh,f"{_fmt(cb)}%",border=1,align="R")
        pdf.cell(w1[5],rh,f"{_fmt(cc)}%",border=1,align="R")
        pdf.cell(w1[6],rh,f"{_fmt(ca)}%",border=1,align="R")
        pdf.cell(w1[7],rh,_fmt(ia),border=1,align="R")
        pdf.cell(w1[8],rh,_fmt(ib),border=1,align="R")
        pdf.cell(w1[9],rh,_fmt(ic),border=1,align="R")
        pdf.set_font("Helvetica","B",9); pdf.cell(w1[10],rh,_fmt(ex),border=1,align="R",ln=True)
        pdf.set_font("Helvetica","",9)
    pdf.set_x(10); pdf.set_font("Helvetica","B",9)
    pdf.cell(w1[0]+w1[1]+w1[2]+w1[3],rh,"TOTALES",border=1,align="R")
    pdf.cell(w1[4],rh,f"{_fmt(tot_cb)}%",border=1,align="R")
    pdf.cell(w1[5],rh,f"{_fmt(tot_cc)}%",border=1,align="R")
    pdf.cell(w1[6],rh,f"{_fmt(tot_ca)}%",border=1,align="R")
    pdf.cell(w1[7],rh,_fmt(tot_ia),border=1,align="R")
    pdf.cell(w1[8],rh,_fmt(tot_ib),border=1,align="R")
    pdf.cell(w1[9],rh,_fmt(tot_ic),border=1,align="R")
    pdf.set_fill_color(255,255,0); pdf.set_font("Helvetica","B",10)
    pdf.cell(w1[10],rh,_fmt(tot_ex),border=1,fill=True,align="R",ln=True)

    # ---- PAGINA 3: RECAUDACION (landscape) ----------------------------------
    pdf.add_page(orientation="L")
    _encabezado_pagina(pdf, "Recaudacion y expensas", periodo, vto_date, nombre_cons, dir_cons)
    w2 = [13,13,14,50,24,24,18,24,26,20,18,33]
    pdf.set_x(10); pdf.set_fill_color(230,230,230); pdf.set_font("Helvetica","B",9)
    pdf.cell(w2[0]+w2[1]+w2[2]+w2[3]+w2[4],rh,"",border=0)
    pdf.cell(w2[5]+w2[6],rh,"COBRANZA",border=1,fill=True,align="C")
    pdf.cell(w2[7]+w2[8]+w2[9]+w2[10]+w2[11],rh,"",border=0,ln=True)
    pdf.set_x(10)
    for lbl,wi in [("Piso",w2[0]),("Dpto",w2[1]),("U.F.",w2[2]),("Nombre y Apellido",w2[3]),
                   ("Saldo",w2[4]),("Mes Ant",w2[5]),("Telec / Vs",w2[6]),("SALDO",w2[7]),
                   ("Expensas",w2[8]),("Reserva",w2[9]),("Redondeo",w2[10]),("TOTAL PAGO",w2[11])]:
        pdf.cell(wi,rh,lbl,border=1,fill=True,align="C")
    pdf.ln()
    pdf.set_font("Helvetica","",9)
    t_sa=t_co=t_tel=t_sn=t_ex=t_re=t_rd=t_tot=0.0
    for u in unis:
        uid=u["id"]; ca,cb,cc=_tf(u["coef_a"]),_tf(u["coef_b"]),_tf(u["coef_c"])
        ex=(tot_a*ca/100.0)+(tot_b*cb/100.0)+(tot_c*cc/100.0)
        if ex == 0: ex = _tf(pagos_map.get(uid,{}).get("imp_mes_override") or 0)
        saldo_ant=_tf(deudas_map.get(uid, saldo_ini_map.get(uid,0.0)))
        cobranza=_tf(cobranza_map.get(uid,0.0)); telec=_tf(telec_map.get(uid,0.0))
        reserva=_tf(pagos_map.get(uid,{}).get("reserva",0.0))
        redondeo=_tf(pagos_map.get(uid,{}).get("redondeo",0.0))
        saldo_neto=max(0.0,saldo_ant-cobranza-telec); total_pagar=saldo_neto+ex+reserva+redondeo
        t_sa+=saldo_ant; t_co+=cobranza; t_tel+=telec; t_sn+=saldo_neto; t_ex+=ex; t_re+=reserva; t_rd+=redondeo; t_tot+=total_pagar
        nom=u.get("propietario") or u.get("inquilino") or ""
        pdf.set_x(10)
        pdf.cell(w2[0],rh,u.get("piso",""),border=1,align="C")
        pdf.cell(w2[1],rh,u.get("dpto",""),border=1,align="C")
        pdf.cell(w2[2],rh,u["unidad"],      border=1,align="C")
        pdf.cell(w2[3],rh,f" {nom[:26]}",   border=1,align="L")
        pdf.cell(w2[4],rh,_fmt(saldo_ant),  border=1,align="R")
        pdf.cell(w2[5],rh,_fmt(cobranza),   border=1,align="R")
        pdf.cell(w2[6],rh,_fmt(telec),      border=1,align="R")
        if saldo_neto<=0.01:
            pdf.set_fill_color(198,224,180); pdf.cell(w2[7],rh,_fmt(saldo_neto),border=1,fill=True,align="R")
        else:
            pdf.cell(w2[7],rh,_fmt(saldo_neto),border=1,align="R")
        pdf.cell(w2[8],rh,_fmt(ex),      border=1,align="R")
        pdf.cell(w2[9],rh,_fmt(reserva), border=1,align="R")
        pdf.cell(w2[10],rh,_fmt(redondeo),border=1,align="R")
        pdf.set_font("Helvetica","B",9); pdf.cell(w2[11],rh,_fmt(total_pagar),border=1,align="R",ln=True)
        pdf.set_font("Helvetica","",9)
    pdf.ln(2); pdf.set_x(10); pdf.set_font("Helvetica","B",9)
    pdf.cell(w2[0]+w2[1]+w2[2]+w2[3],rh,"TOTALES",border=1,align="R")
    pdf.cell(w2[4],rh,_fmt(t_sa),border=1,align="R"); pdf.cell(w2[5],rh,_fmt(t_co),border=1,align="R")
    pdf.cell(w2[6],rh,_fmt(t_tel),border=1,align="R"); pdf.cell(w2[7],rh,_fmt(t_sn),border=1,align="R")
    pdf.cell(w2[8],rh,_fmt(t_ex),border=1,align="R"); pdf.cell(w2[9],rh,_fmt(t_re),border=1,align="R")
    pdf.cell(w2[10],rh,_fmt(t_rd),border=1,align="R")
    pdf.set_fill_color(255,255,0); pdf.set_font("Helvetica","B",10)
    pdf.cell(w2[11],rh,_fmt(t_tot),border=1,fill=True,align="R",ln=True)
    return pdf
