import pandas as pd
import pytest


def _mensual():
    fechas = pd.date_range("2023-01-01", periods=14, freq="MS")
    filas = []
    for i, f in enumerate(fechas):
        filas += [
            (f, "España", "Total", 12.0 - i * 0.1),
            (f, "UE-27", "Total", 6.0),
            (f, "España", "Menores de 25", 28.0 - i * 0.2),
            (f, "UE-27", "Menores de 25", 14.0),
        ]
    return pd.DataFrame(filas, columns=["fecha", "zona", "grupo", "tasa"])


def _regiones():
    filas = []
    for anio in (2023, 2024):
        for codigo, region, tasa in [("ES", "España", 11.0), ("ES30", "Madrid", 8.0), ("ES61", "Andalucía", 16.0),
                                     ("ES21", "País Vasco", 7.0)]:  # fmt: skip
            filas.append((codigo, region, anio, "Total", tasa - (anio - 2023)))
            filas.append((codigo, region, anio, "15 a 24 años", tasa * 2))
    return pd.DataFrame(filas, columns=["codigo", "region", "anio", "grupo", "tasa"])


def _vivienda():
    fechas = pd.date_range("2014-01-01", periods=8, freq="QS")
    es = [96, 95, 97, 100, 104, 108, 112, 120]
    filas = []
    for i, f in enumerate(fechas):
        filas.append((f, "España", es[i], 5.0 + i))
        filas.append((f, "UE-27", 100 + i, 3.0))
    return pd.DataFrame(filas, columns=["fecha", "zona", "indice_2015", "variacion_anual"])


@pytest.fixture
def mensual():
    return _mensual()


@pytest.fixture
def regiones():
    return _regiones()


@pytest.fixture
def vivienda():
    return _vivienda()
