"""Lectura de los resultados reales del proyecto (carpeta outputs/).

La plataforma NO recalcula ni inventa nada: solo lee las tablas agregadas que
produjeron M2–M7. Los datos por paciente (data/) no están en esta copia y no
hacen falta: todos los gráficos usan agregados.

Si falta un archivo, `tabla()` lanza un error claro con la ruta esperada.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from plataforma.config import OUTPUTS


class FaltaResultado(FileNotFoundError):
    """Un archivo de outputs/ que la plataforma necesita no existe."""


def _ruta(relativa: str) -> Path:
    ruta = OUTPUTS / relativa
    if not ruta.exists():
        raise FaltaResultado(
            f"Falta {ruta}. Se genera con el módulo correspondiente (ver README del módulo)."
        )
    return ruta


@lru_cache(maxsize=None)
def tabla(relativa: str) -> pd.DataFrame:
    """CSV de outputs/ (cacheado: las tablas son pequeñas y no cambian en ejecución)."""
    return pd.read_csv(_ruta(relativa))


@lru_cache(maxsize=None)
def json_resultado(relativa: str) -> dict:
    return json.loads(_ruta(relativa).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Figuras Plotly guardadas como HTML por M4 visual: se extraen sus datos.
# ---------------------------------------------------------------------------
def _trazas_plotly(relativa: str) -> tuple[list, dict]:
    """Devuelve (trazas, layout) de un HTML exportado con plotly.write_html."""
    texto = _ruta(relativa).read_text(encoding="utf-8")
    decodificador = json.JSONDecoder()
    inicio = texto.index("[", texto.index("Plotly.newPlot("))
    trazas, fin = decodificador.raw_decode(texto[inicio:])
    inicio_layout = texto.index("{", inicio + fin)
    layout, _ = decodificador.raw_decode(texto[inicio_layout:])
    return trazas, layout


def _titulos_subplots(layout: dict) -> list[str]:
    return [a.get("text", "") for a in layout.get("annotations", [])]


@lru_cache(maxsize=None)
def heatmaps_ocupacion() -> dict:
    """Ocupación media y fracción de horas saturadas por día (Lun–Dom) × hora (0–23).

    Fuente: outputs/m4_visual/html/heatmap_saturacion.html (M4 visual, Persona 3).
    Estructura: {servicio: {"ocupacion": 7×24, "frac_saturada": 7×24}}.
    """
    trazas, layout = _trazas_plotly("m4_visual/html/heatmap_saturacion.html")
    titulos = _titulos_subplots(layout)
    salida: dict = {}
    for traza, titulo in zip(trazas, titulos):
        servicio = "hospitalizacion" if titulo.startswith("Hospitaliz") else "urgencias_observacion"
        medida = "frac_saturada" if "fracci" in titulo else "ocupacion"
        salida.setdefault(servicio, {})[medida] = traza["z"]
        salida[servicio]["dias"] = traza["y"]
    return salida


@lru_cache(maxsize=None)
def heatmaps_llegadas() -> dict:
    """Llegadas medias por hora, día × hora, para los 4 servicios (M4 visual)."""
    trazas, layout = _trazas_plotly("m4_visual/html/heatmap_llegadas.html")
    clave = {
        "Ingreso a urgencias": "urgencias_ingreso",
        "Urgencias / observaci": "urgencias_observacion",
        "Hospitalizaci": "hospitalizacion",
        "Ambulatorio": "ambulatorio",
    }
    salida = {}
    for traza, titulo in zip(trazas, _titulos_subplots(layout)):
        servicio = next(v for k, v in clave.items() if titulo.startswith(k))
        salida[servicio] = traza["z"]
    return salida


@lru_cache(maxsize=None)
def sankey() -> dict:
    """Nodos y aristas del Sankey de rutas de visita (M4)."""
    trazas, _ = _trazas_plotly("m4_visual/html/sankey_flujo.html")
    t = trazas[0]
    return {
        "etiquetas": t["node"]["label"],
        "origen": t["link"]["source"],
        "destino": t["link"]["target"],
        "valor": t["link"]["value"],
    }


# ---------------------------------------------------------------------------
# Escenarios de decisión (M7.2): regla ingenua θ = 0,5 frente a la política θ*.
# ---------------------------------------------------------------------------
@lru_cache(maxsize=None)
def escenarios_decision(modelo: str = "lightgbm") -> dict:
    """Resultados por 100 snapshots en la prueba temporal única (M7.2).

    Devuelve, por servicio, la regla θ = 0,5 (escenario A), la política θ* por
    servicio (escenario B) y las dos referencias sin modelo.
    """
    df = tabla("m7/tablas/m7_2_umbrales_prueba.csv")
    df = df[(df["modelo"] == modelo) & (df["conjunto"].str.startswith("prueba"))]
    salida = {}
    for servicio in ("hospitalizacion", "urgencias_observacion", "todos"):
        sub = df[df["servicio"] == servicio].set_index("regla")
        a = sub.loc["θ = 0,5"]
        b = sub.loc["θ* por servicio"]

        def resumen(fila) -> dict:
            tp = fila["alertas_por_100"] - fila["fp_por_100"]
            return {
                "umbral": None if pd.isna(fila["umbral"]) else float(fila["umbral"]),
                "sensibilidad": float(fila["sensibilidad"]),
                "especificidad": float(fila["especificidad"]),
                "vpp": None if pd.isna(fila["vpp"]) else float(fila["vpp"]),
                "alertas_100": float(fila["alertas_por_100"]),
                "tp_100": float(tp),
                "fn_100": float(fila["fn_por_100"]),
                "fp_100": float(fila["fp_por_100"]),
                "tn_100": float(100 - fila["alertas_por_100"] - fila["fn_por_100"]),
                "costo_100": float(fila["costo_por_100"]),
            }

        salida[servicio] = {
            "n": int(a["n"]),
            "prevalencia": float(resumen(a)["tp_100"] + resumen(a)["fn_100"]) / 100,
            "A": resumen(a),
            "B": resumen(b),
            "costo_alertar_todos": float(a["costo_alertar_a_todos"]),
            "costo_nunca": float(a["costo_no_alertar_nunca"]),
        }
    return salida


@lru_cache(maxsize=None)
def colas() -> pd.DataFrame:
    """λ, W, μ, L, c y ρ por servicio (M1/M4 de Persona 1, resumido en M3)."""
    return tabla("m3/tablas/resumen_colas_p1.csv").set_index("servicio")


@lru_cache(maxsize=None)
def matriz_transicion() -> pd.DataFrame:
    """P(siguiente servicio | servicio actual), con (llegada) y (egreso)."""
    return tabla("m4_visual/tablas/matriz_transicion_prob.csv").set_index("desde")
