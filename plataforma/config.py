"""Configuración de la plataforma: rutas, paleta y parámetros de ejecución.

Todo se puede cambiar por variables de entorno sin tocar el código:
    HUN_PLATAFORMA_PUERTO   (8050 por defecto)
    HUN_PLATAFORMA_DEBUG    ("1" activa el modo depuración de Dash)
    HUN_OUTPUTS             (carpeta de resultados; por defecto <raíz>/outputs)
"""
from __future__ import annotations

import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
OUTPUTS = Path(os.environ.get("HUN_OUTPUTS", RAIZ / "outputs"))

PUERTO = int(os.environ.get("HUN_PLATAFORMA_PUERTO", "8050"))
DEBUG = os.environ.get("HUN_PLATAFORMA_DEBUG", "0") == "1"

# Paleta del sistema de diseño (debe coincidir con assets/css/00_tokens.css)
COLOR = {
    "fondo": "#070B14",
    "fondo_2": "#0B1321",
    "tarjeta": "#101A2B",
    "azul": "#3984FF",
    "cian": "#31D6E8",
    "verde": "#25D69A",
    "naranja": "#FFAA45",
    "rojo": "#FF5D70",
    "gris": "#4A5A70",
    "texto": "#F3F7FC",
    "texto_2": "#A7B5C9",
    "texto_3": "#8292A8",
    "linea": "rgba(137,152,173,0.13)",
    "gris_claro": "#93A3B8",
    "borde": "#26364D",
}

# Nombres legibles de los servicios del HUN (los 4 que existen en los datos)
SERVICIO = {
    "hospitalizacion": "Hospitalización",
    "urgencias_observacion": "Urgencias / observación",
    "urgencias_ingreso": "Ingreso a urgencias",
    "ambulatorio": "Ambulatorio",
}
