"""Cálculo de indicadores y de las frases del resumen. Funciones puras sobre DataFrames."""

from dataclasses import dataclass

import pandas as pd

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]  # fmt: skip


def mes_anio(fecha: pd.Timestamp) -> str:
    return f"{MESES[fecha.month - 1]} de {fecha.year}"


def trimestre(fecha: pd.Timestamp) -> str:
    return f"{(fecha.month - 1) // 3 + 1}.º trimestre de {fecha.year}"


def num(valor: float, decimales: int = 1) -> str:
    """Número con coma decimal, al estilo español."""
    return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def serie(df: pd.DataFrame, valor: str = "tasa", **filtros) -> pd.Series:
    """Serie temporal (índice fecha) filtrada por columnas, p. ej. zona='España'."""
    mask = pd.Series(True, index=df.index)
    for col, val in filtros.items():
        mask &= df[col] == val
    return df[mask].set_index("fecha")[valor].sort_index()


@dataclass(frozen=True)
class Kpi:
    titulo: str
    valor: str
    detalle: str
    tendencia: str  # "mejora", "empeora" o "neutra"


def variacion(s: pd.Series, periodos: int) -> float:
    """Diferencia entre el último valor y el de hace `periodos` observaciones."""
    if len(s) <= periodos:
        raise ValueError("La serie es demasiado corta para esa comparación")
    return float(s.iloc[-1] - s.iloc[-1 - periodos])


def tendencia_paro(cambio: float) -> str:
    # En el paro, bajar es bueno.
    return "mejora" if cambio < 0 else "empeora" if cambio > 0 else "neutra"


def ranking_regiones(regiones: pd.DataFrame, grupo: str = "Total", anio: int | None = None) -> pd.DataFrame:
    """Comunidades ordenadas de menor a mayor paro en un año (por defecto, el último)."""
    anio = anio or int(regiones["anio"].max())
    sel = regiones[(regiones["grupo"] == grupo) & (regiones["anio"] == anio) & (regiones["codigo"] != "ES")]
    return sel.sort_values(["tasa", "region"]).reset_index(drop=True)


def resumen(mensual: pd.DataFrame, regiones: pd.DataFrame, vivienda: pd.DataFrame) -> dict:
    """KPIs y frases clave del panel, calculados a partir de los datos."""
    es = serie(mensual, zona="España", grupo="Total")
    ue = serie(mensual, zona="UE-27", grupo="Total")
    es_joven = serie(mensual, zona="España", grupo="Menores de 25")
    ue_joven = serie(mensual, zona="UE-27", grupo="Menores de 25")
    viv_es = serie(vivienda, "indice_2015", zona="España")
    viv_ue = serie(vivienda, "indice_2015", zona="UE-27")
    var_viv_es = serie(vivienda, "variacion_anual", zona="España")
    var_viv_ue = serie(vivienda, "variacion_anual", zona="UE-27")

    fecha = es.index[-1]
    cambio_anual = variacion(es, 12)
    cambio_joven = variacion(es_joven, 12)
    brecha = float(es.iloc[-1] - ue.loc[fecha])
    pico_fecha, pico = es.idxmax(), float(es.max())
    ranking = ranking_regiones(regiones)
    anio_reg = int(ranking["anio"].iloc[0])
    fecha_viv = viv_es.index[-1]
    minimo_viv_fecha = viv_es.idxmin()
    subida_desde_minimo = float(viv_es.iloc[-1] / viv_es.min() * 100 - 100)

    kpis = [
        Kpi("Tasa de paro", f"{num(es.iloc[-1])} %",
            f"{num(abs(cambio_anual))} puntos {'menos' if cambio_anual < 0 else 'más'} que hace un año",
            tendencia_paro(cambio_anual)),
        Kpi("Paro juvenil (<25)", f"{num(es_joven.iloc[-1])} %",
            f"{num(abs(cambio_joven))} puntos {'menos' if cambio_joven < 0 else 'más'} que hace un año",
            tendencia_paro(cambio_joven)),
        Kpi("Distancia con la UE", f"{num(brecha)} puntos",
            f"UE-27: {num(ue.loc[fecha])} %", "neutra"),
        Kpi("Precio de la vivienda", f"{'+' if var_viv_es.iloc[-1] >= 0 else ''}{num(var_viv_es.iloc[-1])} %",
            f"en un año · UE-27: {num(var_viv_ue.iloc[-1])} %", "neutra"),
    ]  # fmt: skip

    frases = [
        f"En {mes_anio(fecha)} la tasa de paro en España es del {num(es.iloc[-1])} %, "
        f"{num(abs(cambio_anual))} puntos {'menos' if cambio_anual < 0 else 'más'} que un año antes. "
        f"Sigue {num(brecha)} puntos por encima de la media de la UE ({num(ue.loc[fecha])} %).",
        f"El máximo de la serie fue del {num(pico)} % en {mes_anio(pico_fecha)}: "
        f"desde entonces el paro ha bajado {num(pico - es.iloc[-1])} puntos.",
        f"Entre los menores de 25 años el paro es del {num(es_joven.iloc[-1])} %, "
        f"{num(es_joven.iloc[-1] / ue_joven.loc[fecha])} veces la media europea ({num(ue_joven.loc[fecha])} %).",
        f"Por comunidades ({anio_reg}), el paro va del {num(ranking['tasa'].iloc[0])} % de "
        f"{ranking['region'].iloc[0]} al {num(ranking['tasa'].iloc[-1])} % de {ranking['region'].iloc[-1]}.",
        f"La vivienda cuesta un {num(var_viv_es.iloc[-1])} % más que hace un año ({trimestre(fecha_viv)}) "
        f"y un {num(subida_desde_minimo, 0)} % más que en su mínimo de {trimestre(minimo_viv_fecha)}. "
        f"Desde 2015 ha subido un {num(viv_es.iloc[-1] - 100, 0)} % en España y un "
        f"{num(viv_ue.loc[fecha_viv] - 100, 0)} % en la UE.",
    ]
    return {"fecha": fecha, "kpis": kpis, "frases": frases, "anio_regiones": anio_reg}
