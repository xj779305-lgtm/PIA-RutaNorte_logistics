"""Carga datos de demostracion (unidades y operadores) en la base configurada.

Uso: python -m scripts.seed_demo   (con DATABASE_URL definida, o SQLite local por defecto)
"""

from src.domain.model import Operador, Unidad
from src.infrastructure.config import Settings
from src.infrastructure.database import make_engine, make_session_factory
from src.infrastructure.repositories import OperadorRow, OperadorSqlRepository, UnidadRow, UnidadSqlRepository


def main() -> None:
    engine = make_engine(Settings().database_url)
    with make_session_factory(engine)() as s:
        for codigo in ("Eco-12", "Eco-15", "Eco-21"):
            if s.get(UnidadRow, codigo) is None:
                UnidadSqlRepository(s).guardar(Unidad(codigo))
        for ident, comodin in (("OP-01", False), ("OP-02", False), ("OP-COM", True)):
            if s.get(OperadorRow, ident) is None:
                OperadorSqlRepository(s).guardar(Operador(ident, es_comodin=comodin))
        s.commit()
    print("Datos de demostracion cargados: Eco-12, Eco-15, Eco-21; OP-01, OP-02, OP-COM")


if __name__ == "__main__":
    main()
