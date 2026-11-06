# ADR-01 Domain Model como patrón principal de lógica de negocio

**Estado:** Aceptada

## Contexto
El proceso de recolección, traslado y entrega tiene varias decisiones y excepciones (BPMN), estados ordenados (G-16) e invariantes (RN-02, RN-03). Los problemas actuales son reportes informales, evidencias dispersas y poca trazabilidad (PR-01, PR-03, PR-04).

## Alternativas
Transaction Script: rápido, pero duplica reglas en cada script. Table Module: sirve para reportes, pero las reglas que cruzan conceptos no tienen dueño. Domain Model: reglas e invariantes en los objetos del negocio.

## Decisión
Domain Model para el proceso de ejecución del servicio. Transaction Script solo en las consultas de US-14 y US-15. Table Module descartado.

## Consecuencias
Beneficios: invariantes protegidas en un solo lugar, cambios localizados, pruebas sin base de datos. Costos: más diseño inicial, necesidad de Repository y Unit of Work.

## Trazabilidad
PR-01, PR-03, PR-04; OP-01, OP-07; RN-02, RN-03, RN-04; US-04, US-05, US-09, US-11, US-12, US-13; G-16, G-18

## Implementación en el código
`src/domain/model.py`, `src/application/services.py`
