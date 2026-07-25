"""
Fixtures compartidas para la suite de tests del backend.

Cada test corre contra una base SQLite temporal y descartable (via el fixture
`db_path`, respaldado por `tmp_path` de pytest), nunca contra consorcios.db real.
El schema se construye llamando a run_migrations() directamente, asi que estos
tests tambien actuan como regresion del fix de "instalacion nueva sin DB previa".
"""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient

from api.database import get_db, run_migrations
from api.main import app


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "test_consorcios.db")
    run_migrations(path)
    return path


@pytest.fixture()
def client(db_path):
    def _override_get_db():
        con = sqlite3.connect(db_path, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def consorcio(client):
    """Consorcio de prueba con reserva del 5% y vencimiento el dia 10."""
    res = client.post("/api/consorcios", json={
        "nombre": "Edificio Test",
        "cuit": "20-12345678-9",
        "direccion": "Calle Falsa 123",
        "unidades": 0,
        "reserva_pct": 5.0,
        "dia_vto": 10,
    })
    assert res.status_code == 201, res.text
    return res.json()


def crear_unidad(client, consorcio_id, **overrides):
    payload = {
        "unidad": "1", "piso": "1", "dpto": "A", "propietario": "Juan Perez",
        "inquilino": None, "coef_a": 25.0, "coef_b": 25.0, "coef_c": 25.0,
        "email": "juan@test.com",
    }
    payload.update(overrides)
    res = client.post(f"/api/consorcios/{consorcio_id}/unidades", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def crear_gasto(client, consorcio_id, periodo, **overrides):
    payload = {"categoria": "A", "descripcion": "Gasto test", "monto": 1000.0, "tipo": "ordinario"}
    payload.update(overrides)
    res = client.post(
        "/api/finanzas/gastos", json=payload,
        params={"consorcio_id": consorcio_id, "periodo": periodo},
    )
    assert res.status_code == 201, res.text
    return res.json()


def registrar_pago(client, **overrides):
    payload = {
        "unidad_id": 0, "periodo": "2026-01", "pagado": 0, "monto_recibido": 0.0,
        "telec": 0.0, "reserva": 0.0, "redondeo": 0.0, "saldo_inicial": 0.0,
    }
    payload.update(overrides)
    res = client.post("/api/finanzas/pagos", json=payload)
    assert res.status_code == 200, res.text
    return res.json()
