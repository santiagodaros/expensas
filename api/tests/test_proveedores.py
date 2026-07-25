"""CRUD de proveedores y su cuenta corriente agregada por periodo."""
from .conftest import crear_gasto


def _crear_proveedor(client, cid, **overrides):
    payload = {"razon_social": "Plomeria SRL", "cuit": "30-11111111-1", "domicilio": "", "cat_afip": "", "cbu": ""}
    payload.update(overrides)
    res = client.post("/api/proveedores", json=payload, params={"consorcio_id": cid})
    assert res.status_code == 201, res.text
    return res.json()


def test_crud_basico_de_proveedor(client, consorcio):
    cid = consorcio["id"]
    p = _crear_proveedor(client, cid)
    assert p["razon_social"] == "Plomeria SRL"

    res = client.put(f"/api/proveedores/{p['id']}", json={
        "razon_social": "Plomeria y Gas SRL", "cuit": "30-11111111-1",
        "domicilio": "Av. Siempre Viva 742", "cat_afip": "Responsable Inscripto", "cbu": "",
    })
    assert res.status_code == 200
    assert res.json()["razon_social"] == "Plomeria y Gas SRL"

    client.delete(f"/api/proveedores/{p['id']}")
    listado = client.get("/api/proveedores", params={"consorcio": cid}).json()
    assert all(x["id"] != p["id"] for x in listado)


def test_cuenta_corriente_agrupa_gastos_del_proveedor_por_periodo(client, consorcio):
    cid = consorcio["id"]
    p = _crear_proveedor(client, cid)

    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0, proveedor_id=p["id"])
    crear_gasto(client, cid, "2026-01", categoria="B", monto=500.0, proveedor_id=p["id"])
    crear_gasto(client, cid, "2026-02", categoria="A", monto=300.0, proveedor_id=p["id"])
    crear_gasto(client, cid, "2026-01", categoria="A", monto=999.0)  # sin proveedor, no debe contarse

    cc = client.get(f"/api/proveedores/{p['id']}/cuenta_corriente").json()
    por_periodo = {r["periodo"]: r for r in cc}

    assert por_periodo["2026-01"]["total"] == 1500.0
    assert por_periodo["2026-01"]["qty"] == 2
    assert por_periodo["2026-02"]["total"] == 300.0


def test_resumen_ordena_proveedores_por_total_facturado_descendente(client, consorcio):
    cid = consorcio["id"]
    chico = _crear_proveedor(client, cid, razon_social="Chico SRL")
    grande = _crear_proveedor(client, cid, razon_social="Grande SRL")
    crear_gasto(client, cid, "2026-01", categoria="A", monto=100.0, proveedor_id=chico["id"])
    crear_gasto(client, cid, "2026-01", categoria="A", monto=5000.0, proveedor_id=grande["id"])

    resumen = client.get("/api/proveedores/resumen", params={"consorcio": cid}).json()
    assert resumen[0]["proveedor_id"] == grande["id"]
    assert resumen[0]["total_gastos"] == 5000.0


def test_gastos_de_proveedor_filtra_por_periodo(client, consorcio):
    cid = consorcio["id"]
    p = _crear_proveedor(client, cid)
    crear_gasto(client, cid, "2026-01", categoria="A", monto=1000.0, proveedor_id=p["id"], descripcion="Enero")
    crear_gasto(client, cid, "2026-02", categoria="A", monto=300.0, proveedor_id=p["id"], descripcion="Febrero")

    enero = client.get(f"/api/proveedores/{p['id']}/gastos", params={"periodo": "2026-01"}).json()
    assert len(enero) == 1
    assert enero[0]["descripcion"] == "Enero"
