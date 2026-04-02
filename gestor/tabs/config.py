"""
Gestor de Consorcios - Tab Configuracion
"""
import customtkinter as ctk
import os
import threading
from tkinter import messagebox

from gestor.widgets import C, _F, T, E, B, divider, SF
from gestor.db import get_cfg, set_cfg
from gestor.helpers import LOG_PATH


class TabConfiguracion(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app; self._entries = {}; self._build()

    def _build(self):
        h = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0); h.pack(fill="x")
        T(h, "Configuracion del Sistema", size=20, bold=True).pack(side="left", padx=24, pady=16)
        B(h, "  Guardar  ", self._save, w=140, h=38, color=C["success"]).pack(side="right", padx=20)
        B(h, "Ver log errores", self._ver_log, w=140, h=38, color=C["surface2"]).pack(side="right", padx=(0,8))
        B(h, "Probar SMTP", self._test_smtp, w=120, h=38, color=C["surface2"]).pack(side="right", padx=(0,4))
        sf_wrap = ctk.CTkScrollableFrame(self, fg_color="transparent")
        sf_wrap.pack(fill="both", expand=True)
        outer = ctk.CTkFrame(sf_wrap, fg_color="transparent")
        outer.pack(anchor="n", padx=60, pady=30, fill="x")
        # Categorias
        sect = ctk.CTkFrame(outer, fg_color=C["surface"], corner_radius=12)
        sect.pack(fill="x", pady=(0, 16))
        T(sect, "Nombres de Categorias de Gastos", size=13, bold=True).pack(padx=20, pady=(16,6), anchor="w")
        divider(sect).pack(fill="x", padx=20, pady=(0,8))
        for key, label, default in [
            ("nombre_cat_a", "Categoria A", "Gastos Comunes"),
            ("nombre_cat_b", "Categoria B", "Fuerza Motriz"),
            ("nombre_cat_c", "Categoria C", "Locales"),
        ]:
            T(sect, label, size=11, color=C["text2"]).pack(padx=20, pady=(4,0), anchor="w")
            e = E(sect, default, w=500); e.pack(padx=20, pady=2, anchor="w")
            val = get_cfg(key, default)
            if val: e.delete(0, "end"); e.insert(0, val)
            self._entries[key] = e
        ctk.CTkFrame(sect, height=12, fg_color="transparent").pack()
        # SMTP
        sect2 = ctk.CTkFrame(outer, fg_color=C["surface"], corner_radius=12)
        sect2.pack(fill="x", pady=(0, 16))
        T(sect2, "Envio de Email (SMTP)", size=13, bold=True).pack(padx=20, pady=(16,6), anchor="w")
        divider(sect2).pack(fill="x", padx=20, pady=(0,8))
        for key, label, default, pw_field in [
            ("smtp_server", "Servidor SMTP",             "smtp.gmail.com", False),
            ("smtp_port",   "Puerto",                    "587",            False),
            ("smtp_user",   "Usuario / Email remitente", "",               False),
            ("smtp_pass",   "Contrasena",                "",               True),
        ]:
            T(sect2, label, size=11, color=C["text2"]).pack(padx=20, pady=(4,0), anchor="w")
            e = E(sect2, default, w=500)
            if pw_field: e.configure(show="*")
            e.pack(padx=20, pady=2, anchor="w")
            val = get_cfg(key, default)
            if val: e.delete(0, "end"); e.insert(0, val)
            self._entries[key] = e
        ctk.CTkFrame(sect2, height=12, fg_color="transparent").pack()
        # GitHub / Vercel
        sect3 = ctk.CTkFrame(outer, fg_color=C["surface"], corner_radius=12)
        sect3.pack(fill="x", pady=(0, 16))
        T(sect3, "Publicacion Web (GitHub + Vercel)", size=13, bold=True).pack(padx=20, pady=(16,6), anchor="w")
        T(sect3, "Despues de generar expensas, el reporte HTML se sube automaticamente al repositorio.", size=10, color=C["text2"]).pack(padx=20, pady=(0,4), anchor="w")
        divider(sect3).pack(fill="x", padx=20, pady=(0,8))
        for key, label, default, pw_field in [
            ("git_repo_url", "URL del repositorio GitHub (https://github.com/usuario/repo.git)", "", False),
            ("git_token",    "Personal Access Token (GitHub - Settings - Developer settings - PAT)", "", True),
        ]:
            T(sect3, label, size=11, color=C["text2"]).pack(padx=20, pady=(4,0), anchor="w")
            e = E(sect3, default, w=500)
            if pw_field: e.configure(show="*")
            e.pack(padx=20, pady=2, anchor="w")
            val = get_cfg(key, default)
            if val: e.delete(0, "end"); e.insert(0, val)
            self._entries[key] = e
        ctk.CTkFrame(sect3, height=12, fg_color="transparent").pack()

    def _ver_log(self):
        if not os.path.isfile(LOG_PATH):
            self.app.show_toast("No hay errores registrados."); return
        win = ctk.CTkToplevel(self)
        win.title("Log de Errores"); win.geometry("820x500")
        win.configure(fg_color=C["bg"]); win.grab_set()
        T(win, "Log de Errores", size=14, bold=True).pack(padx=20, pady=(16,4), anchor="w")
        btn_row = ctk.CTkFrame(win, fg_color="transparent"); btn_row.pack(fill="x", padx=20, pady=(0,6))
        def _limpiar():
            if messagebox.askyesno("Limpiar log", "Borrar todo el historial de errores?", parent=win):
                open(LOG_PATH, "w").close()
                txt.configure(state="normal"); txt.delete("1.0", "end")
                txt.configure(state="disabled")
        B(btn_row, "Limpiar log", _limpiar, w=120, h=30, color=C["danger"]).pack(side="left")
        txt = ctk.CTkTextbox(win, fg_color=C["surface"], text_color=C["text"],
            font=_F(family="Courier New", size=10), wrap="none")
        txt.pack(fill="both", expand=True, padx=20, pady=(0,16))
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            txt.insert("1.0", content if content.strip() else "Sin errores registrados.")
        except Exception as e:
            txt.insert("1.0", f"Error al leer log: {e}")
        txt.configure(state="disabled")

    def _test_smtp(self):
        smtp_cfg = {
            "server": self._entries["smtp_server"].get().strip() if "smtp_server" in self._entries else "",
            "port":   self._entries["smtp_port"].get().strip()   if "smtp_port"   in self._entries else "587",
            "user":   self._entries["smtp_user"].get().strip()   if "smtp_user"   in self._entries else "",
            "pass":   self._entries["smtp_pass"].get().strip()   if "smtp_pass"   in self._entries else "",
        }
        if not smtp_cfg["server"] or not smtp_cfg["user"]:
            messagebox.showwarning("Faltan datos", "Completa servidor, usuario y contrasena antes de probar.", parent=self)
            return
        self.app.show_toast("Enviando email de prueba...", 8000)
        def _task():
            try:
                from gestor.db import _send_boleta_email
                _send_boleta_email(
                    smtp_cfg, smtp_cfg["user"],
                    b"", "0000-00", "Prueba de configuracion SMTP")
            except Exception as e:
                err = str(e)
                self.after(0, self.app.show_toast, f"Error SMTP: {err[:80]}", 7000)
                return
            self.after(0, self.app.show_toast, f"Email de prueba enviado a {smtp_cfg['user']}.")
        threading.Thread(target=_task, daemon=True).start()

    def _save(self):
        for key, e in self._entries.items():
            set_cfg(key, e.get().strip())
        self.app.show_toast("Configuracion guardada correctamente.")

    def refresh(self):
        for key, e in self._entries.items():
            defaults = {"nombre_cat_a": "Gastos Comunes", "nombre_cat_b": "Fuerza Motriz",
                        "nombre_cat_c": "Locales", "smtp_server": "smtp.gmail.com",
                        "smtp_port": "587", "smtp_user": "", "smtp_pass": "",
                        "git_repo_url": "", "git_token": ""}
            val = get_cfg(key, defaults.get(key, ""))
            e.delete(0, "end"); e.insert(0, val)
