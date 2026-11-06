"""API REST de RutaNorte Logistics. Swagger UI en /docs y OpenAPI en /openapi.json."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse

from src.api import schemas as s
from src.application.services import (
    ConsultasDeSeguimiento,
    ServicioDeCotizaciones,
    ServicioDeEntrega,
    ServicioDeOrdenes,
    ServicioDeRecoleccion,
)
from src.domain import errors as err
from src.domain.enums import Rol
from src.domain.model import Operador, Unidad
from src.domain.policies import CalculadoraDeCotizacion, PoliticaDeCargaDeAltoValor
from src.infrastructure.adapters import DISTANCIAS_KM, AlmacenDeEvidenciasLocal, NotificadorEnLog
from src.infrastructure.config import Settings
from src.infrastructure.database import make_engine, make_session_factory
from src.infrastructure.repositories import (
    CotizacionSqlRepository,
    OperadorSqlRepository,
    OrdenDeServicioSqlRepository,
    UnidadDeTrabajoSql,
    UnidadSqlRepository,
)

# Errores de dominio -> codigo HTTP (el API solo traduce, no decide reglas)
_HTTP = {
    err.OrdenNoEncontrada: 404,
    err.CotizacionNoEncontrada: 404,
    err.RecursoNoEncontrado: 404,
    err.OperacionNoPermitidaParaRol: 403,
    err.TransicionDeEstatusInvalida: 409,
    err.OrdenDetenida: 409,
    err.UnidadNoDisponible: 409,
    err.OperadorNoDisponible: 409,
    err.RecursoDuplicado: 409,
}


class Contexto:
    """Arma los servicios de una peticion con una sola sesion (una transaccion por caso de uso)."""

    def __init__(self, session, settings, notificador, almacen):
        uow = UnidadDeTrabajoSql(session)
        self.session = session
        self.ordenes = OrdenDeServicioSqlRepository(session)
        self.cotizaciones = CotizacionSqlRepository(session)
        self.unidades = UnidadSqlRepository(session)
        self.operadores = OperadorSqlRepository(session)
        self.uow = uow
        politica = PoliticaDeCargaDeAltoValor(settings.umbral_alto_valor)
        calc = CalculadoraDeCotizacion(DISTANCIAS_KM, settings.tarifa_km, settings.tarifa_kg)
        self.cotizar = ServicioDeCotizaciones(self.cotizaciones, calc, notificador, uow)
        self.generar = ServicioDeOrdenes(self.ordenes, self.cotizaciones, self.unidades, self.operadores, notificador, uow)
        self.recoleccion = ServicioDeRecoleccion(self.ordenes, politica, almacen, notificador, uow)
        self.entrega = ServicioDeEntrega(self.ordenes, almacen, uow, notificador)
        self.consultas = ConsultasDeSeguimiento(self.ordenes)


def _rol(valor: str) -> Rol:
    try:
        return Rol(valor)
    except ValueError as exc:
        raise err.DatosInvalidos(f"Rol desconocido: {valor}") from exc


def create_app(database_url: str | None = None) -> FastAPI:
    settings = Settings()
    engine = make_engine(database_url or settings.database_url)
    sesiones = make_session_factory(engine)
    notificador = NotificadorEnLog()
    almacen = AlmacenDeEvidenciasLocal(settings.evidencias_dir)

    app = FastAPI(
        title="RutaNorte Logistics API",
        version="1.0.0",
        description="Cotizacion, recoleccion, traslado y entrega de mercancia (PIA CLN).",
    )
    app.state.notificador = notificador
    app.state.engine = engine

    def ctx():
        session = sesiones()
        try:
            yield Contexto(session, settings, notificador, almacen)
        finally:
            session.close()

    @app.exception_handler(err.ErrorDeDominio)
    async def _dominio(_req: Request, exc: err.ErrorDeDominio):
        codigo = next((c for t, c in _HTTP.items() if isinstance(exc, t)), 422)
        return JSONResponse(status_code=codigo, content={"error": type(exc).__name__, "detalle": str(exc)})

    @app.get("/health", tags=["sistema"])
    def health():
        return {"status": "ok"}

    # ---------------- catalogos de apoyo (unidades y operadores)
    @app.post("/unidades", status_code=201, tags=["recursos"])
    def crear_unidad(body: s.NuevaUnidad, c: Contexto = Depends(ctx)):
        try:
            c.unidades.obtener_por_id(body.codigo)
        except err.RecursoNoEncontrado:
            c.unidades.guardar(Unidad(body.codigo))
            c.session.commit()
            return {"codigo": body.codigo, "disponibilidad": "disponible"}
        raise err.RecursoDuplicado(body.codigo)

    @app.post("/operadores", status_code=201, tags=["recursos"])
    def crear_operador(body: s.NuevoOperador, c: Contexto = Depends(ctx)):
        try:
            c.operadores.obtener_por_id(body.identificador)
        except err.RecursoNoEncontrado:
            c.operadores.guardar(Operador(body.identificador, es_comodin=body.es_comodin))
            c.session.commit()
            return {"identificador": body.identificador, "disponibilidad": "disponible"}
        raise err.RecursoDuplicado(body.identificador)

    # ---------------- cotizaciones (US-01, US-02, US-03)
    @app.post("/cotizaciones", status_code=201, tags=["cotizaciones"])
    def solicitar(body: s.SolicitudDeCotizacion, c: Contexto = Depends(ctx)):
        cot = c.cotizar.solicitar(body.origen, body.destino, body.tipo_mercancia, body.peso_kg, body.valor, body.tipo_de_unidad)
        return {"folio": cot.folio, "estatus": cot.estatus.value}

    @app.post("/cotizaciones/{folio}/cotizar", tags=["cotizaciones"])
    def cotizar(folio: str, x_rol: str = Header(alias="X-Rol"), c: Contexto = Depends(ctx)):
        cot = c.cotizar.cotizar(folio, _rol(x_rol))
        return {"folio": cot.folio, "estatus": cot.estatus.value, "costo": str(cot.costo)}

    @app.post("/cotizaciones/{folio}/aceptar", tags=["cotizaciones"])
    def aceptar(folio: str, c: Contexto = Depends(ctx)):
        cot = c.cotizar.aceptar(folio)
        return {"folio": cot.folio, "estatus": cot.estatus.value}

    @app.post("/cotizaciones/{folio}/rechazar", tags=["cotizaciones"])
    def rechazar(folio: str, c: Contexto = Depends(ctx)):
        cot = c.cotizar.rechazar(folio)
        return {"folio": cot.folio, "estatus": cot.estatus.value, "cancelada": cot.cancelada}

    # ---------------- ordenes (US-04 ... US-13)
    @app.post("/ordenes", status_code=201, tags=["ordenes"])
    def generar_orden(body: s.GenerarOrden, x_rol: str = Header(alias="X-Rol"), c: Contexto = Depends(ctx)):
        o = c.generar.generar_orden(body.numero, body.folio_cotizacion, body.unidad_id, body.operador_id, _rol(x_rol))
        return {"numero": o.numero, "estatus": o.estatus.value}

    @app.get("/ordenes/{numero}", tags=["seguimiento"])
    def consultar(numero: str, c: Contexto = Depends(ctx)):
        return c.consultas.estatus_de_orden(numero)

    @app.post("/ordenes/{numero}/recoleccion", tags=["ordenes"])
    def recolectar(numero: str, body: s.Recoleccion, x_responsable: str = Header("operador", alias="X-Responsable"), c: Contexto = Depends(ctx)):
        est = c.recoleccion.registrar_recoleccion(numero, body.tipo_inspeccionado, body.peso_inspeccionado, body.controles_confirmados, x_responsable)
        return {"numero": numero, "estatus": est.value}

    @app.post("/ordenes/{numero}/rechazo", tags=["ordenes"])
    def rechazar_mercancia(
        numero: str, body: s.RechazoDeMercancia, x_responsable: str = Header("operador", alias="X-Responsable"), c: Contexto = Depends(ctx)
    ):
        c.recoleccion.rechazar_mercancia(numero, body.tipo_discrepancia, body.fotos(), body.observaciones, x_responsable)
        return {"numero": numero, "detenida": True}

    @app.post("/ordenes/{numero}/traslado", tags=["ordenes"])
    def traslado(numero: str, x_responsable: str = Header("operador", alias="X-Responsable"), c: Contexto = Depends(ctx)):
        return {"numero": numero, "estatus": c.entrega.iniciar_traslado(numero, x_responsable).value}

    @app.post("/ordenes/{numero}/averia", tags=["ordenes"])
    def averia(numero: str, body: s.Averia, x_responsable: str = Header("operador", alias="X-Responsable"), c: Contexto = Depends(ctx)):
        c.generar.reportar_averia(numero, body.descripcion, x_responsable)
        return {"numero": numero, "averia": True}

    @app.post("/ordenes/{numero}/reasignar-operador", tags=["ordenes"])
    def reasignar(numero: str, body: s.Reasignacion, x_rol: str = Header(alias="X-Rol"), c: Contexto = Depends(ctx)):
        o = c.generar.reasignar_operador(numero, body.nuevo_operador_id, _rol(x_rol))
        return {"numero": numero, "operador_id": o.operador_id}

    @app.post("/ordenes/{numero}/llegada", tags=["ordenes"])
    def llegada(numero: str, x_responsable: str = Header("operador", alias="X-Responsable"), c: Contexto = Depends(ctx)):
        return {"numero": numero, "estatus": c.entrega.registrar_llegada(numero, x_responsable).value}

    @app.post("/ordenes/{numero}/entrega", tags=["ordenes"])
    def entrega(numero: str, body: s.Entrega, x_responsable: str = Header("operador", alias="X-Responsable"), c: Contexto = Depends(ctx)):
        est = c.entrega.registrar_entrega(
            numero,
            body.receptor_nombre,
            body.receptor_identificacion,
            body.foto(),
            body.firma(),
            body.latitud,
            body.longitud,
            x_responsable,
        )
        return {"numero": numero, "estatus": est.value}

    @app.post("/ordenes/{numero}/destinatario-ausente", tags=["ordenes"])
    def destinatario_ausente(
        numero: str,
        body: s.DestinatarioAusente,
        x_responsable: str = Header("operador", alias="X-Responsable"),
        c: Contexto = Depends(ctx),
    ):
        c.entrega.reportar_destinatario_ausente(numero, body.foto(), body.latitud, body.longitud, body.observaciones, x_responsable)
        return {"numero": numero, "excepcion": "destinatario ausente"}

    @app.post("/ordenes/{numero}/entrega-con-anomalias", tags=["ordenes"])
    def entrega_con_anomalias(
        numero: str,
        body: s.EntregaConAnomalias,
        x_responsable: str = Header("operador", alias="X-Responsable"),
        c: Contexto = Depends(ctx),
    ):
        est = c.entrega.registrar_entrega_con_anomalias(
            numero,
            body.receptor_nombre,
            body.receptor_identificacion,
            body.foto(),
            body.firma(),
            body.latitud,
            body.longitud,
            body.descripcion,
            body.fotos_anomalia(),
            x_responsable,
        )
        return {"numero": numero, "estatus": est.value}

    return app


def get_app() -> FastAPI:
    return create_app()
