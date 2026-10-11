"""Descarga los datasets de Eurostat a data/raw/.

Uso: python -m scripts.descargar_datos
"""

import sys
from pathlib import Path

from analisis.eurostat import fetch, parse_jsonstat, save_raw
from analisis.fuentes import FUENTES

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> int:
    errores = 0
    for fuente in FUENTES:
        try:
            data = fetch(fuente.codigo, fuente.params)
        except Exception as exc:  # noqa: BLE001 - informamos y seguimos con el resto
            print(f"ERROR {fuente.nombre}: {exc}")
            errores += 1
            continue
        save_raw(data, RAW_DIR / f"{fuente.nombre}.json")
        df = parse_jsonstat(data)
        dims = {d: sorted(df[d].unique())[:8] for d in data["id"] if d not in ("time", "geo")}
        print(f"OK {fuente.nombre}: {len(df)} valores · dimensiones {dims}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
