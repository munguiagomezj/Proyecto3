"""Datasets de Eurostat que usa el proyecto y los filtros con los que se piden."""

from dataclasses import dataclass, field

# Comunidades y ciudades autónomas (regiones NUTS 2 de España).
REGIONES_ES = [
    "ES11", "ES12", "ES13", "ES21", "ES22", "ES23", "ES24", "ES30", "ES41", "ES42",
    "ES43", "ES51", "ES52", "ES53", "ES61", "ES62", "ES63", "ES64", "ES70",
]  # fmt: skip


@dataclass(frozen=True)
class Fuente:
    nombre: str
    codigo: str
    descripcion: str
    params: dict = field(default_factory=dict)


FUENTES = [
    Fuente(
        nombre="paro_mensual",
        codigo="une_rt_m",
        descripcion="Tasa de paro mensual desestacionalizada (total y menores de 25 años)",
        params={"geo": ["ES", "EU27_2020"], "s_adj": "SA", "unit": "PC_ACT", "sex": "T", "sinceTimePeriod": "2008-01"},
    ),
    Fuente(
        nombre="paro_regiones",
        codigo="lfst_r_lfu3rt",
        descripcion="Tasa de paro anual por región NUTS 2",
        params={"geo": ["ES", *REGIONES_ES], "sex": "T", "isced11": "TOTAL", "sinceTimePeriod": "2008"},
    ),
    Fuente(
        nombre="precio_vivienda",
        codigo="prc_hpi_q",
        descripcion="Índice de precios de la vivienda, trimestral",
        params={"geo": ["ES", "EU27_2020"], "purchase": "TOTAL", "sinceTimePeriod": "2010-Q1"},
    ),
]
