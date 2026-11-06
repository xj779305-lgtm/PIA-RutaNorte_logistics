# Aplicación de SOLID (evidencia en el código)

| Principio | Cómo se aplica | Dónde |
|---|---|---|
| **S** | Un servicio por familia de casos de uso (cotizaciones, órdenes, recolección, entrega, consultas); las consultas salieron del servicio de entrega. | `src/application/services.py` |
| **O** | Una regla nueva es una Specification nueva (o una fila nueva en la tabla de transiciones), sin tocar `if/else` existentes. | `specifications.py`, `state_machine.py` |
| **L** | El operador comodín (G-07) es un atributo `es_comodin`, no una subclase que rechace operaciones. | `Operador` en `model.py` |
| **I** | Puertos pequeños por agregado, sin `eliminar` (la evidencia es inalterable, RN-03); `IAlmacenDeEvidencias` separada. | `src/application/ports.py` |
| **D** | Dominio y aplicación dependen de `Protocol`; SQL, archivos y avisos están en infraestructura; el API arma las dependencias. | `ports.py`, `src/infrastructure/`, `src/api/main.py` |
