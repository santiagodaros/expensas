"""
Subida y apertura de comprobantes adjuntos a un gasto.

_comprobantes_base() apunta a ~/Documents/Expensas/Comprobantes en la vida real;
para no escribir ahí durante los tests, se monkeypatchea para usar tmp_path.
os.startfile() también se monkeypatchea: no queremos que un test abra una
ventana real del visor de PDFs del sistema operativo.
"""
from pathlib import Path
import api.routers.finanzas as finanzas_mod


def _crear_gasto(client, cid, periodo="2026-01"):
    return client.post(
        "/api/finanzas/gastos",
        json={"categoria": "A", "descripcion": "Test", "monto": 100.0, "tipo": "ordinario"},
        params={"consorcio_id": cid, "periodo": periodo},
    ).json()


def test_subir_comprobante_guarda_archivo_y_actualiza_el_gasto(client, consorcio, tmp_path, monkeypatch):
    monkeypatch.setattr(finanzas_mod, "_comprobantes_base", lambda: tmp_path)
    cid = consorcio["id"]
    gasto = _crear_gasto(client, cid)

    res = client.post(
        f"/api/finanzas/gastos/{gasto['id']}/comprobante",
        files={"file": ("factura.pdf", b"%PDF-1.4 contenido de prueba", "application/pdf")},
    )
    assert res.status_code == 200

    gastos = client.get("/api/finanzas/gastos", params={"consorcio": cid, "periodo": "2026-01"}).json()
    path = gastos[0]["comprobante_path"]
    assert path is not None
    assert Path(path).exists()
    assert Path(path).read_bytes().startswith(b"%PDF")


def test_subir_comprobante_rechaza_extension_no_permitida(client, consorcio, tmp_path, monkeypatch):
    monkeypatch.setattr(finanzas_mod, "_comprobantes_base", lambda: tmp_path)
    cid = consorcio["id"]
    gasto = _crear_gasto(client, cid)

    res = client.post(
        f"/api/finanzas/gastos/{gasto['id']}/comprobante",
        files={"file": ("instalador.exe", b"MZ", "application/octet-stream")},
    )
    assert res.status_code == 400


def test_subir_comprobante_gasto_inexistente_devuelve_404(client):
    res = client.post(
        "/api/finanzas/gastos/999999/comprobante",
        files={"file": ("factura.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert res.status_code == 404


def test_abrir_comprobante_sin_adjunto_devuelve_404(client, consorcio):
    gasto = _crear_gasto(client, consorcio["id"])
    res = client.get(f"/api/finanzas/gastos/{gasto['id']}/comprobante")
    assert res.status_code == 404


def test_abrir_comprobante_con_adjunto_dispara_el_visor_del_sistema(client, consorcio, tmp_path, monkeypatch):
    monkeypatch.setattr(finanzas_mod, "_comprobantes_base", lambda: tmp_path)
    called = {}
    monkeypatch.setattr(finanzas_mod.os, "startfile", lambda p: called.setdefault("path", p))

    gasto = _crear_gasto(client, consorcio["id"])
    client.post(
        f"/api/finanzas/gastos/{gasto['id']}/comprobante",
        files={"file": ("factura.pdf", b"%PDF-1.4", "application/pdf")},
    )

    res = client.get(f"/api/finanzas/gastos/{gasto['id']}/comprobante")
    assert res.status_code == 200
    assert "path" in called
