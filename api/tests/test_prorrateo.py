"""
Prorrateo de gastos por coeficiente (GET /api/finanzas/pagos).

imp_mes de una unidad = tot_categoria_A * coef_a/100 + tot_B * coef_b/100 + tot_C * coef_c/100
                         + suma de sus gastos_particulares del periodo.
"""
from .conftest import crear_unidad, crear_gasto


def test_prorratea_categoria_a_segun_coeficiente(client, consorcio):
    cid = consorcio["id"]
    u1 = crear_unidad(client, cid, unidad="1", coef_a=60.0, coef_b=0.0, coef_c=0.0)
    u2 = crear_unidad(client, cid, unidad="2", coef_a=40.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    res = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"})
    assert res.status_code == 200
    rows = {r["unidad_id"]: r for r in res.json()["unidades"]}

    assert rows[u1["id"]]["imp_mes"] == 600.0
    assert rows[u2["id"]]["imp_mes"] == 400.0


def test_prorratea_tres_categorias_con_coeficientes_independientes(client, consorcio):
    cid = consorcio["id"]
    u1 = crear_unidad(client, cid, unidad="1", coef_a=50.0, coef_b=100.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)
    crear_gasto(client, cid, "2026-01", categoria="B", monto=500.0)
    crear_gasto(client, cid, "2026-01", categoria="C", monto=999.0)  # coef_c=0 -> no debe afectar a u1

    res = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"})
    row = next(r for r in res.json()["unidades"] if r["unidad_id"] == u1["id"])

    # 1000*0.50 + 500*1.00 + 999*0.00 = 500 + 500 + 0
    assert row["imp_mes"] == 1000.0


def test_gasto_particular_solo_afecta_a_su_unidad(client, consorcio):
    cid = consorcio["id"]
    u1 = crear_unidad(client, cid, unidad="1", coef_a=50.0, coef_b=0.0, coef_c=0.0)
    u2 = crear_unidad(client, cid, unidad="2", coef_a=50.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    res = client.post(
        "/api/finanzas/gastos_particulares",
        json={"unidad_id": u1["id"], "descripcion": "Multa por ruidos molestos", "monto": 300.0},
        params={"consorcio_id": cid, "periodo": "2026-01"},
    )
    assert res.status_code == 201

    rows = {r["unidad_id"]: r for r in
            client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}).json()["unidades"]}

    # u1: prorrateo (500) + particular (300) = 800. u2: solo prorrateo (500), sin la multa.
    assert rows[u1["id"]]["imp_mes"] == 800.0
    assert rows[u2["id"]]["imp_mes"] == 500.0


def test_reserva_se_calcula_como_porcentaje_del_importe_del_mes(client, consorcio):
    # El consorcio del fixture tiene reserva_pct = 5.0
    cid = consorcio["id"]
    crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=2000.0)

    res = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"})
    row = res.json()["unidades"][0]

    assert row["imp_mes"] == 2000.0
    assert row["reserva"] == 100.0  # 5% de 2000
    assert row["total_pagar"] == 2100.0


def test_categoria_sin_gastos_no_rompe_el_prorrateo(client, consorcio):
    """Un consorcio sin gastos cargados en el periodo debe devolver importes en cero, no un error."""
    cid = consorcio["id"]
    crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=100.0, coef_c=100.0)

    res = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"})
    assert res.status_code == 200
    row = res.json()["unidades"][0]
    assert row["imp_mes"] == 0.0
    assert row["en_mora"] is False


def test_redondeo_monetario_a_dos_decimales(client, consorcio):
    """El sistema usa ROUND_HALF_UP a 2 decimales para evitar arrastre de flotantes."""
    cid = consorcio["id"]
    crear_unidad(client, cid, unidad="1", coef_a=33.33, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=100.0)

    res = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"})
    row = res.json()["unidades"][0]

    # 100 * 33.33/100 = 33.33 exacto -> no deberia arrastrar ruido de punto flotante
    assert row["imp_mes"] == 33.33
