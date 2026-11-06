"""Pruebas del API REST: flujo completo y codigos HTTP 200/201/403/404/409/422."""

import base64

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app

B64 = base64.b64encode(b"contenido").decode()
SOL = {
    "origen": "Monterrey",
    "destino": "Querétaro",
    "tipo_mercancia": "autopartes",
    "peso_kg": "1500",
    "valor": "80000",
    "tipo_de_unidad": "caja seca",
}
OPS = {"X-Rol": "Operaciones"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("EVIDENCIAS_DIR", str(tmp_path))
    app = create_app("sqlite:///:memory:")
    with TestClient(app) as c:
        c.app_ = app
        yield c


def preparar(c, numero="OS-500", valor="80000"):
    c.post("/unidades", json={"codigo": f"U-{numero}"})
    c.post("/operadores", json={"identificador": f"OP-{numero}"})
    folio = c.post("/cotizaciones", json={**SOL, "valor": valor}).json()["folio"]
    c.post(f"/cotizaciones/{folio}/cotizar", headers={"X-Rol": "Ventas"})
    c.post(f"/cotizaciones/{folio}/aceptar")
    r = c.post("/ordenes", headers=OPS, json={"numero": numero, "folio_cotizacion": folio, "unidad_id": f"U-{numero}", "operador_id": f"OP-{numero}"})
    assert r.status_code == 201
    return numero


def test_health_y_openapi(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert "/ordenes/{numero}/entrega" in client.get("/openapi.json").json()["paths"]


def test_flujo_completo_de_cotizacion_a_entrega(client):
    folio = client.post("/cotizaciones", json=SOL)
    assert folio.status_code == 201 and folio.json()["estatus"] == "Solicitado"
    assert client.app_.state.notificador.enviados[0][0] == "Ventas"  # US-01 notifica a Ventas
    f = folio.json()["folio"]
    cot = client.post(f"/cotizaciones/{f}/cotizar", headers={"X-Rol": "Ventas"}).json()
    assert cot["estatus"] == "Cotizado" and float(cot["costo"]) > 0
    assert client.post(f"/cotizaciones/{f}/aceptar").json()["estatus"] == "Confirmado"
    client.post("/unidades", json={"codigo": "Eco-12"})
    client.post("/operadores", json={"identificador": "OP-01"})
    o = client.post("/ordenes", headers=OPS, json={"numero": "OS-500", "folio_cotizacion": f, "unidad_id": "Eco-12", "operador_id": "OP-01"})
    assert o.status_code == 201 and o.json()["estatus"] == "Unidad asignada"
    assert (
        client.post("/ordenes/OS-500/recoleccion", json={"tipo_inspeccionado": "autopartes", "peso_inspeccionado": "1500"}).json()["estatus"]
        == "Recolectado"
    )
    assert client.post("/ordenes/OS-500/traslado").json()["estatus"] == "En tránsito"
    assert client.post("/ordenes/OS-500/llegada").json()["estatus"] == "Llegada a destino"
    e = client.post(
        "/ordenes/OS-500/entrega",
        json={
            "receptor_nombre": "Ana",
            "receptor_identificacion": "INE1",
            "foto_base64": B64,
            "firma_base64": B64,
            "latitud": 25.6,
            "longitud": -100.3,
        },
    )
    assert e.status_code == 200 and e.json()["estatus"] == "Entregado"
    h = client.get("/ordenes/OS-500").json()
    assert h["estatus"] == "Entregado" and [x["evento"] for x in h["historial"]][-1] == "EntregaRealizada"


def test_404_orden_y_cotizacion_inexistentes(client):
    assert client.get("/ordenes/NO").status_code == 404
    assert client.post("/cotizaciones/NO/aceptar").status_code == 404


def test_403_ventas_no_genera_ordenes(client):
    folio = client.post("/cotizaciones", json=SOL).json()["folio"]
    client.post("/unidades", json={"codigo": "U"})
    client.post("/operadores", json={"identificador": "O"})
    r = client.post("/ordenes", headers={"X-Rol": "Ventas"}, json={"numero": "OS-1", "folio_cotizacion": folio, "unidad_id": "U", "operador_id": "O"})
    assert r.status_code == 403 and r.json()["error"] == "OperacionNoPermitidaParaRol"


def test_422_cotizacion_sin_confirmar_y_rol_desconocido(client):
    folio = client.post("/cotizaciones", json=SOL).json()["folio"]
    client.post("/unidades", json={"codigo": "U"})
    client.post("/operadores", json={"identificador": "O"})
    body = {"numero": "OS-1", "folio_cotizacion": folio, "unidad_id": "U", "operador_id": "O"}
    assert client.post("/ordenes", headers=OPS, json=body).status_code == 422
    assert client.post("/ordenes", headers={"X-Rol": "Dios"}, json=body).status_code == 422
    assert client.post("/cotizaciones", json={**SOL, "peso_kg": "-5"}).status_code == 422


def test_409_transicion_invalida_y_duplicados(client):
    n = preparar(client)
    assert client.post(f"/ordenes/{n}/entrega", json={}).status_code == 409
    assert client.post("/unidades", json={"codigo": "U-OS-500"}).status_code == 409


def test_422_entrega_sin_firma(client):
    n = preparar(client)
    client.post(f"/ordenes/{n}/recoleccion", json={"tipo_inspeccionado": "autopartes", "peso_inspeccionado": "1500"})
    client.post(f"/ordenes/{n}/traslado")
    client.post(f"/ordenes/{n}/llegada")
    r = client.post(
        f"/ordenes/{n}/entrega", json={"receptor_nombre": "Ana", "receptor_identificacion": "I", "foto_base64": B64, "latitud": 1.0, "longitud": 1.0}
    )
    assert r.status_code == 422 and r.json()["error"] == "EvidenciaIncompleta"
    assert client.get(f"/ordenes/{n}").json()["estatus"] == "Llegada a destino"


def test_alto_valor_exige_controles_y_discrepancia(client):
    n = preparar(client, valor="500000")
    r = client.post(f"/ordenes/{n}/recoleccion", json={"tipo_inspeccionado": "autopartes", "peso_inspeccionado": "1500"})
    assert r.status_code == 422 and r.json()["error"] == "ControlesDeAltoValorRequeridos"
    r = client.post(
        f"/ordenes/{n}/recoleccion", json={"tipo_inspeccionado": "autopartes", "peso_inspeccionado": "1400", "controles_confirmados": True}
    )
    assert r.status_code == 422 and r.json()["error"] == "DiscrepanciaDeMercancia"
    ok = client.post(
        f"/ordenes/{n}/recoleccion", json={"tipo_inspeccionado": "autopartes", "peso_inspeccionado": "1500", "controles_confirmados": True}
    )
    assert ok.status_code == 200


def test_rechazo_de_mercancia_detiene_y_notifica(client):
    n = preparar(client)
    r = client.post(f"/ordenes/{n}/rechazo", json={"tipo_discrepancia": "cantidad", "fotos_base64": [B64], "observaciones": "faltan"})
    assert r.status_code == 200
    assert client.app_.state.notificador.enviados[-1][0] == "Operaciones"
    assert client.post(f"/ordenes/{n}/traslado").status_code == 409  # orden detenida


def test_averia_y_reasignacion(client):
    n = preparar(client)
    client.post(f"/ordenes/{n}/recoleccion", json={"tipo_inspeccionado": "autopartes", "peso_inspeccionado": "1500"})
    client.post(f"/ordenes/{n}/traslado")
    assert client.post(f"/ordenes/{n}/averia", json={"descripcion": "motor"}).status_code == 200
    client.post("/operadores", json={"identificador": "OP-REL", "es_comodin": True})
    assert client.post(f"/ordenes/{n}/reasignar-operador", headers={"X-Rol": "Ventas"}, json={"nuevo_operador_id": "OP-REL"}).status_code == 403
    r = client.post(f"/ordenes/{n}/reasignar-operador", headers=OPS, json={"nuevo_operador_id": "OP-REL"})
    assert r.json()["operador_id"] == "OP-REL"
    assert client.post("/ordenes/NO/reasignar-operador", headers=OPS, json={"nuevo_operador_id": "x"}).status_code == 404


def test_cotizacion_rechazada_por_el_cliente(client):
    f = client.post("/cotizaciones", json=SOL).json()["folio"]
    assert client.post(f"/cotizaciones/{f}/rechazar").status_code == 422  # aun no cotizada
    client.post(f"/cotizaciones/{f}/cotizar", headers={"X-Rol": "Ventas"})
    assert client.post(f"/cotizaciones/{f}/rechazar").json()["cancelada"] is True
    assert client.post(f"/cotizaciones/{f}/aceptar").status_code == 422


def _llegar(client, n):
    client.post(f"/ordenes/{n}/recoleccion", json={"tipo_inspeccionado": "autopartes", "peso_inspeccionado": "1500"})
    client.post(f"/ordenes/{n}/traslado")
    client.post(f"/ordenes/{n}/llegada")


def test_us10_destinatario_ausente_alerta_a_operaciones(client):
    n = preparar(client)
    _llegar(client, n)
    r = client.post(
        f"/ordenes/{n}/destinatario-ausente",
        json={"foto_base64": B64, "latitud": 25.6, "longitud": -100.3, "observaciones": "nadie abre"},
    )
    assert r.status_code == 200
    assert client.app_.state.notificador.enviados[-1][0] == "Operaciones"
    h = client.get(f"/ordenes/{n}").json()
    assert h["estatus"] == "Llegada a destino" and h["incidencias"][0]["tipo"] == "destinatario ausente"
    sin_foto = client.post(f"/ordenes/{n}/destinatario-ausente", json={"latitud": 1.0, "longitud": 1.0})
    assert sin_foto.status_code == 422


def test_us10_antes_de_llegar_responde_409(client):
    n = preparar(client)
    r = client.post(f"/ordenes/{n}/destinatario-ausente", json={"foto_base64": B64, "latitud": 1.0, "longitud": 1.0})
    assert r.status_code == 409


def test_us11_entrega_con_anomalias_genera_reporte(client):
    n = preparar(client)
    _llegar(client, n)
    cuerpo = {
        "receptor_nombre": "Ana",
        "receptor_identificacion": "INE1",
        "foto_base64": B64,
        "firma_base64": B64,
        "latitud": 25.6,
        "longitud": -100.3,
        "descripcion": "Dos piezas rotas",
        "fotos_anomalia_base64": [B64],
    }
    r = client.post(f"/ordenes/{n}/entrega-con-anomalias", json=cuerpo)
    assert r.status_code == 200 and r.json()["estatus"] == "Entregado"
    h = client.get(f"/ordenes/{n}").json()
    assert h["incidencias"][0]["tipo"] == "entrega con danos o faltantes"
    assert h["historial"][-1]["evento"] == "EntregaConAnomaliasRegistrada"
    assert client.app_.state.notificador.enviados[-1][0] == "Operaciones"


def test_us11_sin_firma_o_sin_descripcion_responde_422(client):
    n = preparar(client)
    _llegar(client, n)
    base = {"receptor_nombre": "Ana", "receptor_identificacion": "I", "foto_base64": B64, "firma_base64": B64, "latitud": 1.0, "longitud": 1.0}
    assert client.post(f"/ordenes/{n}/entrega-con-anomalias", json={**base, "descripcion": "x", "firma_base64": None}).status_code == 422
    assert client.post(f"/ordenes/{n}/entrega-con-anomalias", json={**base, "descripcion": " "}).status_code == 422
    assert client.get(f"/ordenes/{n}").json()["estatus"] == "Llegada a destino"
