"""Value Objects, Evidencia, Bitacora y Eventos: inmutables (frozen)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.domain.enums import EstatusDelServicio, TipoDeDiscrepancia, TipoDeIncidencia
from src.domain.errors import DatosInvalidos


@dataclass(frozen=True)
class MercanciaDeclarada:
    """G-10: tipo, peso y valor declarados. Se compara contra lo recibido."""

    tipo: str
    peso_kg: Decimal
    valor: Decimal

    def __post_init__(self):
        if not self.tipo.strip():
            raise DatosInvalidos("El tipo de mercancia es obligatorio")
        if self.peso_kg < 0 or self.valor < 0:
            raise DatosInvalidos("Peso y valor no pueden ser negativos")


@dataclass(frozen=True)
class EvidenciaDeEntrega:
    """G-20: foto, firma digital, datos de quien recibe, coordenadas y estampa de tiempo.

    Es frozen: una vez creada no se puede modificar (RN-03, inalterable).
    """

    receptor_nombre: str
    receptor_identificacion: str
    foto_ref: str | None
    firma_ref: str | None
    latitud: float | None
    longitud: float | None
    estampa: datetime | None

    def esta_completa(self) -> bool:
        textos = (self.receptor_nombre, self.receptor_identificacion, self.foto_ref, self.firma_ref)
        hay_textos = all(t is not None and t.strip() for t in textos)
        hay_datos = None not in (self.latitud, self.longitud, self.estampa)
        return hay_textos and hay_datos


@dataclass(frozen=True)
class EntradaDeBitacora:
    """G-18: evento, estatus, fecha y responsable. No se modifica."""

    evento: str
    estatus: EstatusDelServicio
    fecha: datetime
    responsable: str


@dataclass(frozen=True)
class Incidencia:
    tipo: TipoDeIncidencia
    tipo_discrepancia: TipoDeDiscrepancia | None
    fotos: tuple[str, ...]
    observaciones: str


@dataclass(frozen=True)
class EventoDeDominio:
    """Un hecho que ya ocurrio, por eso su nombre esta en pasado."""

    nombre: str
    numero_orden: str
    ocurrio_en: datetime
