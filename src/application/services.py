"""Servicios de aplicacion (CU-01 a CU-05). Solo coordinan; las reglas viven en el dominio.

Cada caso de uso abre una transaccion, invoca al dominio, guarda y confirma. Los avisos
salen solo despues del commit: no se anuncia algo que no se guardo.
"""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal

from src.application.ports import (
    CotizacionRepository,
    IAlmacenDeEvidencias,
    INotificador,
    IUnidadDeTrabajo,
    OperadorRepository,
    OrdenDeServicioRepository,
    UnidadRepository,
)
from src.domain.enums import EstatusDelServicio, Rol, TipoDeDiscrepancia
from src.domain.model import Cotizacion, OrdenDeServicio
from src.domain.policies import CalculadoraDeCotizacion, PoliticaDeCargaDeAltoValor
from src.domain.value_objects import EvidenciaDeEntrega, Incidencia, MercanciaDeclarada


@contextmanager
def transaccion(uow: IUnidadDeTrabajo):
    uow.iniciar()
    try:
        yield
        uow.confirmar()
    except Exception:
        uow.revertir()
        raise


class ServicioDeCotizaciones:
    """US-01, US-02, US-03."""

    def __init__(
        self,
        cotizaciones: CotizacionRepository,
        calculadora: CalculadoraDeCotizacion,
        notificador: INotificador,
        uow: IUnidadDeTrabajo,
    ):
        self.cotizaciones, self.calculadora = cotizaciones, calculadora
        self.notificador, self.uow = notificador, uow

    def solicitar(self, origen, destino, tipo_mercancia, peso_kg, valor, tipo_de_unidad, folio=None) -> Cotizacion:
        folio = folio or f"COT-{uuid.uuid4().hex[:8].upper()}"
        mercancia = MercanciaDeclarada(tipo_mercancia, Decimal(peso_kg), Decimal(valor))
        cot = Cotizacion(folio, EstatusDelServicio.SOLICITADO, mercancia, origen, destino, tipo_de_unidad)
        with transaccion(self.uow):
            self.cotizaciones.guardar(cot)
        self.notificador.alertar("Ventas", folio, "Nueva solicitud de cotizacion")
        return cot

    def cotizar(self, folio: str, rol: Rol) -> Cotizacion:
        with transaccion(self.uow):
            cot = self.cotizaciones.obtener_por_folio(folio)
            costo = self.calculadora.calcular(cot.origen, cot.destino, cot.mercancia.peso_kg, cot.tipo_de_unidad)
            cot.cotizar(costo, rol)
            self.cotizaciones.guardar(cot)
        return cot

    def aceptar(self, folio: str) -> Cotizacion:
        with transaccion(self.uow):
            cot = self.cotizaciones.obtener_por_folio(folio)
            cot.aceptar()
            self.cotizaciones.guardar(cot)
        self.notificador.alertar("Operaciones", folio, "Cotizacion confirmada por el cliente")
        return cot

    def rechazar(self, folio: str) -> Cotizacion:
        with transaccion(self.uow):
            cot = self.cotizaciones.obtener_por_folio(folio)
            cot.rechazar()
            self.cotizaciones.guardar(cot)
        return cot


class ServicioDeOrdenes:
    """CU-01 generar orden (US-04), US-07 averia y US-08 reasignar operador."""

    def __init__(
        self,
        ordenes: OrdenDeServicioRepository,
        cotizaciones: CotizacionRepository,
        unidades: UnidadRepository,
        operadores: OperadorRepository,
        notificador: INotificador,
        uow: IUnidadDeTrabajo,
    ):
        self.ordenes, self.cotizaciones = ordenes, cotizaciones
        self.unidades, self.operadores = unidades, operadores
        self.notificador, self.uow = notificador, uow

    def generar_orden(self, numero, folio, unidad_id, operador_id, rol: Rol, ahora=None) -> OrdenDeServicio:
        with transaccion(self.uow):
            cot = self.cotizaciones.obtener_por_folio(folio)
            unidad = self.unidades.obtener_por_id(unidad_id)
            operador = self.operadores.obtener_por_id(operador_id)
            orden = OrdenDeServicio.generar(numero, cot, unidad, operador, rol, ahora)
            self.ordenes.guardar(orden)
            self.unidades.guardar(unidad)
            self.operadores.guardar(operador)
        return orden

    def reportar_averia(self, numero, descripcion, responsable, ahora=None) -> Incidencia:
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            incidencia = orden.reportar_averia(descripcion, responsable, ahora)
            unidad = self.unidades.obtener_por_id(orden.unidad_id)
            unidad.marcar_averiada()
            self.ordenes.guardar(orden)
            self.unidades.guardar(unidad)
        self.notificador.alertar("Operaciones", numero, f"Averia reportada: {descripcion}")
        return incidencia

    def reasignar_operador(self, numero, nuevo_id, rol: Rol, ahora=None) -> OrdenDeServicio:
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            anterior = self.operadores.obtener_por_id(orden.operador_id)
            nuevo = self.operadores.obtener_por_id(nuevo_id)
            orden.reasignar_operador(nuevo, anterior, rol, ahora)
            self.ordenes.guardar(orden)
            self.operadores.guardar(anterior)
            self.operadores.guardar(nuevo)
        self.notificador.alertar(nuevo_id, numero, "Se te asigno la orden " + numero)
        return orden


