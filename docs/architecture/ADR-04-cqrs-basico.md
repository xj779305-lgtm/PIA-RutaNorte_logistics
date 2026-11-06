# ADR-04 CQRS básico con View Models de lectura, sin bases de datos separadas

**Estado:** Aceptada

## Contexto
Atención al Cliente depende de llamadas a Operaciones (PR-02) y la rentabilidad se consolida a mano (PR-05).

## Alternativas
A: consultar usando los agregados. B: CQRS completo con base de lectura separada. C: Commands con el modelo de dominio y Queries con View Models propios sobre la misma base.

## Decisión
Opción C. Las consultas de US-14 y US-15 usan Transaction Script y vistas de lectura.

## Consecuencias
Beneficios: el modelo de escritura se mantiene limpio. Costos: más clases. **Estado de implementación:** `ConsultasDeSeguimiento` (US-14/US-16) existe; el reporte de eficiencia (US-15) queda pendiente (H-09).

## Trazabilidad
PR-02, PR-04, PR-05; OP-04, OP-06; RN-04; CE-01, CE-04; US-14, US-15

## Implementación en el código
`ConsultasDeSeguimiento` y `GET /ordenes/{numero}`
