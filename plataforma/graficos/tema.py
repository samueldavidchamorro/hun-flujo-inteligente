"""Tema oscuro de Plotly, compartido por todos los gráficos de la plataforma."""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

from plataforma.config import COLOR

FUENTE = "Inter, system-ui, -apple-system, Segoe UI, sans-serif"
FUENTE_MONO = "JetBrains Mono, ui-monospace, Consolas, monospace"

pio.templates["hun_oscuro"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family=FUENTE, color=COLOR["texto_2"], size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[COLOR["azul"], COLOR["cian"], COLOR["verde"], COLOR["naranja"], "#9B8CFF", COLOR["rojo"]],
        margin=dict(l=56, r=20, t=24, b=44),
        hoverlabel=dict(
            bgcolor="#0B1321", bordercolor=COLOR["borde"], align="left",
            font=dict(family=FUENTE, color=COLOR["texto"], size=13),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(color=COLOR["texto_2"], size=12)),
        xaxis=dict(gridcolor=COLOR["linea"], zerolinecolor=COLOR["linea"], linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=COLOR["texto_2"], family=FUENTE_MONO, size=12), ticklen=0,
                   title_font=dict(color=COLOR["texto_2"], size=12), title_standoff=12, automargin=True),
        yaxis=dict(gridcolor=COLOR["linea"], zerolinecolor=COLOR["linea"], linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=COLOR["texto_2"], family=FUENTE_MONO, size=12), ticklen=0,
                   title_font=dict(color=COLOR["texto_2"], size=12), title_standoff=12, automargin=True),
        separators=",.",
        bargap=0.3,
    )
)
pio.templates.default = "hun_oscuro"

# Escala continua azul → cian → blanco para mapas de calor
ESCALA_OCUPACION = [
    [0.0, "#0D1422"], [0.35, "#1B3A7A"], [0.65, COLOR["azul"]], [0.85, COLOR["cian"]], [1.0, "#E9FDFF"],
]

CONFIG_GRAFICO = {"displayModeBar": False, "responsive": True}


def base(alto: int = 360, **kwargs) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(height=alto, **kwargs)
    return fig
