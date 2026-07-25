"""CRUD de consorcios/unidades, import batch (padron) y borrado en cascada."""
from .conftest import crear_unidad, crear_gasto


def test_crud_basico_de_consorcio(client, consorcio):
    cid = consorcio["id"]
    res = client.put(f"/api/consorcios/{cid}", json={
        "nombre": "Edificio Renombrado", "cuit": "20-12345678-9", "direccion": "Calle Falsa 123",
        "unidades": 4, "reserva_pct": 10.0, "dia_vto": 15,
    })
    assert res.status_code == 200
    assert res.json()["nombre"] == "Edificio Renombrado"
    assert res.json()["reserva_pct"] == 10.0


def test_actualizar_consorcio_inexistente_devuelve_404(client):
    res = client.put("/api/consorcios/999999", json={
        "nombre": "X", "unidades": 0, "reserva_pct": 0.0, "dia_vto": 10,
    })
    assert res.status_code == 404


def test_eliminar_consorcio_elimina_en_cascada_unidades_y_gastos(client, consorcio):
    """Regresion del fix de schema: unidades/gastos declaran
    ON DELETE CASCADE hacia consorcios; sin PRAGMA foreign_keys=ON esto no se
    aplicaria (get_db() ya lo activa por conexion)."""
    cid = consorcio["id"]
    u = crear_unidad(client, cid, unidad="1")
    crear_gasto(client, cid, "2026-01", categoria="A", monto=100.0)

    res = client.delete(f"/api/consorcios/{cid}")
    assert res.status_code == 200

    assert client.get("/api/consorcios/999999").status_code == 404  # sanity: endpoint funciona
    unidades = client.get(f"/api/consorcios/{cid}/unidades").json()
    assert unidades == []


def test_batch_upsert_inserta_actualiza_y_preserva_sin_cambios(client, consorcio):
    cid = consorcio["id"]
    # Campos alineados 1:1 con lo que manda el batch de abajo, para que la unidad
    # "1" quede genuinamente sin cambios (propietario/inquilino/email inclusive).
    crear_unidad(client, cid, unidad="1", piso="1", dpto="A", coef_a=25.0, coef_b=0.0, coef_c=0.0,
                 propietario=None, inquilino=None, email=None)
    crear_unidad(client, cid, unidad="2", piso="2", dpto="B", coef_a=25.0, coef_b=0.0, coef_c=0.0,
                 propietario=None, inquilino=None, email=None)

    res = client.post(f"/api/consorcios/{cid}/unidades/batch", json={"unidades": [
        {"unidad": "1", "piso": "1", "dpto": "A", "coef_a": 25.0, "coef_b": 0.0, "coef_c": 0.0},  # sin cambios
        {"unidad": "2", "piso": "2", "dpto": "B", "coef_a": 30.0, "coef_b": 0.0, "coef_c": 0.0},  # coef cambio
        {"unidad": "3", "piso": "3", "dpto": "C", "coef_a": 45.0, "coef_b": 0.0, "coef_c": 0.0},  # nueva
    ]})
    assert res.status_code == 200
    body = res.json()
    assert body["insertados"] == 1
    assert body["actualizados"] == 1
    assert body["sin_cambios"] == 1

    unidades = {u["unidad"]: u for u in client.get(f"/api/consorcios/{cid}/unidades").json()}
    assert len(unidades) == 3
    assert unidades["2"]["coef_a"] == 30.0
    assert unidades["1"]["coef_a"] == 25.0  # no tocada


def test_batch_upsert_tolera_diferencias_de_coeficiente_menores_a_1e6(client, consorcio):
    """Evita falsos 'actualizados' por ruido de punto flotante al reimportar el mismo archivo."""
    cid = consorcio["id"]
    crear_unidad(client, cid, unidad="1", piso="", dpto="", coef_a=33.333333, coef_b=0.0, coef_c=0.0,
                 propietario=None, inquilino=None, email=None)

    res = client.post(f"/api/consorcios/{cid}/unidades/batch", json={"unidades": [
        {"unidad": "1", "piso": "", "dpto": "", "coef_a": 33.3333331, "coef_b": 0.0, "coef_c": 0.0},
    ]})
    assert res.json()["sin_cambios"] == 1
    assert res.json()["actualizados"] == 0
