"""Pruebas de dominio (sin base de datos). Los nombres cpNN trazan la matriz de pruebas de U5."""

from decimal import Decimal

import pytest

from src.domain.enums import DisponibilidadDeOperador, DisponibilidadDeUnidad, Rol, TipoDeDiscrepancia
from src.domain.enums import EstatusDelServicio as E
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
from src.domain.model import Cotizacion, Operador, OrdenDeServicio, Unidad
from src.domain.value_objects import MercanciaDeclarada
from tests.conftest import AHORA, evidencia, hacer_orden


def cot(estatus):
    return Cotizacion("COT-1", estatus, MercanciaDeclarada("autopartes", Decimal("1500"), Decimal("5000")))


def test_cp01_entrega_con_evidencia_completa_pasa_a_entregado():
    o = hacer_orden(E.LLEGADA_A_DESTINO)
    o.registrar_entrega(evidencia(), "op", AHORA)
    assert o.estatus is E.ENTREGADO
    assert o.bitacora[-1].evento == "EntregaRealizada"
    assert [e.nombre for e in o.pull_events()] == ["EntregaRealizada"]


@pytest.mark.parametrize("campo", ["firma_ref", "foto_ref", "receptor_nombre", "latitud", "estampa"])
def test_cp02_entrega_incompleta_se_rechaza_y_no_cambia_nada(campo):
    o = hacer_orden(E.LLEGADA_A_DESTINO)
    with pytest.raises(EvidenciaIncompleta):
        o.registrar_entrega(evidencia(**{campo: None}), "op", AHORA)
    assert o.estatus is E.LLEGADA_A_DESTINO and o.bitacora == [] and o.pull_events() == []


def test_cp03_no_se_puede_saltar_llegada_a_destino():
    o = hacer_orden(E.EN_TRANSITO)
    with pytest.raises(TransicionDeEstatusInvalida):
        o.registrar_entrega(evidencia(), "op", AHORA)
    assert o.estatus is E.EN_TRANSITO


def test_evidencia_es_inalterable():
    with pytest.raises(AttributeError):
        evidencia().foto_ref = "otra"


def test_cp04_operaciones_genera_orden_de_cotizacion_confirmada():
    u, op = Unidad("Eco-12"), Operador("OP-01")
    o = OrdenDeServicio.generar("OS-500", cot(E.CONFIRMADO), u, op, Rol.OPERACIONES, AHORA)
    assert o.estatus is E.UNIDAD_ASIGNADA
    assert u.disponibilidad is DisponibilidadDeUnidad.ASIGNADA and op.disponibilidad is DisponibilidadDeOperador.ASIGNADO
    assert [e.nombre for e in o.pull_events()] == ["OrdenDeServicioGenerada", "UnidadAsignada"]


def test_cp05_ventas_no_puede_generar_la_orden():
    u = Unidad("Eco-12")
    with pytest.raises(OperacionNoPermitidaParaRol):
        OrdenDeServicio.generar("OS-1", cot(E.CONFIRMADO), u, Operador("OP-01"), Rol.VENTAS)
    assert u.puede_asignarse()


def test_cp06_cotizacion_cotizada_no_genera_orden():
    u = Unidad("Eco-12")
    with pytest.raises(CotizacionNoConfirmada):
        OrdenDeServicio.generar("OS-1", cot(E.COTIZADO), u, Operador("OP-01"), Rol.OPERACIONES)
    assert u.puede_asignarse()


def test_cp07_alto_valor_con_controles_confirmados_se_recolecta(politica):
    o = hacer_orden(valor="100000.01")
    o.registrar_recoleccion("autopartes", Decimal("1500"), politica, True, "op", AHORA)
    assert o.estatus is E.RECOLECTADO and o.pull_events()[0].nombre == "MercanciaRecolectada"


def test_cp08_alto_valor_sin_controles_no_se_recolecta(politica):
    o = hacer_orden(valor="250000")
    with pytest.raises(ControlesDeAltoValorRequeridos):
        o.registrar_recoleccion("autopartes", Decimal("1500"), politica, False, "op", AHORA)
    assert o.estatus is E.UNIDAD_ASIGNADA


