# Decisiones técnicas y patrones

| Patrón / decisión | Justificación | Código |
|---|---|---|
| Domain Model + Aggregates | Invariantes RN-02/RN-03 protegidas en un solo lugar (ADR-01, ADR-02) | `src/domain/model.py` |
| Value Objects inmutables (`frozen`) | Evidencia inalterable (RN-03); `Decimal` para peso y valor (límites exactos como 1500.01 vs 1500) | `value_objects.py` |
| Specification | Reglas con nombre combinables AND/OR/NOT (ADR-06) | `specifications.py` |
| State Machine | Transiciones válidas de G-16 en una tabla (ADR-06) | `state_machine.py` |
| Domain Events | Hechos en pasado, registrados después de validar y cambiar el estado | `OrdenDeServicio._registrar` |
| Domain Services | Política de alto valor (umbral configurable, H-01) y calculadora de cotización (RN-01) | `policies.py` |
| Repository + Unit of Work | Persistencia sin que el dominio conozca SQL; commit/rollback por caso de uso (ADR-03) | `repositories.py`, `services.transaccion` |
| Ports and Adapters | Probar con Mock y cambiar proveedor (ADR-05) | `ports.py`, `adapters.py` |
| API REST (FastAPI) | Solo traduce HTTP y errores de dominio: 403, 404, 409, 422 | `src/api/main.py` |
| 12-Factor | Configuración por variables de entorno, sin secretos en el código | `config.py`, `.env.example` |
| Aviso después del commit | No se anuncia algo que no se guardó | `ServicioDeRecoleccion` |

## Diferencias respecto al modelo de pruebas del docente
El paquete `02_RutaNorte_Logistics` propone estados REGISTRADO → ASIGNADO → EN_RUTA → ENTREGADO y reglas ilustrativas (cliente preferente, total ≥ 1500). El propio LEEME indica que no reemplazan los requerimientos del equipo, por lo que se implementó el modelo del BRD/G-16 (Solicitado → … → Entregado). Equivalencia: REGISTRADO ≈ Solicitado, ASIGNADO ≈ Unidad asignada, EN_RUTA ≈ En tránsito, ENTREGADO ≈ Entregado.
