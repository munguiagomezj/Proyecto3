"""Genera el panel web estático (site/index.html) con Plotly y una plantilla Jinja2."""

import json
import shutil
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from analisis.indicadores import num, ranking_regiones, resumen, serie

PLANTILLAS = Path(__file__).parent / "plantillas"
PLOTLY_JS = "https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"
ANIO_CRISIS = 2013  # año con el paro más alto de la serie

# Los colores reales se aplican en el navegador según el tema (claro/oscuro).
# Aquí cada traza solo indica qué papel tiene: "es", "ue", "pasado" o "barra".
BASE_LAYOUT = {
    "margin": {"l": 8, "r": 8, "t": 8, "b": 8},
    "hovermode": "x unified",
    "legend": {"orientation": "h", "y": 1.12, "x": 0},
    "xaxis": {"showgrid": False, "automargin": True, "hoverformat": "%m/%Y"},
    "yaxis": {"ticksuffix": " %", "automargin": True, "zeroline": False},
    "font": {"family": "system-ui, -apple-system, Segoe UI, Roboto, sans-serif", "size": 13},
    "separators": ",.",
}


def _linea(s: pd.Series, nombre: str, rol: str, formato: str = "%{y:.1f} %") -> dict:
    return {
        "type": "scatter",
        "mode": "lines",
        "name": nombre,
        "x": [d.strftime("%Y-%m-%d") for d in s.index],
        "y": [round(v, 2) for v in s.values],
        "line": {"width": 2},
        "hovertemplate": formato,
        "meta": rol,
    }


def figura_paro(mensual: pd.DataFrame, grupo: str) -> dict:
    trazas = [
        _linea(serie(mensual, zona="España", grupo=grupo), "España", "es"),
        _linea(serie(mensual, zona="UE-27", grupo=grupo), "UE-27", "ue"),
    ]
    return {"data": trazas, "layout": {**BASE_LAYOUT, "yaxis": {**BASE_LAYOUT["yaxis"], "rangemode": "tozero"}}}


def figura_regiones(regiones: pd.DataFrame) -> dict:
    """Barras horizontales por comunidad, una traza por grupo de edad."""
    trazas, media = [], []
    grupos = ["Total", "15 a 24 años"]
    for i, grupo in enumerate(grupos):
        r = ranking_regiones(regiones, grupo)
        espana = regiones[(regiones.grupo == grupo) & (regiones.codigo == "ES") & (regiones.anio == r.anio.iloc[0])]
        media.append(float(espana.tasa.iloc[0]))
        trazas.append(
            {
                "type": "bar",
                "orientation": "h",
                "name": grupo,
                "x": [round(v, 1) for v in r.tasa],
                "y": list(r.region),
                "text": [f"{num(v)} %" for v in r.tasa],
                "textposition": "outside",
                "cliponaxis": False,
                "hovertemplate": "%{y}: %{x:.1f} %<extra></extra>",
                "visible": i == 0,
                "meta": "barra",
            }
        )
    layout = {
        **BASE_LAYOUT,
        "hovermode": "closest",
        "height": 620,
        "bargap": 0.25,
        "showlegend": False,
        "margin": {"l": 8, "r": 48, "t": 24, "b": 32},
        "xaxis": {"ticksuffix": " %", "showgrid": True, "zeroline": False},
        "yaxis": {"automargin": True},
        "shapes": [_linea_media(media[0])],
        "annotations": [_nota_media(media[0])],
    }
    # El navegador usa estas medias al cambiar de grupo con los botones de la página.
    return {"data": trazas, "layout": layout, "grupos": grupos, "medias": media}


def _linea_media(valor: float) -> dict:
    return {"type": "line", "x0": valor, "x1": valor, "yref": "paper", "y0": 0, "y1": 1,
            "line": {"dash": "dot", "width": 1.5}, "name": "media"}  # fmt: skip


def _nota_media(valor: float) -> dict:
    return {"x": valor, "y": 1, "yref": "paper", "yanchor": "bottom", "showarrow": False,
            "text": f"España: {num(valor)} %", "xanchor": "left", "xshift": 4}  # fmt: skip


