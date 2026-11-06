**Objetivo:**

Analizar y documentar los requerimientos de RutaNorte Logistics mediante el levantamiento de información, identificando las necesidades, reglas de negocio y funcionalidades necesarias para mejorar el proceso de cotización, recolección, traslado y entrega de mercancía.

# **RutaNorte Logistics**

## **Contexto del Negocio**

RutaNorte Logistics es una empresa de transporte terrestre que opera rutas estratégicas conectando Monterrey, Saltillo, Reynosa, San Luis Potosí y Querétaro. Su modelo de negocio atiende tanto a clientes empresariales recurrentes como a servicios ocasionales, calculando sus tarifas en función de la distancia, el peso, el volumen, el tipo de unidad y los requerimientos especiales de la carga. Los clientes frecuentes o corporativos suelen operar bajo un tarifario o contrato con precios preestablecidos, mientras que los clientes eventuales o nuevos solicitan una cotización por cada viaje.

## **Objetivos**

A nivel de negocio, se busca aumentar la eficiencia operativa y fortalecer la relación con clientes corporativos mediante mayor visibilidad y trazabilidad. A nivel de proyecto, se busca reducir los tiempos de respuesta de Atención al Cliente, eliminar el uso de WhatsApp como canal operativo, y asegurar evidencia digital en las entregas.

## **Problemas**

| **ID**    | **Problema**                                                                                                                                                    |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PR-01** | Los operadores reportan estatus e incidencias de manera informal a través de WhatsApp.                                                                          |
| **PR-02** | Atención al Cliente depende por completo de llamadas o consultas manuales a Operaciones para conocer el estado real de un envío.                                |
| **PR-03** | Las evidencias de entrega se encuentran dispersas o corren riesgo de pérdida.                                                                                   |
| **PR-04** | Existe dificultad para medir tiempos reales de traslado, detectar cuellos de botella y auditar retrasos.                                                        |
| **PR-05** | Los cálculos de rentabilidad por ruta o por cliente requieren consolidar información de distintas áreas manualmente, por lo que no se obtienen de forma rápida. |

## **Oportunidades**

| **ID**    | **Oportunidad**                                                                                                                                                                       |
|-----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **OP-01** | Centralizar y digitalizar el ciclo de vida del servicio, desde la cotización hasta la entrega.                                                                                        |
| **OP-02** | Eliminar la dependencia de WhatsApp como canal operativo, sustituyéndolo por reportes estructurados en la plataforma.                                                                 |
| **OP-03** | Asegurar evidencias digitales de entrega (foto, firma, geolocalización) que no se pierdan ni se dispersen.                                                                            |
| **OP-04** | Brindar visibilidad en tiempo real del estatus del servicio a clientes, Atención al Cliente y áreas internas.                                                                         |
| **OP-05** | Aprovechar el sistema de GPS que ya existe en las unidades, integrando su estatus a la plataforma en vez de construir rastreo desde cero.                                             |
| **OP-06** | Automatizar los reportes de rentabilidad por ruta/cliente que hoy se arman manualmente.                                                                                               |
| **OP-07** | Formalizar reglas claras de priorización cuando dos clientes solicitan la misma unidad (contrato, volumen, antigüedad, rentabilidad, orden de llegada), reduciendo decisiones ad-hoc. |

## **Actores y Stakeholders**

| **Actor**                  | **Rol en el proceso**                                                                                                                                                              |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Cliente**                | Solicita servicios de transporte, cotizaciones y consulta el estatus de su carga.                                                                                                  |
| **Ventas**                 | Recibe requerimientos, elabora y envía cotizaciones al cliente.                                                                                                                    |
| **Operaciones**            | Gestiona la planeación logística, genera órdenes de servicio y asigna unidades, operadores, rutas y horarios de recolección.                                                       |
| **Gerente de Operaciones** | Consulta reportes de tiempos reales contra estimados y de rentabilidad por ruta/cliente para medir el rendimiento y detectar cuellos de botella. Pertenece al área de Operaciones. |
| **Operador**               | Ejecuta el traslado físico de la mercancía, valida cargas en origen, reporta incidencias y registra evidencias de entrega.                                                         |
| **Destinatario**           | Recibe físicamente la mercancía y proporciona la confirmación o firma de recepción.                                                                                                |
| **Atención al Cliente**    | Consulta el estado de los servicios para dar soporte y resolver dudas a los clientes.                                                                                              |

## **Alcance del Proyecto**

| **Dentro del alcance**                                                  | **Fuera del alcance**                                                                   |
|-------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| Módulo de gestión y generación de cotizaciones                          | Contabilidad y facturación fiscal automatizada (ERP externo)                            |
| Creación y administración de órdenes de servicio                        | Sistemas de telemetría satelital física (GPS de terceros; solo se consumen sus estatus) |
| Asignación de recursos (unidades, operadores, rutas)                    | Negociación y administración de contratos/tarifarios con clientes corporativos          |
| Seguimiento de estados del servicio e incidencias                       | Gestión de nómina o pagos a operadores                                                  |
| App/portal para operadores (evidencias y reportes en ruta)              | Trámites aduanales o de comercio exterior                                               |
| Panel de consulta para Atención al Cliente y clientes finales           |                                                                                         |
| Módulo gerencial de reportes de tiempos y rentabilidad por ruta/cliente |                                                                                         |

## **Requerimientos de Negocio**

| **ID**    | **Requerimiento**                                                                                                                                          |
|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **RN-01** | El sistema debe permitir el cálculo automático de cotizaciones en menos de 5 minutos basándose en la matriz de distancias, peso, volumen y tipo de unidad. |
| **RN-02** | El sistema debe restringir la modificación de órdenes de servicio confirmadas exclusivamente al rol de Operaciones.                                        |
| **RN-03** | El sistema debe registrar de forma digital e inalterable la evidencia de entrega (fotografía y firma digital del destinatario).                            |
| **RN-04** | El sistema debe proveer trazabilidad en tiempo real del estatus del envío para consulta de Atención al Cliente y el Cliente final.                         |

## **Restricciones**

El sistema debe operar en una arquitectura web responsiva accesible desde computadoras de escritorio y dispositivos móviles. Toda evidencia de entrega digital debe guardarse con estampa de tiempo y coordenadas geográficas. La integración con el sistema de GPS existente dependerá de la disponibilidad de una API del proveedor externo, ya que la telemetría física queda fuera del alcance del proyecto.

## **Supuestos**

Se asume que los operadores cuentan con un teléfono inteligente con conectividad de datos móviles durante las rutas, y que los clientes proporcionan datos reales y precisos sobre las dimensiones y peso de la mercancía al solicitar la cotización. También se asume que los clientes corporativos con tarifario fijo ya cuentan con un contrato vigente registrado previamente, por lo que el sistema no gestiona la negociación de dichos contratos.

## **Criterios de Éxito**

| **ID**    | **Criterio**                      | **Descripción**                                                                                                                   |
|-----------|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **CE-01** | Tiempo de respuesta               | Reducir en 50% el tiempo que tarda Atención al Cliente en responder sobre el estatus de un envío.                                 |
| **CE-02** | Eliminación de WhatsApp operativo | Eliminar totalmente el uso de WhatsApp para reportes operativos críticos, centralizándolos en la plataforma.                      |
| **CE-03** | Evidencia digital completa        | Lograr que el 100% de las órdenes de entrega cuenten con evidencia digital capturada de forma inmediata al finalizar el servicio. |
| **CE-04** | Reportes de rentabilidad          | Generar reportes de rentabilidad por ruta/cliente de forma automática, sin necesidad de consolidación manual entre áreas.         |
