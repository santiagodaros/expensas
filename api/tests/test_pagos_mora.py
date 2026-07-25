"""
Traslado de deuda (mora) entre periodos consecutivos.

GET /api/finanzas/pagos NUNCA escribe en la tabla `pagos`: es una vista calculada.
La deuda de una unidad solo persiste a partir del periodo en que en algun momento
se llamo a POST /api/finanzas/pagos (registrar_pago) para esa unidad, aunque sea
con pagado=0. A partir de ahi, el saldo se sigue arrastrando hacia adelante desde
el ULTIMO periodo registrado (no necesariamente el mes calendario inmediato
anterior): si se salta algun mes sin registrar nada, la mora o el credito no se
resetea a cero, sigue viniendo del ultimo registro real.
"""
from .conftest import crear_unidad, crear_gasto, registrar_pago


def _prorratear(client, cid, unidad_id, periodo, monto_gasto=1000.0):
    crear_gasto(client, cid, periodo, categoria="A", monto=monto_gasto)


def test_sin_registrar_pago_la_deuda_no_persiste_al_mes_siguiente(client, consorcio):
    """Si nunca se llama a registrar_pago, no queda ninguna fila en `pagos`:
    el mes siguiente arranca en cero, aunque el mes anterior haya quedado en mora."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)
    # No se llama a registrar_pago para 2026-01.

    ene = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}).json()["unidades"][0]
    assert ene["en_mora"] is True
    assert ene["total_pagar"] == 1050.0  # 1000 + 5% reserva

    # Febrero sin gastos propios: si la mora de enero se trasladara, deberia verse aca.
    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == 0.0
    assert feb["en_mora"] is False


def test_pago_parcial_no_saldado_traslada_correctamente_la_deuda(client, consorcio):
    """registrar_pago con pagado=0 SI persiste la fila en `pagos`, y esa deuda
    se traslada como saldo_anterior del periodo siguiente. Este es el camino
    correcto para reflejar mora real."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(
        client, unidad_id=u["id"], periodo="2026-01", pagado=0,
        monto_recibido=200.0, reserva=50.0, saldo_inicial=0.0,
    )
    # deuda enero = 0 - 200 - 0 + 1000 + 50 + 0 = 850

    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == 850.0
    assert feb["total_pagar"] == 850.0  # sin gastos nuevos en febrero
    assert feb["en_mora"] is True


def test_pago_parcial_marcado_como_pagado_igual_traslada_el_saldo(client, consorcio):
    """
    Regresion del bug arreglado en registrar_pago(): antes, marcar "pagado" en un
    pago parcial pre-sembraba la deuda restante en el `monto_recibido` del mes
    siguiente, que se cancelaba contra el `saldo_anterior` heredado de la misma
    deuda — el saldo pendiente desaparecia en vez de arrastrarse. Ahora que ese
    bloque se elimino, la deuda se traslada correctamente sin importar el flag
    `pagado`, porque get_pagos() ya lee `monto_deuda` del periodo anterior.
    """
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(
        client, unidad_id=u["id"], periodo="2026-01", pagado=1,
        monto_recibido=500.0, reserva=50.0, saldo_inicial=0.0,
    )
    # deuda enero = 0 - 500 - 0 + 1000 + 50 + 0 = 550

    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == 550.0
    assert feb["total_pagar"] == 550.0
    assert feb["en_mora"] is True


def test_sobrepago_marcado_como_pagado_no_genera_mora_falsa(client, consorcio):
    """
    Regresion del mismo bug para el caso de sobrepago: antes, el credito a favor
    (deuda negativa) se escribia como `monto_recibido` negativo del mes siguiente,
    que al RESTARSE en la formula de saldo aparecia como una deuda nueva.
    """
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(
        client, unidad_id=u["id"], periodo="2026-01", pagado=1,
        monto_recibido=1200.0, reserva=50.0, saldo_inicial=0.0,
    )
    # deuda enero = 0 - 1200 - 0 + 1000 + 50 + 0 = -150 (a favor de la unidad)

    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["en_mora"] is False


