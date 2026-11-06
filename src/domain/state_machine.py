"""State Machine del estatus del servicio (G-16, invariante 3).

Una sola tabla de transiciones valida el avance de cotizaciones y ordenes. Cualquier salto
que no este en la tabla se rechaza con TransicionDeEstatusInvalida.
"""

from src.domain.enums import EstatusDelServicio as E
from src.domain.errors import TransicionDeEstatusInvalida

TRANSICIONES: dict[E, frozenset[E]] = {
    E.SOLICITADO: frozenset({E.COTIZADO}),
    E.COTIZADO: frozenset({E.CONFIRMADO}),
    E.CONFIRMADO: frozenset({E.UNIDAD_ASIGNADA}),
    E.UNIDAD_ASIGNADA: frozenset({E.RECOLECTADO}),
    E.RECOLECTADO: frozenset({E.EN_TRANSITO}),
    E.EN_TRANSITO: frozenset({E.LLEGADA_A_DESTINO}),
    E.LLEGADA_A_DESTINO: frozenset({E.ENTREGADO}),
    E.ENTREGADO: frozenset(),
}


class MaquinaDeEstatus:
    @staticmethod
    def puede_pasar(origen: E, destino: E) -> bool:
        return destino in TRANSICIONES[origen]

    @classmethod
    def validar(cls, origen: E, destino: E) -> None:
        if not cls.puede_pasar(origen, destino):
            raise TransicionDeEstatusInvalida(f"{origen.value} -> {destino.value}")

    @staticmethod
    def es_final(estatus: E) -> bool:
        return not TRANSICIONES[estatus]
