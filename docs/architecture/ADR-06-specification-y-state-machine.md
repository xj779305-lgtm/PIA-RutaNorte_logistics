# ADR-06 Specification Pattern y State Machine (añadida en el PIA)

**Estado:** Aceptada

## Contexto
El PIA exige Specification y State Machine. Las reglas de recolección (US-05, US-09, US-12) combinan condiciones (coincide AND (NOT alto valor OR controles)) y el estatus solo avanza por transiciones válidas (G-16).

## Alternativas
A: `if/else` dentro de los métodos de la orden. B: Specification con AND/OR/NOT y una tabla de transiciones.

## Decisión
Opción B. `src/domain/specifications.py` (7 reglas con nombre) y `src/domain/state_machine.py` (una sola tabla de transiciones para cotizaciones y órdenes).

## Consecuencias
Reglas probadas por separado y combinables sin duplicar condiciones; un estatus nuevo es una fila en la tabla. Costo: una capa más de objetos.

## Trazabilidad
RN-03; US-04, US-05, US-07, US-08, US-09, US-12, US-13; G-12, G-13, G-16
