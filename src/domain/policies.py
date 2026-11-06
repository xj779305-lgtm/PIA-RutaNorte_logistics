"""Domain Service: PoliticaDeCargaDeAltoValor (US-12, G-12)."""

from decimal import Decimal


class PoliticaDeCargaDeAltoValor:
    """G-12 / US-12: evalua si una carga supera el umbral y devuelve los controles.

    El umbral NO esta definido en la Unidad 2 (pendiente H-01), por eso se recibe como
    configuracion y nunca se fija dentro de la regla.
    """

    CONTROLES = ("unidad escolta", "doble firma")

    def __init__(self, umbral: Decimal):
        self.umbral = umbral

    def es_alto_valor(self, valor: Decimal) -> bool:
        return valor > self.umbral  # "supera el umbral": igual al umbral NO es alto valor

    def controles_obligatorios(self, valor: Decimal) -> tuple[str, ...]:
        return self.CONTROLES if self.es_alto_valor(valor) else ()


class CalculadoraDeCotizacion:
    """RN-01 / US-02: costo por distancia, peso y tipo de unidad.

    Las tarifas y la matriz de distancias son configuracion de ejemplo (la matriz real de
    RutaNorte queda fuera del alcance de las Unidades 2 y 3).
    """

    FACTOR_UNIDAD = {"caja seca": Decimal("1.0"), "refrigerada": Decimal("1.35"), "plataforma": Decimal("1.15")}

    def __init__(self, distancias_km: dict[frozenset, Decimal], tarifa_km: Decimal, tarifa_kg: Decimal):
        self.distancias = distancias_km
        self.tarifa_km = tarifa_km
        self.tarifa_kg = tarifa_kg

    def calcular(self, origen: str, destino: str, peso_kg: Decimal, tipo_de_unidad: str) -> Decimal:
        from src.domain.errors import DatosInvalidos

        km = self.distancias.get(frozenset({origen.strip().title(), destino.strip().title()}))
        if km is None:
            raise DatosInvalidos(f"Ruta sin distancia definida: {origen} - {destino}")
        factor = self.FACTOR_UNIDAD.get(tipo_de_unidad.strip().lower())
        if factor is None:
            raise DatosInvalidos(f"Tipo de unidad desconocido: {tipo_de_unidad}")
        return ((km * self.tarifa_km + peso_kg * self.tarifa_kg) * factor).quantize(Decimal("0.01"))
