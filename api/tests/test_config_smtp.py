"""POST /api/config/test_smtp — valida credenciales sin mandar un email real.

smtplib.SMTP se monkeypatchea siempre: no queremos que un test intente una
conexión de red real a un servidor de correo.
"""
import api.routers.config_router as config_mod


class _FakeSmtpOk:
    def __init__(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): pass
    def login(self, user, pwd): pass


class _FakeSmtpAuthError:
    def __init__(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): pass
    def login(self, user, pwd):
        raise Exception("Authentication failed")


def test_smtp_test_rechaza_sin_usuario_o_password(client):
    res = client.post("/api/config/test_smtp", json={"smtp_server": "smtp.gmail.com", "smtp_port": "587", "smtp_user": ""})
    assert res.status_code == 400


def test_smtp_test_exitoso(client, monkeypatch):
    monkeypatch.setattr(config_mod.smtplib, "SMTP", _FakeSmtpOk)
    res = client.post("/api/config/test_smtp", json={
        "smtp_server": "smtp.gmail.com", "smtp_port": "587",
        "smtp_user": "admin@test.com", "smtp_pass": "clave-de-app",
    })
    assert res.status_code == 200


def test_smtp_test_devuelve_400_si_falla_la_autenticacion(client, monkeypatch):
    monkeypatch.setattr(config_mod.smtplib, "SMTP", _FakeSmtpAuthError)
    res = client.post("/api/config/test_smtp", json={
        "smtp_server": "smtp.gmail.com", "smtp_port": "587",
        "smtp_user": "admin@test.com", "smtp_pass": "clave-mala",
    })
    assert res.status_code == 400
    assert "Authentication failed" in res.json()["detail"]


def test_smtp_test_puerto_invalido_devuelve_400(client):
    res = client.post("/api/config/test_smtp", json={
        "smtp_server": "smtp.gmail.com", "smtp_port": "no-es-un-puerto",
        "smtp_user": "admin@test.com", "smtp_pass": "x",
    })
    assert res.status_code == 400
