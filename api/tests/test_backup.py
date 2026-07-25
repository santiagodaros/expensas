"""POST /api/config/backup — copia timestamped de la base a Backups/.

Usa la ruta real de la conexion activa (la base temporal del fixture `client`),
nunca la constante global DB_PATH, para no tocar la base real durante los tests.
"""
import os


def test_backup_crea_un_archivo_en_backups(client, db_path):
    res = client.post("/api/config/backup")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["ok"] is True
    assert os.path.exists(body["path"])
    assert body["total_backups"] == 1

    dest_dir = os.path.join(os.path.dirname(db_path), "Backups")
    assert os.path.dirname(body["path"]) == dest_dir


def test_backup_repetido_acumula_archivos(client):
    res1 = client.post("/api/config/backup")
    res2 = client.post("/api/config/backup")
    assert res1.json()["path"] != res2.json()["path"]
    assert res2.json()["total_backups"] == 2
