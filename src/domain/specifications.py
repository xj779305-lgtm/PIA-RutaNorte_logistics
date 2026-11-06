"""Specification Pattern: reglas de negocio con nombre, combinables con AND, OR y NOT.

Cada regla vive en un objeto pequeno que se prueba por separado (BRD RN-03, US-05, US-09,
US-12, US-04). Se combinan con &, | y ~ sin repetir condiciones.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Generic, TypeVar

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, candidato: T) -> bool: ...

    def __and__(self, otra: Specification[T]) -> Specification[T]:
        return _And(self, otra)

    def __or__(self, otra: Specification[T]) -> Specification[T]:
        return _Or(self, otra)

    def __invert__(self) -> Specification[T]:
        return _Not(self)


class _And(Specification[T]):
    def __init__(self, a: Specification[T], b: Specification[T]):
        self.a, self.b = a, b

    def is_satisfied_by(self, candidato: T) -> bool:
        return self.a.is_satisfied_by(candidato) and self.b.is_satisfied_by(candidato)


class _Or(Specification[T]):
    def __init__(self, a: Specification[T], b: Specification[T]):
        self.a, self.b = a, b

    def is_satisfied_by(self, candidato: T) -> bool:
        return self.a.is_satisfied_by(candidato) or self.b.is_satisfied_by(candidato)


class _Not(Specification[T]):
    def __init__(self, a: Specification[T]):
        self.a = a

    def is_satisfied_by(self, candidato: T) -> bool:
        return not self.a.is_satisfied_by(candidato)


# ------------------------------------------------------------ reglas de RutaNorte


class EvidenciaCompleta(Specification):
    """RN-03 / US-13: foto, firma, receptor, identificacion, coordenadas y estampa."""

    def is_satisfied_by(self, evidencia) -> bool:
        return evidencia is not None and evidencia.esta_completa()


class MercanciaCoincide(Specification):
    """US-05 / G-13: tipo y peso inspeccionados iguales a lo declarado (sin tolerancia)."""

    def __init__(self, tipo_inspeccionado: str, peso_inspeccionado: Decimal):
        self.tipo = tipo_inspeccionado
        self.peso = peso_inspeccionado

    def is_satisfied_by(self, mercancia) -> bool:
        mismo_tipo = self.tipo.strip().casefold() == mercancia.tipo.strip().casefold()
        return mismo_tipo and self.peso == mercancia.peso_kg


class CargaDeAltoValor(Specification):
    """US-12 / G-12: el valor SUPERA el umbral (igual al umbral no es alto valor)."""

    def __init__(self, umbral: Decimal):
        self.umbral = umbral

    def is_satisfied_by(self, mercancia) -> bool:
        return mercancia.valor > self.umbral


class ControlesConfirmados(Specification):
    """US-12: unidad escolta y doble firma confirmadas por Operaciones."""

    def __init__(self, confirmados: bool):
        self.confirmados = confirmados

    def is_satisfied_by(self, _candidato=None) -> bool:
        return self.confirmados


class UnidadDisponible(Specification):
    """US-07 / G-14: una unidad averiada o ya asignada no se asigna."""

    def is_satisfied_by(self, unidad) -> bool:
        return unidad.puede_asignarse()


class OperadorDisponible(Specification):
    """US-08: un operador indispuesto o ya asignado no se asigna."""

    def is_satisfied_by(self, operador) -> bool:
        return operador.puede_asignarse()


class CotizacionConfirmada(Specification):
    """US-03 / US-04: solo una cotizacion 'Confirmado' genera orden."""

    def is_satisfied_by(self, cotizacion) -> bool:
        return cotizacion.esta_confirmada()


def recoleccion_permitida(tipo_inspeccionado: str, peso_inspeccionado: Decimal, umbral: Decimal, controles: bool) -> Specification:
    """Composicion: coincide AND (NOT alto valor OR controles confirmados)."""
    return MercanciaCoincide(tipo_inspeccionado, peso_inspeccionado) & (~CargaDeAltoValor(umbral) | ControlesConfirmados(controles))