class ServicioDeRecoleccion:
    """CU-02 registrarRecoleccion y CU-03 rechazarMercancia."""

    def __init__(
        self,
        ordenes: OrdenDeServicioRepository,
        politica: PoliticaDeCargaDeAltoValor,
        almacen: IAlmacenDeEvidencias,
        notificador: INotificador,
        uow: IUnidadDeTrabajo,
    ):
        self.ordenes, self.politica = ordenes, politica
        self.almacen, self.notificador, self.uow = almacen, notificador, uow

    def registrar_recoleccion(
        self, numero, tipo_inspeccionado, peso_inspeccionado, controles_confirmados, responsable, ahora=None
    ) -> EstatusDelServicio:
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            orden.registrar_recoleccion(tipo_inspeccionado, peso_inspeccionado, self.politica, controles_confirmados, responsable, ahora)
            self.ordenes.guardar(orden)
        return orden.estatus

    def rechazar_mercancia(
        self, numero, tipo_discrepancia: TipoDeDiscrepancia, fotos: list[bytes], observaciones, responsable, ahora=None
    ) -> Incidencia:
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            referencias = [self.almacen.guardar(f) for f in fotos]
            incidencia = orden.rechazar_mercancia(tipo_discrepancia, referencias, observaciones, responsable, ahora)
            self.ordenes.guardar(orden)
        self.notificador.alertar("Operaciones", numero, f"Mercancía rechazada en origen: {tipo_discrepancia.value}")
        return incidencia


class ServicioDeEntrega:
    """US-06 iniciar traslado, llegada a destino (H-06) y CU-04 registrarEntrega."""

    def __init__(
        self,
        ordenes: OrdenDeServicioRepository,
        almacen: IAlmacenDeEvidencias,
        uow: IUnidadDeTrabajo,
        notificador: INotificador | None = None,
    ):
        self.ordenes, self.almacen, self.uow = ordenes, almacen, uow
        self.notificador = notificador

    def iniciar_traslado(self, numero, responsable, ahora=None) -> EstatusDelServicio:
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            orden.iniciar_traslado(responsable, ahora)
            self.ordenes.guardar(orden)
        return orden.estatus

    def registrar_llegada(self, numero, responsable, ahora=None) -> EstatusDelServicio:
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            orden.registrar_llegada(responsable, ahora)
            self.ordenes.guardar(orden)
        return orden.estatus

    def registrar_entrega(
        self, numero, receptor_nombre, receptor_identificacion, foto, firma, latitud, longitud, responsable, ahora=None
    ) -> EstatusDelServicio:
        ahora = ahora or datetime.now(UTC)
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            foto_ref = self.almacen.guardar(foto) if foto else None
            firma_ref = self.almacen.guardar(firma) if firma else None
            evidencia = EvidenciaDeEntrega(receptor_nombre, receptor_identificacion, foto_ref, firma_ref, latitud, longitud, ahora)
            orden.registrar_entrega(evidencia, responsable, ahora)
            self.ordenes.guardar(orden)
        return orden.estatus

    def reportar_destinatario_ausente(self, numero, foto: bytes | None, latitud, longitud, observaciones, responsable, ahora=None) -> Incidencia:
        """US-10."""
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            referencias = [self.almacen.guardar(foto)] if foto else []
            incidencia = orden.reportar_destinatario_ausente(referencias, latitud, longitud, observaciones, responsable, ahora)
            self.ordenes.guardar(orden)
        self._avisar(numero, "Destinatario ausente: se requieren instrucciones")
        return incidencia

    def registrar_entrega_con_anomalias(
        self,
        numero,
        receptor_nombre,
        receptor_identificacion,
        foto,
        firma,
        latitud,
        longitud,
        descripcion,
        fotos_anomalia: list[bytes],
        responsable,
        ahora=None,
    ) -> EstatusDelServicio:
        """US-11 / CU-05."""
        ahora = ahora or datetime.now(UTC)
        with transaccion(self.uow):
            orden = self.ordenes.obtener_por_numero(numero)
            foto_ref = self.almacen.guardar(foto) if foto else None
            firma_ref = self.almacen.guardar(firma) if firma else None
            refs = [self.almacen.guardar(f) for f in fotos_anomalia]
            evidencia = EvidenciaDeEntrega(receptor_nombre, receptor_identificacion, foto_ref, firma_ref, latitud, longitud, ahora)
            orden.registrar_entrega_con_anomalias(evidencia, descripcion, refs, responsable, ahora)
            self.ordenes.guardar(orden)
        self._avisar(numero, f"Entrega con anomalias: {descripcion}")
        return orden.estatus

    def _avisar(self, numero: str, mensaje: str) -> None:
        if self.notificador is not None:  # el aviso sale solo despues del commit
            self.notificador.alertar("Operaciones", numero, mensaje)


class ConsultasDeSeguimiento:
    """US-14 y US-16 / RN-04: estatus e historial de una orden (solo lectura)."""

    def __init__(self, ordenes: OrdenDeServicioRepository):
        self.ordenes = ordenes

    def estatus_de_orden(self, numero: str) -> dict:
        o = self.ordenes.obtener_por_numero(numero)
        return {
            "numero": o.numero,
            "folio_cotizacion": o.folio_cotizacion,
            "estatus": o.estatus.value,
            "detenida": o.detenida,
            "unidad_id": o.unidad_id,
            "operador_id": o.operador_id,
            "incidencias": [{"tipo": i.tipo.value, "fotos": len(i.fotos), "observaciones": i.observaciones} for i in o.incidencias],
            "historial": [
                {"evento": b.evento, "estatus": b.estatus.value, "fecha": b.fecha.isoformat(), "responsable": b.responsable} for b in o.bitacora
            ],
        }
