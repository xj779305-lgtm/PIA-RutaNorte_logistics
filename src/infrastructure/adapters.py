"""Adaptadores de los puertos: almacen de evidencias, notificador y matriz de distancias."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from pathlib import Path

log = logging.getLogger("rutanorte.notificaciones")

# Distancias aproximadas por carretera (km). Configuracion de ejemplo, no un dato del negocio.
DISTANCIAS_KM = {
    frozenset({"Monterrey", "Saltillo"}): Decimal("85"),
    frozenset({"Monterrey", "Reynosa"}): Decimal("220"),
    frozenset({"Monterrey", "San Luis Potosí"}): Decimal("520"),
    frozenset({"Monterrey", "Querétaro"}): Decimal("830"),
    frozenset({"Saltillo", "San Luis Potosí"}): Decimal("430"),
    frozenset({"Saltillo", "Querétaro"}): Decimal("740"),
    frozenset({"San Luis Potosí", "Querétaro"}): Decimal("200"),
    frozenset({"Reynosa", "Saltillo"}): Decimal("300"),
}


class AlmacenDeEvidenciasLocal:
    """IAlmacenDeEvidencias sobre el disco. En produccion se cambiaria por almacenamiento de objetos."""

    def __init__(self, carpeta: str):
        self.carpeta = Path(carpeta)

    def guardar(self, contenido: bytes) -> str:
        self.carpeta.mkdir(parents=True, exist_ok=True)
        nombre = f"{uuid.uuid4().hex}.bin"
        (self.carpeta / nombre).write_bytes(contenido)
        return nombre


class NotificadorEnLog:
    """INotificador en la plataforma: registra el aviso (sustituye a WhatsApp, OP-02)."""

    def __init__(self):
        self.enviados: list[tuple[str, str, str]] = []

    def alertar(self, destino: str, numero_orden: str, mensaje: str) -> None:
        self.enviados.append((destino, numero_orden, mensaje))
        log.info("[%s] %s: %s", destino, numero_orden, mensaje)
