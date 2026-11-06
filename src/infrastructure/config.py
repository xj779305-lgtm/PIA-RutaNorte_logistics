"""Configuracion por variables de entorno (12-Factor App). Sin secretos en el codigo."""

import os
from decimal import Decimal


def normalizar_url(url: str) -> str:
    """Render y otros proveedores entregan postgres://...; SQLAlchemy necesita el driver."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo) :]
    return url


class Settings:
    def __init__(self):
        self.database_url = normalizar_url(os.getenv("DATABASE_URL", "sqlite:///./rutanorte.db"))
        self.umbral_alto_valor = Decimal(os.getenv("UMBRAL_ALTO_VALOR", "100000"))  # H-01 pendiente
        self.evidencias_dir = os.getenv("EVIDENCIAS_DIR", "./evidencias")
        self.tarifa_km = Decimal(os.getenv("TARIFA_KM", "18.50"))
        self.tarifa_kg = Decimal(os.getenv("TARIFA_KG", "0.45"))
