"""Integracion: servicios + repositorios SQL (SQLite en memoria) y mocks de servicios externos."""

from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from src.application.services import ServicioDeEntrega, ServicioDeRecoleccion
from src.domain.enums import EstatusDelServicio as E
from src.domain.enums import TipoDeDiscrepancia
from src.domain.errors import EvidenciaIncompleta, OrdenNoEncontrada
from src.domain.model import Operador, Unidad
from src.domain.policies import PoliticaDeCargaDeAltoValor
from src.infrastructure.database import make_engine
from src.infrastructure.repositories import (
    CotizacionSqlRepository,
    OperadorSqlRepository,
    OrdenDeServicioSqlRepository,
    UnidadDeTrabajoSql,
    UnidadSqlRepository,
)
from tests.conftest import AHORA, evidencia, hacer_orden


@pytest.fixture
def engine():
    e = make_engine()
    yield e
    e.dispose()


def test_cp14_commit_guarda_la_orden_completa_y_rollback_no_deja_nada(engine):
    with Session(engine) as s:
        o = hacer_orden(E.LLEGADA_A_DESTINO, valor="1234.56")
        o.registrar_entrega(evidencia(), "op", AHORA)
        OrdenDeServicioSqlRepository(s).guardar(o)
        s.commit()
    with Session(engine) as s:
        r = OrdenDeServicioSqlRepository(s).obtener_por_numero("OS-500")
        assert r.estatus is E.ENTREGADO and r.evidencia.esta_completa()
        assert r.mercancia.valor == Decimal("1234.56") and r.bitacora[0].evento == "EntregaRealizada"
    with Session(engine) as s:
        o2 = hacer_orden()
        o2.numero = "OS-999"
        OrdenDeServicioSqlRepository(s).guardar(o2)
        s.rollback()
    with Session(engine) as s, pytest.raises(OrdenNoEncontrada):
        OrdenDeServicioSqlRepository(s).obtener_por_numero("OS-999")


def _recoleccion(engine):
    s = Session(engine)
    repo = OrdenDeServicioSqlRepository(s)
    repo.guardar(hacer_orden())
    s.commit()
    almacen, notif = Mock(), Mock()
    almacen.guardar.side_effect = lambda b: f"ref-{len(b)}"
    uow = UnidadDeTrabajoSql(s)
    return s, ServicioDeRecoleccion(repo, PoliticaDeCargaDeAltoValor(Decimal("100000")), almacen, notif, uow), almacen, notif


def test_cp15_rechazo_notifica_a_operaciones_una_vez_y_despues_del_commit(engine):
    s, srv, almacen, notif = _recoleccion(engine)
    srv.rechazar_mercancia("OS-500", TipoDeDiscrepancia.CANTIDAD, [b"aa", b"bbb"], "faltan", "op", AHORA)
    notif.alertar.assert_called_once()
    assert notif.alertar.call_args.args[:2] == ("Operaciones", "OS-500")
    assert almacen.guardar.call_count == 2
    with Session(engine) as s2:
        o = OrdenDeServicioSqlRepository(s2).obtener_por_numero("OS-500")
        assert o.detenida and len(o.incidencias) == 1 and o.incidencias[0].fotos == ("ref-2", "ref-3")


def test_rechazo_sin_fotos_hace_rollback_y_no_notifica(engine):
    s, srv, _, notif = _recoleccion(engine)
    with pytest.raises(EvidenciaIncompleta):
        srv.rechazar_mercancia("OS-500", TipoDeDiscrepancia.TIPO, [], "x", "op", AHORA)
    notif.alertar.assert_not_called()
    assert not OrdenDeServicioSqlRepository(Session(engine)).obtener_por_numero("OS-500").detenida


def test_recoleccion_por_servicio(engine):
    s, srv, *_ = _recoleccion(engine)
    assert srv.registrar_recoleccion("OS-500", "autopartes", Decimal("1500"), False, "op", AHORA) is E.RECOLECTADO


def test_cp16_si_el_almacen_falla_la_orden_no_pasa_a_entregado(engine):
    with Session(engine) as s:
        OrdenDeServicioSqlRepository(s).guardar(hacer_orden(E.LLEGADA_A_DESTINO))
        s.commit()
    s = Session(engine)
    almacen = Mock()
    almacen.guardar.side_effect = TimeoutError("sin respuesta")
    srv = ServicioDeEntrega(OrdenDeServicioSqlRepository(s), almacen, UnidadDeTrabajoSql(s))
    with pytest.raises(TimeoutError):
        srv.registrar_entrega("OS-500", "Ana", "INE1", b"f", b"s", 25.0, -100.0, "op", AHORA)
    with Session(engine) as s2:
        o = OrdenDeServicioSqlRepository(s2).obtener_por_numero("OS-500")
        assert o.estatus is E.LLEGADA_A_DESTINO and o.evidencia is None


def test_si_el_commit_falla_se_revierte(engine):
    s = Session(engine)
    OrdenDeServicioSqlRepository(s).guardar(hacer_orden(E.LLEGADA_A_DESTINO))
    s.commit()
    uow = Mock(wraps=UnidadDeTrabajoSql(s))
    uow.confirmar.side_effect = RuntimeError("commit fallido")
    srv = ServicioDeEntrega(OrdenDeServicioSqlRepository(s), Mock(guardar=Mock(return_value="r")), uow)
    with pytest.raises(RuntimeError):
        srv.registrar_entrega("OS-500", "Ana", "INE1", b"f", b"s", 25.0, -100.0, "op", AHORA)
    uow.revertir.assert_called_once()
    s.expire_all()
    assert OrdenDeServicioSqlRepository(s).obtener_por_numero("OS-500").estatus is E.LLEGADA_A_DESTINO


def test_repositorios_de_cotizacion_unidad_operador(engine):
    with Session(engine) as s:
        UnidadSqlRepository(s).guardar(Unidad("Eco-12"))
        OperadorSqlRepository(s).guardar(Operador("OP-01", es_comodin=True))
        s.commit()
        assert UnidadSqlRepository(s).obtener_por_id("Eco-12").puede_asignarse()
        assert OperadorSqlRepository(s).obtener_por_id("OP-01").es_comodin
        with pytest.raises(Exception):
            CotizacionSqlRepository(s).obtener_por_folio("NO")
