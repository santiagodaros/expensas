"""
API Database - SQLite connection dependency for FastAPI.
En produccion (frozen): usa %APPDATA%\GestorConsorcios\consorcios.db
En desarrollo: usa la raiz del proyecto.
"""
import sqlite3
import sys
import os
import shutil


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
