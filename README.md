# RutaNorte Logistics: lógica de negocio (PIA · Componentes de Lógica de Negocios)

Sistema de cotización, recolección, traslado y entrega de mercancía. Implementa DDD, Specification, State Machine y una API REST con FastAPI, con pruebas (≥ 80 %), CI/CD, Docker Compose y variables de entorno.

- **Equipo:** Ximena Alejandra Benavides Jasso (2052453) · Gerardo Alberto Bautista Hernández (2062418)
- **Repositorio:** `<URL del repositorio>`
- **Sistema desplegado:** `<URL de Render/Railway>` · Swagger UI: `<URL>/docs`

## Estructura
```
docs/            BRD.md · analisis/ (User Stories, Glosario) · architecture/ (ADRs, SOLID, diagramas, BPMN, trazabilidad) · api/openapi.json
src/domain/      entidades, Value Objects, agregados, eventos, Specifications, State Machine
src/application/ casos de uso y puertos
src/infrastructure/ repositorios SQLAlchemy, Unit of Work, adaptadores, configuración
src/api/         endpoints REST
tests/           unitarias + integración + API
.github/workflows/ci.yml · docker-compose.yml · Dockerfile · .env.example
```

## Ejecución local
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.api            # http://localhost:8000/docs  (SQLite por defecto)
python -m scripts.seed_demo  # unidades y operadores de demostración (opcional)
```

## Pruebas y calidad
```bash
python -m pytest -v --cov=src --cov-report=term-missing --cov-fail-under=80
python -m ruff check src tests
```

## Docker Compose (DB + App + Tests)
```bash
cp .env.example .env          # cambia POSTGRES_PASSWORD (y la misma clave en DATABASE_URL)
docker compose up --build     # PostgreSQL + API en http://localhost:8000/docs
docker compose --profile tests run --rm tests   # suite completa con cobertura
```

## Despliegue (Render)
Conecta el repositorio en Render como *Blueprint* (`render.yaml`): crea la base PostgreSQL y el servicio web con Docker. `DATABASE_URL` se inyecta sola. Swagger queda en `/docs`.

## Demostración (orden de las llamadas)
Roles por encabezado `X-Rol` (Ventas, Operaciones, Cliente…).
1. `POST /unidades` `{"codigo":"Eco-12"}` y `POST /operadores` `{"identificador":"OP-01"}`
2. `POST /cotizaciones` → folio (Solicitado)
3. `POST /cotizaciones/{folio}/cotizar` con `X-Rol: Ventas` → Cotizado
4. `POST /cotizaciones/{folio}/aceptar` → Confirmado
5. `POST /ordenes` con `X-Rol: Operaciones` → Unidad asignada (con `Ventas` responde 403)
6. `.../recoleccion` → Recolectado · `.../traslado` → En tránsito · `.../llegada` → Llegada a destino
7. `.../entrega` con foto, firma, receptor y coordenadas → Entregado (sin firma responde 422)
8. `GET /ordenes/{numero}` → estatus, incidencias e historial

Excepciones en destino (desde "Llegada a destino"):
- `POST /ordenes/{n}/destinatario-ausente` (US-10): foto y ubicación obligatorias; alerta a Operaciones.
- `POST /ordenes/{n}/entrega-con-anomalias` (US-11): evidencia completa + descripción; queda Entregado con reporte vinculado.

Códigos: 403 rol no permitido · 404 no existe · 409 transición/recurso no disponible · 422 regla violada.

## Trazabilidad y decisiones
Ver `docs/architecture/trazabilidad.md`, los ADR-01 a ADR-06, `SOLID.md` y `decisiones-tecnicas.md`.
