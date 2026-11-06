"""Aggregates de RutaNorte: Cotizacion, Unidad, Operador y OrdenDeServicio.

Las reglas viven aqui, no en los servicios, el API ni la infraestructura. Cada metodo valida
primero, cambia el estado despues y registra el evento al final.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from src.domain.enums import (
    DisponibilidadDeOperador,
    DisponibilidadDeUnidad,
    EstatusDelServicio,
    Rol,
    TipoDeDiscrepancia,
    TipoDeIncidencia,
)
from src.domain.errors import (
    ControlesDeAltoValorRequeridos,
    CotizacionNoConfirmada,
    DatosInvalidos,
    DiscrepanciaDeMercancia,
    EvidenciaIncompleta,
    OperacionNoPermitidaParaRol,
    OperadorNoDisponible,
    OrdenDetenida,
    TransicionDeEstatusInvalida,
    UnidadNoDisponible,
)
from src.domain.specifications import (
    CotizacionConfirmada,
    EvidenciaCompleta,
    MercanciaCoincide,
    OperadorDisponible,
    UnidadDisponible,
    recoleccion_permitida,
)
from src.domain.state_machine import MaquinaDeEstatus
from src.domain.value_objects import (
    EntradaDeBitacora,
    EventoDeDominio,
    EvidenciaDeEntrega,
    Incidencia,
    MercanciaDeclarada,
)


@dataclass
class Cotizacion:
    """Aggregate Cotizacion (US-01, US-02, US-03). Solicitado -> Cotizado -> Confirmado."""

    folio: str
    estatus: EstatusDelServicio
    mercancia: MercanciaDeclarada
    origen: str = ""
    destino: str = ""
    tipo_de_unidad: str = ""
    costo: Decimal | None = None
    cancelada: bool = False  # rechazo del cliente: G-16 no define un estatus propio

    def esta_confirmada(self) -> bool:
        return self.estatus is EstatusDelServicio.CONFIRMADO and not self.cancelada

    def cotizar(self, costo: Decimal, rol: Rol) -> None:
        if rol is not Rol.VENTAS:
            raise OperacionNoPermitidaParaRol("Solo Ventas cotiza")
        if costo <= 0:
            raise DatosInvalidos("El costo debe ser mayor a cero")
        MaquinaDeEstatus.validar(self.estatus, EstatusDelServicio.COTIZADO)
        self.costo = costo
        self.estatus = EstatusDelServicio.COTIZADO

    def aceptar(self) -> None:
        if self.cancelada:
            raise CotizacionNoConfirmada(self.folio)
        MaquinaDeEstatus.validar(self.estatus, EstatusDelServicio.CONFIRMADO)
        self.estatus = EstatusDelServicio.CONFIRMADO

    def rechazar(self) -> None:
        if self.estatus is not EstatusDelServicio.COTIZADO:
            raise CotizacionNoConfirmada(self.folio)
        self.cancelada = True


class Unidad:
    def __init__(self, codigo: str, disponibilidad=DisponibilidadDeUnidad.DISPONIBLE):
        self.codigo = codigo
        self.disponibilidad = disponibilidad

    def puede_asignarse(self) -> bool:
        return self.disponibilidad is DisponibilidadDeUnidad.DISPONIBLE

    def asignar(self) -> None:
        if not self.puede_asignarse():
            raise UnidadNoDisponible(self.codigo)
        self.disponibilidad = DisponibilidadDeUnidad.ASIGNADA

    def marcar_averiada(self) -> None:
        self.disponibilidad = DisponibilidadDeUnidad.AVERIADA


class Operador:
    def __init__(self, identificador: str, disponibilidad=DisponibilidadDeOperador.DISPONIBLE, es_comodin=False):
        self.identificador = identificador
        self.disponibilidad = disponibilidad
        self.es_comodin = es_comodin  # G-07: atributo, no subclase (LSP)

    def puede_asignarse(self) -> bool:
        return self.disponibilidad is DisponibilidadDeOperador.DISPONIBLE

    def asignar(self) -> None:
        if not self.puede_asignarse():
            raise OperadorNoDisponible(self.identificador)
        self.disponibilidad = DisponibilidadDeOperador.ASIGNADO

    def marcar_indispuesto(self) -> None:
        self.disponibilidad = DisponibilidadDeOperador.INDISPUESTO


class OrdenDeServicio:
    """Raiz del aggregate. Protege las invariantes 1 a 7 de la ficha del DDD.

    Cada metodo valida primero, cambia el estado despues y registra el evento al final:
    si una validacion falla, la orden conserva su estado y no se anuncia nada.
    """

    def __init__(
        self,
        numero: str,
        folio_cotizacion: str,
        unidad_id: str,
        operador_id: str,
        mercancia: MercanciaDeclarada,
        estatus: EstatusDelServicio,
        bitacora=None,
        incidencias=None,
        evidencia: EvidenciaDeEntrega | None = None,
        detenida: bool = False,
    ):
        self.numero = numero
        self.folio_cotizacion = folio_cotizacion
        self.unidad_id = unidad_id
        self.operador_id = operador_id
        self.mercancia = mercancia
        self.estatus = estatus
        self.bitacora = list(bitacora or [])
        self.incidencias = list(incidencias or [])
        self.evidencia = evidencia
        self.detenida = detenida
        self._eventos: list[EventoDeDominio] = []

    # ---- creacion (CU-01)

    @classmethod
    def generar(cls, numero, cotizacion, unidad, operador, rol, ahora=None):
        ahora = ahora or datetime.now(UTC)
        if rol is not Rol.OPERACIONES:
            raise OperacionNoPermitidaParaRol(f"El rol {rol.value} no puede generar ordenes")
        if not CotizacionConfirmada().is_satisfied_by(cotizacion):
            raise CotizacionNoConfirmada(cotizacion.folio)
        if not UnidadDisponible().is_satisfied_by(unidad):
            raise UnidadNoDisponible(unidad.codigo)
        if not OperadorDisponible().is_satisfied_by(operador):
            raise OperadorNoDisponible(operador.identificador)
        unidad.asignar()
        operador.asignar()
        orden = cls(
            numero,
            cotizacion.folio,
            unidad.codigo,
            operador.identificador,
            cotizacion.mercancia,
            EstatusDelServicio.UNIDAD_ASIGNADA,
        )
        orden._registrar("OrdenDeServicioGenerada", rol.value, ahora)
        orden._publicar("UnidadAsignada", ahora)
        return orden

    # ---- comportamiento del negocio

    def registrar_recoleccion(self, tipo_inspeccionado, peso_inspeccionado, politica, controles_confirmados, responsable, ahora=None):
        """CU-02: valida la mercancia en origen y pasa a 'Recolectado'."""
        self._validar_transicion(EstatusDelServicio.RECOLECTADO)
        if not MercanciaCoincide(tipo_inspeccionado, peso_inspeccionado).is_satisfied_by(self.mercancia):
            raise DiscrepanciaDeMercancia(self._clasificar_discrepancia(tipo_inspeccionado))
        regla = recoleccion_permitida(tipo_inspeccionado, peso_inspeccionado, politica.umbral, controles_confirmados)
        if not regla.is_satisfied_by(self.mercancia):
            raise ControlesDeAltoValorRequeridos(", ".join(politica.CONTROLES))
        self._avanzar(EstatusDelServicio.RECOLECTADO, "MercanciaRecolectada", responsable, ahora)

    def rechazar_mercancia(self, tipo_discrepancia, fotos, observaciones, responsable, ahora=None):
        """CU-03: registra la incidencia y detiene el flujo (sin estatus propio, H-05)."""
        self._validar_transicion(EstatusDelServicio.RECOLECTADO)
        if not fotos:
            raise EvidenciaIncompleta("El rechazo requiere fotos")
        incidencia = Incidencia(TipoDeIncidencia.MERCANCIA_RECHAZADA, tipo_discrepancia, tuple(fotos), observaciones)
        self.incidencias.append(incidencia)
        self.detenida = True
        self._registrar("MercanciaRechazada", responsable, ahora)
        return incidencia

    def iniciar_traslado(self, responsable, ahora=None):
        """US-06 (dentro del aggregate, fuera de los CU seleccionados)."""
        self._validar_transicion(EstatusDelServicio.EN_TRANSITO)
        self._avanzar(EstatusDelServicio.EN_TRANSITO, "TrasladoIniciado", responsable, ahora)

    def registrar_llegada(self, responsable, ahora=None):
        """Supuesto: G-16 incluye 'Llegada a destino' aunque no hay historia (H-06)."""
        self._validar_transicion(EstatusDelServicio.LLEGADA_A_DESTINO)
        self._avanzar(EstatusDelServicio.LLEGADA_A_DESTINO, "LlegadaADestinoRegistrada", responsable, ahora)

    def registrar_entrega(self, evidencia, responsable, ahora=None):
        """CU-04: no pasa a 'Entregado' sin evidencia completa, y esta es inalterable."""
        self._validar_transicion(EstatusDelServicio.ENTREGADO)
        if not EvidenciaCompleta().is_satisfied_by(evidencia):
            raise EvidenciaIncompleta("Faltan datos de la evidencia de entrega")
        self.evidencia = evidencia
        self._avanzar(EstatusDelServicio.ENTREGADO, "EntregaRealizada", responsable, ahora)

    def reportar_averia(self, descripcion, responsable, ahora=None):
        """US-07: la unidad sufre una falla en el trayecto; se alerta a Operaciones."""
        if self.estatus not in (EstatusDelServicio.RECOLECTADO, EstatusDelServicio.EN_TRANSITO):
            raise TransicionDeEstatusInvalida("Solo se reporta averia durante el trayecto")
        incidencia = Incidencia(TipoDeIncidencia.AVERIA, None, (), descripcion)
        self.incidencias.append(incidencia)
        self._registrar("AveriaReportada", responsable, ahora)
        return incidencia

    def reasignar_operador(self, nuevo, anterior, rol, ahora=None):
        """US-08: solo Operaciones sustituye al operador indispuesto por uno libre."""
        if rol is not Rol.OPERACIONES:
            raise OperacionNoPermitidaParaRol(f"El rol {rol.value} no puede reasignar")
        if not OperadorDisponible().is_satisfied_by(nuevo):
            raise OperadorNoDisponible(nuevo.identificador)
        anterior.marcar_indispuesto()
        nuevo.asignar()
        self.operador_id = nuevo.identificador
        self._registrar("OperadorReasignado", rol.value, ahora)

    def reportar_destinatario_ausente(self, fotos, latitud, longitud, observaciones, responsable, ahora=None):
        """US-10 / G-19: nadie recibe en destino; exige foto del domicilio y ubicacion."""
        self._validar_transicion(EstatusDelServicio.ENTREGADO)  # solo desde 'Llegada a destino'
        if not fotos or latitud is None or longitud is None:
            raise EvidenciaIncompleta("El reporte de ausencia requiere foto y ubicacion")
        detalle = f"{observaciones} (ubicacion {latitud}, {longitud})".strip()
        incidencia = Incidencia(TipoDeIncidencia.DESTINATARIO_AUSENTE, None, tuple(fotos), detalle)
        self.incidencias.append(incidencia)
        self._registrar("DestinatarioAusenteReportado", responsable, ahora)
        return incidencia

    def registrar_entrega_con_anomalias(self, evidencia, descripcion, fotos_anomalia, responsable, ahora=None):
        """US-11 / G-17 / CU-05: entrega con danos o faltantes. La evidencia sigue siendo obligatoria (RN-03)."""
        self._validar_transicion(EstatusDelServicio.ENTREGADO)
        if not EvidenciaCompleta().is_satisfied_by(evidencia):
            raise EvidenciaIncompleta("Faltan datos de la evidencia de entrega")
        if not descripcion.strip():
            raise DatosInvalidos("Describe los danos o faltantes")
        incidencia = Incidencia(TipoDeIncidencia.ENTREGA_CON_DANOS_O_FALTANTES, None, tuple(fotos_anomalia), descripcion)
        self.incidencias.append(incidencia)
        self.evidencia = evidencia
        self._avanzar(EstatusDelServicio.ENTREGADO, "EntregaConAnomaliasRegistrada", responsable, ahora)
        return incidencia

    def pull_events(self) -> list[EventoDeDominio]:
        eventos, self._eventos = self._eventos, []
        return eventos

    # ---- internos

    def _validar_transicion(self, destino: EstatusDelServicio) -> None:
        if self.detenida:
            raise OrdenDetenida(self.numero)
        MaquinaDeEstatus.validar(self.estatus, destino)

    def _clasificar_discrepancia(self, tipo_inspeccionado):
        if tipo_inspeccionado.strip().casefold() != self.mercancia.tipo.strip().casefold():
            return TipoDeDiscrepancia.TIPO
        return TipoDeDiscrepancia.CANTIDAD  # sin tolerancia: no esta definida

    def _avanzar(self, destino, evento, responsable, ahora) -> None:
        self.estatus = destino
        self._registrar(evento, responsable, ahora)

    def _registrar(self, evento, responsable, ahora) -> None:
        ahora = ahora or datetime.now(UTC)
        self.bitacora.append(EntradaDeBitacora(evento, self.estatus, ahora, responsable))
        self._publicar(evento, ahora)

    def _publicar(self, nombre, ahora) -> None:
        self._eventos.append(EventoDeDominio(nombre, self.numero, ahora))
