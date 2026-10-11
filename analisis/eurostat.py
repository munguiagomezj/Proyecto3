"""Cliente mínimo de la API de Eurostat y parser del formato JSON-stat 2.0."""

import json
import time
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{code}"


def fetch(code: str, params: dict, retries: int = 3, timeout: int = 60) -> dict:
    """Descarga un dataset de Eurostat en JSON-stat. Reintenta con espera exponencial."""
    query = {"format": "JSON", "lang": "EN", **params}
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(BASE_URL.format(code=code), params=query, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(2**attempt)
    raise AssertionError("inalcanzable")


def parse_jsonstat(data: dict) -> pd.DataFrame:
    """Convierte un dataset JSON-stat 2.0 en una tabla «larga»: una fila por valor.

    JSON-stat guarda los valores en una lista plana (o un diccionario disperso
    {posición: valor}). La posición de cada valor se obtiene combinando las
    posiciones de cada dimensión, igual que los índices de un array multidimensional.
    """
    dims = data["id"]
    sizes = data["size"]
    # Para cada dimensión: lista de códigos ordenados por su posición.
    codes = []
    for dim in dims:
        index = data["dimension"][dim]["category"]["index"]
        ordered = sorted(index, key=index.get) if isinstance(index, dict) else list(index)
        codes.append(ordered)

    values = data["value"]
    items = values.items() if isinstance(values, dict) else enumerate(values)

    rows = []
    for flat_pos, value in items:
        if value is None:
            continue
        pos = int(flat_pos)
        row = {}
        # Recorremos las dimensiones de la última a la primera (orden row-major).
        for dim, size, dim_codes in zip(reversed(dims), reversed(sizes), reversed(codes), strict=True):
            pos, i = divmod(pos, size)
            row[dim] = dim_codes[i]
        row["value"] = float(value)
        rows.append(row)

    return pd.DataFrame(rows, columns=[*dims, "value"])


def labels(data: dict, dim: str) -> dict[str, str]:
    """Etiquetas legibles de una dimensión (p. ej. códigos de región → nombres)."""
    return data["dimension"][dim]["category"].get("label", {})


def save_raw(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def load_raw(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
