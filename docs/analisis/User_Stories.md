**Objetivo:**

Definir y documentar los User Stories de RutaNorte Logistics mediante el levantamiento de información, describiendo las capacidades y necesidades de cada actor con sus respectivos criterios de aceptación en Gherkin, para asegurar que el sistema cubra correctamente el proceso de cotización, recolección, traslado y entrega de mercancía.










ID
Rol
User Story
Criterios de Aceptación (Gherkin)




US-01
Cliente
Como cliente, quiero ingresar origen, destino, mercancía, peso, dimensiones, tipo de unidad y requerimientos especiales, para solicitar formalmente una cotización de transporte.
Escenario: Solicitud exitosa
Dado que el cliente está en el portal
Cuando ingresa Monterrey, Querétaro, 1500kg, tipo de unidad y requerimientos
Entonces el sistema genera folio y notifica a Ventas


US-02
Agente de Ventas
Como agente de Ventas, quiero calcular y registrar el costo del servicio según las especificaciones, para enviar una propuesta comercial formal al cliente.
Escenario: Generar cotización
Dado que ve solicitud pendiente
Cuando calcula costo por distancia/peso
Entonces emite cotización estatus "Cotizado"


US-03
Cliente
Como cliente, quiero aceptar o rechazar la cotización enviada, para autorizar el inicio del proceso logístico.
Escenario: Cliente aprueba
Dado que recibió la cotización
Cuando hace clic en "Aceptar"
Entonces estatus pasa a "Confirmado" para Operaciones


US-04
Personal de Operaciones
Como personal de Operaciones, quiero generar la orden de servicio asignando unidad, operador, ruta y horario (priorizando por contrato, volumen, antigüedad, rentabilidad u orden de llegada si hay conflicto), para planificar formalmente la recolección.
Escenario: Asignar recursos
Dado cotización confirmada
Cuando selecciona Eco-12, operador y ruta
Entonces genera Orden y estatus "Unidad asignada"


US-05
Operador
Como operador, quiero registrar la llegada a origen y validar la mercancía física, para confirmar que coincide con lo declarado.
Escenario: Validar carga
Dado que está en origen con orden OS-500
Cuando inspecciona que coincide peso y tipo
Entonces actualiza estatus a "Recolectado"


US-06
Operador
Como operador, quiero actualizar el estatus al iniciar el viaje a destino, para mantener informada a la central sobre el progreso.
Escenario: Iniciar trayecto
Dado mercancía recolectada y cargada
Cuando presiona "Iniciar Trayecto" en app
Entonces estatus cambia a "En tránsito"


US-07
Operador
Como operador, quiero reportar una falla mecánica durante el trayecto, para alertar a Operaciones y activar auxilio vial o transbordo.
Escenario: Avería en carretera
Dado que la unidad sufre fallo mecánico
Cuando reporta incidencia con descripción
Entonces notifica a Operaciones con ubicación GPS


US-08
Personal de Operaciones
Como personal de Operaciones, quiero reasignar un operador ante una emergencia, para evitar retrasos en el itinerario de entrega.
Escenario: Reasignar operador
Dado operador indispuesto por salud
Cuando operaciones sustituye por recurso libre
Entonces actualiza bitácora y notifica al nuevo


US-09
Operador
Como operador, quiero registrar cuando la mercancía en origen no coincide con lo declarado (cantidad, tipo o estado) o está dañada, para documentar la excepción y notificar a Operaciones.
Escenario: Mercancía distinta
Dado discrepancia de volumen o daño previo
Cuando selecciona "Mercancía rechazada" y adjunta fotos
Entonces detiene flujo y avisa a Operaciones


US-10
Operador
Como operador, quiero reportar cuando no hay quien reciba en destino (con foto y ubicación), para solicitar instrucciones adicionales a Operaciones.
Escenario: Destinatario ausente
Dado que llega al destino y nadie recibe
Cuando registra incidencia con foto del domicilio
Entonces marca excepción y alerta a Operaciones


US-11
Operador
Como operador, quiero registrar anomalías en la entrega (daños o faltantes), para dejar constancia legal y operativa.
Escenario: Daños parciales
Dado que destinatario detecta piezas rotas
Cuando registra "Entrega parcial con daños"
Entonces genera reporte vinculado a la orden


US-12
Personal de Operaciones
Como personal de Operaciones, quiero activar protocolos de seguridad para cargas de alto valor, para mitigar riesgos de siniestro o robo.
Escenario: Carga alto valor
Dado orden que supera umbral de valor
Cuando el sistema valida las características
Entonces exige unidad escolta y doble firma


US-13
Operador
Como operador, quiero capturar identificación oficial, firma digital y fotografía de quien recibe, para cerrar formalmente el ciclo del servicio.
Escenario: Éxito en entrega
Dado mercancía entregada al destinatario
Cuando captura identificación, nombre, foto y firma táctil
Entonces almacena evidencia y estatus "Entregado"


US-14
Atención al Cliente
Como agente de Atención al Cliente, quiero consultar en el sistema el estatus actualizado de cualquier orden, para responder de inmediato sin llamar a Operaciones.
Escenario: Consulta rápida
Dado llamada de cliente por orden OS-302
Cuando el agente busca el folio en el sistema
Entonces ve ubicación, estatus y historial sin llamadas


US-15
Gerente de Operaciones
Como gerente de Operaciones, quiero generar un reporte de tiempos reales vs. estimados y de rentabilidad por ruta/cliente, para medir rendimiento y detectar cuellos de botella.
Escenario: Reporte de eficiencia
Dado acceso al módulo gerencial
Cuando solicita indicador mensual de tiempos y rentabilidad
Entonces genera tabla de promedios, retrasos y rentabilidad


US-16
Cliente
Como cliente, quiero consultar el estatus y la ubicación de mi servicio con mi folio, para conocer el avance de mi carga sin llamar a la empresa.
Escenario: Consulta de estatus por el cliente
Dado que el cliente tiene un servicio activo con orden OS-500
Cuando ingresa su folio en el portal
Entonces ve el estatus actual, la ubicación y el historial


US-17
Operador
Como operador, quiero registrar la llegada al destino, para dejar constancia del inicio de la entrega y habilitar la captura de evidencia.
Escenario: Llegada a destino
Dado que la orden está "En tránsito"
Cuando presiona "Llegué a destino" en la app
Entonces estatus cambia a "Llegada a destino" y se registra en bitácora


US-18
Personal de Operaciones
Como personal de Operaciones, quiero definir un reintento de entrega cuando el destinatario está ausente o la dirección es incorrecta, para completar el servicio sin perder trazabilidad.
Escenario: Reintento de entrega
Dado una excepción de destinatario ausente o dirección incorrecta
Cuando Operaciones define nueva fecha y horario de reintento
Entonces registra el reintento en bitácora y notifica al operador



