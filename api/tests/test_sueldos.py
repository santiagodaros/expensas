"""
POST/PUT/DELETE /api/sueldos — cada recibo de sueldo mantiene un `gasto`
Categoria A vinculado (gasto_id) que debe mantenerse sincronizado.
"""


def _crear_sueldo(client, cid, periodo, **overrides):
    payload = {
        "empleado": "Roberto Gomez", "concepto": "Encargado",
        "sueldo_bruto": 500000.0, "cargas_suterh": 150000.0,
        "cargas_fateryh": 50000.0, "otras_cargas": 0.0,
    }
    payload.update(overrides)
    res = client.post("/api/sueldos", json=payload, params={"consorcio_id": cid, "periodo": periodo})
    assert res.status_code == 201, res.text
    return res.json()


def test_crear_sueldo_genera_gasto_ordinario_categoria_a_vinculado(client, consorcio):
    cid = consorcio["id"]
    sueldo = _crear_sueldo(client, cid, "2026-01")

    assert sueldo["total_gasto"] == 700000.0  # 500000 + 150000 + 50000
    assert sueldo["gasto_id"] is not None

    gastos = client.get("/api/finanzas/gastos", params={"consorcio": cid, "periodo": "2026-01"}).json()
    assert len(gastos) == 1
    assert gastos[0]["id"] == sueldo["gasto_id"]
    assert gastos[0]["categoria"] == "A"
    assert gastos[0]["tipo"] == "ordinario"
    assert gastos[0]["monto"] == 700000.0
    assert "Roberto Gomez" in gastos[0]["descripcion"]


def test_actualizar_sueldo_actualiza_el_gasto_vinculado(client, consorcio):
    cid = consorcio["id"]
    sueldo = _crear_sueldo(client, cid, "2026-01", sueldo_bruto=500000.0)

    res = client.put(f"/api/sueldos/{sueldo['id']}", json={
        "empleado": "Roberto Gomez", "concepto": "Encargado",
        "sueldo_bruto": 600000.0, "cargas_suterh": 150000.0,
        "cargas_fateryh": 50000.0, "otras_cargas": 0.0,
    })
    assert res.status_code == 200
    assert res.json()["total_gasto"] == 800000.0

    gastos = client.get("/api/finanzas/gastos", params={"consorcio": cid, "periodo": "2026-01"}).json()
    assert gastos[0]["monto"] == 800000.0


def test_eliminar_sueldo_elimina_tambien_el_gasto_vinculado(client, consorcio):
    cid = consorcio["id"]
    sueldo = _crear_sueldo(client, cid, "2026-01")
    gasto_id = sueldo["gasto_id"]

    res = client.delete(f"/api/sueldos/{sueldo['id']}")
    assert res.status_code == 200

    gastos = client.get("/api/finanzas/gastos", params={"consorcio": cid, "periodo": "2026-01"}).json()
    assert all(g["id"] != gasto_id for g in gastos)


def test_sueldo_impacta_el_prorrateo_como_cualquier_gasto_categoria_a(client, consorcio):
    from .conftest import crear_unidad
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1", coef_a=100.0, coef_b=0.0, coef_c=0.0)
    _crear_sueldo(client, cid, "2026-01", sueldo_bruto=1000.0, cargas_suterh=0.0,
                  cargas_fateryh=0.0, otras_cargas=0.0)

    row = client.get("/api/finanzas/pagos", params={"consorcio": cid, "periodo": "2026-01"}).json()["unidades"][0]
    assert row["imp_mes"] == 1000.0


def test_historial_devuelve_los_recibos_del_empleado_en_todos_los_periodos(client, consorcio):
    cid = consorcio["id"]
    _crear_sueldo(client, cid, "2026-01", empleado="Roberto Gomez", sueldo_bruto=500000.0)
    _crear_sueldo(client, cid, "2026-02", empleado="Roberto Gomez", sueldo_bruto=550000.0)
    _crear_sueldo(client, cid, "2026-01", empleado="Otro Empleado", sueldo_bruto=300000.0)

    historial = client.get("/api/sueldos/historial", params={"consorcio": cid, "empleado": "Roberto Gomez"}).json()
    assert len(historial) == 2
    assert {h["periodo"] for h in historial} == {"2026-01", "2026-02"}
    assert all(h["empleado"] == "Roberto Gomez" for h in historial)