def test_cp09_valor_igual_al_umbral_no_es_alto_valor(politica):
    o = hacer_orden(valor="100000")
    o.registrar_recoleccion("autopartes", Decimal("1500"), politica, False, "op", AHORA)
    assert o.estatus is E.RECOLECTADO


def test_cp10_mercancia_que_coincide_se_recolecta(politica):
    o = hacer_orden()
    o.registrar_recoleccion("Autopartes", Decimal("1500"), politica, False, "op", AHORA)
    assert o.estatus is E.RECOLECTADO


def test_cp11_peso_distinto_es_discrepancia_y_no_se_recolecta(politica):
    o = hacer_orden()
    with pytest.raises(DiscrepanciaDeMercancia) as exc:
        o.registrar_recoleccion("autopartes", Decimal("1400"), politica, False, "op", AHORA)
    assert exc.value.tipo is TipoDeDiscrepancia.CANTIDAD
    assert o.estatus is E.UNIDAD_ASIGNADA and o.pull_events() == []


def test_cp12_diferencia_minima_de_peso_ya_es_discrepancia(politica):
    with pytest.raises(DiscrepanciaDeMercancia):
        hacer_orden().registrar_recoleccion("autopartes", Decimal("1500.01"), politica, False, "op", AHORA)


def test_tipo_distinto_es_discrepancia_de_tipo(politica):
    with pytest.raises(DiscrepanciaDeMercancia) as exc:
        hacer_orden().registrar_recoleccion("textiles", Decimal("1500"), politica, False, "op", AHORA)
    assert exc.value.tipo is TipoDeDiscrepancia.TIPO


def test_cp13_unidad_averiada_no_se_asigna_y_no_se_modifica_nada():
    u, op = Unidad("Eco-12", DisponibilidadDeUnidad.AVERIADA), Operador("OP-01")
    with pytest.raises(UnidadNoDisponible):
        OrdenDeServicio.generar("OS-1", cot(E.CONFIRMADO), u, op, Rol.OPERACIONES)
    assert u.disponibilidad is DisponibilidadDeUnidad.AVERIADA and op.puede_asignarse()


def test_operador_indispuesto_no_se_asigna():
    with pytest.raises(OperadorNoDisponible):
        OrdenDeServicio.generar("OS-1", cot(E.CONFIRMADO), Unidad("U"), Operador("OP", DisponibilidadDeOperador.INDISPUESTO), Rol.OPERACIONES)


def test_rechazar_mercancia_detiene_la_orden_y_exige_fotos():
    o = hacer_orden()
    with pytest.raises(EvidenciaIncompleta):
        o.rechazar_mercancia(TipoDeDiscrepancia.CANTIDAD, [], "x", "op", AHORA)
    o.rechazar_mercancia(TipoDeDiscrepancia.CANTIDAD, ["a.bin"], "faltan cajas", "op", AHORA)
    assert o.detenida and o.estatus is E.UNIDAD_ASIGNADA
    with pytest.raises(OrdenDetenida):
        o.iniciar_traslado("op", AHORA)


def test_flujo_completo_hasta_entregado(politica):
    o = hacer_orden()
    o.registrar_recoleccion("autopartes", Decimal("1500"), politica, False, "op", AHORA)
    o.iniciar_traslado("op", AHORA)
    o.registrar_llegada("op", AHORA)
    o.registrar_entrega(evidencia(), "op", AHORA)
    assert o.estatus is E.ENTREGADO and len(o.bitacora) == 4


def test_averia_solo_durante_el_trayecto():
    o = hacer_orden(E.EN_TRANSITO)
    o.reportar_averia("falla de motor", "op", AHORA)
    assert o.incidencias[0].tipo.value == "avería"
    with pytest.raises(TransicionDeEstatusInvalida):
        hacer_orden().reportar_averia("x", "op", AHORA)


def test_reasignar_operador_solo_operaciones_y_con_recurso_libre():
    o = hacer_orden(E.EN_TRANSITO)
    viejo, nuevo = Operador("OP-01"), Operador("OP-02", es_comodin=True)
    with pytest.raises(OperacionNoPermitidaParaRol):
        o.reasignar_operador(nuevo, viejo, Rol.VENTAS)
    with pytest.raises(OperadorNoDisponible):
        o.reasignar_operador(Operador("OP-03", DisponibilidadDeOperador.INDISPUESTO), viejo, Rol.OPERACIONES)
    o.reasignar_operador(nuevo, viejo, Rol.OPERACIONES, AHORA)
    assert o.operador_id == "OP-02" and viejo.disponibilidad is DisponibilidadDeOperador.INDISPUESTO


