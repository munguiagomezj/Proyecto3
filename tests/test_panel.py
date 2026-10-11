import json
import re

from analisis.panel import construir


def _guardar(tmp_path, mensual, regiones, vivienda):
    datos = tmp_path / "datos"
    datos.mkdir()
    mensual.to_csv(datos / "paro_mensual.csv", index=False)
    regiones.to_csv(datos / "paro_regiones.csv", index=False)
    vivienda.to_csv(datos / "precio_vivienda.csv", index=False)
    return datos


def test_construir_panel(tmp_path, mensual, regiones, vivienda, monkeypatch):
    monkeypatch.setattr("analisis.panel.ANIO_CRISIS", 2023)
    salida = tmp_path / "site"
    destino = construir(_guardar(tmp_path, mensual, regiones, vivienda), salida)
    html = destino.read_text(encoding="utf-8")

    assert "<title>Empleo y vivienda en España</title>" in html
    assert "10,7 %" in html  # KPI de paro
    assert (salida / "datos" / "paro_mensual.csv").exists()

    figuras = json.loads(re.search(r"const FIGURAS = (\{.*?\});\n", html).group(1))
    assert set(figuras) == {"paro_total", "paro_joven", "regiones", "recuperacion", "vivienda"}
    regiones_fig = figuras["regiones"]
    assert regiones_fig["grupos"] == ["Total", "15 a 24 años"]
    assert regiones_fig["medias"] == [10.0, 22.0]
    # Cada traza indica su papel para que el navegador le dé el color del tema.
    for fig in figuras.values():
        assert all("meta" in t for t in fig["data"])


def test_el_panel_escapa_el_html(tmp_path, mensual, regiones, vivienda, monkeypatch):
    monkeypatch.setattr("analisis.panel.ANIO_CRISIS", 2023)
    regiones = regiones.replace({"Madrid": "<script>alert(1)</script>"})
    html = construir(_guardar(tmp_path, mensual, regiones, vivienda), tmp_path / "site").read_text()
    assert "<td><script>" not in html
    assert "&lt;script&gt;" in html  # en la tabla
    assert html.count("</script>") == 3  # solo las etiquetas reales: tema, Plotly y el panel
    assert "\\u003cscript\\u003e" in html  # en los datos del gráfico
