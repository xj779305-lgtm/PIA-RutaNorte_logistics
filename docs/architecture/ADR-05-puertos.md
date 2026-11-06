# ADR-05 Puertos (interfaces) para GPS, almacenamiento de evidencias y notificaciones

**Estado:** Aceptada

## Contexto
El BRD pide aprovechar el GPS existente y reemplazar WhatsApp por reportes en la plataforma. La integración con el GPS depende de la API del proveedor.

## Alternativas
A: llamar a la API y al almacenamiento directamente desde los servicios. B: interfaces en la capa de aplicación con adaptadores en infraestructura.

## Decisión
Opción B: `IAlmacenDeEvidencias`, `INotificador` e `IUnidadDeTrabajo` implementados. `IProveedorGps` queda como puerto pendiente (H-04).

## Consecuencias
Beneficios: se prueba con simuladores (Mock) y se cambia de proveedor sin tocar casos de uso. Costos: adaptadores adicionales.

## Trazabilidad
OP-02, OP-05; RN-03, RN-04; US-07, US-10, US-14

## Implementación en el código
`src/application/ports.py`, `src/infrastructure/adapters.py`
