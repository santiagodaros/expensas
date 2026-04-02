"""
Gestor de Consorcios - Tab Resumen General
"""
import customtkinter as ctk

from gestor.widgets import C, _F, T, B, SF, divider, _clear, _PeriodBar
from gestor.db import get_cfg
from gestor.helpers import _tf, _fmt, _pl_of, _pa_of
from gestor.db import db as _db_ctx


class TabResumen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app; self._build()

    def _build(self):
        h = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        h.pack(fill="x", padx=30, pady=(20,0))
        
        self.lbl_c = T(h, "Resumen General de Operaciones", size=15, color=C["text2"])
        self.lbl_c.pack(side="left")
        
        self._perbar = _PeriodBar(h, self.refresh, app=self.app)
        self._perbar.pack(side="left", padx=20)
        
        B(h, "Generar Reporte Mensual", w=190, h=38, font=_F(size=12, weight="bold")).pack(side="right")
        B(h, "Exportar Datos", w=140, h=38, color=C["surface2"], font=_F(size=12, weight="bold")).pack(side="right", padx=(0, 15))
        
        self.body = ctk.CTkFrame(self, fg_color=C["bg"])
        self.body.pack(fill="both", expand=True, padx=30, pady=20)

    def refresh(self):
        _clear(self.body)
        if not self.app.consorcio_activo:
            self.lbl_c.configure(text="Sin consorcio activo -- selecciona uno en la barra superior")
            T(self.body, "No hay consorcio activo.", color=C["text2"], size=15).pack(pady=100)
            return

        cid = self.app.consorcio_activo["id"]
        per = self._perbar.get()
        self.lbl_c.configure(text=f"Resumen General  •  {self.app.consorcio_activo['nombre']}")

        data = self.app.get_period_data(cid, per)
        unis = data["unis"]; gs = data["gastos"]
        p_act_rows = data["pagos_act"]
        p_rows = p_act_rows

        n_unis     = len(unis)
        pagaron    = sum(1 for p in p_rows if p["pagado"])
        pendientes = n_unis - pagaron
        pct_cob    = (pagaron / n_unis * 100) if n_unis > 0 else 0.0

        tot_a = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "A")
        tot_b = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "B")
        tot_c = sum(_tf(g["monto"]) for g in gs if g["categoria"] == "C")
        total_gastos = tot_a + tot_b + tot_c
        recaudado    = sum(_tf(p["monto_recibido"]) for p in p_rows)
        deuda_pend   = sum(_tf(p["monto_deuda"]) for p in p_rows if not p["pagado"])

        row1 = ctk.CTkFrame(self.body, fg_color="transparent"); row1.pack(fill="x", pady=(10, 20))
        
        def metric_card(parent, title, value, subtitle, outline_color=None):
            c = ctk.CTkFrame(parent, fg_color=C["surface2"], corner_radius=16, height=140)
            c.pack(side="left", fill="x", expand=True, padx=6)
            c.pack_propagate(False)
            
            if outline_color:
                bar = ctk.CTkFrame(c, width=6, fg_color=outline_color, corner_radius=6)
                bar.pack(side="left", fill="y", pady=20, padx=(10, 0))
            else:
                ctk.CTkFrame(c, width=6, fg_color="transparent").pack(side="left")
                
            inner = ctk.CTkFrame(c, fg_color="transparent")
            inner.pack(side="left", fill="both", expand=True, padx=15, pady=20)
            
            T(inner, title.upper(), size=11, bold=True, color=C["text2"]).pack(anchor="w")
            T(inner, str(value), size=36, bold=True, color=C["text"]).pack(anchor="w", pady=(10, 0))
            T(inner, subtitle, size=11, color=C["text2"]).pack(anchor="w", pady=(6, 0))
            return c

        metric_card(row1, "Total Unidades", n_unis, "Unidades activas", outline_color=C["accent"])
        metric_card(row1, "Pagados", pagaron, "Recibidos este mes", outline_color=C["success"])
        metric_card(row1, "Pendiente", pendientes, "Unidades con deuda", outline_color=C["danger"])
        metric_card(row1, "% Cobranza", f"{pct_cob:.1f}%", "Tasa de eficiencia", outline_color=C["text2"])

        row2 = ctk.CTkFrame(self.body, fg_color="transparent"); row2.pack(fill="both", expand=True, pady=10, padx=6)
        row2.columnconfigure(0, weight=2); row2.columnconfigure(1, weight=1)
        row2.rowconfigure(0, weight=1)
        
        fin = ctk.CTkFrame(row2, fg_color=C["surface2"], corner_radius=16)
        fin.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        hh = ctk.CTkFrame(fin, fg_color="transparent")
        hh.pack(fill="x", padx=24, pady=(24, 6))
        T(hh, "Resumen Financiero", size=20, bold=True).pack(side="left")
        
        # Legend (Ingresos, Egresos) mocks
        lg = ctk.CTkFrame(hh, fg_color="transparent"); lg.pack(side="right")
        T(lg, "EGRESOS", size=10, bold=True, color=C["text2"]).pack(side="right", padx=10)
        ctk.CTkFrame(lg, width=12, height=12, corner_radius=6, fg_color=C["warning"]).pack(side="right")
        T(lg, "INGRESOS", size=10, bold=True, color=C["text2"]).pack(side="right", padx=10)
        ctk.CTkFrame(lg, width=12, height=12, corner_radius=6, fg_color=C["accent_h"]).pack(side="right")

        T(fin, "Comparativa historica de flujos de caja (Actual)", size=12, color=C["text2"]).pack(anchor="w", padx=24)
        
        fin_stats = ctk.CTkFrame(fin, fg_color="transparent")
        fin_stats.pack(fill="x", padx=24, pady=(40, 20))
        
        def st_item(parent, label, val, c=C["text"]):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(side="left", expand=True, fill="x")
            T(f, label.upper(), size=11, bold=True, color=C["text2"]).pack(anchor="w")
            T(f, f"${_fmt(val)}", size=26, bold=True, color=c).pack(anchor="w", pady=(8,0))
            
        st_item(fin_stats, "Recaudado", recaudado, C["success"])
        st_item(fin_stats, "Gastos del Mes", total_gastos, C["warning"])
        st_item(fin_stats, "Deuda Flotante", deuda_pend, C["danger"])
        
        gb = ctk.CTkFrame(fin, fg_color=C["surface"], corner_radius=12)
        gb.pack(fill="x", padx=24, pady=20)
        T(gb, "Desglose de Gastos", size=12, bold=True, color=C["text2"]).pack(anchor="w", padx=16, pady=(16, 8))
        d_f = ctk.CTkFrame(gb, fg_color="transparent"); d_f.pack(fill="x", padx=16, pady=(0, 16))
        T(d_f, f"Cat A: ${_fmt(tot_a)}", size=13).pack(side="left", expand=True, anchor="w")
        T(d_f, f"Cat B: ${_fmt(tot_b)}", size=13).pack(side="left", expand=True, anchor="w")
        T(d_f, f"Cat C: ${_fmt(tot_c)}", size=13).pack(side="left", expand=True, anchor="w")

        pend = ctk.CTkFrame(row2, fg_color=C["surface2"], corner_radius=16)
        pend.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        p_hdr = ctk.CTkFrame(pend, fg_color="transparent")
        p_hdr.pack(fill="x", padx=20, pady=(24, 6))
        T(p_hdr, "Cobranzas Pendientes", size=16, bold=True).pack(side="left")
        B(p_hdr, "VER TODO", w=70, h=24, color="transparent", hover_color=C["surface"], text_color=C["accent"]).pack(side="right")
        T(pend, f"Periodo actual", size=11, color=C["text2"]).pack(anchor="w", padx=20)
        
        deudores_lst = [p for p in p_rows if not p["pagado"] and _tf(p["monto_deuda"]) > 0]
        deudores_lst.sort(key=lambda x: _tf(x["monto_deuda"]), reverse=True)
        
        sc = SF(pend); sc.pack(fill="both", expand=True, padx=10, pady=10)
        if not deudores_lst:
            T(sc, "No hay deuda pendiente.", color=C["success"], size=12).pack(pady=40)
        else:
            for d in deudores_lst[:15]:
                uid = d["unidad_id"]
                u_info = next((u for u in unis if u["id"] == uid), {})
                p_nam = u_info.get("propietario") or "Sin Asignar"
                if len(p_nam) > 18: p_nam = p_nam[:15] + "..."
                
                dr = ctk.CTkFrame(sc, fg_color=C["surface"], corner_radius=10)
                dr.pack(fill="x", pady=6, padx=6)
                
                bd = ctk.CTkFrame(dr, fg_color=C["row_alt"], corner_radius=8, width=44, height=44)
                bd.pack(side="left", padx=12, pady=12); bd.pack_propagate(False)
                T(bd, u_info.get("unidad", ""), size=12, bold=True).place(relx=0.5, rely=0.5, anchor="center")
                
                info = ctk.CTkFrame(dr, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True, pady=12)
                T(info, p_nam, size=13, bold=True, color=C["text"]).pack(anchor="w")
                T(info, f"Piso {u_info.get('piso','-')}, Unidad {u_info.get('unidad','-')}", size=10, color=C["text2"]).pack(anchor="w", pady=(2,0))
                
                monto = ctk.CTkFrame(dr, fg_color="transparent")
                monto.pack(side="right", padx=15, pady=12)
                T(monto, f"${_fmt(d['monto_deuda'])}", size=13, bold=True, color=C["danger"]).pack(anchor="e")
                T(monto, "Vence: 15 OCT", size=9, color=C["text2"]).pack(anchor="e", pady=(4,0))
