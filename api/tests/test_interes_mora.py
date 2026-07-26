"""Interes punitorio mensual sobre mora, configurable por consorcio
(consorcios.interes_mora_pct). 0 = desactivado (comportamiento por defecto,
igual que antes de esta feature)."""
from .conftest import crear_unidad, crear_gasto, registrar_pago


def _crear_consorcio_con_interes(client, interes_pct):
    res = client.post("/api/consorcios", json={
        "nombre": "Consorcio Interes Test", "unidades": 0,
        "reserva_pct": 0.0, "dia_vto": 10, "interes_mora_pct": interes_pct,
    })
    assert res.status_code == 201, res.text
    return res.json()


def test_interes_mora_se_aplica_sobre_deuda_arrastrada(client):
    cons = _crear_consorcio_con_interes(client, 10.0)
    cid = cons["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(client, unidad_id=u["id"], periodo="2026-01", pagado=0, monto_recibido=0.0)
    # deuda enero = 1000 (sin reserva, reserva_pct=0 en este consorcio)

    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == 1100.0  # 1000 * 1.10
    assert feb["en_mora"] is True


def test_interes_mora_compone_mes_a_mes_si_sigue_sin_pagarse(client):
    cons = _crear_consorcio_con_interes(client, 10.0)
    cid = cons["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(client, unidad_id=u["id"], periodo="2026-01", pagado=0, monto_recibido=0.0)
    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == 1100.0

    registrar_pago(client, unidad_id=u["id"], periodo="2026-02", pagado=0, monto_recibido=0.0, saldo_inicial=1100.0)
    # deuda feb = 1100 (sin gastos nuevos en feb)
    mar = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-03"}).json()["unidades"][0]
    assert mar["saldo_anterior"] == 1210.0  # 1100 * 1.10, interes compuesto


def test_interes_mora_no_se_aplica_a_saldo_a_favor(client):
    cons = _crear_consorcio_con_interes(client, 10.0)
    cid = cons["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(client, unidad_id=u["id"], periodo="2026-01", pagado=1, monto_recibido=1200.0)
    # deuda enero = 1000 - 1200 = -200 (a favor)

    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == -200.0  # el credito no se ve afectado por el interes
    assert feb["en_mora"] is False


def test_interes_mora_no_se_aplica_al_saldo_de_apertura_del_primer_periodo(client):
    cons = _crear_consorcio_con_interes(client, 10.0)
    cid = cons["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0, saldo_apertura=1000.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=0.0)

    ene = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}).json()["unidades"][0]
    assert ene["saldo_anterior"] == 1000.0  # sin interes: todavia no paso ningun periodo desde que se cargo


def test_interes_mora_desactivado_por_defecto(client, consorcio):
    """El fixture `consorcio` no manda interes_mora_pct: debe quedar en 0 y no
    afectar el arrastre de deuda, igual que antes de esta feature."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)
    registrar_pago(client, unidad_id=u["id"], periodo="2026-01", pagado=0, monto_recibido=200.0, reserva=50.0)

    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == 850.0  # igual que test_pago_parcial_no_saldado_traslada_correctamente_la_deuda
