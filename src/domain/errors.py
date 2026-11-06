"""Errores de negocio, explicados en terminos del dominio."""

from src.domain.enums import TipoDeDiscrepancia


class ErrorDeDominio(Exception):
    """Base de los errores de negocio, explicados en terminos del dominio."""


class DatosInvalidos(ErrorDeDominio):
    """Un valor viola una regla de un Value Object (por ejemplo, peso negativo)."""


class CotizacionNoConfirmada(ErrorDeDominio):
    """Solo una cotizacion 'Confirmado' genera una orden (US-03, US-04)."""


class OperacionNoPermitidaParaRol(ErrorDeDominio):
    """Solo Operaciones genera o modifica ordenes confirmadas (RN-02)."""


class UnidadNoDisponible(ErrorDeDominio):
    """Una unidad averiada o ya asignada no se asigna (US-07, G-14, OP-07)."""


class OperadorNoDisponible(ErrorDeDominio):
    """Un operador indispuesto o ya asignado no se asigna (US-08)."""


class TransicionDeEstatusInvalida(ErrorDeDominio):
    """El estatus solo avanza por las transiciones validas de G-16."""


class EvidenciaIncompleta(ErrorDeDominio):
    """No hay entrega sin evidencia completa (RN-03, CE-03, US-13)."""


class DiscrepanciaDeMercancia(ErrorDeDominio):
    """La mercancia recibida no coincide con la declarada (G-13, US-05, US-09)."""

    def __init__(self, tipo: TipoDeDiscrepancia):
        super().__init__(f"Discrepancia de mercancia: {tipo.value}")
        self.tipo = tipo


class ControlesDeAltoValorRequeridos(ErrorDeDominio):
    """Una carga de alto valor exige unidad escolta y doble firma (US-12, G-12)."""


class OrdenDetenida(ErrorDeDominio):
    """Una orden con mercancia rechazada no avanza hasta que Operaciones resuelva (US-09)."""


class OrdenNoEncontrada(ErrorDeDominio):
    """No existe una orden con ese numero."""


class CotizacionNoEncontrada(ErrorDeDominio):
    """No existe una cotizacion con ese folio."""


class RecursoNoEncontrado(ErrorDeDominio):
    """No existe la unidad o el operador indicado."""


class RecursoDuplicado(ErrorDeDominio):
    """Ya existe un registro con ese identificador."""
