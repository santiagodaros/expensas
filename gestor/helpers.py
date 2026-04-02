"""
Gestor de Consorcios - Helper Functions
Pure utility functions: formatting, period helpers, logging, paths.
"""
import os
import sys
from functools import lru_cache
from datetime import datetime

BASE_DIR = (os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)
            else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH  = os.path.join(BASE_DIR, "consorcios.db")
KEY_PATH = os.path.join(BASE_DIR, "consorcios.key")
LOG_PATH = os.path.join(BASE_DIR, "errores.log")
PDF_DIR  = os.path.join(BASE_DIR, "expensas_pdf")
WEB_DIR  = os.path.join(BASE_DIR, "web_reportes")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(WEB_DIR, exist_ok=True)

# --- HELPERS MATEMATICOS Y FORMATO ---
@lru_cache(maxsize=4096)
def _tf(val):
    if val is None or val == "": return 0.0
    try: return float(str(val).replace(",", ".").replace("$", "").replace(" ", "").strip())
    except Exception: return 0.0

def _fmt(val):
    try:
        f = float(val)
    except Exception:
        return "0,00"
    s = f"{f:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

# --- HELPERS DE PERIODO ---
_MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def _pk_now():
    return datetime.now().strftime("%Y-%m")

def _pa_of(k):
    y, m = int(k[:4]), int(k[5:])
    m -= 1
    if m == 0: m, y = 12, y - 1
    return f"{y}-{m:02d}"

def _pn_of(k):
    y, m = int(k[:4]), int(k[5:])
    m += 1
    if m == 13: m, y = 1, y + 1
    return f"{y}-{m:02d}"

def _pl_of(k):
    y, m = k.split("-")
    return f"{_MESES[int(m)]} {y}"

# --- LOG DE ERRORES ---
_LOG_MAX_KB = 200  # rotar cuando el log supera este tamano

def _log_error(context: str, exc: Exception):
    """Escribe un error con timestamp en errores.log. Rota si supera _LOG_MAX_KB."""
    try:
        import traceback
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n[{ts}] {context}\n{traceback.format_exc()}" + "-" * 60 + "\n"
        # Rotacion: si el archivo supera el limite, descartar la primera mitad
        if os.path.isfile(LOG_PATH) and os.path.getsize(LOG_PATH) > _LOG_MAX_KB * 1024:
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as lf:
                lines = lf.readlines()
            mid = len(lines) // 2
            with open(LOG_PATH, "w", encoding="utf-8") as lf:
                lf.writelines(lines[mid:])
        with open(LOG_PATH, "a", encoding="utf-8") as lf:
            lf.write(entry)
    except Exception:
        pass
