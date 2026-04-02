"""
Gestor de Consorcios - Dialog Windows
VentanaHistorial, VentanaConsorcio
"""
import customtkinter as ctk
from tkinter import messagebox

from gestor.widgets import C, _F, T, E, B, divider, SF
from gestor.db import db
from gestor.helpers import _tf, _fmt, _pl_of


class VentanaHistorial(ctk.CTkToplevel):
    def __init__(self, parent, uid, nombre, unidad_num):
        super().__init__(parent)
        self.title(f"Historial - Unidad {unidad_num} | {nombre}")
        self.geometry("760x480"); self.resizable(True, True)
        self.configure(fg_color=C["bg"]); self.grab_set()
        T(self, f"Historial de Pagos  -  Unidad {unidad_num}  |  {nombre}",
            size=14, bold=True).pack(padx=24, pady=(18,4), anchor="w")
        divider(self).pack(fill="x", padx=24, pady=(0,8))
        _COLS = [("Periodo", 120), ("Deuda Bruta", 120), ("Recibido", 110),
                 ("Telec/Vs", 90), ("Saldo Neto", 110), ("Estado", 90)]
        ch = ctk.CTkFrame(self, fg_color=C["accent"], corner_radius=8)
        ch.pack(fill="x", padx=16, pady=(0,4))
        for tx, ww in _COLS:
            ctk.CTkLabel(ch, text=tx, width=ww, anchor="center",
                font=_F(size=10, weight="bold")).pack(side="left", padx=4, pady=6)
        sf = SF(self); sf.pack(fill="both", expand=True, padx=16, pady=4)
        with db() as con:
            rows = con.execute(
                "SELECT * FROM pagos WHERE unidad_id=? ORDER BY periodo DESC", (uid,)
            ).fetchall()
        if not rows:
            T(sf, "Sin historial de pagos registrado.", color=C["text2"]).pack(pady=30)
            return
        for idx, r in enumerate(rows):
            bg = C["surface2"] if idx % 2 == 0 else C["row_alt"]
            frm = ctk.CTkFrame(sf, fg_color=bg, corner_radius=6); frm.pack(fill="x", pady=2)
            deuda = _tf(r["monto_deuda"]); rec = _tf(r["monto_recibido"])
            telec = _tf(dict(r).get("telec", 0.0))
            saldo_neto = max(0.0, deuda)  # monto_deuda ya tiene rec y telec restados
            pagado_flag = bool(r["pagado"])
            ctk.CTkLabel(frm, text=_pl_of(r["periodo"]), width=120, anchor="center").pack(side="left", padx=4, pady=6)
            ctk.CTkLabel(frm, text=f"${_fmt(deuda)}", width=120, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(frm, text=f"${_fmt(rec)}", width=110, anchor="e",
                text_color=C["success"]).pack(side="left", padx=4)
            ctk.CTkLabel(frm, text=f"${_fmt(telec)}", width=90, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(frm, text=f"${_fmt(saldo_neto)}", width=110, anchor="e",
                text_color=C["danger"] if saldo_neto > 0.01 else C["text"]).pack(side="left", padx=4)
            ctk.CTkLabel(frm, text="Pagado" if pagado_flag else "Pendiente", width=90, anchor="center",
                text_color=C["success"] if pagado_flag else C["danger"],
                font=_F(size=10, weight="bold")).pack(side="left", padx=4)


class VentanaConsorcio(ctk.CTkToplevel):
    def __init__(self, parent, on_save, data=None):
        super().__init__(parent)
        self.on_save = on_save; self.data = data
        self.title("Nuevo Consorcio" if not data else "Editar Consorcio")
        self.geometry("460x620"); self.resizable(False, False)
        self.configure(fg_color=C["bg"]); self.grab_set()
        T(self, "Nuevo Consorcio" if not data else "Editar Consorcio",
            size=17, bold=True).pack(padx=30, pady=(22, 4), anchor="w")
        divider(self).pack(fill="x", padx=30, pady=(0, 14))
        p = {"padx": 30, "pady": 5}
        for label, attr, ph in [
            ("Nombre del Consorcio", "e_n", "Ej: Consorcio Av. Corrientes 1234"),
            ("CUIT",                 "e_c", "XX-XXXXXXXX-X"),
            ("Direccion",            "e_d", "Calle, numero, ciudad"),
        ]:
            T(self, label, size=11, color=C["text2"]).pack(**p, anchor="w")
            e = E(self, ph, w=400); e.pack(**p)
            setattr(self, attr, e)
        T(self, "Cantidad de Unidades", size=11, color=C["text2"]).pack(**p, anchor="w")
        self.e_u = E(self, "0", w=100); self.e_u.pack(**p, anchor="w")
        T(self, "% Reserva (se aplica automaticamente en Estado de Pagos)", size=11, color=C["text2"]).pack(**p, anchor="w")
        self.e_res = E(self, "0.0", w=100); self.e_res.pack(**p, anchor="w")
        T(self, "Dia de vencimiento (del mes siguiente, ej: 10)", size=11, color=C["text2"]).pack(**p, anchor="w")
        self.e_vto = E(self, "10", w=100); self.e_vto.pack(**p, anchor="w")
        B(self, "  Guardar Consorcio  ", self._guardar, w=400, h=44).pack(pady=20, padx=30)
        if data:
            for attr, key in [("e_n","nombre"),("e_c","cuit"),("e_d","direccion")]:
                getattr(self, attr).insert(0, data.get(key) or "")
            self.e_u.insert(0, str(data.get("unidades", 0)))
            self.e_res.insert(0, str(_tf(data.get("reserva_pct", 0.0))))
            self.e_vto.insert(0, str(data.get("dia_vto", 10) or 10))
        self.bind("<Return>", lambda e: self._guardar())

    def _guardar(self):
        nombre = self.e_n.get().strip()
        if not nombre: return
        try:
            unidades = int(self.e_u.get() or 0)
        except ValueError:
            messagebox.showerror("Error de validacion",
                "El campo 'Cantidad de Unidades' debe ser un numero entero.", parent=self)
            return
        reserva_pct = _tf(self.e_res.get())
        try: dia_vto = int(self.e_vto.get() or 10)
        except ValueError: dia_vto = 10
        row = (nombre, self.e_c.get().strip(), self.e_d.get().strip(), unidades, reserva_pct, dia_vto)
        with db() as con:
            if self.data:
                con.execute(
                    "UPDATE consorcios SET nombre=?,cuit=?,direccion=?,unidades=?,reserva_pct=?,dia_vto=? WHERE id=?",
                    row + (self.data["id"],))
            else:
                con.execute(
                    "INSERT INTO consorcios(nombre,cuit,direccion,unidades,reserva_pct,dia_vto) VALUES(?,?,?,?,?,?)",
                    row)
        self.on_save(); self.destroy()
