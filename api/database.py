"""
API Database - SQLite connection dependency for FastAPI.
En produccion (frozen): usa %APPDATA%\GestorConsorcios\consorcios.db
En desarrollo: usa la raiz del proyecto.
"""
import sqlite3
import sys
import os
import shutil
import base64
import hashlib


def _get_db_path() -> str:
    if getattr(sys, "frozen", False):
        # Produccion: almacenar en AppData para que sobreviva reinstalaciones
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_dir = os.path.join(app_data, "GestorConsorcios")
        os.makedirs(data_dir, exist_ok=True)
        db_dest = os.path.join(data_dir, "consorcios.db")

        # Migracion automatica: si la DB no existe en AppData pero hay una
        # junto al ejecutable (instalacion anterior), la copiamos una sola vez.
        if not os.path.exists(db_dest):
            legacy = os.path.join(os.path.dirname(sys.executable), "consorcios.db")
            if os.path.exists(legacy):
                shutil.copy2(legacy, db_dest)

        return db_dest
    else:
        # Desarrollo: raiz del proyecto
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "consorcios.db")


DB_PATH = _get_db_path()


def run_migrations(db_path: str):
    """Aplica migraciones idempotentes al inicio de la aplicacion."""
    con = sqlite3.connect(db_path)
    try:
        # Agregar columna tipo a gastos (ignorar si ya existe)
        try:
            con.execute("ALTER TABLE gastos ADD COLUMN tipo TEXT DEFAULT 'ordinario'")
            con.commit()
        except sqlite3.OperationalError:
            pass  # columna ya existe

        # Crear tabla gastos_particulares si no existe
        con.execute("""
            CREATE TABLE IF NOT EXISTS gastos_particulares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consorcio_id INTEGER NOT NULL,
                periodo TEXT NOT NULL,
                unidad_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                monto REAL DEFAULT 0.0,
                FOREIGN KEY(consorcio_id) REFERENCES consorcios(id) ON DELETE CASCADE,
                FOREIGN KEY(unidad_id) REFERENCES unidades(id) ON DELETE CASCADE
            )
        """)
        con.commit()

        # Tabla proveedores
        con.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consorcio_id INTEGER NOT NULL,
                razon_social TEXT NOT NULL,
                cuit TEXT,
                domicilio TEXT,
                cat_afip TEXT,
                cbu TEXT,
                FOREIGN KEY(consorcio_id) REFERENCES consorcios(id) ON DELETE CASCADE
            )
        """)
        con.commit()

        # FK proveedor_id en gastos
        try:
            con.execute("ALTER TABLE gastos ADD COLUMN proveedor_id INTEGER REFERENCES proveedores(id)")
            con.commit()
        except sqlite3.OperationalError:
            pass  # ya existe

        # Tabla sueldos
        con.execute("""
            CREATE TABLE IF NOT EXISTS sueldos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consorcio_id INTEGER NOT NULL,
                periodo TEXT NOT NULL,
                empleado TEXT NOT NULL,
                concepto TEXT DEFAULT 'Encargado',
                sueldo_bruto REAL DEFAULT 0.0,
                cargas_suterh REAL DEFAULT 0.0,
                cargas_fateryh REAL DEFAULT 0.0,
                otras_cargas REAL DEFAULT 0.0,
                total_gasto REAL DEFAULT 0.0,
                gasto_id INTEGER,
                FOREIGN KEY(consorcio_id) REFERENCES consorcios(id) ON DELETE CASCADE,
                FOREIGN KEY(gasto_id) REFERENCES gastos(id) ON DELETE SET NULL
            )
        """)
        con.commit()
    finally:
        con.close()


def get_db():
    """FastAPI Dependency: connection SQLite por request."""
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]

# --- ENCRIPTACION DE DATOS SENSIBLES ---
_SENSITIVE_KEYS = {"smtp_pass", "git_token"}
_ENC_PREFIX    = "ENC1:"   # legacy XOR
_ENC_PREFIX_V2 = "ENC2:"   # Fernet (AES-128-CBC + HMAC)

def _get_fernet_key_path():
    return os.path.join(os.path.dirname(DB_PATH), "consorcios_fernet.key")

def _get_legacy_key_path():
    return os.path.join(os.path.dirname(DB_PATH), "consorcios.key")

_fernet_instance = None

def _get_fernet():
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance
    try:
        from cryptography.fernet import Fernet
        key_path = _get_fernet_key_path()
        if os.path.isfile(key_path):
            with open(key_path, "rb") as f:
                key = f.read().strip()
        else:
            key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(key)
        _fernet_instance = Fernet(key)
        return _fernet_instance
    except Exception:
        return None

def _get_key() -> bytes:
    key_path = _get_legacy_key_path()
    if os.path.isfile(key_path):
        with open(key_path, "rb") as f:
            raw = f.read()
        if len(raw) == 32:
            return raw
    key = os.urandom(32)
    with open(key_path, "wb") as f:
        f.write(key)
    return key

def _enc_val(val: str) -> str:
    if not val:
        return val
    fernet = _get_fernet()
    if fernet:
        return _ENC_PREFIX_V2 + fernet.encrypt(val.encode("utf-8")).decode("ascii")
    key = _get_key()
    data = val.encode("utf-8")
    xored = bytes(b ^ key[i % 32] for i, b in enumerate(data))
    return _ENC_PREFIX + base64.b64encode(xored).decode("ascii")

def dec_val(val: str) -> str:
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

# --- CONFIG HELPERS ---
_cfg_cache: dict = {}

def load_cfg_cache():
    global _cfg_cache
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT clave, valor FROM configuracion").fetchall()
        _cfg_cache = {r["clave"]: r["valor"] for r in rows}
        con.close()
    except Exception:
        _cfg_cache = {}

def get_cfg(key: str, default: str = "") -> str:
    raw = _cfg_cache.get(key, default)
    if raw is None: raw = default
    return dec_val(raw) if key in _SENSITIVE_KEYS else raw

def set_cfg(key: str, val: str):
    stored = _enc_val(val) if key in _SENSITIVE_KEYS and val else val
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)"
        )
        con.execute(
            "INSERT INTO configuracion(clave,valor) VALUES(?,?) "
            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
            (key, stored)
        )
        con.commit()
        con.close()
        _cfg_cache[key] = stored
    except Exception:
        pass

