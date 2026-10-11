"""Genera site/index.html a partir de data/processed/.

Uso: python -m scripts.generar_panel
"""

from pathlib import Path

from analisis.panel import construir

RAIZ = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    print(f"Panel generado en {construir(RAIZ / 'data' / 'processed', RAIZ / 'site')}")
