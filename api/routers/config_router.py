"""Router: Configuracion del sistema"""
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import smtplib
from api.database import get_db, load_cfg_cache, get_cfg, set_cfg, dec_val, create_backup, backups_dir
from api.schemas import ConfigOut, ConfigUpdate, MessageOut, SmtpTestRequest, BackupOut
import os

router = APIRouter(tags=["Configuracion"])

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
    )

@router.put("/config", response_model=MessageOut)
def update_config(body: ConfigUpdate):
    data = body.model_dump(exclude_none=True)
    for key, val in data.items():
        set_cfg(key, val)
    return {"ok": True, "message": f"{len(data)} valores guardados"}


@router.post("/config/test_smtp", response_model=MessageOut)
def test_smtp(body: SmtpTestRequest):
    """Prueba usuario/contraseña contra el servidor SMTP sin guardar nada,
    para no tener que enviar una boleta real recién al primer error."""
    load_cfg_cache()
    smtp_pass = body.smtp_pass
    if not smtp_pass:
        raw = get_cfg("smtp_pass", "")
        smtp_pass = dec_val(raw) if raw else ""
    if not body.smtp_user or not smtp_pass:
        raise HTTPException(400, "Completá usuario y contraseña")
    try:
        port = int(body.smtp_port or 587)
    except ValueError:
        raise HTTPException(400, "Puerto inválido")
    try:
        with smtplib.SMTP(body.smtp_server, port, timeout=10) as s:
            s.starttls()
            s.login(body.smtp_user, smtp_pass)
        return {"ok": True, "message": "Conexión SMTP exitosa"}
    except Exception as e:
        raise HTTPException(400, detail=f"No se pudo conectar: {type(e).__name__}: {e}")


@router.post("/config/backup", response_model=BackupOut)
def backup_ahora(db: sqlite3.Connection = Depends(get_db)):
    # Se usa la ruta real de la conexion activa (no una constante global) para
    # que el backup respalde siempre la base que esta efectivamente en uso.
    db_path = next(r[2] for r in db.execute("PRAGMA database_list").fetchall() if r[1] == "main")
    path = create_backup(db_path)
    if not path:
        raise HTTPException(400, "No se encontró la base de datos para respaldar")
    total = len([f for f in os.listdir(backups_dir(db_path)) if f.startswith("consorcios_") and f.endswith(".db")])
    return {"ok": True, "message": "Backup creado correctamente", "path": path, "total_backups": total}
