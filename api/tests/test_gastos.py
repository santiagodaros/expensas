"""CRUD de gastos generales — incluye regresion de un bug encontrado al testear:
POST /api/finanzas/gastos ignoraba proveedor_id al crear (solo se guardaba
al editar via PUT), asi que asociar un proveedor desde el formulario de
"Nuevo Comprobante" no tenia efecto real. Se corrigio en el mismo router."""


def _crear_proveedor(client, cid):
    res = client.post("/api/proveedores", json={"razon_social": "Plomeria SRL"}, params={"consorcio_id": cid})
    assert res.status_code == 201
    return res.json()


def test_crear_gasto_persiste_el_proveedor_asociado(client, consorcio):
    cid = consorcio["id"]
    prov = _crear_proveedor(client, cid)

    res = client.post(
        "/api/finanzas/gastos",
        json={"categoria": "A", "descripcion": "Arreglo caño", "monto": 500.0,
              "tipo": "ordinario", "proveedor_id": prov["id"]},
        params={"consorcio_id": cid, "periodo": "2026-01"},
    )
    assert res.status_code == 201
    assert res.json()["proveedor_id"] == prov["id"]

    gastos = client.get("/api/finanzas/gastos", params={"consorcio": cid, "periodo": "2026-01"}).json()
    assert gastos[0]["proveedor_id"] == prov["id"]


def test_editar_gasto_permite_cambiar_categoria_monto_y_proveedor(client, consorcio):
    cid = consorcio["id"]
    prov = _crear_proveedor(client, cid)
    creado = client.post(
        "/api/finanzas/gastos",
        json={"categoria": "A", "descripcion": "Gasto original", "monto": 100.0, "tipo": "ordinario"},
        params={"consorcio_id": cid, "periodo": "2026-01"},
    ).json()

    res = client.put(f"/api/finanzas/gastos/{creado['id']}", json={
        "categoria": "B", "descripcion": "Gasto corregido", "monto": 250.0,
        "tipo": "extraordinario", "proveedor_id": prov["id"],
    })
    assert res.status_code == 200

    gastos = client.get("/api/finanzas/gastos", params={"consorcio": cid, "periodo": "2026-01"}).json()
    g = gastos[0]
    assert g["categoria"] == "B"
    assert g["monto"] == 250.0
    assert g["tipo"] == "extraordinario"
    assert g["proveedor_id"] == prov["id"]


def test_eliminar_gasto(client, consorcio):
    cid = consorcio["id"]
    creado = client.post(
        "/api/finanzas/gastos",
        json={"categoria": "A", "descripcion": "Gasto a borrar", "monto": 100.0, "tipo": "ordinario"},
        params={"consorcio_id": cid, "periodo": "2026-01"},
    ).json()

    res = client.delete(f"/api/finanzas/gastos/{creado['id']}")
    assert res.status_code == 200

    gastos = client.get("/api/finanzas/gastos", params={"consorcio": cid, "periodo": "2026-01"}).json()
    assert gastos == []
