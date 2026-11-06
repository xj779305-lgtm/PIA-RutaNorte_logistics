from datetime import UTC, datetime
from decimal import Decimal

import pytest

from src.domain.enums import EstatusDelServicio as E
from src.domain.model import OrdenDeServicio
from src.domain.policies import PoliticaDeCargaDeAltoValor
from src.domain.value_objects import EvidenciaDeEntrega, MercanciaDeclarada

AHORA = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)


@pytest.fixture
def politica():
    return PoliticaDeCargaDeAltoValor(Decimal("100000"))


def hacer_orden(estatus=E.UNIDAD_ASIGNADA, valor="50000", tipo="autopartes", peso="1500"):
    return OrdenDeServicio("OS-500", "COT-1", "Eco-12", "OP-01", MercanciaDeclarada(tipo, Decimal(peso), Decimal(valor)), estatus)


def evidencia(**cambios):
    datos = dict(
        receptor_nombre="Ana",
        receptor_identificacion="INE123",
        foto_ref="f.bin",
        firma_ref="s.bin",
        latitud=25.68,
        longitud=-100.31,
        estampa=AHORA,
    )
    datos.update(cambios)
    return EvidenciaDeEntrega(**datos)
