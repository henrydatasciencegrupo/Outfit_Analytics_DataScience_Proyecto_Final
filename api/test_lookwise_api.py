from fastapi.testclient import TestClient
from lookwise_api import app, modelo, COLUMNAS

web = TestClient(app)

NUEVO = "009d1f01410c945ed5f25c733f2c8261c5f17800fab8b4c8875efee404ca59fc"
HISTORIAL = "00164322e9af7460e84207c8d172912a2c13da209bb0eab92f74545ba217d885"


def test_salud():
    r = web.get("/salud")
    assert r.status_code == 200
    assert r.json()["clientes"] == 4162


def test_cliente_nuevo():
    r = web.get("/recomendar", params={"cliente": NUEVO})
    assert r.status_code == 200
    assert r.json()["etapa"] == "nuevo"
    assert len(r.json()["prendas"]) == 12


def test_cliente_con_historial():
    r = web.get("/recomendar", params={"cliente": HISTORIAL})
    assert r.status_code == 200
    assert r.json()["etapa"] == "con_historial"
    assert len(r.json()["prendas"]) == 12


def test_estabilidad():
    a = web.get("/recomendar", params={"cliente": HISTORIAL}).json()
    b = web.get("/recomendar", params={"cliente": HISTORIAL}).json()
    assert a == b


def test_cliente_inexistente():
    r = web.get("/recomendar", params={"cliente": "abc123"})
    assert r.status_code == 404


def test_sin_parametro():
    r = web.get("/recomendar")
    assert r.status_code == 422


def test_variables_del_modelo():
    # Avisa si el modelo de models/ se reentrenó con otras variables u otro orden
    assert list(modelo.feature_names_in_) == COLUMNAS
