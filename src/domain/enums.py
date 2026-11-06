"""Enumeraciones del lenguaje ubicuo (G-13, G-16, G-07)."""

from enum import StrEnum


class EstatusDelServicio(StrEnum):
    """G-16: etapas ordenadas del envio."""

    SOLICITADO = "Solicitado"
    COTIZADO = "Cotizado"
    CONFIRMADO = "Confirmado"
    UNIDAD_ASIGNADA = "Unidad asignada"
    RECOLECTADO = "Recolectado"
    EN_TRANSITO = "En tránsito"
    LLEGADA_A_DESTINO = "Llegada a destino"
    ENTREGADO = "Entregado"


class Rol(StrEnum):
    CLIENTE = "Cliente"
    VENTAS = "Ventas"
    OPERACIONES = "Operaciones"
    OPERADOR = "Operador"
    ATENCION_AL_CLIENTE = "Atención al Cliente"
    GERENTE_DE_OPERACIONES = "Gerente de Operaciones"


class TipoDeDiscrepancia(StrEnum):
    """G-13: cantidad, tipo o estado."""

    CANTIDAD = "cantidad"
    TIPO = "tipo"
    ESTADO = "estado"


class TipoDeIncidencia(StrEnum):
    AVERIA = "avería"
    MERCANCIA_RECHAZADA = "mercancía rechazada"
    DESTINATARIO_AUSENTE = "destinatario ausente"
    ENTREGA_CON_DANOS_O_FALTANTES = "entrega con danos o faltantes"


class DisponibilidadDeUnidad(StrEnum):
    DISPONIBLE = "disponible"
    ASIGNADA = "asignada"
    AVERIADA = "averiada"


class DisponibilidadDeOperador(StrEnum):
    DISPONIBLE = "disponible"
    ASIGNADO = "asignado"
    INDISPUESTO = "indispuesto"
