# ADR-02 OrdenDeServicio como Aggregate que contiene Incidencias, Bitácora y EvidenciaDeEntrega

**Estado:** Aceptada

## Contexto
Cada cambio de estatus debe quedar en la bitácora (G-18), no puede haber entrega sin evidencia completa (RN-03) y las incidencias detienen o modifican el flujo (US-09, US-10, US-11).

## Alternativas
A: Bitácora, evidencia e incidencia como agregados separados. B: un solo agregado que también contenga Unidad y Operador. C: OrdenDeServicio con sus partes y recursos referenciados por identificador.

## Decisión
Opción C. La Unidad y el Operador son agregados propios. Los archivos de evidencia se guardan en infraestructura y la orden conserva su referencia.

## Consecuencias
Beneficios: consistencia dentro de un límite claro; la raíz controla todos los cambios. Costos: la bitácora crece con el tiempo.

## Trazabilidad
RN-02, RN-03; G-18; US-09, US-10, US-11, US-13

## Implementación en el código
`OrdenDeServicio`, `Unidad`, `Operador` en `src/domain/model.py`; `EvidenciaDeEntrega` frozen en `value_objects.py`
