from decimal import Decimal

from src.infrastructure.config import Settings, normalizar_url


def test_normalizar_url_de_postgres():
    assert normalizar_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalizar_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalizar_url("sqlite:///x.db") == "sqlite:///x.db"


def test_settings_lee_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("UMBRAL_ALTO_VALOR", "250000")
    assert Settings().umbral_alto_valor == Decimal("250000")
