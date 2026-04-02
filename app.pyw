"""
Gestor de Consorcios | Python + CustomTkinter + SQLite + FPDF
UI Moderna Dark Professional - v4.5 (modular)
"""
import customtkinter as ctk
import os
import shutil
import socket as _socket
import atexit
from datetime import datetime

from gestor.helpers import BASE_DIR, DB_PATH, _pk_now, _pl_of
from gestor.db import init_db, _migrate, _load_cfg_cache, _maybe_vacuum
from gestor.widgets import C, _F, T, B, divider
from gestor.tabs.consorcios import TabConsorcios
from gestor.tabs.gastos import TabGastos
from gestor.tabs.pagos import TabPagos
from gestor.tabs.resumen import TabResumen
from gestor.tabs.deudores import TabDeudores
from gestor.tabs.generar import TabGenerar
from gestor.tabs.config import TabConfiguracion

APP_VERSION = "4.5"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ===== APLICACION PRINCIPAL ================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Consorcios")
        self.geometry("1360x830"); self.minsize(1100, 680)
        self.configure(fg_color=C["bg"])
        self.consorcio_activo = None; self._tj = None; self._current_tab_key = None
        self.periodo = _pk_now()
        self._data_cache = {}  # (cid, per) -> {unis, gastos, pagos_ant, pagos_act}
        self._build()

    def _build(self):
        # --- LEFT SIDEBAR ---
        sb = ctk.CTkFrame(self, width=250, fg_color=C["surface"], corner_radius=0)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)
        
        # Logo Area
        lo = ctk.CTkFrame(sb, fg_color="transparent", corner_radius=0)
        lo.pack(fill="x", padx=20, pady=(30, 30))
        T(lo, "Architectural", size=18, bold=True, color=C["text"]).pack(anchor="w")
        T(lo, "Ledger", size=18, bold=True, color=C["text"]).pack(anchor="w")
        T(lo, "MANAGEMENT SUITE", size=9, bold=True, color=C["text2"]).pack(anchor="w", pady=(4,0))
        
        # Navigation
        self._nb = []
        nav = [
            ("Dashboard",        "resumen"),
            ("Consorcios",       "consorcios"),
            ("Carga de Gastos",  "gastos"),
            ("Estado de Pagos",  "pagos"),
            ("Deudores",         "deudores"),
            ("Generar Expensas", "generar"),
            ("Configuracion",    "config"),
        ]
        
        self._nav_indicator = ctk.CTkFrame(sb, width=4, fg_color=C["accent"], corner_radius=0)
        
        for label, key in nav:
            b = ctk.CTkButton(sb, text=f"  {label}", width=250, height=44,
                fg_color="transparent", hover_color=C["surface2"],
                anchor="w", font=_F(size=14, weight="bold"),
                text_color=C["text2"], corner_radius=0,
                command=lambda k=key: self._nav(k))
            b.pack(pady=4)
            self._nb.append((b, key))
            
        # Profile Area
        prof = ctk.CTkFrame(sb, fg_color=C["surface2"], corner_radius=8)
        prof.pack(side="bottom", fill="x", padx=20, pady=20)
        T(prof, "Admin Principal", size=12, bold=True).pack(anchor="w", padx=15, pady=(15,0))
        T(prof, "SUPERUSUARIO", size=9, bold=True, color=C["text2"]).pack(anchor="w", padx=15, pady=(0,15))

        self.bind_all("<Control-s>", self._on_ctrl_s)
        
        # --- MAIN RIGHT AREA ---
        self.main_area = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

        # Top Bar
        self.topbar = ctk.CTkFrame(self.main_area, height=80, fg_color=C["bg"], corner_radius=0)
        self.topbar.pack(side="top", fill="x"); self.topbar.pack_propagate(False)
        
        tb_inner = ctk.CTkFrame(self.topbar, fg_color="transparent")
        tb_inner.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Search Bar centralizado
        search_fr = ctk.CTkFrame(tb_inner, fg_color=C["surface"], height=44, corner_radius=8)
        search_fr.pack(side="left", fill="none", pady=0)
        T(search_fr, "🔍", size=14, color=C["text2"]).pack(side="left", padx=(15, 5))
        search_entry = ctk.CTkEntry(search_fr, placeholder_text="Buscar registros, unidades, facturas...", 
            width=320, fg_color="transparent", border_width=0, text_color=C["text"])
        search_entry.pack(side="left", fill="y", pady=2)
        
        # Profile Section
        prof_fr = ctk.CTkFrame(tb_inner, fg_color="transparent")
        prof_fr.pack(side="right", padx=(20, 0))
        T(prof_fr, "Administración", size=12, bold=True).pack(anchor="e")
        T(prof_fr, "PERFIL ACTUAL", size=9, bold=True, color=C["text2"]).pack(anchor="e")
        
        # Consorcio Selector
        from gestor.db import db
        with db() as con:
            cons = con.execute("SELECT id, nombre, direccion FROM consorcios ORDER BY nombre").fetchall()
        self._consorcios_list = [dict(c) for c in cons]
        cb_vals = [c["nombre"] for c in cons] if cons else ["Sin consorcios"]
        
        self.cb_global_cons = ctk.CTkOptionMenu(tb_inner, values=cb_vals,
            width=200, height=44, fg_color="transparent", button_color="transparent",
            button_hover_color=C["row_alt"], text_color=C["text"],
            dropdown_fg_color=C["surface2"], dropdown_text_color=C["text"],
            dropdown_hover_color=C["row_alt"], font=_F(size=14, weight="bold"),
            command=self._on_global_cons_change)
        self.cb_global_cons.pack(side="right", padx=10)
        T(tb_inner, "🏢", size=16, color=C["text2"]).pack(side="right", padx=5)
        T(tb_inner, "🔔", size=16, color=C["text2"]).pack(side="right", padx=15)
        
        if self._consorcios_list:
            self.consorcio_activo = self._consorcios_list[0]
            self.cb_global_cons.set(self.consorcio_activo["nombre"])

        self.cont = ctk.CTkFrame(self.main_area, fg_color=C["bg"], corner_radius=0)
        self.cont.pack(side="top", fill="both", expand=True, padx=40, pady=(0, 30))
        
        self.toast = ctk.CTkLabel(self.main_area, text="",
            fg_color=C["success"], corner_radius=10,
            font=_F(size=13, weight="bold"), text_color="white",
            width=460, height=50)
            
        self.tabs = {}
        self._tab_pagos = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._nav("resumen")

    def _on_global_cons_change(self, choice):
        for c in self._consorcios_list:
            if c["nombre"] == choice:
                self.consorcio_activo = c
                break
        if self._current_tab_key in self.tabs:
            tab = self.tabs[self._current_tab_key]
            if hasattr(tab, "refresh"):
                tab.refresh()

    _TAB_CLASSES = {
        "resumen":    None,  # filled after class definitions
        "consorcios": None,
        "gastos":     None,
        "pagos":      None,
        "deudores":   None,
        "generar":    None,
        "config":     None,
    }

    def _nav(self, key):
        if self._current_tab_key and self._current_tab_key != key:
            cur = self.tabs.get(self._current_tab_key)
            if cur and getattr(cur, "_dirty", False):
                self.show_toast("Atencion: hay cambios sin guardar.", 4500)
        self._current_tab_key = key
        
        titles = {
            "resumen": "Dashboard",
            "consorcios": "Gestión de Consorcios",
            "gastos": "Carga de Gastos",
            "pagos": "Estado de Pagos",
            "deudores": "Lista de Deudores",
            "generar": "Generar Expensas",
            "config": "Configuración del Sistema"
        }
        for b, k in self._nb:
            if k == key:
                b.configure(fg_color=C["surface2"], text_color=C["text"])
                self.after(20, lambda bn=b: self._nav_indicator.place(x=0, y=bn.winfo_y(), height=bn.winfo_height()))
            else:
                b.configure(fg_color="transparent", text_color=C["text2"])
        for w in self.cont.winfo_children(): w.pack_forget()
        self.update_idletasks()
        if key not in self.tabs:
            cls = App._TAB_CLASSES.get(key)
            if cls is None:
                return
            self.tabs[key] = cls(self.cont, self)
            if key == "pagos":
                self._tab_pagos = self.tabs[key]
        tab = self.tabs[key]
        if hasattr(tab, "_perbar") and tab._perbar._per != self.periodo:
            tab._perbar._per = self.periodo
            tab._perbar.lbl.configure(text=_pl_of(self.periodo))
        tab.pack(fill="both", expand=True)
        if hasattr(tab, "refresh"):
            # Overlay opaco: cubre todo el tab mientras refresh() construye los widgets
            overlay = ctk.CTkFrame(tab, fg_color=C["bg"], corner_radius=0)
            overlay.place(x=0, y=0, relwidth=1, relheight=1)
            overlay.lift()
            ctk.CTkLabel(overlay, text="Cargando...",
                font=_F(size=15), text_color=C["text2"]).place(relx=0.5, rely=0.5, anchor="center")
            def _deferred_refresh(_t=tab, _ov=overlay):
                try:
                    _t.refresh()
                except Exception as e:
                    self.show_toast(f"Error interno cargando pestana: {e}", 5000)
                finally:
                    try: _ov.destroy()
                    except Exception: pass
            self.after(50, _deferred_refresh)

    # --- CACHE DE DATOS COMPARTIDA ---
    def get_period_data(self, cid, per):
        from gestor.helpers import _pa_of
        from gestor.db import db, _fetch_pagos_2per
        key = (cid, per)
        cached = self._data_cache.get(key)
        if cached is not None:
            return cached
        per_a = _pa_of(per)
        with db() as con:
            unis = con.execute(
                "SELECT * FROM unidades WHERE consorcio_id=? ORDER BY CAST(unidad AS INTEGER)",
                (cid,)).fetchall()
            gs = con.execute(
                "SELECT * FROM gastos WHERE consorcio_id=? AND periodo=?",
                (cid, per)).fetchall()
            uid_list = [u["id"] for u in unis]
            p_ant, p_act = _fetch_pagos_2per(con, uid_list, per_a, per)
        result = {"unis": unis, "gastos": gs, "pagos_ant": p_ant, "pagos_act": p_act}
        self._data_cache[key] = result
        return result

    def invalidate_cache(self, cid=None, per=None):
        if cid is None and per is None:
            self._data_cache.clear(); return
        self._data_cache = {k: v for k, v in self._data_cache.items()
                           if not ((cid is None or k[0] == cid) and
                                   (per is None or k[1] == per))}

    def set_activo(self, data):
        self.consorcio_activo = data
        if data:
            self.cb_global_cons.set(data["nombre"])
        else:
            self.cb_global_cons.set("Sin consorcios")

    def show_toast(self, msg, ms=3400):
        self.toast.configure(text=f"  {msg}  ")
        self.toast.place(relx=0.5, rely=0.97, anchor="s")
        self.toast.lift()
        if self._tj: self.after_cancel(self._tj)
        self._tj = self.after(ms, self.toast.place_forget)

    def _on_ctrl_s(self, event=None):
        if self._current_tab_key == "gastos":
            tab = self.tabs.get("gastos")
            if tab and hasattr(tab, "_confirm"):
                tab._confirm()

    def _on_close(self):
        try:
            bk_dir = os.path.join(BASE_DIR, "backups")
            os.makedirs(bk_dir, exist_ok=True)
            _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bk_name = f"backup_{_ts}.db"
            shutil.copy2(DB_PATH, os.path.join(bk_dir, bk_name))
            bk_files = sorted(
                [f for f in os.listdir(bk_dir) if f.startswith("backup_") and f.endswith(".db")])
            for old in bk_files[:-10]:
                try: os.remove(os.path.join(bk_dir, old))
                except Exception: pass
        except Exception:
            pass
        self.destroy()


