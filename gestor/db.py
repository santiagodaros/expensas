"""
Gestor de Consorcios - Database & Data Layer
DB access, encryption, config, email, importers, query helpers.
"""
import sqlite3, os, threading, smtplib, base64, hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from gestor.helpers import DB_PATH, KEY_PATH, _tf, _pl_of

# --- ENCRIPTACION DE DATOS SENSIBLES ---
_SENSITIVE_KEYS = {"smtp_pass", "git_token"}
_ENC_PREFIX    = "ENC1:"   # legacy XOR
_ENC_PREFIX_V2 = "ENC2:"   # Fernet (AES-128-CBC + HMAC)

_FERNET_KEY_PATH = os.path.join(os.path.dirname(KEY_PATH), "consorcios_fernet.key")
_fernet_instance = None

def _get_fernet():
    """Devuelve instancia Fernet, generando la clave si no existe."""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance
    try:
        from cryptography.fernet import Fernet
        if os.path.isfile(_FERNET_KEY_PATH):
            with open(_FERNET_KEY_PATH, "rb") as f:
                key = f.read().strip()
        else:
            key = Fernet.generate_key()
            with open(_FERNET_KEY_PATH, "wb") as f:
                f.write(key)
        _fernet_instance = Fernet(key)
        return _fernet_instance
    except Exception:
        return None

