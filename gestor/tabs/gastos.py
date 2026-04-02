"""
Gestor de Consorcios - Tab Gastos (Split View)
"""
import customtkinter as ctk
import os
import shutil
from tkinter import messagebox, filedialog

from gestor.widgets import C, _F, T, E, B, SF, _clear, _PeriodBar
from gestor.db import db, get_cfg, importar_excel_gastos
from gestor.helpers import _tf, _pa_of, _pl_of, WEB_DIR, _log_error

def _fmt(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class TabGastos(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app
        self._pending = []  # Lista temporal
        self._build()

    def _build(self):
        # HEADER
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.pack(fill="x", padx=40, pady=(30, 0))
        
        T(h, "Carga de Gastos", size=24, bold=True).pack(side="left")
        self._perbar = _PeriodBar(h, self._render, app=self.app)
        self._perbar.pack(side="left", padx=30)
        
        # MAIN SPLIT
        self.split_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.split_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # --- LEFT PANE (Form) ---
        self.lp = ctk.CTkFrame(self.split_frame, fg_color=C["surface"], corner_radius=12, width=420)
        self.lp.pack(side="left", fill="y", padx=(0, 10))
        self.lp.pack_propagate(False)
        
        T(self.lp, "Nuevo Comprobante", size=18, bold=True).pack(anchor="w", padx=24, pady=(24, 4))
        T(self.lp, "Complete la información detallada del gasto\npara su procesamiento contable.", size=12, color=C["text2"]).pack(anchor="w", padx=24, pady=(0, 24))
        
        T(self.lp, "CATEGORÍA DEL GASTO", size=10, bold=True, color=C["text2"]).pack(anchor="w", padx=24, pady=(0, 6))
        
        nom_a = get_cfg("nombre_cat_a", "Mantenimiento General")
        nom_b = get_cfg("nombre_cat_b", "Fuerza Motriz")
        nom_c = get_cfg("nombre_cat_c", "Locales y Cocheras")
        self.cats = [f"A - {nom_a}", f"B - {nom_b}", f"C - {nom_c}"]
        self.var_cat = ctk.StringVar(value=self.cats[0])
        
        self.cb_cat = ctk.CTkOptionMenu(self.lp, values=self.cats, variable=self.var_cat, width=372, height=44,
            fg_color=C["surface2"], button_color=C["surface2"], font=_F(size=13), corner_radius=8)
        self.cb_cat.pack(padx=24, pady=(0, 20))
        
        T(self.lp, "DESCRIPCIÓN DETALLADA", size=10, bold=True, color=C["text2"]).pack(anchor="w", padx=24, pady=(0, 6))
        self.ent_desc = E(self.lp, ph="Ej: Reparación de ascensor...", w=372)
        self.ent_desc.configure(height=44)
        self.ent_desc.pack(padx=24, pady=(0, 20))
        
        # Monto y Fecha side by side
        row_mf = ctk.CTkFrame(self.lp, fg_color="transparent")
        row_mf.pack(fill="x", padx=24, pady=(0, 20))
        
        c1 = ctk.CTkFrame(row_mf, fg_color="transparent"); c1.pack(side="left", expand=True, fill="x", padx=(0,10))
        T(c1, "MONTO ($)", size=10, bold=True, color=C["text2"]).pack(anchor="w", pady=(0,6))
        self.ent_monto = E(c1, ph="0.00", w=176); self.ent_monto.configure(height=44)
        self.ent_monto.pack(anchor="w", fill="x")
        
        c2 = ctk.CTkFrame(row_mf, fg_color="transparent"); c2.pack(side="right", expand=True, fill="x")
        T(c2, "FECHA EMISIÓN", size=10, bold=True, color=C["text2"]).pack(anchor="w", pady=(0,6))
        import datetime
        cur_date = datetime.datetime.now().strftime("%d/%m/%Y")
        self.ent_fecha = E(c2, ph=cur_date, w=176); self.ent_fecha.configure(height=44)
        self.ent_fecha.insert(0, cur_date)
        self.ent_fecha.pack(anchor="w", fill="x")
        
        T(self.lp, "SOPORTE DIGITAL (PDF / JPG)", size=10, bold=True, color=C["text2"]).pack(anchor="w", padx=24, pady=(0, 6))
        self.btn_file = ctk.CTkButton(self.lp, text="Arrastrar archivo aquí\no haz click para explorar",
            width=372, height=90, fg_color=C["surface2"], hover_color=C["row_alt"],
            border_color=C["border"], border_width=1, corner_radius=8,
            text_color=C["text2"], font=_F(size=12), command=self._pick_file)
        self.btn_file.pack(padx=24, pady=(0, 20))
        self._current_file = None
        
        B(self.lp, "+ Agregar Comprobante", self._add_pending, w=372, h=44, color=C["accent"]).pack(padx=24, pady=(10,0))
        
        # --- RIGHT PANE (List + Accumulator) ---
        self.rp = ctk.CTkFrame(self.split_frame, fg_color="transparent")
        self.rp.pack(side="right", fill="both", expand=True)
        
        # Right Header
        rh = ctk.CTkFrame(self.rp, fg_color="transparent")
        rh.pack(fill="x", pady=(0, 20))
        
        rht = ctk.CTkFrame(rh, fg_color="transparent")
        rht.pack(side="left")
        T(rht, "Resumen de Carga Mensual", size=20, bold=True).pack(anchor="w")
        self.lbl_rsub = T(rht, "Octubre 2023 • Liquidación Actual", size=12, color=C["text2"])
        self.lbl_rsub.pack(anchor="w")
        
        rha = ctk.CTkFrame(rh, fg_color="transparent")
        rha.pack(side="right")
        B(rha, "Filtrar", w=90, h=36, color=C["surface"]).pack(side="left", padx=4)
        B(rha, "Exportar", self._export, w=90, h=36, color=C["surface"]).pack(side="left", padx=4)
        
        # Scrollable List
        self.list_wrap = ctk.CTkFrame(self.rp, fg_color=C["surface"], corner_radius=12)
        self.list_wrap.pack(fill="both", expand=True, pady=(0, 0))
        
        li_hdr = ctk.CTkFrame(self.list_wrap, fg_color=C["surface2"], corner_radius=8)
        li_hdr.pack(fill="x", padx=16, pady=(16, 8))
        T(li_hdr, "CATEGORÍA", size=10, bold=True, color=C["text2"]).pack(side="left", padx=16, pady=10)
        T(li_hdr, "DESCRIPCIÓN DEL GASTO", size=10, bold=True, color=C["text2"]).pack(side="left", padx=80, pady=10)
        
        self.sg = SF(self.list_wrap)
        self.sg.pack(fill="both", expand=True, padx=8, pady=0)
        
        # Accumulator Card
        self.acc = ctk.CTkFrame(self.rp, fg_color=C["surface"], corner_radius=12, height=140)
        self.acc.pack(fill="x", pady=(20, 0))
        self.acc.pack_propagate(False)
        
        T(self.acc, "MONTO TOTAL ACUMULADO", size=10, bold=True, color=C["text2"]).place(x=24, y=20)
        self.lbl_acc_total = T(self.acc, "$ 0.00", size=32, bold=True)
        self.lbl_acc_total.place(x=24, y=45)
        
        bdg = ctk.CTkFrame(self.acc, fg_color=C["surface2"], corner_radius=4)
        bdg.place(x=250, y=55)
        T(bdg, "ARS", size=10, bold=True, color=C["text2"]).pack(padx=8, pady=2)
        
        self.lbl_subneto = T(self.acc, "Subtotal Neto: $ 0.00", size=12, color=C["text2"])
        self.lbl_subneto.place(x=400, y=30)
        self.lbl_iva = T(self.acc, "IVA Aplicado (21%): $ 0.00", size=12, color=C["text2"])
        self.lbl_iva.place(x=400, y=60)
        
        # --- BOTTOM BAR (Fixed floating) ---
        self.bb = ctk.CTkFrame(self, height=80, fg_color=C["surface2"], corner_radius=0)
        self.bb.pack(side="bottom", fill="x")
        self.bb.pack_propagate(False)
        
        bi = ctk.CTkFrame(self.bb, fg_color=C["surface"], corner_radius=20, height=40)
        bi.pack(side="left", padx=40, pady=20)
        bi.pack_propagate(False)
        self.lbl_pend = T(bi, "0 Comprobantes Pendientes", size=12, bold=True)
        self.lbl_pend.place(relx=0.5, rely=0.5, anchor="center")
        
        mod = ctk.CTkFrame(self.bb, fg_color="transparent")
        mod.pack(side="left", padx=20, pady=20)
        T(mod, "Última modificación realizada\nhace unos momentos", size=11, color=C["text2"]).pack(anchor="w")
        
        B(self.bb, "Confirmar y Procesar Gastos", self._confirm, w=240, h=48, color=C["accent"]).pack(side="right", padx=40, pady=16)
        B(self.bb, "Descartar Cambios", self._discard, w=150, h=48, color="transparent", text_color=C["text2"]).pack(side="right", padx=10)
        
        self._render()

    def _pick_file(self):
        p = filedialog.askopenfilename(title="Seleccionar comprobante", filetypes=[("Dig", "*.pdf *.jpg *.png"), ("All", "*.*")])
        if p:
            self._current_file = p
            self.btn_file.configure(text=os.path.basename(p), fg_color=C["surface2"], text_color=C["success"])

    def _add_pending(self):
        desc = self.ent_desc.get().strip(); monto = _tf(self.ent_monto.get())
        if not desc or monto <= 0:
            self.app.show_toast("Ingrese descripción y monto válido."); return
        cat = self.var_cat.get()[0]
        self._pending.append({
            "id": None, "categoria": cat, "descripcion": desc, "monto": monto,
            "comprobante_path": self._current_file, "fecha": self.ent_fecha.get()
        })
        self.ent_desc.delete(0, "end"); self.ent_monto.delete(0, "end")
        self.btn_file.configure(text="Arrastrar archivo aquí\no haz click para explorar", fg_color=C["surface2"], text_color=C["text2"])
        self._current_file = None
        self._render_list()

    def _discard(self):
        if messagebox.askyesno("Descartar", "¿Descartar cambios no guardados?", parent=self):
            self._render()

    def _export(self):
        self.app.show_toast("Exportación no disp. en esta preview.")

    def _import_excel_g(self):
        if not self.app.consorcio_activo: return
        per = self._perbar.get()
        if not messagebox.askyesno("Importar Excel", f"¿Reemplazar gastos de {_pl_of(per)}?", parent=self): return
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if path:
            importar_excel_gastos(path, self.app.consorcio_activo["id"], per)
            self._render()

    def _copiar_anterior(self):
        pass

    def _aplicar_aumento(self):
        pass

    def _render(self, force=False):
        if not self.app.consorcio_activo:
            self.lbl_rsub.configure(text="Sin consorcio seleccionado")
            _clear(self.sg); self._pending.clear(); return
            
        cid = self.app.consorcio_activo["id"]; per = self._perbar.get()
        self.lbl_rsub.configure(text=f"{_pl_of(per)} • Liquidación Actual")
        
        with db() as con:
            rows = con.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=? ORDER BY id", (cid, per)).fetchall()
        self._pending = [dict(r) for r in rows]
        self._render_list()

    def _render_list(self):
        _clear(self.sg)
        tot = 0.0
        for idx, fi in enumerate(self._pending):
            tot += fi["monto"]
            f = ctk.CTkFrame(self.sg, fg_color="transparent")
            f.pack(fill="x", pady=2)
            
            c_col = C["accent"] if fi["categoria"]=="A" else (C["warning"] if fi["categoria"]=="B" else C["success"])
            bc = ctk.CTkFrame(f, fg_color=c_col, corner_radius=4, width=80, height=24)
            bc.pack(side="left", padx=16, pady=10); bc.pack_propagate(False)
            T(bc, f"CAT {fi['categoria']}", size=10, bold=True, color="white").place(relx=0.5, rely=0.5, anchor="center")
            
            T(f, fi["descripcion"][:45], size=13, color=C["text"]).pack(side="left", padx=(10, 10))
            T(f, f"${_fmt(fi['monto'])}", size=13, bold=True).pack(side="right", padx=16)
            if fi.get("comprobante_path"): T(f, "📎", size=12).pack(side="right", padx=8)
            
            def _rm(_id=idx):
                self._pending.pop(_id); self._render_list()
            B(f, "X", _rm, w=28, h=28, color="transparent", text_color=C["text2"], hover_color=C["row_alt"]).pack(side="right", padx=4)
            
            divider(self.sg).pack(fill="x", padx=16, pady=2)
            
        self.lbl_acc_total.configure(text=f"$ {_fmt(tot)}")
        self.lbl_subneto.configure(text=f"Subtotal Neto: $ {_fmt(tot * 0.79)}")
        self.lbl_iva.configure(text=f"IVA Aplicado: $ {_fmt(tot * 0.21)}")
        self.lbl_pend.configure(text=f"{len(self._pending)} Comprobantes Pendientes")

    def _confirm(self):
        if not self.app.consorcio_activo: return
        cid = self.app.consorcio_activo["id"]; per = self._perbar.get()
        cf = os.path.join(WEB_DIR, self.app.consorcio_activo["nombre"].replace(" ","_"), per, "comprobantes")
        try: os.makedirs(cf, exist_ok=True)
        except: cf = ""
        try:
            with db() as con:
                con.execute("SAVEPOINT sp_g")
                con.execute("DELETE FROM gastos WHERE consorcio_id=? AND periodo=?", (cid, per))
                ga = []
                for p in self._pending:
                    src = p.get("comprobante_path") or ""
                    dst = src
                    if src and os.path.isfile(src) and cf:
                        safe = "".join(c if c.isalnum() else "_" for c in p["descripcion"][:20])
                        test_dst = os.path.join(cf, f"{p['categoria']}_{safe}.pdf")
                        if os.path.abspath(src) != os.path.abspath(test_dst):
                            try: shutil.copy2(src, test_dst); dst = test_dst
                            except: pass
                    ga.append((cid, per, p["categoria"], p["descripcion"], p["monto"], dst))
                if ga: con.executemany("INSERT INTO gastos(consorcio_id,periodo,categoria,descripcion,monto,comprobante_path) VALUES(?,?,?,?,?,?)", ga)
                con.execute("RELEASE sp_g")
            self.app.show_toast("Resumen mensual guardado exitosamente.")
            self.app.invalidate_cache(cid, per)
        except Exception as e:
            self.app.show_toast(f"Error: {e}")

    def refresh(self): self._render()