def test_cotizacion_flujo_y_reglas():
    c = Cotizacion("C", E.SOLICITADO, MercanciaDeclarada("x", Decimal(1), Decimal(1)))
    with pytest.raises(OperacionNoPermitidaParaRol):
        c.cotizar(Decimal(100), Rol.CLIENTE)
    with pytest.raises(DatosInvalidos):
        c.cotizar(Decimal(0), Rol.VENTAS)
    with pytest.raises(TransicionDeEstatusInvalida):
        c.aceptar()
    c.cotizar(Decimal(100), Rol.VENTAS)
    c.aceptar()
    assert c.esta_confirmada()


def test_cotizacion_rechazada_no_se_acepta():
    c = Cotizacion("C", E.SOLICITADO, MercanciaDeclarada("x", Decimal(1), Decimal(1)))
    with pytest.raises(CotizacionNoConfirmada):
        c.rechazar()
    c.cotizar(Decimal(10), Rol.VENTAS)
    c.rechazar()
    with pytest.raises(CotizacionNoConfirmada):
        c.aceptar()


def test_value_objects_validan_datos():
    with pytest.raises(DatosInvalidos):
        MercanciaDeclarada(" ", Decimal(1), Decimal(1))
    with pytest.raises(DatosInvalidos):
        MercanciaDeclarada("x", Decimal(-1), Decimal(1))


def test_us10_destinatario_ausente_registra_incidencia_y_no_cambia_el_estatus():
    o = hacer_orden(E.LLEGADA_A_DESTINO)
    inc = o.reportar_destinatario_ausente(["casa.bin"], 25.68, -100.31, "nadie abre", "op", AHORA)
    assert inc.tipo.value == "destinatario ausente" and inc.fotos == ("casa.bin",)
    assert o.estatus is E.LLEGADA_A_DESTINO
    assert [e.nombre for e in o.pull_events()] == ["DestinatarioAusenteReportado"]


@pytest.mark.parametrize("fotos,lat,lon", [([], 1.0, 1.0), (["f"], None, 1.0), (["f"], 1.0, None)])
def test_us10_exige_foto_y_ubicacion(fotos, lat, lon):
    o = hacer_orden(E.LLEGADA_A_DESTINO)
    with pytest.raises(EvidenciaIncompleta):
        o.reportar_destinatario_ausente(fotos, lat, lon, "x", "op", AHORA)
    assert o.incidencias == [] and o.bitacora == []


def test_us10_solo_desde_llegada_a_destino():
    with pytest.raises(TransicionDeEstatusInvalida):
        hacer_orden(E.EN_TRANSITO).reportar_destinatario_ausente(["f"], 1.0, 1.0, "x", "op", AHORA)


def test_us11_entrega_con_anomalias_genera_reporte_vinculado_a_la_orden():
    o = hacer_orden(E.LLEGADA_A_DESTINO)
    o.registrar_entrega_con_anomalias(evidencia(), "dos piezas rotas", ["d1.bin"], "op", AHORA)
    assert o.estatus is E.ENTREGADO and o.evidencia.esta_completa()
    assert o.incidencias[0].tipo.value == "entrega con danos o faltantes"
    assert [e.nombre for e in o.pull_events()] == ["EntregaConAnomaliasRegistrada"]


def test_us11_la_evidencia_sigue_siendo_obligatoria_y_exige_descripcion():
    o = hacer_orden(E.LLEGADA_A_DESTINO)
    with pytest.raises(EvidenciaIncompleta):
        o.registrar_entrega_con_anomalias(evidencia(firma_ref=None), "rotas", [], "op", AHORA)
    with pytest.raises(DatosInvalidos):
        o.registrar_entrega_con_anomalias(evidencia(), "  ", [], "op", AHORA)
    assert o.estatus is E.LLEGADA_A_DESTINO and o.incidencias == [] and o.pull_events() == []
