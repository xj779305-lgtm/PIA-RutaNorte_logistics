from decimal import Decimal

import pytest

from src.domain.enums import EstatusDelServicio as E
from src.domain.errors import DatosInvalidos, TransicionDeEstatusInvalida
from src.domain.model import Cotizacion, Operador, Unidad
from src.domain.policies import CalculadoraDeCotizacion
from src.domain.specifications import (
    CargaDeAltoValor,
    ControlesConfirmados,
    CotizacionConfirmada,
    EvidenciaCompleta,
    MercanciaCoincide,
    OperadorDisponible,
    UnidadDisponible,
    recoleccion_permitida,
)
from src.domain.state_machine import MaquinaDeEstatus
from src.domain.value_objects import MercanciaDeclarada
from src.infrastructure.adapters import DISTANCIAS_KM
from tests.conftest import evidencia

M = MercanciaDeclarada("autopartes", Decimal("1500"), Decimal("200000"))


def test_specifications_simples():
    assert EvidenciaCompleta().is_satisfied_by(evidencia())
    assert not EvidenciaCompleta().is_satisfied_by(None)
    assert MercanciaCoincide("AUTOPARTES", Decimal("1500")).is_satisfied_by(M)
    assert CargaDeAltoValor(Decimal("100000")).is_satisfied_by(M)
    assert UnidadDisponible().is_satisfied_by(Unidad("U"))
    assert OperadorDisponible().is_satisfied_by(Operador("O"))
    assert CotizacionConfirmada().is_satisfied_by(Cotizacion("C", E.CONFIRMADO, M))


def test_composicion_and_or_not():
    alto, ok, no = CargaDeAltoValor(Decimal("100000")), ControlesConfirmados(True), ControlesConfirmados(False)
    assert (alto & ok).is_satisfied_by(M)
    assert not (alto & no).is_satisfied_by(M)
    assert (~alto | no).is_satisfied_by(M) is False
    assert (alto | no).is_satisfied_by(M)
    assert (~~alto).is_satisfied_by(M)


@pytest.mark.parametrize("controles,esperado", [(True, True), (False, False)])
def test_recoleccion_permitida_composicion(controles, esperado):
    regla = recoleccion_permitida("autopartes", Decimal("1500"), Decimal("100000"), controles)
    assert regla.is_satisfied_by(M) is esperado


def test_maquina_de_estatus():
    assert MaquinaDeEstatus.puede_pasar(E.CONFIRMADO, E.UNIDAD_ASIGNADA)
    assert MaquinaDeEstatus.es_final(E.ENTREGADO) and not MaquinaDeEstatus.es_final(E.SOLICITADO)
    with pytest.raises(TransicionDeEstatusInvalida):
        MaquinaDeEstatus.validar(E.SOLICITADO, E.ENTREGADO)
    with pytest.raises(TransicionDeEstatusInvalida):
        MaquinaDeEstatus.validar(E.ENTREGADO, E.SOLICITADO)


def test_calculadora_de_cotizacion():
    c = CalculadoraDeCotizacion(DISTANCIAS_KM, Decimal("18.50"), Decimal("0.45"))
    base = c.calcular("Monterrey", "Saltillo", Decimal("1000"), "caja seca")
    assert base == Decimal("2022.50")  # 85*18.5 + 1000*0.45
    assert c.calcular("saltillo", "monterrey", Decimal("1000"), "refrigerada") == (base * Decimal("1.35")).quantize(Decimal("0.01"))
    with pytest.raises(DatosInvalidos):
        c.calcular("Monterrey", "Mérida", Decimal("1"), "caja seca")
    with pytest.raises(DatosInvalidos):
        c.calcular("Monterrey", "Saltillo", Decimal("1"), "barco")


def test_politica_de_alto_valor():
    from src.domain.policies import PoliticaDeCargaDeAltoValor

    p = PoliticaDeCargaDeAltoValor(Decimal("100000"))
    assert p.controles_obligatorios(Decimal("100000")) == ()
    assert p.controles_obligatorios(Decimal("100000.01")) == ("unidad escolta", "doble firma")
