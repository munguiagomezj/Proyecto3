"""Transforma los datos brutos de Eurostat en tablas limpias y fáciles de analizar."""

import pandas as pd

from analisis.eurostat import labels, parse_jsonstat

ZONAS = {"ES": "España", "EU27_2020": "UE-27"}
GRUPOS_MENSUAL = {"TOTAL": "Total", "Y_LT25": "Menores de 25"}
GRUPOS_REGION = {"Y15-74": "Total", "Y15-24": "15 a 24 años"}

# Nombres cortos en castellano para los gráficos.
NOMBRES_REGION = {
    "Principado de Asturias": "Asturias",
    "Comunidad Foral de Navarra": "Navarra",
    "Comunidad de Madrid": "Madrid",
    "Cataluña": "Cataluña",
    "Comunitat Valenciana": "C. Valenciana",
    "Illes Balears": "Baleares",
    "Región de Murcia": "Murcia",
    "Ciudad de Ceuta": "Ceuta",
    "Ciudad de Melilla": "Melilla",
}


def periodo_a_fecha(periodo: pd.Series) -> pd.Series:
    """Convierte '2024-03', '2024-Q2' o '2024' en la fecha del primer día del periodo."""
    texto = periodo.astype(str)
    trimestral = texto.str.contains("Q")
    fechas = pd.Series(pd.NaT, index=texto.index, dtype="datetime64[ns]")
    if trimestral.any():
        fechas[trimestral] = pd.PeriodIndex(texto[trimestral], freq="Q").to_timestamp()
    if (~trimestral).any():
        fechas[~trimestral] = pd.to_datetime(texto[~trimestral], format="mixed")
    return fechas


def paro_mensual(raw: dict) -> pd.DataFrame:
    df = parse_jsonstat(raw)
    df = df[df["age"].isin(GRUPOS_MENSUAL)]
    return (
        pd.DataFrame(
            {
                "fecha": periodo_a_fecha(df["time"]),
                "zona": df["geo"].map(ZONAS),
                "grupo": df["age"].map(GRUPOS_MENSUAL),
                "tasa": df["value"],
            }
        )
        .sort_values(["grupo", "zona", "fecha"])
        .reset_index(drop=True)
    )


def paro_regiones(raw: dict) -> pd.DataFrame:
    df = parse_jsonstat(raw)
    df = df[df["age"].isin(GRUPOS_REGION)]
    nombres = labels(raw, "geo")
    region = df["geo"].map(nombres).replace(NOMBRES_REGION).replace({"Spain": "España"})
    return (
        pd.DataFrame(
            {
                "codigo": df["geo"],
                "region": region,
                "anio": df["time"].astype(int),
                "grupo": df["age"].map(GRUPOS_REGION),
                "tasa": df["value"],
            }
        )
        .sort_values(["grupo", "codigo", "anio"])
        .reset_index(drop=True)
    )


def precio_vivienda(raw: dict) -> pd.DataFrame:
    df = parse_jsonstat(raw)
    df = df[df["unit"].isin(["I15_Q", "RCH_A"])]
    tabla = df.pivot_table(index=["geo", "time"], columns="unit", values="value").reset_index()
    return (
        pd.DataFrame(
            {
                "fecha": periodo_a_fecha(tabla["time"]),
                "zona": tabla["geo"].map(ZONAS),
                "indice_2015": tabla["I15_Q"],
                "variacion_anual": tabla["RCH_A"],
            }
        )
        .sort_values(["zona", "fecha"])
        .reset_index(drop=True)
    )
