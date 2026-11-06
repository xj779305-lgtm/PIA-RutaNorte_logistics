# ADR-03 Unit of Work por caso de uso; asignación de recursos en la misma transacción que la creación de la orden

**Estado:** Aceptada

## Contexto
Dos clientes pueden pedir la misma unidad y Operaciones debe aplicar reglas de prioridad (US-04, OP-07). Una unidad asignada dos veces sería un error de negocio.

## Alternativas
A: consistencia eventual con un evento. B: una sola transacción para la orden, la Unidad y el Operador.

## Decisión
Opción B solo para CU-01, como excepción documentada a la regla de un agregado por transacción. Los demás casos modifican un solo agregado.

## Consecuencias
Beneficios: no se asigna la misma unidad a dos servicios. Costos: posibles conflictos de concurrencia (control de versión pendiente, H-02/H-03).

## Trazabilidad
OP-07; US-04, US-08; G-05, G-06

## Implementación en el código
`transaccion()` en `services.py`; `UnidadDeTrabajoSql`; `ServicioDeOrdenes.generar_orden`
