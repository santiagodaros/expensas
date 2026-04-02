"""Router: Configuracion del sistema"""
from fastapi import APIRouter, Depends
import sqlite3
from api.database import get_db
from api.schemas import ConfigOut, ConfigUpdate, MessageOut
import sys, os

# Reutilizamos las funciones de encriptacion del proyecto original
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from gestor.db import get_cfg, set_cfg, _load_cfg_cache
    _USE_GESTOR = True
except ImportError:
    _USE_GESTOR = False

router = APIRouter(tags=["Configuracion"])

_SENSITIVE = {"smtp_pass", "git_token"}
_DEFAULTS = {"nombre_cat_a": "Gastos Comunes", "nombre_cat_b": "Fuerza Motriz",
              "nombre_cat_c": "Locales", "smtp_server": "smtp.gmail.com",
              "smtp_port": "587", "smtp_user": "", "smtp_pass": "",
              "git_repo_url": "", "git_token": ""}

@router.get("/config", response_model=ConfigOut)
def get_config():
    if _USE_GESTOR:
        _load_cfg_cache()
        return ConfigOut(
            nombre_cat_a=get_cfg("nombre_cat_a", "Gastos Comunes"),
            nombre_cat_b=get_cfg("nombre_cat_b", "Fuerza Motriz"),
            nombre_cat_c=get_cfg("nombre_cat_c", "Locales"),
            smtp_server=get_cfg("smtp_server", ""),
            smtp_port=get_cfg("smtp_port", "587"),
            smtp_user=get_cfg("smtp_user", ""),
            git_repo_url=get_cfg("git_repo_url", ""),
        )
    return ConfigOut()

@router.put("/config", response_model=MessageOut)
def update_config(body: ConfigUpdate):
    if not _USE_GESTOR:
        return {"ok": False, "message": "gestor module not available"}
    data = body.model_dump(exclude_none=True)
    for key, val in data.items():
        set_cfg(key, val)
    return {"ok": True, "message": f"{len(data)} valores guardados"}
