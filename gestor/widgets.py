"""
Gestor de Consorcios - UI Widgets & Helpers
Shared UI primitives: color palette, font cache, widget factories, _PeriodBar.
"""
import customtkinter as ctk
from gestor.helpers import _pa_of, _pn_of, _pl_of, _pk_now

C = {
    "bg":        "#0B0C10",
    "surface":   "#131419",
    "surface2":  "#1C1D24",
    "row_alt":   "#181920",
    "accent":    "#3B82F6",
    "accent_h":  "#2563EB",
    "success":   "#10B981",
    "warning":   "#F59E0B",
    "danger":    "#EF4444",
    "text":      "#FFFFFF",
    "text2":     "#9CA3AF",
    "border":    "#2A2A35",
}

# --- FONT CACHE (evita recrear objetos CTkFont en cada render) ---
_font_cache: dict = {}
def _F(size=12, weight="normal", family="Inter"):
    key = (size, weight, family)
    f = _font_cache.get(key)
    if f is None:
        kw = {"size": size, "weight": weight}
        if family: kw["family"] = family
        f = ctk.CTkFont(**kw)
        _font_cache[key] = f
    return f

# ===== HELPERS UI ===========================================================
def T(parent, text, size=12, bold=False, color=None, **kw):
    if "font" not in kw: kw["font"] = _F(size=size, weight="bold" if bold else "normal")
    return ctk.CTkLabel(parent, text=text, text_color=color or C["text"], **kw)

def E(parent, ph="", w=200, **kw):
    return ctk.CTkEntry(parent, placeholder_text=ph, width=w,
        fg_color=C["surface2"], border_color=C["border"],
        text_color=C["text"], corner_radius=8, **kw)

def B(parent, text, cmd=None, color=None, w=140, h=36, **kw):
    if "font" not in kw: kw["font"] = _F(size=12, weight="bold")
    if "fg_color" not in kw: kw["fg_color"] = color or C["accent"]
    if "hover_color" not in kw: kw["hover_color"] = C["accent_h"] if not color else color
    if "corner_radius" not in kw: kw["corner_radius"] = 10
    return ctk.CTkButton(parent, text=text, command=cmd, width=w, height=h, **kw)

class SF(ctk.CTkScrollableFrame):
    def __init__(self, p, **kw):
        super().__init__(p, fg_color="transparent",
            scrollbar_button_color=C["accent"],
            scrollbar_button_hover_color=C["accent_h"], **kw)

def divider(parent):
    return ctk.CTkFrame(parent, height=1, fg_color=C["border"])

def _clear(container):
    """Destruye hijos en batch: oculta el contenedor para evitar recalculos de layout intermedios."""
    pack_info = None
    try: pack_info = container.pack_info()
    except Exception: pass
    if pack_info:
        container.pack_forget()
    for w in container.winfo_children():
        w.destroy()
    if pack_info:
        container.pack(**pack_info)

# ===== WIDGET SELECTOR DE PERIODO ==========================================
class _PeriodBar(ctk.CTkFrame):
    """Barra de navegacion de mes/anio con botones < y >."""
    def __init__(self, parent, on_change, app=None, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._app = app
        self._per = app.periodo if app else _pk_now()
        self._cb  = on_change
        B(self, "<", self._prev, w=32, h=30).pack(side="left", padx=2)
        self.lbl = T(self, _pl_of(self._per), size=13, bold=True)
        self.lbl.pack(side="left", padx=10)
        B(self, ">", self._nxt, w=32, h=30).pack(side="left", padx=2)

    def get(self):
        return self._per

    def _prev(self):
        self._per = _pa_of(self._per)
        if self._app: self._app.periodo = self._per
        self.lbl.configure(text=_pl_of(self._per))
        self._cb()

    def _nxt(self):
        self._per = _pn_of(self._per)
        if self._app: self._app.periodo = self._per
        self.lbl.configure(text=_pl_of(self._per))
        self._cb()
