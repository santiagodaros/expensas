"""
Gestor de Consorcios - Tab Deudores
"""
import customtkinter as ctk
import os
from tkinter import filedialog

from gestor.widgets import C, _F, T, B, SF, _clear, _PeriodBar
from gestor.helpers import _tf, _fmt, _pl_of
from gestor.tabs.dialogs import VentanaHistorial


class TabDeudores(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app; self._build()

    def _build(self):
        h = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0); h.pack(fill="x")
        T(h, "Deudores / Saldos Pendientes", size=20, bold=True).pack(side="left", padx=24, pady=16)
        self._perbar = _PeriodBar(h, self.refresh, app=self.app)
        self._perbar.pack(side="right", padx=20)
        B(h, "Actualizar", self.refresh, w=110, h=38).pack(side="right", padx=4)
        self.lbl_c = T(self, "Sin consorcio activo", size=12, color=C["text2"])
        self.lbl_c.pack(anchor="w", padx=24, pady=(10, 0))
        sf2 = ctk.CTkFrame(self, fg_color="transparent"); sf2.pack(fill="x", padx=16, pady=(4,0))
        T(sf2, "Buscar:", size=11, color=C["text2"]).pack(side="left", padx=(8,4))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh())
        ctk.CTkEntry(sf2, textvariable=self._search_var, placeholder_text="Nombre o unidad...",
            width=260, fg_color=C["surface2"], border_color=C["border"],
            text_color=C["text"], corner_radius=8).pack(side="left")
        wrap = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        wrap.pack(fill="both", expand=True, padx=16, pady=10)
        _COLS = [("Unidad", 80), ("Nombre", 320), ("Total Pagar", 180), ("", 70)]
        ch = ctk.CTkFrame(wrap, fg_color=C["accent"], corner_radius=8)
        ch.pack(fill="x", padx=10, pady=(10, 4))
        for tx, w in _COLS:
            ctk.CTkLabel(ch, text=tx, font=_F(size=10, weight="bold"),
                width=w, anchor="center").pack(side="left", padx=4, pady=7)
        self.sf = SF(wrap); self.sf.pack(fill="both", expand=True, padx=10, pady=4)
        b_row = ctk.CTkFrame(self, fg_color="transparent"); b_row.pack(fill="x", padx=16, pady=(0,4))
        B(b_row, "Exportar Excel", self._export_excel, w=145, h=36, color=C["surface2"]).pack(side="right")
        self.lbl_tot = T(self, "", size=12, color=C["text2"])
        self.lbl_tot.pack(anchor="e", padx=24, pady=4)
        self._deudores_cache = []

    def refresh(self):
        _clear(self.sf)
        if not self.app.consorcio_activo:
            self.lbl_c.configure(text="Sin consorcio activo -- selecciona uno en Mis Consorcios")
            self.lbl_tot.configure(text=""); return
        cid = self.app.consorcio_activo["id"]
        per = self._perbar.get()
        self.lbl_c.configure(text=f"Consorcio: {self.app.consorcio_activo['nombre']}   |   Periodo: {_pl_of(per)}")
        data = self.app.get_period_data(cid, per)
        unis = data["unis"]; gs = data["gastos"]
        p_ant_rows = data["pagos_ant"]; p_act_rows = data["pagos_act"]
        map_ant = {p["unidad_id"]: dict(p) for p in p_ant_rows}
        map_act = {p["unidad_id"]: dict(p) for p in p_act_rows}
        tot_a = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "A")
        tot_b = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "B")
        tot_c = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "C")
        deudores = []
        for u in unis:
            u_d = dict(u); uid = u_d["id"]
            p_ant = map_ant.get(uid, {}); p_act = map_act.get(uid, {})
            if p_ant:
                saldo_ant = max(0.0, _tf(p_ant["monto_deuda"]))
            else:
                saldo_ant = _tf(p_act.get("saldo_inicial", 0.0))
            monto_rec = _tf(p_act.get("monto_recibido", 0.0))
            telec_val = _tf(p_act.get("telec", 0.0))
            ca, cb, cc = _tf(u_d.get("coef_a")), _tf(u_d.get("coef_b")), _tf(u_d.get("coef_c"))
            imp_mes = tot_a*ca/100.0 + tot_b*cb/100.0 + tot_c*cc/100.0
            if imp_mes == 0:
                imp_mes = _tf(p_act.get("imp_mes_override") or 0)
            reserva_val  = _tf(p_act.get("reserva", 0.0))
            redondeo_val = _tf(p_act.get("redondeo", 0.0))
            saldo_cobr   = saldo_ant - monto_rec - telec_val
            total_pagar  = saldo_cobr + imp_mes + reserva_val + redondeo_val
            esta_pagado  = bool(p_act.get("pagado", 0))
            if not esta_pagado and total_pagar > 0.01:
                nom = u_d.get("propietario") or u_d.get("inquilino") or "-"
                deudores.append((u_d["unidad"], nom, total_pagar))
        deudores.sort(key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0)
        self._deudores_cache = deudores
        term = getattr(self, "_search_var", None)
        term = term.get().strip().lower() if term else ""
        if term:
            deudores = [(u, n, d) for u, n, d in deudores
                        if term in str(u).lower() or term in n.lower()]
        if not deudores:
            T(self.sf, "No hay deudores para este periodo.", color=C["success"], size=12).pack(pady=30)
            self.lbl_tot.configure(text=""); return
        total = 0.0
        for idx, (unidad, nom, deuda) in enumerate(deudores):
            total += deuda
            uid_row = next((dict(u)["id"] for u in unis if str(dict(u)["unidad"]) == str(unidad)), None)
            bg = C["surface2"] if idx % 2 == 0 else C["row_alt"]
            frm = ctk.CTkFrame(self.sf, fg_color=bg, corner_radius=6); frm.pack(fill="x", pady=2)
            ctk.CTkLabel(frm, text=str(unidad), width=80, anchor="center",
                font=_F(size=11, weight="bold")).pack(side="left", padx=4, pady=8)
            ctk.CTkLabel(frm, text=nom[:44], width=320, anchor="w",
                text_color=C["text"]).pack(side="left", padx=4)
            ctk.CTkLabel(frm, text=f"${_fmt(deuda)}", width=180, anchor="e",
                text_color=C["danger"],
                font=_F(size=12, weight="bold")).pack(side="left", padx=4)
            if uid_row is not None:
                B(frm, "Hist.",
                    lambda _uid=uid_row, _nom=nom, _u=str(unidad): VentanaHistorial(self, _uid, _nom, _u),
                    w=60, h=28).pack(side="left", padx=4)
        self.lbl_tot.configure(text=f"Deuda total pendiente: ${_fmt(total)}")

    def _export_excel(self):
        if not self._deudores_cache:
            self.app.show_toast("No hay deudores para exportar."); return
        try:
            per = self._perbar.get()
            nom = self.app.consorcio_activo["nombre"].replace(" ","_") if self.app.consorcio_activo else "sin_consorcio"
            dest = filedialog.asksaveasfilename(
                title="Exportar Deudores", defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")],
                initialfile=f"deudores_{nom}_{per}.xlsx")
            if not dest: return
            import openpyxl
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Deudores"
            ws.append(["Unidad", "Nombre", "Total Pagar"])
            total = 0.0
            for unidad, nom_u, deuda in self._deudores_cache:
                ws.append([str(unidad), nom_u, round(deuda, 2)])
                total += deuda
            ws.append(["", "TOTAL", round(total, 2)])
            wb.save(dest)
            self.app.show_toast(f"Exportado: {os.path.basename(dest)}")
        except Exception as e:
            self.app.show_toast(f"Error exportando: {e}", 5000)
