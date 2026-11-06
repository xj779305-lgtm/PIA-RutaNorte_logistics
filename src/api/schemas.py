"""Contratos de entrada del API (Pydantic)."""

from __future__ import annotations

import base64
from decimal import Decimal

from pydantic import BaseModel, Field

from src.domain.enums import TipoDeDiscrepancia


class SolicitudDeCotizacion(BaseModel):
    origen: str = Field(examples=["Monterrey"])
    destino: str = Field(examples=["Querétaro"])
    tipo_mercancia: str = Field(examples=["autopartes"])
    peso_kg: Decimal = Field(examples=["1500"])
    valor: Decimal = Field(examples=["80000"])
    tipo_de_unidad: str = Field(examples=["caja seca"])


class NuevaUnidad(BaseModel):
    codigo: str = Field(examples=["Eco-12"])


class NuevoOperador(BaseModel):
    identificador: str = Field(examples=["OP-01"])
    es_comodin: bool = False


class GenerarOrden(BaseModel):
    numero: str = Field(examples=["OS-500"])
    folio_cotizacion: str
    unidad_id: str
    operador_id: str


class Recoleccion(BaseModel):
    tipo_inspeccionado: str
    peso_inspeccionado: Decimal
    controles_confirmados: bool = False


class RechazoDeMercancia(BaseModel):
    tipo_discrepancia: TipoDeDiscrepancia
    fotos_base64: list[str] = []
    observaciones: str = ""

    def fotos(self) -> list[bytes]:
        return [base64.b64decode(f) for f in self.fotos_base64]


class Averia(BaseModel):
    descripcion: str


class Reasignacion(BaseModel):
    nuevo_operador_id: str


class Entrega(BaseModel):
    receptor_nombre: str = ""
    receptor_identificacion: str = ""
    foto_base64: str | None = None
    firma_base64: str | None = None
    latitud: float | None = None
    longitud: float | None = None

    def foto(self) -> bytes | None:
        return base64.b64decode(self.foto_base64) if self.foto_base64 else None

    def firma(self) -> bytes | None:
        return base64.b64decode(self.firma_base64) if self.firma_base64 else None


class DestinatarioAusente(BaseModel):
    foto_base64: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    observaciones: str = ""

    def foto(self) -> bytes | None:
        return base64.b64decode(self.foto_base64) if self.foto_base64 else None


class EntregaConAnomalias(Entrega):
    descripcion: str = Field(default="", examples=["Dos piezas rotas"])
    fotos_anomalia_base64: list[str] = []

    def fotos_anomalia(self) -> list[bytes]:
        return [base64.b64decode(f) for f in self.fotos_anomalia_base64]