def test_sobrepago_se_traslada_como_credito_real_al_mes_siguiente(client, consorcio):
    """El credito de un sobrepago debe descontarse del mes siguiente en vez de
    perderse: si la unidad pago $150 de mas y febrero no tiene gastos nuevos,
    febrero debe reflejar un saldo a favor (total_pagar negativo), no $0."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(
        client, unidad_id=u["id"], periodo="2026-01", pagado=1,
        monto_recibido=1200.0, reserva=50.0, saldo_inicial=0.0,
    )
    # deuda enero = 0 - 1200 - 0 + 1000 + 50 + 0 = -150 (a favor de la unidad)

    feb = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-02"}).json()["unidades"][0]
    assert feb["saldo_anterior"] == -150.0
    assert feb["total_pagar"] == -150.0
    assert feb["en_mora"] is False

    # Si en marzo hay $100 de gastos nuevos, el credito debe descontarlos.
    crear_gasto(client, cid, "2026-02", categoria="A", monto=100.0)
    registrar_pago(
        client, unidad_id=u["id"], periodo="2026-02", pagado=0,
        monto_recibido=0.0, reserva=5.0, saldo_inicial=-150.0,
    )
    # deuda feb = -150 - 0 - 0 + 100 + 5 + 0 = -45 (todavia a favor)
    mar = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-03"}).json()["unidades"][0]
    assert mar["saldo_anterior"] == -45.0
    assert mar["en_mora"] is False


def test_saldo_apertura_de_la_unidad_se_usa_en_el_primer_periodo(client, consorcio):
    """Una unidad que ya arrastraba deuda antes de empezar a usar el sistema
    debe reflejarla desde el primer periodo, tomando unidades.saldo_apertura."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0, saldo_apertura=5000.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    ene = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}).json()["unidades"][0]
    assert ene["saldo_anterior"] == 5000.0
    assert ene["total_pagar"] == 6050.0  # 1000 + 5000 + 5% reserva
    assert ene["en_mora"] is True


def test_saldo_apertura_negativo_representa_credito_previo(client, consorcio):
    """Una unidad que ya tenia saldo a favor antes de empezar a usar el sistema
    (saldo_apertura negativo) debe arrancar con ese credito, no en mora."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0, saldo_apertura=-2000.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    ene = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}).json()["unidades"][0]
    assert ene["saldo_anterior"] == -2000.0
    assert ene["total_pagar"] == -950.0  # 1000 - 2000 + 5% reserva
    assert ene["en_mora"] is False


def test_saldo_apertura_se_bloquea_despues_del_primer_pago_registrado(client, consorcio):
    """Una vez que la unidad ya tiene un pago registrado, el saldo de apertura
    no debe poder modificarse via PUT (evita reescribir el arrastre inicial
    despues de haber empezado a operar)."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0, saldo_apertura=1000.0)
    assert u["saldo_apertura_editable"] is True

    registrar_pago(client, unidad_id=u["id"], periodo="2026-01", pagado=1, monto_recibido=100.0)

    put_payload = {
        "unidad": "1", "piso": "1", "dpto": "A", "propietario": "Juan Perez",
        "coef_a": 100.0, "coef_b": 0.0, "coef_c": 0.0, "saldo_apertura": 99999.0,
    }
    res = client.put(f"/api/unidades/{u['id']}", json=put_payload)
    assert res.status_code == 200
    assert res.json()["saldo_apertura"] == 1000.0  # se ignora el intento de cambio
    assert res.json()["saldo_apertura_editable"] is False


def test_mora_se_arrastra_aunque_se_salte_un_mes_sin_registrar_nada(client, consorcio):
    """Si enero queda registrado con deuda y febrero se salta por completo (ni
    siquiera con pagado=0), marzo debe seguir mostrando la deuda de enero, no
    resetear a cero por no encontrar un registro en el mes calendario anterior."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(client, unidad_id=u["id"], periodo="2026-01", pagado=0, monto_recibido=200.0, reserva=50.0)
    # deuda enero = 0 - 200 - 0 + 1000 + 50 + 0 = 850
    # Nada se registra para 2026-02 (se "salta" el mes por completo).

    mar = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-03"}).json()["unidades"][0]
    assert mar["saldo_anterior"] == 850.0
    assert mar["en_mora"] is True


def test_credito_se_arrastra_aunque_se_salte_un_mes_sin_registrar_nada(client, consorcio):
    """Mismo caso que el anterior pero con un saldo a favor: el credito de
    enero debe seguir viéndose en marzo aunque febrero no tenga ningun registro."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0)

    registrar_pago(client, unidad_id=u["id"], periodo="2026-01", pagado=1, monto_recibido=1200.0, reserva=50.0)
    # deuda enero = 0 - 1200 - 0 + 1000 + 50 + 0 = -150 (a favor)
    # Nada se registra para 2026-02.

    mar = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-03"}).json()["unidades"][0]
    assert mar["saldo_anterior"] == -150.0
    assert mar["en_mora"] is False
