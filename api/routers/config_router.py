"""Router: Configuracion del sistema"""
from fastapi import APIRouter, Depends
import sqlite3
from api.database import get_db, load_cfg_cache, get_cfg, set_cfg
from api.schemas import ConfigOut, ConfigUpdate, MessageOut
import sys, os

router = APIRouter(tags=["Configuracion"])

_SENSITIVE = {"smtp_pass", "git_token"}
_DEFAULTS = {"nombre_cat_a": "Gastos Comunes", "nombre_cat_b": "Fuerza Motriz",
              "nombre_cat_c": "Locales", "smtp_server": "smtp.gmail.com",
              "smtp_port": "587", "smtp_user": "", "smtp_pass": "",
              "git_repo_url": "", "git_token": ""}

@router.get("/config", response_model=ConfigOut)
def get_config():
    load_cfg_cache()
    return ConfigOut(
        nombre_cat_a=get_cfg("nombre_cat_a", "Gastos Comunes"),
        nombre_cat_b=get_cfg("nombre_cat_b", "Fuerza Motriz"),
        nombre_cat_c=get_cfg("nombre_cat_c", "Locales"),
        smtp_server=get_cfg("smtp_server", ""),
        smtp_port=get_cfg("smtp_port", "587"),
        smtp_user=get_cfg("smtp_user", ""),
        git_repo_url=get_cfg("git_repo_url", ""),
    )

@router.put("/config", response_model=MessageOut)
def update_config(body: ConfigUpdate):
    data = body.model_dump(exclude_none=True)
    for key, val in data.items():
        set_cfg(key, val)
    return {"ok": True, "message": f"{len(data)} valores guardados"}