# Wire lazy tab class references
App._TAB_CLASSES = {
    "resumen":    TabResumen,
    "consorcios": TabConsorcios,
    "gastos":     TabGastos,
    "pagos":      TabPagos,
    "deudores":   TabDeudores,
    "generar":    TabGenerar,
    "config":     TabConfiguracion,
}


def _auto_backup():
    """Crea un backup automatico al arrancar si no hay uno del dia de hoy."""
    try:
        if not os.path.isfile(DB_PATH):
            return
        bk_dir = os.path.join(BASE_DIR, "backups")
        os.makedirs(bk_dir, exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        existing = [f for f in os.listdir(bk_dir)
                    if f.startswith(f"auto_{today}") and f.endswith(".db")]
        if existing:
            return
        _ts2 = datetime.now().strftime("%Y%m%d_%H%M%S")
        bk_name = f"auto_{_ts2}.db"
        shutil.copy2(DB_PATH, os.path.join(bk_dir, bk_name))
        auto_files = sorted(
            [f for f in os.listdir(bk_dir) if f.startswith("auto_") and f.endswith(".db")])
        for old in auto_files[:-30]:
            try: os.remove(os.path.join(bk_dir, old))
            except Exception: pass
    except Exception:
        pass


# ===== INSTANCIA UNICA =====================================================
_LOCK_SOCK = None

def _acquire_single_instance():
    """Intenta reservar un puerto local para garantizar una sola instancia."""
    global _LOCK_SOCK
    try:
        _LOCK_SOCK = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        _LOCK_SOCK.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 0)
        _LOCK_SOCK.bind(("127.0.0.1", 47832))
        return True
    except OSError:
        return False


if __name__ == "__main__":
    if not _acquire_single_instance():
        import tkinter as tk
        from tkinter import messagebox
        _r = tk.Tk(); _r.withdraw()
        messagebox.showwarning(
            "Ya esta abierto",
            "El Gestor de Consorcios ya esta en ejecucion.\nRevisa la barra de tareas.")
        _r.destroy()
        raise SystemExit(0)
    atexit.register(_auto_backup)
    init_db()
    _migrate()
    _load_cfg_cache()
    _maybe_vacuum()
    _auto_backup()
    # DB integrity check
    try:
        from gestor.db import db as _db
        with _db() as _con:
            _ic = _con.execute("PRAGMA integrity_check").fetchone()
        if _ic and _ic[0] != "ok":
            import tkinter as tk
            from tkinter import messagebox
            _r = tk.Tk(); _r.withdraw()
            messagebox.showwarning(
                "Integridad de base de datos",
                f"La base de datos reporta un problema: {_ic[0]}\n\n"
                "Se recomienda restaurar un backup desde la carpeta 'backups'.\n"
                "La aplicacion intentara continuar de todas formas.",
                parent=_r)
            _r.destroy()
    except Exception:
        pass
    App().mainloop()
