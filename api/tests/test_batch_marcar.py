"""POST /api/finanzas/pagos/batch_marcar — marca varias unidades como pagadas
de una vez, cobrando exactamente lo que cada una debia."""
from .conftest import crear_unidad, crear_gasto


def test_batch_marcar_paga_exactamente_lo_que_cada_unidad_debia(client, consorcio):
    cid = consorcio["id"]
    u1 = crear_unidad(client, cid, unidad="1", coef_a=60.0, coef_b=0.0, coef_c=0.0)
    u2 = crear_unidad(client, cid, unidad="2", coef_a=40.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    res = client.post("/api/finanzas/pagos/batch_marcar", json={
        "consorcio_id": cid, "periodo": "2026-01", "unidad_ids": [u1["id"], u2["id"]],
    })
    assert res.status_code == 200, res.text
    assert res.json()["message"] == "2 unidades marcadas como pagadas"

    rows = {r["unidad_id"]: r for r in client.get(
        "/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}
    ).json()["unidades"]}
    assert rows[u1["id"]]["pagado"] is True
    assert rows[u1["id"]]["total_pagar"] == 0.0
    assert rows[u2["id"]]["pagado"] is True
    assert rows[u2["id"]]["total_pagar"] == 0.0


def test_batch_marcar_solo_afecta_las_unidades_seleccionadas(client, consorcio):
    cid = consorcio["id"]
    u1 = crear_unidad(client, cid, unidad="1", coef_a=60.0, coef_b=0.0, coef_c=0.0)
    u2 = crear_unidad(client, cid, unidad="2", coef_a=40.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    client.post("/api/finanzas/pagos/batch_marcar", json={
        "consorcio_id": cid, "periodo": "2026-01", "unidad_ids": [u1["id"]],
    })

    rows = {r["unidad_id"]: r for r in client.get(
        "/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}
    ).json()["unidades"]}
    assert rows[u1["id"]]["pagado"] is True
    assert rows[u2["id"]]["pagado"] is False


def test_batch_marcar_con_saldo_a_favor_no_cobra_de_mas(client, consorcio):
    """Si una unidad ya tenia un credito que cubre todo el mes, el batch no
    debe pedirle plata: cobra $0 y la deja marcada como pagada."""
    cid = consorcio["id"]
    u1 = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0, saldo_apertura=-5000.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    res = client.post("/api/finanzas/pagos/batch_marcar", json={
        "consorcio_id": cid, "periodo": "2026-01", "unidad_ids": [u1["id"]],
    })
    assert res.status_code == 200

    rows = {r["unidad_id"]: r for r in client.get(
        "/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}
    ).json()["unidades"]}
    assert rows[u1["id"]]["pagado"] is True
    assert rows[u1["id"]]["monto_recibido"] == 0.0
