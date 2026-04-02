"""
Gestor de Consorcios - Tab Consorcios
"""
import customtkinter as ctk
import os
import threading
import tempfile
from tkinter import messagebox, filedialog

from gestor.widgets import C, _F, T, E, B, SF, divider, _clear
from gestor.db import db, get_cfg, importar_excel, _send_boleta_email, _fetch_pagos_2per
from gestor.helpers import _tf, _fmt, _pa_of, _pl_of
from gestor.pdf import generar_pdf_email_unidad
from gestor.tabs.dialogs import VentanaHistorial, VentanaConsorcio


class TabConsorcios(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app; self._rk_cards = None; self._rk_unis = None; self._build()

    def _build(self):
        h = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0); h.pack(fill="x")
        T(h, "Gestión de Consorcios y Unidades", size=24, bold=True).pack(side="left", padx=30, pady=20)
        B(h, "+ Nuevo Edificio", self._agregar, w=185, h=40, font=_F(size=13, weight="bold")).pack(side="right", padx=30, pady=20)
        
        body = ctk.CTkFrame(self, fg_color=C["bg"])
        body.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        body.columnconfigure(0, weight=0, minsize=320); body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        
        left = ctk.CTkFrame(body, fg_color=C["surface"], corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        lt = ctk.CTkFrame(left, fg_color="transparent")
        lt.pack(fill="x", padx=20, pady=20)
        T(lt, "Portafolio de Edificios", bold=True, size=15, color=C["text"]).pack(side="left")
        
        divider(left).pack(fill="x", padx=20)
        self.sc = SF(left); self.sc.pack(fill="both", expand=True, padx=10, pady=10)
        
        right = ctk.CTkFrame(body, fg_color=C["surface"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew")
        tr = ctk.CTkFrame(right, fg_color="transparent")
        tr.pack(fill="x", padx=20, pady=20)
        self.lbl_u = T(tr, "Unidades Funcionales", bold=True, size=18)
        self.lbl_u.pack(side="left")
        B(tr, "+ Agregar Unidad", self._add_uni, w=140, h=36).pack(side="right", padx=(10, 0))
        B(tr, "Importar Excel", self._import_excel, w=135, h=36, color=C["surface2"]).pack(side="right")
        
        divider(right).pack(fill="x", padx=20)
        self.su = SF(right); self.su.pack(fill="both", expand=True, padx=10, pady=10)
        bot = ctk.CTkFrame(right, fg_color="transparent")
        bot.pack(fill="x", padx=20, pady=(0, 20))
        B(bot, "Guardar Cambios", self._save_all_unis, w=200, h=40, color=C["success"]).pack(side="right")
        self._unit_rows = []
        self._render_cards(); self._render_unis()

    def _render_cards(self):
        with db() as con:
            rows = con.execute("SELECT * FROM consorcios ORDER BY nombre").fetchall()
        rk = tuple(r["id"] for r in rows)
        if rk == self._rk_cards: return
        self._rk_cards = rk
        _clear(self.sc)
        if not rows:
            T(self.sc, "No hay consorcios. Haz clic en + Nuevo Consorcio",
                color=C["text2"], size=11).pack(pady=30)
        for r in rows: self._card(dict(r))

    def _card(self, r):
        activo = self.app.consorcio_activo and self.app.consorcio_activo["id"] == r["id"]
        c = ctk.CTkFrame(self.sc,
            fg_color=C["surface2"] if activo else C["bg"],
            corner_radius=12, border_width=2 if activo else 1,
            border_color=C["accent"] if activo else C["border"])
        c.pack(fill="x", pady=6, padx=6)
        
        t_frame = ctk.CTkFrame(c, fg_color="transparent")
        t_frame.pack(fill="x", padx=16, pady=(16, 6))
        T(t_frame, r["nombre"], bold=True, size=14, color=C["accent"] if activo else C["text"]).pack(side="left")
        
        T(c, r.get("direccion") or "Sin dirección", size=11, color=C["text2"]).pack(padx=16, anchor="w", pady=(0, 4))
        T(c, f"{r.get('unidades',0)} unidades  •  CUIT: {r.get('cuit') or '-'}",
            size=11, color=C["text2"]).pack(padx=16, pady=(0,12), anchor="w")
            
        rid = r["id"]
        bf_grid = ctk.CTkFrame(c, fg_color="transparent")
        bf_grid.pack(fill="x", padx=16, pady=(0,16))
        
        if not activo:
            B(bf_grid, "Activar Selección", lambda i=rid: self._sel(i), h=32, color=C["surface2"], hover_color=C["border"]).pack(fill="x", pady=(0, 8))
            
        bf2 = ctk.CTkFrame(bf_grid, fg_color="transparent"); bf2.pack(fill="x")
        B(bf2, "Editar",  lambda i=rid: self._edit(i), h=30, color=C["surface2"]).pack(side="left", expand=True, fill="x", padx=(0,4))
        B(bf2, "Borrar",  lambda i=rid: self._del(i),  h=30, color=C["danger"]).pack(side="left", expand=True, fill="x", padx=(4,0))

    def _sel(self, cid):
        with db() as con:
            row = con.execute("SELECT * FROM consorcios WHERE id=?", (cid,)).fetchone()
        self.app.set_activo(dict(row)); self._render_cards(); self._render_unis()

    def _edit(self, cid):
        with db() as con:
            row = con.execute("SELECT * FROM consorcios WHERE id=?", (cid,)).fetchone()
        def _after_save():
            self._render_cards()
            if self.app.consorcio_activo and self.app.consorcio_activo["id"] == cid:
                with db() as con2:
                    updated = con2.execute("SELECT * FROM consorcios WHERE id=?", (cid,)).fetchone()
                if updated:
                    self.app.set_activo(dict(updated))
        VentanaConsorcio(self, _after_save, dict(row))

    def _del(self, cid):
        if not messagebox.askyesno("Confirmar borrado",
                "Borrar este consorcio y TODOS sus datos (unidades, gastos, pagos)?",
                parent=self):
            return
        with db() as con: con.execute("DELETE FROM consorcios WHERE id=?", (cid,))
        if self.app.consorcio_activo and self.app.consorcio_activo["id"] == cid:
            self.app.set_activo(None)
        self._render_cards(); self._render_unis()

    def _agregar(self): VentanaConsorcio(self, self._render_cards)

    def _import_excel(self):
        if not self.app.consorcio_activo:
            self.app.show_toast("Activa un consorcio primero."); return
        if not messagebox.askyesno("Confirmar importacion",
                "Esto reemplazara TODAS las unidades actuales del consorcio. Continuar?",
                parent=self):
            return
        path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if not path: return
        cid = self.app.consorcio_activo["id"]
        count, err = importar_excel(path, cid)
        if err:
            self.app.show_toast(f"Error: {err[:60]}")
        else:
            self.app.show_toast(f"{count} unidades importadas correctamente.")
            self._render_unis()

    def _render_unis(self, force=False):
        cid = self.app.consorcio_activo["id"] if self.app.consorcio_activo else None
        with db() as con:
            cnt = con.execute("SELECT COUNT(*) FROM unidades WHERE consorcio_id=?", (cid,)).fetchone()[0] if cid else 0
        rk = (cid, cnt)
        if not force and rk == self._rk_unis: return
        self._rk_unis = rk
        self._unit_rows = []
        _clear(self.su)
        if not self.app.consorcio_activo:
            T(self.su, "Selecciona un consorcio para ver sus unidades.", color=C["text2"]).pack(pady=30)
            return
        cid = self.app.consorcio_activo["id"]
        self.lbl_u.configure(text=f"Unidades -- {self.app.consorcio_activo['nombre']}")
        _COLS = [("Piso", 40), ("Dpto", 40), ("U.F.", 50), ("Propietario / Inquilino", 150),
                 ("Coef A%", 60), ("Coef B%", 60), ("Coef C%", 60), ("Email Contacto", 180), ("Acciones", 80)]
        h = ctk.CTkFrame(self.su, fg_color=C["surface2"], corner_radius=8)
        h.pack(fill="x", pady=(0,8))
        for txt, ww in _COLS:
            ctk.CTkLabel(h, text=txt.upper(), width=ww, font=_F(size=10, weight="bold"),
                text_color=C["text2"], anchor="center").pack(side="left", padx=4, pady=10)
        with db() as con:
            rows = con.execute(
                "SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (cid,)
            ).fetchall()
        for i, r in enumerate(rows): self._row_uni(dict(r), i)
        if rows:
            sa = sum(_tf(r["coef_a"]) for r in rows)
            sb = sum(_tf(r["coef_b"]) for r in rows)
            sc = sum(_tf(r["coef_c"]) for r in rows)
            ft = ctk.CTkFrame(self.su, fg_color=C["surface"], corner_radius=6)
            ft.pack(fill="x", pady=(8,2))
            ctk.CTkLabel(ft, text="SUMA TOTAL DE COEFICIENTES:", width=284, anchor="e",
                         font=_F(size=11, weight="bold")).pack(side="left", padx=3, pady=6)
            for val in (sa, sb, sc):
                ok = 99.5 <= val <= 100.5
                ctk.CTkLabel(ft, text=f"{val:.2f}", width=60, anchor="center",
                    text_color=C["success"] if ok else C["danger"],
                    font=_F(size=11, weight="bold")).pack(side="left", padx=3)
            if not (99.5 <= sa <= 100.5 and 99.5 <= sb <= 100.5 and 99.5 <= sc <= 100.5):
                bad = []
                if not 99.5 <= sa <= 100.5: bad.append(f"A={sa:.1f}%")
                if not 99.5 <= sb <= 100.5: bad.append(f"B={sb:.1f}%")
                if not 99.5 <= sc <= 100.5: bad.append(f"C={sc:.1f}%")
                ctk.CTkLabel(ft, text=f"  Advertencia: coef. no suman 100% ({', '.join(bad)})",
                    text_color=C["danger"], font=_F(size=10)).pack(side="left", padx=8)

    def _row_uni(self, r, idx=0):
        bg = C["surface2"] if idx % 2 == 0 else C["row_alt"]
        frm = ctk.CTkFrame(self.su, fg_color=bg, corner_radius=8)
        frm.pack(fill="x", pady=2)
        
        def e_str(val, ww, justify="center"):
            x = ctk.CTkEntry(frm, width=ww, fg_color="transparent", border_width=1, corner_radius=6,
                border_color=C["border"], text_color=C["text"], font=_F(size=12), justify=justify)
            x.insert(0, str(val) if val is not None else ""); x.pack(side="left", padx=4, pady=6)
            return x
        def e_num(val, ww):
            x = ctk.CTkEntry(frm, width=ww, fg_color="transparent", border_width=1, corner_radius=6,
                border_color=C["border"], text_color=C["text"], font=_F(size=12), justify="center")
            x.insert(0, f"{_tf(val):.2f}"); x.pack(side="left", padx=4, pady=6)
            return x
        eps = e_str(r.get("piso"),        40)
        edp = e_str(r.get("dpto"),        40)
        euf = e_str(r["unidad"],          50)
        enm = e_str(r.get("propietario"), 100, justify="left")
        eca = e_num(r.get("coef_a"),      60)
        ecb = e_num(r.get("coef_b"),      60)
        ecc = e_num(r.get("coef_c"),      60)
        eem = e_str(r.get("email") or "", 170, justify="left")
        rid = r["id"]
        def guardar():
            with db() as con:
                con.execute(
                    "UPDATE unidades SET piso=?,dpto=?,unidad=?,propietario=?,"
                    "coef_a=?,coef_b=?,coef_c=?,email=? WHERE id=?",
                    (eps.get(), edp.get(), euf.get(), enm.get(),
                     _tf(eca.get()), _tf(ecb.get()), _tf(ecc.get()), eem.get().strip(), rid))
                cid_r = r.get("consorcio_id")
                if cid_r:
                    all_u = con.execute(
                        "SELECT coef_a,coef_b,coef_c FROM unidades WHERE consorcio_id=?", (cid_r,)
                    ).fetchall()
                    sa2 = sum(_tf(u["coef_a"]) for u in all_u)
                    sb2 = sum(_tf(u["coef_b"]) for u in all_u)
                    sc2 = sum(_tf(u["coef_c"]) for u in all_u)
                    bad = [f"A={sa2:.1f}%" for _ in [1] if not 99.5<=sa2<=100.5] + \
                          [f"B={sb2:.1f}%" for _ in [1] if not 99.5<=sb2<=100.5] + \
                          [f"C={sc2:.1f}%" for _ in [1] if not 99.5<=sc2<=100.5]
                    if bad:
                        self.app.show_toast(f"Atencion: coef. no suman 100% - {', '.join(bad)}", 5000)
            self._render_unis(force=True)
        def eliminar():
            nom = r.get("propietario") or r.get("inquilino") or f"UF {r['unidad']}"
            if not messagebox.askyesno("Confirmar borrado",
                    f"Borrar la unidad {r['unidad']} ({nom}) y todos sus pagos?\n\nEsta accion no se puede deshacer.",
                    parent=self):
                return
            with db() as con: con.execute("DELETE FROM unidades WHERE id=?", (rid,))
            self._render_unis(force=True)
        def _test_email(_e=eem, _uid=rid, _u=r):
            addr = _e.get().strip()
            if not addr:
                self.app.show_toast("Ingresa un email primero.", 3000); return
            if not self.app.consorcio_activo:
                self.app.show_toast("Activa un consorcio primero.", 3000); return
            smtp_cfg = {
                "server": get_cfg("smtp_server"), "port": get_cfg("smtp_port", "587"),
                "user": get_cfg("smtp_user"),     "pass": get_cfg("smtp_pass"),
                "from": get_cfg("smtp_from"),
            }
            if not smtp_cfg["server"] or not smtp_cfg["user"]:
                self.app.show_toast("Configura SMTP en Configuracion antes de enviar.", 5000); return
            cons = dict(self.app.consorcio_activo)
            per  = self.app.periodo
            self.app.show_toast(f"Generando y enviando boleta a {addr}...")
            def _send():
                try:
                    cid = cons["id"]; per_a = _pa_of(per)
                    with db() as con:
                        unis = con.execute("SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)", (cid,)).fetchall()
                        gs   = con.execute("SELECT * FROM gastos WHERE consorcio_id=? AND periodo=?", (cid, per)).fetchall()
                        uid_list = [u["id"] for u in unis]
                        p_ant_rows, p_act_rows = _fetch_pagos_2per(con, uid_list, per_a, per)
                    pagos_map     = {p["unidad_id"]: dict(p) for p in p_act_rows}
                    deudas_map    = {p["unidad_id"]: _tf(p["monto_deuda"]) for p in p_ant_rows}
                    cobranza_map  = {p["unidad_id"]: _tf(p["monto_recibido"]) for p in p_act_rows}
                    saldo_ini_map = {p["unidad_id"]: _tf(dict(p).get("saldo_inicial", 0.0)) for p in p_act_rows}
                    telec_map     = {p["unidad_id"]: _tf(dict(p).get("telec", 0.0)) for p in p_act_rows}
                    unis_list = [dict(u) for u in unis]; gs_list = [dict(g) for g in gs]
                    pdf = generar_pdf_email_unidad(_uid, cons, unis_list, gs_list, pagos_map, deudas_map, cobranza_map, saldo_ini_map, telec_map, per)
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf_:
                        tmp = tf_.name
                    try:
                        pdf.output(tmp)
                        with open(tmp, "rb") as f: pdf_bytes = f.read()
                    finally:
                        try: os.unlink(tmp)
                        except Exception: pass
                    _send_boleta_email(smtp_cfg, addr, pdf_bytes, per, cons["nombre"])
                    try: self.app.after(0, self.app.show_toast, f"Boleta enviada a {addr}")
                    except Exception: pass
                except Exception as ex:
                    try: self.app.after(0, self.app.show_toast, f"Error al enviar: {ex}", 6000)
                    except Exception: pass
            threading.Thread(target=_send, daemon=True).start()
        bf = ctk.CTkFrame(frm, fg_color="transparent"); bf.pack(side="left", padx=3)
        B(bf, "@", _test_email, w=28, h=24, color=C["accent"]).pack(side="left", padx=1)
        B(bf, "X", eliminar,   w=28, h=24, color=C["danger"]).pack(side="left")
        self._unit_rows.append({"id": rid, "eps": eps, "edp": edp, "euf": euf,
                                 "enm": enm, "eca": eca, "ecb": ecb, "ecc": ecc, "eem": eem,
                                 "cid": r.get("consorcio_id")})

    def _save_all_unis(self):
        if not self._unit_rows: return
        with db() as con:
            for row in self._unit_rows:
                con.execute(
                    "UPDATE unidades SET piso=?,dpto=?,unidad=?,propietario=?,"
                    "coef_a=?,coef_b=?,coef_c=?,email=? WHERE id=?",
                    (row["eps"].get(), row["edp"].get(), row["euf"].get(), row["enm"].get(),
                     _tf(row["eca"].get()), _tf(row["ecb"].get()), _tf(row["ecc"].get()),
                     row["eem"].get().strip(), row["id"]))
        cid_r = self._unit_rows[0]["cid"] if self._unit_rows else None
        if cid_r:
            with db() as con:
                all_u = con.execute(
                    "SELECT coef_a,coef_b,coef_c FROM unidades WHERE consorcio_id=?", (cid_r,)
                ).fetchall()
            sa = sum(_tf(u["coef_a"]) for u in all_u)
            sb = sum(_tf(u["coef_b"]) for u in all_u)
            sc = sum(_tf(u["coef_c"]) for u in all_u)
            bad = ([f"A={sa:.1f}%"] if not 99.5<=sa<=100.5 else []) + \
                  ([f"B={sb:.1f}%"] if not 99.5<=sb<=100.5 else []) + \
                  ([f"C={sc:.1f}%"] if not 99.5<=sc<=100.5 else [])
            if bad:
                self.app.show_toast(f"Atencion: coef. no suman 100% - {', '.join(bad)}", 5000)
            else:
                self.app.show_toast("Unidades guardadas correctamente.")
        else:
            self.app.show_toast("Unidades guardadas correctamente.")
        self._render_unis(force=True)

    def _add_uni(self):
        if not self.app.consorcio_activo: return
        with db() as con:
            con.execute(
                "INSERT INTO unidades(consorcio_id,unidad,piso,dpto,propietario,coef_a,coef_b,coef_c)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (self.app.consorcio_activo["id"], "Nueva", "", "", "", 0.0, 0.0, 0.0))
        self._render_unis(force=True)

    def refresh(self): self._render_cards(); self._render_unis()

    def invalidate(self):
        """Fuerza reconstruccion en el proximo refresh."""
        self._rk_cards = None; self._rk_unis = None
