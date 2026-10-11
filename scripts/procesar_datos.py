"""Convierte data/raw/*.json en data/processed/*.csv.

Uso: python -m scripts.procesar_datos
"""

from pathlib import Path

from analisis import limpieza
from analisis.eurostat import load_raw

DATA = Path(__file__).resolve().parent.parent / "data"

TRANSFORMACIONES = {
    "paro_mensual": limpieza.paro_mensual,
    "paro_regiones": limpieza.paro_regiones,
    "precio_vivienda": limpieza.precio_vivienda,
}


def main() -> None:
    (DATA / "processed").mkdir(exist_ok=True)
    for nombre, transformar in TRANSFORMACIONES.items():
        df = transformar(load_raw(DATA / "raw" / f"{nombre}.json"))
        df.to_csv(DATA / "processed" / f"{nombre}.csv", index=False, float_format="%.2f")
        print(f"{nombre}: {len(df)} filas")


if __name__ == "__main__":
    main()
