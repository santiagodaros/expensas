"""
Gestor de Consorcios - Tab Pagos (Estado de Pagos)
"""
import customtkinter as ctk
import os
import threading
import tempfile
from tkinter import messagebox, filedialog

from gestor.widgets import C, _F, T, E, B, SF, _clear, _PeriodBar
from gestor.db import db, get_cfg, _send_boleta_email, _fetch_pagos_2per
from gestor.helpers import _tf, _fmt, _pa_of, _pn_of, _pl_of, _log_error
from gestor.pdf import generar_pdf_boletas
from gestor.tabs.dialogs import VentanaHistorial


class TabPagos(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app; self._ch = {}; self._dirty = False; self._build()

    def _build(self):
        h = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0); h.pack(fill="x")
        T(h, "Estado de Pagos", size=20, bold=True).pack(side="left", padx=24, pady=16)
        self._perbar = _PeriodBar(h, self._render, app=self.app)
        self._perbar.pack(side="right", padx=20)
        self.lbl_c = T(self, "Sin consorcio activo", size=12, color=C["text2"])
        self.lbl_c.pack(anchor="w", padx=24, pady=(10,0))
        wrap = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        wrap.pack(fill="both", expand=True, padx=16, pady=10)
        _COLS = [
            ("Unidad", 52), ("Nombre", 130), ("Saldo Ant.", 80),
            ("Recibido", 85), ("Telec/Vs", 70), ("SALDO", 80),
            ("Imp. Mes", 75), ("Reserva", 70), ("Redondeo", 70),
            ("Total Pagar", 80), ("Estado", 75), ("", 50), ("", 50),
        ]
        ch = ctk.CTkFrame(wrap, fg_color=C["accent"], corner_radius=8)
        ch.pack(fill="x", padx=10, pady=(10,4))
        for tx, w in _COLS:
            ctk.CTkLabel(ch, text=tx, font=_F(size=10, weight="bold"),
                width=w, anchor="center").pack(side="left", padx=4, pady=7)
        self.sp = SF(wrap); self.sp.pack(fill="both", expand=True, padx=10, pady=4)
        bo = ctk.CTkFrame(self, fg_color="transparent"); bo.pack(fill="x", padx=16, pady=10)
        B(bo, "  Guardar Estado de Pagos  ", self._save_wrapper, w=260, h=44, color=C["success"]).pack(side="right")
        B(bo, "Exportar Excel", self._export_excel, w=145, h=44, color=C["surface2"]).pack(side="right", padx=8)
        self._render_key = None
        self._render()

    def _render(self, force=False):
        if not self.app.consorcio_activo:
            if self._ch:
                _clear(self.sp)
                self._ch.clear()
                self._render_key = None
            self.lbl_c.configure(text="Sin consorcio activo -- selecciona uno en Mis Consorcios")
            return
        cid = self.app.consorcio_activo["id"]
        per = self._perbar.get(); per_a = _pa_of(per)
        reserva_pct = _tf(self.app.consorcio_activo.get("reserva_pct", 0.0))
        with db() as con:
            gs_count = con.execute(
                "SELECT COUNT(*) FROM gastos WHERE consorcio_id=? AND periodo=?", (cid, per)
            ).fetchone()[0]
        rk = (cid, per, gs_count)
        if not force and self._render_key == rk and self._ch:
            return
        self._render_key = rk
        _clear(self.sp)
        self._ch.clear()
        self.lbl_c.configure(text=f"Consorcio: {self.app.consorcio_activo['nombre']}   |   Periodo: {_pl_of(per)}")
        with db() as con:
            unis = con.execute(
                "SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (cid,)
            ).fetchall()
            gs = con.execute(
                "SELECT * FROM gastos WHERE consorcio_id=? AND periodo=?", (cid, per)
            ).fetchall()
            uid_list = [u["id"] for u in unis]
            p_ant_rows, p_act_rows = _fetch_pagos_2per(con, uid_list, per_a, per)
        map_ant = {p["unidad_id"]: dict(p) for p in p_ant_rows}
        map_act = {p["unidad_id"]: dict(p) for p in p_act_rows}
        tot_a = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "A")
        tot_b = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "B")
        tot_c = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "C")
        font_bold = _F(size=11, weight="bold")
        for idx, u_row in enumerate(unis):
            u = dict(u_row); uid = u["id"]
            imp_mes = (tot_a * _tf(u.get("coef_a")) / 100.0 +
                       tot_b * _tf(u.get("coef_b")) / 100.0 +
                       tot_c * _tf(u.get("coef_c")) / 100.0)
            p_ant = map_ant.get(uid, {}); p_act = map_act.get(uid, {})
            if p_ant:
                saldo_ant = max(0.0, _tf(p_ant["monto_deuda"]))
                tiene_ant = True
            else:
                saldo_ant = _tf(p_act.get("saldo_inicial", 0.0))
                tiene_ant = False
            monto_rec    = _tf(p_act.get("monto_recibido", 0.0))
            telec_val    = _tf(p_act.get("telec", 0.0))
            tiene_gastos = imp_mes > 0
            imp_display  = imp_mes if tiene_gastos else _tf((p_act.get("imp_mes_override") or 0) if p_act else 0)
            if p_act:
                reserva_val = _tf(p_act.get("reserva", 0.0))
            else:
                reserva_val = round(imp_display * reserva_pct / 100.0, 2)
            redondeo_val = _tf(p_act.get("redondeo", 0.0))
            saldo_cobr   = saldo_ant - monto_rec - telec_val
            total_pagar  = saldo_cobr + imp_display + reserva_val + redondeo_val
            esta_pagado  = bool(p_act.get("pagado", 0))
            bg = C["surface2"] if idx % 2 == 0 else C["row_alt"]
            r = ctk.CTkFrame(self.sp, fg_color=bg, corner_radius=6)
            r.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(r, text=str(u.get("unidad", "")), width=52, anchor="center",
                font=font_bold).pack(side="left", padx=4, pady=9)
            persona = str(u.get("inquilino") or u.get("propietario") or "-")
            ctk.CTkLabel(r, text=persona[:20], width=130, anchor="w",
                text_color=C["text2"]).pack(side="left", padx=4)
            e_saldo = ctk.CTkEntry(r, width=80, fg_color=C["surface"] if not tiene_ant else C["bg"], justify="right")
            e_saldo.insert(0, f"{saldo_ant:.2f}")
            if tiene_ant:
                e_saldo.configure(state="disabled")
            e_saldo.pack(side="left", padx=4)
            e_monto = ctk.CTkEntry(r, width=85, fg_color=C["surface"], justify="right")
            e_monto.insert(0, f"{monto_rec:.2f}"); e_monto.pack(side="left", padx=4)
            e_telec = ctk.CTkEntry(r, width=70, fg_color=C["surface"], justify="right")
            e_telec.insert(0, f"{telec_val:.2f}"); e_telec.pack(side="left", padx=4)
            lbl_saldo_cobr = ctk.CTkLabel(r, text=f"${saldo_cobr:.2f}", width=80, anchor="e",
                font=font_bold,
                text_color=C["danger"] if saldo_cobr > 0.01 else C["success"])
            lbl_saldo_cobr.pack(side="left", padx=4)
            e_imp = ctk.CTkEntry(r, width=75,
                fg_color=C["bg"] if tiene_gastos else C["surface"], justify="right")
            e_imp.insert(0, f"{imp_display:.2f}")
            if tiene_gastos:
                e_imp.configure(state="disabled")
            e_imp.pack(side="left", padx=4)
            e_reserva = ctk.CTkEntry(r, width=70, fg_color=C["surface"], justify="right")
            e_reserva.insert(0, f"{reserva_val:.2f}"); e_reserva.pack(side="left", padx=4)
            e_redondeo = ctk.CTkEntry(r, width=70, fg_color=C["surface"], justify="right")
            e_redondeo.insert(0, f"{redondeo_val:.2f}"); e_redondeo.pack(side="left", padx=4)
            lbl_total = ctk.CTkLabel(r, text=f"${total_pagar:.2f}", width=80, anchor="e",
                font=font_bold)
            lbl_total.pack(side="left", padx=4)
            _upd_timer = [None]
            def _upd(event=None, _lbl=lbl_total, _lbl_sc=lbl_saldo_cobr,
                     _es=e_saldo, _em=e_monto, _et=e_telec,
                     _ei=e_imp, _er=e_reserva, _ed=e_redondeo,
                     _tmr=_upd_timer):
                if _tmr[0] is not None:
                    self.after_cancel(_tmr[0])
                def _do():
                    _tmr[0] = None
                    sc = _tf(_es.get()) - _tf(_em.get()) - _tf(_et.get())
                    total = sc + _tf(_ei.get()) + _tf(_er.get()) + _tf(_ed.get())
                    _lbl_sc.configure(text=f"${sc:.2f}",
                        text_color=C["danger"] if sc > 0.01 else C["success"])
                    _lbl.configure(text=f"${total:.2f}")
                self._dirty = True
                _tmr[0] = self.after(150, _do)
            e_saldo.bind("<KeyRelease>", _upd)
            e_monto.bind("<KeyRelease>", _upd)
            e_telec.bind("<KeyRelease>", _upd)
            e_imp.bind("<KeyRelease>", _upd)
            e_reserva.bind("<KeyRelease>", _upd)
            e_redondeo.bind("<KeyRelease>", _upd)
            v = ctk.BooleanVar(value=esta_pagado)
            ctk.CTkCheckBox(r, text="Pagado", variable=v, width=75,
                fg_color=C["success"], hover_color=C["accent"], corner_radius=6).pack(side="left", padx=4)
            B(r, "Hist.", lambda _u=u, _uid=uid: VentanaHistorial(self, _uid, str(_u.get("propietario") or _u.get("inquilino") or "-"), str(_u.get("unidad",""))),
              w=50, h=30).pack(side="left", padx=2)
            email_addr = str(u.get("email") or "").strip()
            if email_addr:
                B(r, "Email", lambda _uid=uid, _em=email_addr, _u=u, _per=per: self._enviar_email(_uid, _em, _u, _per),
                  w=50, h=30, color=C["accent_h"]).pack(side="left", padx=2)
            self._ch[uid] = {
                "v": v, "e_saldo": e_saldo, "tiene_ant": tiene_ant,
                "e_monto": e_monto, "e_telec": e_telec, "e_imp": e_imp,
                "e_reserva": e_reserva, "e_redondeo": e_redondeo,
                "imp_mes": imp_mes, "tiene_gastos": tiene_gastos,
                "saldo_ant": saldo_ant, "per": per,
                "unidad": str(u.get("unidad", "")), "nombre": persona,
            }

    def _save(self):
        if not self.app.consorcio_activo: return
        invalid = []
        for uid, d in self._ch.items():
            for key, entry in [("Recibido", d["e_monto"]), ("Telec", d["e_telec"]),
                               ("Reserva", d["e_reserva"]), ("Redondeo", d["e_redondeo"])]:
                raw = entry.get().strip()
                if not raw: continue
                try:
                    float(raw.replace(",", "."))
                    entry.configure(border_color=C["border"])
                except ValueError:
                    entry.configure(border_color=C["danger"])
                    invalid.append(f"UF{d.get('unidad','?')} {key}='{raw}'")
        if invalid:
            self.app.show_toast(f"Valor invalido: {invalid[0]}", 5000)
            return
        with db() as con:
            for uid, d in self._ch.items():
                pagado         = 1 if d["v"].get() else 0
                monto_recibido = _tf(d["e_monto"].get())
                telec          = _tf(d["e_telec"].get())
                reserva        = _tf(d["e_reserva"].get())
                redondeo       = _tf(d["e_redondeo"].get())
                imp_val      = d["imp_mes"] if d["tiene_gastos"] else _tf(d["e_imp"].get())
                imp_override = imp_val if not d["tiene_gastos"] else None
                saldo_ini = _tf(d["e_saldo"].get()) if not d["tiene_ant"] else d["saldo_ant"]
                deuda     = saldo_ini - monto_recibido - telec + imp_val + reserva + redondeo
                con.execute(
                    "INSERT INTO pagos(unidad_id,periodo,pagado,monto_deuda,monto_recibido,telec,reserva,redondeo,saldo_inicial,imp_mes_override) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(unidad_id,periodo) DO UPDATE SET "
                    "pagado=excluded.pagado, monto_deuda=excluded.monto_deuda, "
                    "monto_recibido=excluded.monto_recibido, telec=excluded.telec, "
                    "reserva=excluded.reserva, redondeo=excluded.redondeo, "
                    "saldo_inicial=excluded.saldo_inicial, "
                    "imp_mes_override=excluded.imp_mes_override",
                    (uid, d["per"], pagado, deuda, monto_recibido, telec, reserva, redondeo, saldo_ini, imp_override))
                if pagado:
                    per_n = _pn_of(d["per"])
                    con.execute(
                        "INSERT INTO pagos(unidad_id, periodo, monto_recibido) VALUES(?, ?, ?) "
                        "ON CONFLICT(unidad_id, periodo) DO UPDATE SET "
                        "monto_recibido=excluded.monto_recibido",
                        (uid, per_n, deuda))
        self._dirty = False
        self.app.show_toast("Estado de pagos guardado.")
        self.app.invalidate_cache()

    def _save_wrapper(self):
        try:
            self._save()
        except Exception as e:
            _log_error("TabPagos._save", e)
            self.app.show_toast(f"Error al guardar pagos: {e}")

    def _export_excel(self):
        if not self.app.consorcio_activo or not self._ch:
            self.app.show_toast("Nada para exportar."); return
        try:
            dest = filedialog.asksaveasfilename(
                title="Exportar Estado de Pagos",
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")],
                initialfile=f"pagos_{self.app.consorcio_activo['nombre'].replace(' ','_')}_{self._perbar.get()}.xlsx")
            if not dest: return
            import openpyxl
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Estado de Pagos"
            ws.append(["Unidad", "Nombre", "Saldo Ant.", "Recibido", "Telec",
                        "SALDO", "Imp. Mes", "Reserva", "Redondeo", "Total Pagar", "Pagado"])
            for uid, d in self._ch.items():
                sa = _tf(d["e_saldo"].get()); rec = _tf(d["e_monto"].get())
                tel = _tf(d["e_telec"].get()); imp = d["imp_mes"] if d["tiene_gastos"] else _tf(d["e_imp"].get())
                res = _tf(d["e_reserva"].get()); red = _tf(d["e_redondeo"].get())
                saldo = sa - rec - tel; total = saldo + imp + res + red
                ws.append([d.get("unidad",""), d.get("nombre",""), round(sa,2), round(rec,2), round(tel,2),
                            round(saldo,2), round(imp,2), round(res,2), round(red,2),
                            round(total,2), "Si" if d["v"].get() else "No"])
            wb.save(dest)
            self.app.show_toast(f"Exportado: {os.path.basename(dest)}")
        except Exception as e:
            self.app.show_toast(f"Error exportando: {e}", 5000)

    def refresh(self): self._render()

    def _enviar_email(self, uid, email_addr, u_dict, per):
        smtp_cfg = {
            "server": get_cfg("smtp_server"),
            "port":   get_cfg("smtp_port", "587"),
            "user":   get_cfg("smtp_user"),
            "pass":   get_cfg("smtp_pass"),
            "from":   get_cfg("smtp_from"),
        }
        if not smtp_cfg["server"] or not smtp_cfg["user"]:
            self.app.show_toast("Configura SMTP en Configuracion antes de enviar emails.", 5000)
            return
        cons = self.app.consorcio_activo
        threading.Thread(target=self._task_email,
            args=(smtp_cfg, email_addr, cons, uid, per), daemon=True).start()

    def _task_email(self, smtp_cfg, email_addr, cons, uid, per):
        try:
            cid = cons["id"]; per_a = _pa_of(per)
            with db() as con:
                unis = con.execute("SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (cid,)).fetchall()
                gs   = con.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=?", (cid, per)).fetchall()
                uid_list = [u["id"] for u in unis]
                p_ant_rows, p_act_rows = _fetch_pagos_2per(con, uid_list, per_a, per)
            pagos_map    = {p["unidad_id"]: dict(p) for p in p_act_rows}
            deudas_map   = {p["unidad_id"]: _tf(p["monto_deuda"]) for p in p_ant_rows}
            cobranza_map = {p["unidad_id"]: _tf(p["monto_recibido"]) for p in p_act_rows}
            saldo_ini_map = {p["unidad_id"]: _tf(dict(p).get("saldo_inicial", 0.0)) for p in p_act_rows}
            telec_map    = {p["unidad_id"]: _tf(dict(p).get("telec", 0.0)) for p in p_act_rows}
            unis_list = [dict(u) for u in unis]; gs_list = [dict(g) for g in gs]
            pdf = generar_pdf_boletas(dict(cons), unis_list, gs_list, pagos_map, deudas_map, cobranza_map, saldo_ini_map, telec_map, per)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf_:
                tmp = tf_.name
            pdf.output(tmp)
            with open(tmp, "rb") as f:
                pdf_bytes = f.read()
            os.unlink(tmp)
            _send_boleta_email(smtp_cfg, email_addr, pdf_bytes, per, cons["nombre"])
            try: self.after(0, self.app.show_toast, f"Email enviado a {email_addr}")
            except Exception: pass
        except Exception as e:
            try: self.after(0, self.app.show_toast, f"Error al enviar email: {e}", 6000)
            except Exception: pass
