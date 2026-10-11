import json
from pathlib import Path

import pandas as pd

from analisis.limpieza import paro_mensual, paro_regiones, periodo_a_fecha, precio_vivienda


def _dataset(dims: dict[str, list[str]], valores: list[float], etiquetas: dict | None = None) -> dict:
    """Construye un JSON-stat mínimo con las dimensiones dadas, en el orden dado."""
    dimension = {}
    for d, codigos in dims.items():
        cat = {"index": {c: i for i, c in enumerate(codigos)}}
        if etiquetas and d in etiquetas:
            cat["label"] = etiquetas[d]
        dimension[d] = {"category": cat}
    return {"id": list(dims), "size": [len(c) for c in dims.values()], "dimension": dimension,
            "value": dict(enumerate(valores))}  # fmt: skip


def test_periodo_a_fecha():
    fechas = periodo_a_fecha(pd.Series(["2024-03", "2024-Q2", "2025"]))
    assert list(fechas) == [pd.Timestamp("2024-03-01"), pd.Timestamp("2024-04-01"), pd.Timestamp("2025-01-01")]


def test_paro_mensual_filtra_grupos_y_traduce():
    raw = _dataset({"age": ["TOTAL", "Y25-74", "Y_LT25"], "geo": ["ES", "EU27_2020"], "time": ["2024-01"]},
                   [11.0, 6.0, 9.0, 5.0, 28.0, 14.0])  # fmt: skip
    df = paro_mensual(raw)
    assert set(df.grupo) == {"Total", "Menores de 25"}
    assert set(df.zona) == {"España", "UE-27"}
    assert df[(df.zona == "España") & (df.grupo == "Menores de 25")].tasa.item() == 28.0


def test_paro_regiones_usa_nombres_cortos():
    raw = _dataset(
        {"age": ["Y15-24", "Y15-74"], "geo": ["ES", "ES30"], "time": ["2024", "2025"]},
        [25.0, 24.0, 20.0, 19.0, 11.0, 10.5, 8.5, 8.0],
        {"geo": {"ES": "Spain", "ES30": "Comunidad de Madrid"}},
    )
    df = paro_regiones(raw)
    assert set(df.region) == {"España", "Madrid"}
    assert df.anio.dtype.kind == "i"
    assert df[(df.region == "Madrid") & (df.anio == 2025) & (df.grupo == "Total")].tasa.item() == 8.0


def test_precio_vivienda_pivota_unidades():
    raw = _dataset({"unit": ["I15_Q", "RCH_A", "RCH_Q"], "geo": ["ES"], "time": ["2025-Q4", "2026-Q1"]},
                   [190.0, 194.0, 12.5, 12.8, 2.0, 2.1])  # fmt: skip
    df = precio_vivienda(raw)
    assert list(df.columns) == ["fecha", "zona", "indice_2015", "variacion_anual"]
    assert df.iloc[-1].to_dict() == {"fecha": pd.Timestamp("2026-01-01"), "zona": "España",
                                     "indice_2015": 194.0, "variacion_anual": 12.8}  # fmt: skip


def test_datos_reales_tienen_el_formato_esperado():
    """Los JSON descargados de Eurostat siguen produciendo tablas completas y sin nulos."""
    raw_dir = Path(__file__).parent.parent / "data" / "raw"
    df = paro_mensual(json.loads((raw_dir / "paro_mensual.json").read_text()))
    assert not df.isna().any().any()
    assert set(df.zona) == {"España", "UE-27"}