def _get_key() -> bytes:
    """Lee o genera la clave XOR legacy (backward-compat)."""
    if os.path.isfile(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            raw = f.read()
        if len(raw) == 32:
            return raw
    key = os.urandom(32)
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    return key

def _enc_val(val: str) -> str:
    """Encripta con Fernet (AES); fallback a XOR si cryptography no disponible."""
    if not val:
        return val
    fernet = _get_fernet()
    if fernet:
        return _ENC_PREFIX_V2 + fernet.encrypt(val.encode("utf-8")).decode("ascii")
    # Fallback XOR
    key = _get_key()
    data = val.encode("utf-8")
    xored = bytes(b ^ key[i % 32] for i, b in enumerate(data))
    return _ENC_PREFIX + base64.b64encode(xored).decode("ascii")

def _dec_val(val: str) -> str:
    """Desencripta ENC2 (Fernet) o ENC1 (XOR legacy)."""
    if not val:
        return val
    if val.startswith(_ENC_PREFIX_V2):
        try:
            fernet = _get_fernet()
            if fernet:
                return fernet.decrypt(val[len(_ENC_PREFIX_V2):].encode("ascii")).decode("utf-8")
        except Exception:
            return ""
    if val.startswith(_ENC_PREFIX):
        try:
            key = _get_key()
            xored = base64.b64decode(val[len(_ENC_PREFIX):])
            data = bytes(b ^ key[i % 32] for i, b in enumerate(xored))
            return data.decode("utf-8")
        except Exception:
            return ""
    return val


# --- BASE DE DATOS ---
_db_local = threading.local()

class _DBCtx:
    def __enter__(self):
        tl = _db_local
        if not getattr(tl, "con", None):
            con = sqlite3.connect(DB_PATH, check_same_thread=False)
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys = ON")
            tl.con = con
        self._con = tl.con
        return self._con

    def __exit__(self, exc_type, *_):
        if exc_type:
            self._con.rollback()
        else:
            self._con.commit()
        # Los threads de background (email/PDF) cierran su conexion al terminar
        if threading.current_thread() is not threading.main_thread():
            try: self._con.close()
            except Exception: pass
            _db_local.con = None

def db():
    return _DBCtx()

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS consorcios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, cuit TEXT,
            direccion TEXT, unidades INTEGER DEFAULT 0,
            reserva_pct REAL DEFAULT 0.0,
            dia_vto INTEGER DEFAULT 10
        );
        CREATE TABLE IF NOT EXISTS unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consorcio_id INTEGER NOT NULL,
            unidad TEXT NOT NULL,
            piso TEXT DEFAULT '',
            dpto TEXT DEFAULT '',
            propietario TEXT,
            inquilino TEXT,
            coef_a REAL DEFAULT 0.0,
            coef_b REAL DEFAULT 0.0,
            coef_c REAL DEFAULT 0.0,
            email TEXT,
            FOREIGN KEY(consorcio_id) REFERENCES consorcios(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consorcio_id INTEGER NOT NULL, periodo TEXT NOT NULL,
            categoria TEXT, descripcion TEXT, monto REAL DEFAULT 0.0,
            FOREIGN KEY(consorcio_id) REFERENCES consorcios(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidad_id INTEGER NOT NULL, periodo TEXT NOT NULL,
            pagado INTEGER DEFAULT 0, monto_deuda REAL DEFAULT 0.0,
            monto_recibido REAL DEFAULT 0.0,
            reserva REAL DEFAULT 0.0,
            redondeo REAL DEFAULT 0.0,
            saldo_inicial REAL DEFAULT 0.0,
            telec REAL DEFAULT 0.0,
            UNIQUE(unidad_id, periodo),
            FOREIGN KEY(unidad_id) REFERENCES unidades(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        );
    """)
    con.commit(); con.close()

def _migrate():
    with db() as con:
        for col, typ, default in [
            ("piso",   "TEXT", "''"),
            ("dpto",   "TEXT", "''"),
            ("coef_a", "REAL", "0.0"),
            ("coef_b", "REAL", "0.0"),
            ("coef_c", "REAL", "0.0"),
        ]:
            try: con.execute(f"ALTER TABLE unidades ADD COLUMN {col} {typ} DEFAULT {default}")
            except Exception: pass
        for col in ["monto_recibido", "reserva", "redondeo"]:
            try: con.execute(f"ALTER TABLE pagos ADD COLUMN {col} REAL DEFAULT 0.0")
            except Exception: pass
        try: con.execute("ALTER TABLE consorcios ADD COLUMN reserva_pct REAL DEFAULT 0.0")
        except Exception: pass
        try: con.execute("ALTER TABLE pagos ADD COLUMN saldo_inicial REAL DEFAULT 0.0")
        except Exception: pass
        try: con.execute("ALTER TABLE consorcios ADD COLUMN dia_vto INTEGER DEFAULT 10")
        except Exception: pass
        try: con.execute("ALTER TABLE pagos ADD COLUMN telec REAL DEFAULT 0.0")
        except Exception: pass
        try: con.execute("CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)")
        except Exception: pass
        try: con.execute("ALTER TABLE unidades ADD COLUMN email TEXT")
        except Exception: pass
        try: con.execute("ALTER TABLE pagos ADD COLUMN imp_mes_override REAL")
        except Exception: pass
        try: con.execute("ALTER TABLE gastos ADD COLUMN comprobante_path TEXT")
        except Exception: pass
        # Indices de performance
        try: con.execute("CREATE INDEX IF NOT EXISTS idx_pagos_uid_per ON pagos(unidad_id, periodo)")
        except Exception: pass
        try: con.execute("CREATE INDEX IF NOT EXISTS idx_gastos_cid_per ON gastos(consorcio_id, periodo)")
        except Exception: pass
        try: con.execute("CREATE INDEX IF NOT EXISTS idx_unidades_cid ON unidades(consorcio_id)")
        except Exception: pass
        # WAL mode + cache para escrituras más rápidas
        try:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA cache_size=10000")
            con.execute("PRAGMA synchronous=NORMAL")
        except Exception: pass

# --- QUERY HELPER: dos periodos en una sola consulta ---
def _fetch_pagos_2per(con, uid_list, per_a, per):
    """Trae pagos de dos periodos (anterior y actual) en una sola query."""
    if not uid_list:
        return [], []
    ph = ",".join("?" * len(uid_list))
    rows = con.execute(
        f"SELECT * FROM pagos WHERE periodo IN (?,?) AND unidad_id IN ({ph})",
        [per_a, per] + uid_list
    ).fetchall()
    p_ant = [r for r in rows if r["periodo"] == per_a]
    p_act = [r for r in rows if r["periodo"] == per]
    return p_ant, p_act


# --- CONFIG HELPERS (con cache en memoria) ---
_cfg_cache: dict = {}

def _load_cfg_cache():
    """Carga toda la tabla configuracion en memoria de una sola vez."""
    global _cfg_cache
    try:
        with db() as con:
            rows = con.execute("SELECT clave, valor FROM configuracion").fetchall()
        _cfg_cache = {r[0]: r[1] for r in rows}
    except Exception:
        _cfg_cache = {}

def get_cfg(key, default=""):
    raw = _cfg_cache.get(key, default)
    if raw is None: raw = default
    return _dec_val(raw) if key in _SENSITIVE_KEYS else raw

def set_cfg(key, val):
    stored = _enc_val(val) if key in _SENSITIVE_KEYS and val else val
    with db() as con:
        con.execute(
            "INSERT INTO configuracion(clave,valor) VALUES(?,?) "
            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
            (key, stored))
    _cfg_cache[key] = stored

# --- EMAIL ---
def _send_boleta_email(smtp_cfg, to_email, pdf_bytes, periodo, nombre_cons):
    msg = MIMEMultipart()
    msg["From"]    = smtp_cfg.get("from") or smtp_cfg.get("user", "")
    msg["To"]      = to_email
    msg["Subject"] = f"Expensas {_pl_of(periodo)} - {nombre_cons}"
    cuerpo = (
        f"Estimado propietario/inquilino,\n\n"
        f"Se adjunta la boleta de expensas del consorcio {nombre_cons} "
        f"correspondiente al periodo {_pl_of(periodo)}.\n\n"
        f"Por favor, ante cualquier consulta no dude en comunicarse con la administracion.\n\n"
        f"Saludos,\nAdministracion de Consorcios"
    )
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))
    att = MIMEBase("application", "octet-stream")
    att.set_payload(pdf_bytes)
    encoders.encode_base64(att)
    att.add_header("Content-Disposition", f'attachment; filename="boleta_{periodo}.pdf"')
    msg.attach(att)
    port = int(smtp_cfg.get("port") or 587)
    with smtplib.SMTP(smtp_cfg["server"], port, timeout=15) as s:
        s.starttls()
        s.login(smtp_cfg["user"], smtp_cfg["pass"])
        s.send_message(msg)

# --- VACUUM PERIODICO ---
def _maybe_vacuum():
    """Ejecuta VACUUM si no se hizo en los ultimos 30 dias."""
    try:
        from datetime import datetime as _dt
        last = get_cfg("last_vacuum", "")
        today = _dt.now().strftime("%Y-%m-%d")
        if last:
            if (_dt.strptime(today, "%Y-%m-%d") - _dt.strptime(last, "%Y-%m-%d")).days < 30:
                return
        # VACUUM no puede correr dentro de una transaccion; usar conexion directa
        import sqlite3 as _sq3
        con = _sq3.connect(DB_PATH, isolation_level=None)
        con.execute("VACUUM")
        con.close()
        set_cfg("last_vacuum", today)
    except Exception:
        pass

# --- IMPORTACION EXCEL UNIDADES ---
def importar_excel(path, consorcio_id):
    try:
        import pandas as pd
    except ImportError:
        return 0, "pandas no instalado. Ejecuta: pip install pandas openpyxl"
    try:
        df = pd.read_excel(path, sheet_name=0, header=None)
    except Exception as e:
        return 0, str(e)

    c_uf = -1; start_row = -1
    for r_idx in range(min(20, len(df))):
        for c_idx, val in enumerate(df.iloc[r_idx]):
            v = str(val).strip().lower().replace(".", "")
            if v in ("uf", "unidad"):
                c_uf = c_idx; start_row = r_idx + 1; break
        if start_row != -1: break
    if c_uf == -1:
        return 0, "Error: No se encontro la columna 'U.F.' en el archivo."

    def get_val(row, offset):
        idx = c_uf + offset
        if idx < 0 or idx >= len(row): return ""
        v = str(row.iloc[idx]).strip()
        return "" if v.lower() in ("nan", "none", "<na>") else v

    def get_float(row, offset):
        v = get_val(row, offset)
        if not v: return 0.0
        try:
            f = float(v.replace(",", ".").replace("%", ""))
            if 0 < abs(f) <= 1.5: f = round(f * 100, 6)
            return f
        except Exception: return 0.0

    try:
        count = 0
        with db() as con:
            con.execute("DELETE FROM unidades WHERE consorcio_id=?", (consorcio_id,))
            for r_idx in range(start_row, len(df)):
                row = df.iloc[r_idx]
                uf_val = get_val(row, 0)
                if not uf_val or "total" in uf_val.lower(): continue
                try: uf_str = str(int(float(uf_val)))
                except Exception: uf_str = uf_val
                piso = get_val(row, -2); dpto = get_val(row, -1)
                nom  = get_val(row, 1)
                cb   = get_float(row, 2); cc = get_float(row, 3); ca = get_float(row, 4)
                con.execute(
                    "INSERT INTO unidades (consorcio_id, unidad, piso, dpto, propietario, coef_a, coef_b, coef_c) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (consorcio_id, uf_str, piso, dpto, nom, ca, cb, cc))
                count += 1
    except Exception as e:
        return 0, str(e)
    return count, None

# --- IMPORTACION EXCEL GASTOS ---
def importar_excel_gastos(path, consorcio_id, periodo):
    try:
        import pandas as pd
    except ImportError:
        return 0, "pandas no instalado. Ejecuta: pip install pandas openpyxl"
    try:
        df = pd.read_excel(path, sheet_name=0)
    except Exception as e:
        return 0, str(e)

    try:
        count = 0
        with db() as con:
            con.execute("DELETE FROM gastos WHERE consorcio_id=? AND periodo=?", (consorcio_id, periodo))
            for _, row in df.iterrows():
                if len(row) < 3: continue
                cat_val = str(row.iloc[0]).strip().upper()
                if cat_val not in ["A", "B", "C"]: cat_val = "A"
                desc_val = str(row.iloc[1]).strip()
                if not desc_val or str(desc_val).lower() in ("nan", "nat"): continue
                monto_val = _tf(row.iloc[2])
                if monto_val <= 0: continue
                con.execute(
                    "INSERT INTO gastos (consorcio_id, periodo, categoria, descripcion, monto) VALUES (?,?,?,?,?)",
                    (consorcio_id, periodo, cat_val, desc_val, monto_val))
                count += 1
    except Exception as e:
        return 0, str(e)
    return count, None
