import pandas as pd
import pytest

from analisis.indicadores import mes_anio, num, ranking_regiones, resumen, serie, trimestre, variacion


def test_formato_numeros_y_fechas():
    assert num(1234.567) == "1.234,6"
    assert num(10, 0) == "10"
    assert num(-0.25, 2) == "-0,25"
    assert mes_anio(pd.Timestamp("2026-08-01")) == "agosto de 2026"
    assert trimestre(pd.Timestamp("2026-04-01")) == "2.º trimestre de 2026"


def test_variacion(mensual):
    es = serie(mensual, zona="España", grupo="Total")
    assert variacion(es, 12) == pytest.approx(-1.2)
    with pytest.raises(ValueError):
        variacion(es, 14)


def test_ranking_excluye_el_total_de_espana(regiones):
    r = ranking_regiones(regiones)
    assert list(r["region"]) == ["País Vasco", "Madrid", "Andalucía"]
    assert set(r["anio"]) == {2024}
    assert list(ranking_regiones(regiones, anio=2023)["tasa"]) == [7.0, 8.0, 16.0]


def test_resumen(mensual, regiones, vivienda):
    r = resumen(mensual, regiones, vivienda)
    assert r["fecha"] == pd.Timestamp("2024-02-01")
    paro, joven, brecha, casa = r["kpis"]
    assert paro.valor == "10,7 %"
    assert paro.tendencia == "mejora"
    assert "1,2 puntos menos" in paro.detalle
    assert joven.valor == "25,4 %"
    assert brecha.valor == "4,7 puntos"
    assert casa.valor == "+12,0 %"
    texto = " ".join(r["frases"])
    assert "febrero de 2024" in texto
    assert "12,0 % en enero de 2023" in texto  # máximo de la serie
    assert "del 6,0 % de País Vasco al 15,0 % de Andalucía" in texto
    assert "1,8 veces la media europea" in texto
    assert "26 % más que en su mínimo de 2.º trimestre de 2014" in texto
