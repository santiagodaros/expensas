"""
Gestor de Consorcios - Tab Generar Expensas
"""
import customtkinter as ctk
import os
import threading
import tempfile
from tkinter import messagebox

from gestor.widgets import C, _F, T, B, _PeriodBar
from gestor.db import db, get_cfg, _fetch_pagos_2per, _send_boleta_email
from gestor.helpers import _tf, _fmt, _pa_of, _pl_of, PDF_DIR, WEB_DIR, _log_error
from gestor.pdf import generar_pdf_consorcio, generar_pdf_email_unidad
from gestor.web import generar_html_reporte, generar_html_index, _git_push_web


class TabGenerar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app; self._build()

    def _build(self):
        h = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        h.pack(fill="x", padx=30, pady=(20, 0))
        
        self.lbl_c = T(h, "Panel de Emisión", size=15, color=C["text2"])
        self.lbl_c.pack(side="left")
        
        self._perbar = _PeriodBar(h, self._on_period_change, app=self.app)
        self._perbar.pack(side="right", padx=10)
        
        self.btn_boletas = ctk.CTkButton(h, text="  BOLETAS U.F.  ",
            command=self._gen_boletas, width=140, height=38,
            fg_color=C["surface2"], hover_color=C["surface"],
            corner_radius=8, font=_F(size=12, weight="bold"))
        self.btn_boletas.pack(side="right", padx=6)
        
        self.btn_email = ctk.CTkButton(h, text="  NOTIFICAR EMAIL  ",
            command=self._gen_email, width=155, height=38,
            fg_color=C["surface2"], hover_color=C["surface"],
            corner_radius=8, font=_F(size=12, weight="bold"))
        self.btn_email.pack(side="right", padx=6)
        
        body = ctk.CTkFrame(self, fg_color=C["bg"]); body.pack(fill="both", expand=True)
        ctk.CTkFrame(body, fg_color="transparent", height=1).pack(expand=True)
        
        bn = ctk.CTkFrame(body, fg_color="transparent", corner_radius=16)
        bn.pack(fill="x", padx=60, pady=(0, 20))
        bn_in = ctk.CTkFrame(bn, fg_color=C["accent"], corner_radius=16)
        bn_in.pack(fill="x")
        T(bn_in, "EXPENSAS DE ESTE PERÍODO LISTAS PARA CÁLCULO", size=18, bold=True).pack(anchor="w", padx=30, pady=(24, 6))
        T(bn_in, "Asegúrese de haber revisado los comprobantes ingresados y verificado el estado de recaudación.", size=12).pack(anchor="w", padx=30, pady=(0, 24))
        
        fr = ctk.CTkFrame(body, fg_color="transparent")
        fr.pack(fill="x", padx=60)
        
        self.lbl_card_a = T(fr, "$0.00", size=26, bold=True)
        self.lbl_card_b = T(fr, "$0.00", size=26, bold=True)
        self.lbl_card_c = T(fr, "$0.00", size=26, bold=True)
        
        def mock_card(parent, title, lbl):
            c = ctk.CTkFrame(parent, fg_color=C["surface"], corner_radius=16, height=130)
            c.pack(side="left", fill="x", expand=True, padx=6)
            c.pack_propagate(False)
            T(c, title.upper(), size=12, bold=True, color=C["text2"]).pack(anchor="w", padx=24, pady=(24, 8))
            lbl.pack(in_=c, anchor="w", padx=24)
            
        mock_card(fr, "Gastos Comunes (A)", self.lbl_card_a)
        mock_card(fr, "Gastos Especiales (B/C)", self.lbl_card_b)
        mock_card(fr, "Fondo de Reserva Estimado", self.lbl_card_c)

        self.btn_big = ctk.CTkButton(body,
            text="  CALCULAR Y GENERAR REPORTE DEFINITIVO  ",
            command=self._gen, width=640, height=80,
            fg_color=C["accent"], hover_color=C["accent_h"],
            corner_radius=20, font=_F(size=22, weight="bold"))
        self.btn_big.pack(pady=(40, 20))
        
        self.ls = T(body, "", size=12, color=C["text2"]); self.ls.pack()
        self.pb = ctk.CTkProgressBar(body, width=640,
            fg_color=C["surface2"], progress_color=C["success"], corner_radius=8)
        self.pb.set(0); self.pb.pack(pady=12)
        T(body, f"Respaldo de auditoría: {PDF_DIR[3:]}...", size=10, color=C["text2"]).pack(pady=4)
        self.btn_abrir = ctk.CTkButton(body, text="  Abrir Carpeta Local  ",
            command=self._abrir_carpeta, width=200, height=36,
            fg_color=C["surface2"], hover_color=C["surface"],
            corner_radius=10, font=_F(size=12))
        self._last_folder = None
        ctk.CTkFrame(body, fg_color="transparent", height=1).pack(expand=True)

    def _on_period_change(self):
        if self.app.consorcio_activo: self._resumen()

    def refresh(self):
        if self.app.consorcio_activo:
            self.lbl_c.configure(text=f"Consorcio activo: {self.app.consorcio_activo['nombre']}")
            self._resumen()
        else:
            self.lbl_c.configure(text="Sin consorcio activo -- selecciona uno en la barra superior")

    def _resumen(self):
        cid = self.app.consorcio_activo["id"]; per = self._perbar.get()
        data_cache = self.app.get_period_data(cid, per)
        gs = data_cache["gastos"]
        tot_a = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "A")
        tot_b = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "B")
        tot_c = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "C")
        reserva_pct = _tf(self.app.consorcio_activo.get("reserva_pct", 0.0))
        reserva_val = (tot_a + tot_b + tot_c) * reserva_pct / 100.0
        
        self.lbl_card_a.configure(text=f"${_fmt(tot_a)}")
        self.lbl_card_b.configure(text=f"${_fmt(tot_b + tot_c)}")
        self.lbl_card_c.configure(text=f"${_fmt(reserva_val)}")

    def _gen(self):
        if not self.app.consorcio_activo:
            self.app.show_toast("Selecciona un consorcio primero."); return
        self.btn_big.configure(state="disabled")
        self.btn_boletas.configure(state="disabled")
        self.btn_email.configure(state="disabled")
        self.btn_abrir.pack_forget()
        self.pb.set(0)
        threading.Thread(target=self._task, daemon=True).start()

    def _task(self):
        try:
            cons  = dict(self.app.consorcio_activo)
            cid   = cons["id"]; per = self._perbar.get(); per_a = _pa_of(per)
            data_cache = self.app.get_period_data(cid, per)
            unis = data_cache["unis"]
            gs = data_cache["gastos"]
            p_ant_rows = data_cache["pagos_ant"]
            p_act_rows = data_cache["pagos_act"]
            if unis:
                sa = sum(_tf(u["coef_a"]) for u in unis)
                sb = sum(_tf(u["coef_b"]) for u in unis)
                sc = sum(_tf(u["coef_c"]) for u in unis)
                bad = []
                if gs:
                    if not 99.5 <= sa <= 100.5: bad.append(f"A={sa:.2f}%")
                    if not 99.5 <= sb <= 100.5: bad.append(f"B={sb:.2f}%")
                    if not 99.5 <= sc <= 100.5: bad.append(f"C={sc:.2f}%")
                if bad:
                    msg = (f"Los coeficientes no suman 100%: {', '.join(bad)}.\n\n"
                           f"Corregir en Mis Consorcios antes de generar el PDF.")
                    self.after(0, self._err_coef, msg)
                    return
            pagos_map    = {p["unidad_id"]: dict(p) for p in p_act_rows}
            deudas_map   = {p["unidad_id"]: _tf(p["monto_deuda"]) for p in p_ant_rows}
            cobranza_map = {p["unidad_id"]: _tf(p["monto_recibido"]) for p in p_act_rows}
            saldo_ini_map = {p["unidad_id"]: _tf(dict(p).get("saldo_inicial", 0.0)) for p in p_act_rows}
            telec_map    = {p["unidad_id"]: _tf(dict(p).get("telec", 0.0)) for p in p_act_rows}
            self.after(0, self.ls.configure, {"text": "Generando PDF consorcio..."})
            self.after(0, self.pb.set, 0.1)
            unis_list = [dict(u) for u in unis]; gs_list = [dict(g) for g in gs]
            total_unis = max(len(unis_list), 1)
            def _prog(i, etapa):
                pct = 0.1 + (i / total_unis) * 0.65
                self.after(0, self.pb.set, pct)
                self.after(0, self.ls.configure, {"text": f"Generando PDF... {etapa} ({i}/{total_unis})"})
            pdf = generar_pdf_consorcio(cons, unis_list, gs_list, pagos_map, deudas_map,
                                        cobranza_map, saldo_ini_map, telec_map, per,
                                        progress_cb=_prog)
            folder = os.path.join(PDF_DIR, cons["nombre"].replace(" ", "_"), per)
            os.makedirs(folder, exist_ok=True)
            fname  = f"Expensas_{cons['nombre'].replace(' ','_')}_{per}.pdf"
            fpath  = os.path.join(folder, fname)
            pdf.output(fpath)
            self.after(0, self.ls.configure, {"text": "Generando reporte web..."})
            self.after(0, self.pb.set, 0.82)
            web_folder = os.path.join(WEB_DIR, cons["nombre"].replace(" ", "_"), per)
            os.makedirs(web_folder, exist_ok=True)
            html_path = generar_html_reporte(cons, gs_list, per, web_folder)
            generar_html_index()
            git_ok = None; git_msg = ""
            if get_cfg("git_repo_url", "").strip():
                self.after(0, self.ls.configure, {"text": "Publicando en GitHub/Vercel..."})
                self.after(0, self.pb.set, 0.93)
                git_ok, git_msg = _git_push_web()
            self.after(0, self._done, fpath, html_path, git_ok, git_msg)
        except Exception as e:
            _log_error("TabGenerar._task", e)
            self.after(0, self._err, str(e))

    def _done(self, fpath, html_path=None, git_ok=None, git_msg=""):
        self.pb.set(1)
        self.ls.configure(text=f"Listo! PDF: {fpath}")
        self._last_folder = os.path.dirname(fpath)
        self.btn_abrir.pack(pady=(4, 0))
        self.btn_big.configure(state="normal")
        if hasattr(self, "btn_top"): self.btn_top.configure(state="normal")
        self.btn_boletas.configure(state="normal")
        self.btn_email.configure(state="normal")
        msg = "PDF generado correctamente."
        if html_path:
            msg += f" Web: {os.path.basename(os.path.dirname(html_path))}/index.html"
        if git_ok is True:
            msg += f" | Git: {git_msg}"
        elif git_ok is False:
            msg += f" | Git ERROR: {git_msg}"
        self.app.show_toast(msg)

    def _err(self, msg):
        self.pb.set(0)
        self.ls.configure(text=f"Error: {msg}")
        self.btn_big.configure(state="normal")
        if hasattr(self, "btn_top"): self.btn_top.configure(state="normal")
        self.btn_boletas.configure(state="normal")
        self.btn_email.configure(state="normal")
        self.app.show_toast(f"Error al generar PDF: {msg}")

    def _err_coef(self, msg):
        """Error de coeficientes: re-habilita botones y muestra dialogo."""
        self.pb.set(0)
        self.ls.configure(text="Generacion cancelada: coeficientes incorrectos.")
        self.btn_big.configure(state="normal")
        if hasattr(self, "btn_top"): self.btn_top.configure(state="normal")
        self.btn_boletas.configure(state="normal")
        self.btn_email.configure(state="normal")
        messagebox.showwarning("Coeficientes incorrectos", msg, parent=self)

    def _gen_boletas(self):
        if not self.app.consorcio_activo:
            self.app.show_toast("Selecciona un consorcio primero."); return
        self.btn_big.configure(state="disabled")
        self.btn_top.configure(state="disabled")
        self.btn_boletas.configure(state="disabled")
        self.btn_email.configure(state="disabled")
        self.pb.set(0)
        threading.Thread(target=self._task_boletas, daemon=True).start()

    def _task_boletas(self):
        try:
            cons = dict(self.app.consorcio_activo)
            cid  = cons["id"]; per = self._perbar.get(); per_a = _pa_of(per)
            data_cache = self.app.get_period_data(cid, per)
            unis = data_cache["unis"]
            gs = data_cache["gastos"]
            p_ant_rows = data_cache["pagos_ant"]
            p_act_rows = data_cache["pagos_act"]
            pagos_map     = {p["unidad_id"]: dict(p) for p in p_act_rows}
            deudas_map    = {p["unidad_id"]: _tf(p["monto_deuda"]) for p in p_ant_rows}
            cobranza_map  = {p["unidad_id"]: _tf(p["monto_recibido"]) for p in p_act_rows}
            saldo_ini_map = {p["unidad_id"]: _tf(dict(p).get("saldo_inicial", 0.0)) for p in p_act_rows}
            telec_map     = {p["unidad_id"]: _tf(dict(p).get("telec", 0.0)) for p in p_act_rows}
            unis_list = [dict(u) for u in unis]; gs_list = [dict(g) for g in gs]
            folder = os.path.join(PDF_DIR, cons["nombre"].replace(" ", "_"), per, "boletas")
            os.makedirs(folder, exist_ok=True)
            total = len(unis_list)
            for i, u in enumerate(unis_list):
                uid = u["id"]
                nom = (u.get("propietario") or u.get("inquilino") or f"UF{u['unidad']}").strip()
                safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in nom).strip()
                fname = f"UF{u['unidad']}_{safe}.pdf"
                fpath = os.path.join(folder, fname)
                self.after(0, self.ls.configure, {"text": f"Generando boleta {i+1}/{total}: {nom}..."})
                self.after(0, self.pb.set, (i + 1) / total)
                pdf = generar_pdf_email_unidad(uid, cons, unis_list, gs_list,
                    pagos_map, deudas_map, cobranza_map, saldo_ini_map, telec_map, per)
                pdf.output(fpath)
            self.after(0, self._done_boletas, folder)
        except Exception as e:
            _log_error("TabGenerar._task_boletas", e)
            self.after(0, self._err, str(e))

    def _done_boletas(self, folder):
        self.pb.set(1)
        self.ls.configure(text=f"Boletas guardadas en: {folder}")
        self._last_folder = folder
        self.btn_abrir.pack(pady=(4, 0))
        self.btn_big.configure(state="normal")
        if hasattr(self, "btn_top"): self.btn_top.configure(state="normal")
        self.btn_boletas.configure(state="normal")
        self.btn_email.configure(state="normal")
        self.app.show_toast(f"Boletas individuales generadas correctamente.")

    def _abrir_carpeta(self):
        if self._last_folder and os.path.isdir(self._last_folder):
            try:
                os.startfile(self._last_folder)
            except Exception:
                self.app.show_toast(f"No se pudo abrir: {self._last_folder}", 4000)

    def _gen_email(self):
        if not self.app.consorcio_activo:
            self.app.show_toast("Selecciona un consorcio primero."); return
        smtp_cfg = {
            "server": get_cfg("smtp_server"), "port": get_cfg("smtp_port", "587"),
            "user":   get_cfg("smtp_user"),   "pass": get_cfg("smtp_pass"),
            "from":   get_cfg("smtp_from"),
        }
        if not smtp_cfg["server"] or not smtp_cfg["user"]:
            self.app.show_toast("Configura SMTP en Configuracion antes de enviar emails.", 5000)
            return
        self.btn_big.configure(state="disabled")
        self.btn_top.configure(state="disabled")
        self.btn_boletas.configure(state="disabled")
        self.btn_email.configure(state="disabled")
        self.pb.set(0)
        threading.Thread(target=self._task_email_todos, args=(smtp_cfg,), daemon=True).start()

    def _task_email_todos(self, smtp_cfg):
        try:
            cons = dict(self.app.consorcio_activo)
            cid  = cons["id"]; per = self._perbar.get(); per_a = _pa_of(per)
            data_cache = self.app.get_period_data(cid, per)
            unis = data_cache["unis"]
            gs = data_cache["gastos"]
            p_ant_rows = data_cache["pagos_ant"]
            p_act_rows = data_cache["pagos_act"]
            pagos_map     = {p["unidad_id"]: dict(p) for p in p_act_rows}
            deudas_map    = {p["unidad_id"]: _tf(p["monto_deuda"]) for p in p_ant_rows}
            cobranza_map  = {p["unidad_id"]: _tf(p["monto_recibido"]) for p in p_act_rows}
            saldo_ini_map = {p["unidad_id"]: _tf(dict(p).get("saldo_inicial", 0.0)) for p in p_act_rows}
            telec_map     = {p["unidad_id"]: _tf(dict(p).get("telec", 0.0)) for p in p_act_rows}
            unis_list = [dict(u) for u in unis]; gs_list = [dict(g) for g in gs]
            units_with_email = [u for u in unis_list if (u.get("email") or "").strip()]
            if not units_with_email:
                self.after(0, self._done_email, 0, 0)
                return
            total = len(units_with_email); sent = 0; errors = 0
            for i, u in enumerate(units_with_email):
                uid = u["id"]; email_addr = u["email"].strip()
                nom = (u.get("propietario") or u.get("inquilino") or f"UF{u['unidad']}").strip()
                self.after(0, self.ls.configure, {"text": f"Enviando email {i+1}/{total}: {nom} ({email_addr})..."})
                self.after(0, self.pb.set, (i + 1) / total)
                try:
                    from gestor.pdf import generar_pdf_email_unidad
                    pdf = generar_pdf_email_unidad(uid, cons, unis_list, gs_list,
                        pagos_map, deudas_map, cobranza_map, saldo_ini_map, telec_map, per)
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf_:
                        tmp = tf_.name
                    try:
                        pdf.output(tmp)
                        with open(tmp, "rb") as f:
                            pdf_bytes = f.read()
                    finally:
                        try: os.unlink(tmp)
                        except Exception: pass
                    _send_boleta_email(smtp_cfg, email_addr, pdf_bytes, per, cons["nombre"])
                    sent += 1
                except Exception as e:
                    _log_error(f"TabGenerar._task_email_todos uid={uid}", e)
                    errors += 1
            self.after(0, self._done_email, sent, errors)
        except Exception as e:
            _log_error("TabGenerar._task_email_todos", e)
            self.after(0, self._err, str(e))

    def _done_email(self, sent, errors):
        self.pb.set(1 if sent > 0 else 0)
        self.btn_abrir.pack_forget()  # email no genera carpeta local
        self.btn_big.configure(state="normal")
        self.btn_top.configure(state="normal")
        self.btn_boletas.configure(state="normal")
        self.btn_email.configure(state="normal")
        if sent == 0 and errors == 0:
            self.ls.configure(text="Ninguna unidad tiene email configurado.")
            self.app.show_toast("Ninguna unidad tiene email configurado.", 4000)
        elif errors == 0:
            self.ls.configure(text=f"Emails enviados: {sent} unidades.")
            self.app.show_toast(f"Emails enviados correctamente a {sent} unidades.")
        else:
            self.ls.configure(text=f"Enviados: {sent} | Errores: {errors}")
            self.app.show_toast(f"Emails: {sent} enviados, {errors} con error. Ver errores.log.", 6000)

