# Matriz de trazabilidad: BRD / User Story → regla → componente → prueba → endpoint

| Origen | Regla de negocio | Componente (código) | Prueba | Endpoint |
|---|---|---|---|---|
| US-01 | Solicitud genera folio y notifica a Ventas | `ServicioDeCotizaciones.solicitar` | `test_flujo_completo_de_cotizacion_a_entrega` | `POST /cotizaciones` |
| US-02, RN-01 | Solo Ventas cotiza; costo por distancia, peso y tipo de unidad | `Cotizacion.cotizar`, `CalculadoraDeCotizacion` | `test_cotizacion_flujo_y_reglas`, `test_calculadora_de_cotizacion` | `POST /cotizaciones/{folio}/cotizar` |
| US-03 | Aceptar → Confirmado; rechazar cancela | `Cotizacion.aceptar/rechazar` | `test_cotizacion_rechazada_por_el_cliente` | `POST /cotizaciones/{folio}/aceptar` · `/rechazar` |
| US-04, RN-02 | Solo Operaciones genera la orden de una cotización Confirmada | `OrdenDeServicio.generar`, `CotizacionConfirmada` | CP-04, CP-05, CP-06; `test_403_ventas_no_genera_ordenes` | `POST /ordenes` |
| US-04, OP-07 | Unidad/operador no disponibles no se asignan | `UnidadDisponible`, `OperadorDisponible` | CP-13, `test_operador_indispuesto_no_se_asigna` | `POST /ordenes` (409) |
| US-05 | Mercancía debe coincidir en peso y tipo (sin tolerancia) | `MercanciaCoincide`, `registrar_recoleccion` | CP-10, CP-11, CP-12 | `POST /ordenes/{n}/recoleccion` |
| US-12, G-12 | Alto valor (> umbral) exige unidad escolta y doble firma | `CargaDeAltoValor`, `recoleccion_permitida`, `PoliticaDeCargaDeAltoValor` | CP-07, CP-08, CP-09, `test_composicion_and_or_not` | `POST /ordenes/{n}/recoleccion` |
| US-09, G-13 | Rechazo exige fotos, detiene el flujo y avisa a Operaciones | `rechazar_mercancia`, `OrdenDetenida` | `test_rechazar_mercancia_detiene…`, CP-15, `test_rechazo_de_mercancia_detiene_y_notifica` | `POST /ordenes/{n}/rechazo` |
| US-06 | Iniciar traslado → En tránsito | `iniciar_traslado` | `test_flujo_completo_hasta_entregado` | `POST /ordenes/{n}/traslado` |
| US-07, G-14 | Avería durante el trayecto marca la unidad averiada y alerta | `reportar_averia`, `Unidad.marcar_averiada` | `test_averia_solo_durante_el_trayecto`, `test_averia_y_reasignacion` | `POST /ordenes/{n}/averia` |
| US-08 | Solo Operaciones reasigna con un operador libre | `reasignar_operador` | `test_reasignar_operador_solo_operaciones…` | `POST /ordenes/{n}/reasignar-operador` |
| US-17 (H-06) | Llegada a destino (G-16) | `registrar_llegada` | CP-03 | `POST /ordenes/{n}/llegada` |
| US-10, G-19 | Destinatario ausente: exige foto y ubicación, registra excepción y alerta a Operaciones | `reportar_destinatario_ausente`, `ServicioDeEntrega.reportar_destinatario_ausente` | `test_us10_*` (dominio y API) | `POST /ordenes/{n}/destinatario-ausente` |
| US-11, G-17, RN-03 | Entrega con daños o faltantes: la evidencia sigue obligatoria y se genera reporte vinculado a la orden | `registrar_entrega_con_anomalias` (CU-05) | `test_us11_*` (dominio y API) | `POST /ordenes/{n}/entrega-con-anomalias` |
| US-13, RN-03, CE-03 | No hay entrega sin evidencia completa e inalterable | `EvidenciaCompleta`, `EvidenciaDeEntrega` (frozen) | CP-01, CP-02, `test_evidencia_es_inalterable`, `test_422_entrega_sin_firma` | `POST /ordenes/{n}/entrega` |
| G-16 | El estatus solo avanza por transiciones válidas | `MaquinaDeEstatus` | CP-03, `test_maquina_de_estatus` | 409 |
| G-18 | Todo cambio queda en la bitácora | `_registrar` | CP-01, CP-14 | `GET /ordenes/{n}` |
| US-14, US-16, RN-04 | Consulta de estatus, ubicación lógica e historial | `ConsultasDeSeguimiento` | `test_flujo_completo_de_cotizacion_a_entrega` | `GET /ordenes/{n}` |
| ADR-03 | Commit confirma y rollback deshace | `transaccion`, `UnidadDeTrabajoSql` | CP-14, `test_si_el_commit_falla_se_revierte` | — |
| ADR-05, OP-02 | Avisos por puerto, después del commit | `INotificador`, `NotificadorEnLog` | CP-15, CP-16 | — |

## Pendientes declarados (no implementados en esta versión)
- **US-18** reintento de entrega (Operaciones define el reintento tras US-10).
- **US-15** reporte de eficiencia y rentabilidad (requiere H-09: fuente del tiempo estimado y costos).
- **IProveedorGps** (OP-05): depende de la API del proveedor (H-04).
- **PriorizaciónDeAsignación** (OP-07): orden de criterios sin definir (H-02).
- Umbral de alto valor (H-01): configurable por `UMBRAL_ALTO_VALOR`; 100000 es solo un valor de prueba.
