# RutaNorte Logistics

## Descripción del proyecto

**RutaNorte Logistics** es un proyecto de software orientado a la gestión y seguimiento de operaciones logísticas. Su propósito es organizar los procesos relacionados con las solicitudes de servicio, la asignación de unidades, la ejecución de entregas y el control de incidencias, facilitando la trazabilidad de las operaciones.

El sistema se basa en las necesidades operativas del negocio y busca mantener la integridad de la información, controlar los estados de las órdenes y garantizar que las entregas cuenten con evidencia digital.

## Objetivo

Desarrollar una solución de software que permita gestionar las operaciones logísticas de RutaNorte, aplicando una arquitectura organizada por capas, reglas de negocio centralizadas y mecanismos de persistencia y pruebas que faciliten el mantenimiento y la evolución del sistema.

## Alcance del sistema

El proyecto contempla los siguientes procesos:

- **Gestión de órdenes de servicio:** registro y seguimiento de las órdenes.
- **Asignación de unidades:** priorización de solicitudes cuando existe competencia por una misma unidad.
- **Seguimiento de entregas:** consulta del estado y avance de las órdenes.
- **Registro de incidencias:** control de situaciones como averías y problemas durante la entrega.
- **Evidencia digital:** registro de evidencias para respaldar la finalización de una entrega.
- **Control de estados:** transición ordenada de los estados de las órdenes.
- **Reportes de eficiencia:** consulta de información relacionada con tiempos y rentabilidad de las operaciones.

## Arquitectura y diseño

La solución se estructura tomando como referencia los principios de Domain-Driven Design (DDD) y una arquitectura por capas, separando las responsabilidades del sistema:

- **Dominio:** contiene las entidades, reglas de negocio, objetos de valor y políticas.
- **Aplicación:** coordina los casos de uso mediante servicios, comandos y consultas.
- **Infraestructura:** contempla la persistencia y las integraciones externas mediante interfaces y sus implementaciones.
- **API:** proporciona los puntos de acceso para interactuar con las operaciones del sistema.
- **Pruebas:** permiten verificar el comportamiento de las reglas y los casos de uso.

Se consideran patrones como Repository, Unit of Work, Service Layer y CQRS, además de los principios SOLID.

## Reglas importantes del negocio

- Una orden debe respetar la secuencia de estados establecida.
- Una entrega no puede marcarse como completada sin evidencia digital completa e inalterable.
- La asignación de unidades debe considerar los criterios de prioridad definidos por el negocio.
- Las reglas de negocio deben permanecer centralizadas en el dominio y no depender directamente de la API o de la infraestructura.

## Tecnologías

- Python
- FastAPI
- SQLAlchemy
- SQLite para pruebas
- PostgreSQL para el entorno de despliegue previsto
- Pytest para pruebas automatizadas
- Git y GitHub para el control de versiones
- Docker para la configuración del entorno
