"""GET /api/dashboard — KPIs agregados y ranking de deudores."""
from .conftest import crear_unidad, crear_gasto, registrar_pago


def test_kpis_cuentan_pagados_y_mora_correctamente(client, consorcio):
    cid = consorcio["id"]
    pagado = crear_unidad(client, cid, unidad="1", coef_a=50.0, coef_b=0.0, coef_c=0.0)
    moroso = crear_unidad(client, cid, unidad="2", coef_a=50.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    # unidad 1: paga exactamente lo que debe (500 prorrateo + 25 reserva)
    registrar_pago(client, unidad_id=pagado["id"], periodo="2026-01", pagado=1,
                    monto_recibido=525.0, reserva=25.0)
    # unidad 2: no paga nada -> queda en mora (sin registrar_pago, en_mora igual se calcula en la vista)

    res = client.get("/api/dashboard", params={"consorcio": cid, "periodo": "2026-01"})
    assert res.status_code == 200
    kpi = res.json()["kpi"]

    assert kpi["total_unidades"] == 2
    assert kpi["pagados"] == 1
    assert kpi["pendientes"] == 1
    assert kpi["v_recaudado"] == 525.0
    assert kpi["v_deuda"] == 525.0  # 500 + 25 reserva para la unidad morosa


def test_deudores_ordenados_de_mayor_a_menor_deuda(client, consorcio):
    cid = consorcio["id"]
    chica = crear_unidad(client, cid, unidad="1", coef_a=20.0, coef_b=0.0, coef_c=0.0)
    grande = crear_unidad(client, cid, unidad="2", coef_a=80.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)
    # Ninguna paga -> ambas en mora, la de coef_a=80 debe encabezar el ranking.

    res = client.get("/api/dashboard", params={"consorcio": cid, "periodo": "2026-01"})
    deudores = res.json()["deudores"]

    assert len(deudores) == 2
    assert deudores[0]["unidad_id"] == grande["id"]
    assert deudores[0]["total_pagar"] > deudores[1]["total_pagar"]


def test_consorcio_inexistente_devuelve_dashboard_vacio_sin_error(client):
    res = client.get("/api/dashboard", params={"consorcio": 999999, "periodo": "2026-01"})
    assert res.status_code == 200
    body = res.json()
    assert body["kpi"]["total_unidades"] == 0
    assert body["chart"] == []
    assert body["deudores"] == []


def test_chart_devuelve_ultimos_8_periodos_en_orden_cronologico(client, consorcio):
    cid = consorcio["id"]
    crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)

    res = client.get("/api/dashboard", params={"consorcio": cid, "periodo": "2026-01"})
    chart = res.json()["chart"]

    assert len(chart) == 8
    periodos = [c["periodo"] for c in chart]
    assert periodos == sorted(periodos)  # cronologico ascendente (mas viejo primero)