def figura_recuperacion(regiones: pd.DataFrame) -> dict:
    """Gráfico de pesas: paro en el peor año de la crisis frente al último año."""
    ultimo = ranking_regiones(regiones, "Total")
    antes = ranking_regiones(regiones, "Total", ANIO_CRISIS).set_index("region")["tasa"]
    orden = ultimo  # mismo orden que el gráfico de barras: el paro más alto arriba
    x_lineas, y_lineas = [], []
    for region, tasa in zip(orden.region, orden.tasa, strict=True):
        x_lineas += [antes[region], tasa, None]
        y_lineas += [region, region, None]
    anio = int(ultimo.anio.iloc[0])
    trazas = [
        {"type": "scatter", "mode": "lines", "x": x_lineas, "y": y_lineas, "hoverinfo": "skip",
         "showlegend": False, "line": {"width": 2}, "meta": "conector"},
        {"type": "scatter", "mode": "markers", "name": str(ANIO_CRISIS), "x": [antes[r] for r in orden.region],
         "y": list(orden.region), "marker": {"size": 10}, "meta": "pasado",
         "hovertemplate": f"%{{y}} · {ANIO_CRISIS}: %{{x:.1f}} %<extra></extra>"},
        {"type": "scatter", "mode": "markers", "name": str(anio), "x": list(orden.tasa), "y": list(orden.region),
         "marker": {"size": 10}, "meta": "es", "hovertemplate": f"%{{y}} · {anio}: %{{x:.1f}} %<extra></extra>"},
    ]  # fmt: skip
    layout = {**BASE_LAYOUT, "hovermode": "closest", "height": 620, "margin": {"l": 8, "r": 8, "t": 8, "b": 32},
              "xaxis": {"ticksuffix": " %", "showgrid": True, "zeroline": False, "rangemode": "tozero"},
              "yaxis": {"automargin": True}}  # fmt: skip
    return {"data": trazas, "layout": layout}


def figura_vivienda(vivienda: pd.DataFrame) -> dict:
    fmt = "%{y:.1f}"
    trazas = [
        _linea(serie(vivienda, "indice_2015", zona="España"), "España", "es", fmt),
        _linea(serie(vivienda, "indice_2015", zona="UE-27"), "UE-27", "ue", fmt),
    ]
    layout = {
        **BASE_LAYOUT,
        "yaxis": {**BASE_LAYOUT["yaxis"], "ticksuffix": ""},
        "shapes": [
            {
                "type": "line",
                "xref": "paper",
                "x0": 0,
                "x1": 1,
                "y0": 100,
                "y1": 100,
                "line": {"dash": "dot", "width": 1.5},
                "name": "media",
            }
        ],  # fmt: skip
        "annotations": [
            {
                "xref": "paper",
                "x": 0,
                "y": 100,
                "yanchor": "bottom",
                "xanchor": "left",
                "showarrow": False,
                "text": "2015 = 100",
            }
        ],  # fmt: skip
    }
    return {"data": trazas, "layout": layout}


def tabla_mensual(mensual: pd.DataFrame, meses: int = 12) -> pd.DataFrame:
    t = mensual.pivot_table(index="fecha", columns=["grupo", "zona"], values="tasa").sort_index().tail(meses)
    t = t[[("Total", "España"), ("Total", "UE-27"), ("Menores de 25", "España"), ("Menores de 25", "UE-27")]]
    t.index = t.index.strftime("%Y-%m")
    return t.iloc[::-1]


def _a_python(valor):
    """Convierte números de numpy (np.int64, np.float64...) en tipos que json sabe guardar."""
    if hasattr(valor, "item"):
        return valor.item()
    raise TypeError(f"No se puede convertir {type(valor).__name__} a JSON")


def _json_para_script(datos) -> str:
    """JSON seguro para incrustar en <script>: un texto con «</script>» no puede cerrar la etiqueta."""
    texto = json.dumps(datos, ensure_ascii=False, default=_a_python)
    return texto.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def construir(datos: Path, salida: Path) -> Path:
    mensual = pd.read_csv(datos / "paro_mensual.csv", parse_dates=["fecha"])
    regiones = pd.read_csv(datos / "paro_regiones.csv")
    vivienda = pd.read_csv(datos / "precio_vivienda.csv", parse_dates=["fecha"])

    figuras = {
        "paro_total": figura_paro(mensual, "Total"),
        "paro_joven": figura_paro(mensual, "Menores de 25"),
        "regiones": figura_regiones(regiones),
        "recuperacion": figura_recuperacion(regiones),
        "vivienda": figura_vivienda(vivienda),
    }
    res = resumen(mensual, regiones, vivienda)
    tabla_reg = (
        regiones[regiones.anio == res["anio_regiones"]]
        .pivot_table(index="region", columns="grupo", values="tasa")
        .sort_values("Total")
    )

    env = Environment(loader=FileSystemLoader(PLANTILLAS), autoescape=select_autoescape(["html", "j2"]))
    env.filters["num"] = num
    html = env.get_template("panel.html.j2").render(
        resumen=res,
        figuras_json=_json_para_script(figuras),
        plotly_js=PLOTLY_JS,
        anio_crisis=ANIO_CRISIS,
        tabla_mensual=tabla_mensual(mensual),
        tabla_regiones=tabla_reg,
        actualizado=pd.Timestamp.now(tz="Europe/Madrid").strftime("%d/%m/%Y"),
    )
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "datos").mkdir(exist_ok=True)
    for csv in datos.glob("*.csv"):
        shutil.copy(csv, salida / "datos" / csv.name)
    destino = salida / "index.html"
    destino.write_text(html, encoding="utf-8")
    return destino
