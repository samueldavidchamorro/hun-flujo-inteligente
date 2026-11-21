"""Gráficos compactos del panel de inteligencia operativa (resumen de toda la plataforma)."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from plataforma.config import COLOR, SERVICIO
from plataforma.datos import cargar
from plataforma.graficos.tema import base

COLOR_SERVICIO = {"hospitalizacion": COLOR["azul"], "urgencias_observacion": COLOR["cian"]}
UMBRAL = {"hospitalizacion": 0.95, "urgencias_observacion": 0.85}


def fig_perfil_horario() -> go.Figure:
    """Ocupación media por hora del día (promedio de los 7 días de la semana típica, M4 visual)."""
    h = cargar.heatmaps_ocupacion()
    fig = base(230)
    horas = list(range(24))
    for servicio in ("hospitalizacion", "urgencias_observacion"):
        z = np.array(h[servicio]["ocupacion"])
        perfil = z.mean(axis=0)
        fig.add_trace(go.Scatter(
            x=horas, y=perfil, mode="lines", name=SERVICIO[servicio], line=dict(color=COLOR_SERVICIO[servicio], width=2.4, shape="spline"),
            customdata=np.stack([z.min(axis=0), z.max(axis=0)], axis=1),
            hovertemplate="%{x:02d}:00 · ocupación media %{y:.0%}<br>según el día: %{customdata[0]:.0%} – %{customdata[1]:.0%}"
                          "<br><span style='color:#A7B5C9'>" + SERVICIO[servicio] + "</span><extra></extra>",
        ))
        fig.add_hline(y=UMBRAL[servicio], line=dict(color=COLOR_SERVICIO[servicio], dash="dot", width=1), opacity=0.6)
    fig.update_xaxes(title="hora del día", tickvals=[0, 6, 12, 18, 23], ticktext=["0 h", "6 h", "12 h", "18 h", "23 h"])
    fig.update_yaxes(tickformat=".0%", range=[0.55, 1.0])
    fig.update_layout(margin=dict(l=44, r=8, t=30, b=40), legend=dict(y=1.02, font=dict(size=11)))
    return fig


def fig_riesgo_tau() -> go.Figure:
    """Proporción observada de estancias largas según el momento de evaluación τ (OOF, M7.1)."""
    df = cargar.tabla("m7/tablas/m7_1_por_servicio_tau.csv")
    df = df[df["modelo"] == "lightgbm"].copy()
    df["servicio"] = df["estrato"].str.split(" · ").str[0]
    df["tau"] = df["estrato"].str.split(" · ").str[1].str.replace("τ", "").str.replace("h", " h")
    fig = base(230)
    for servicio in ("hospitalizacion", "urgencias_observacion"):
        sub = df[df["servicio"] == servicio]
        fig.add_trace(go.Bar(
            x=sub["tau"], y=sub["prevalencia"], name=SERVICIO[servicio], marker_color=COLOR_SERVICIO[servicio], marker_line_width=0,
            customdata=np.stack([sub["auc_roc"], sub["n"]], axis=1),
            text=[f"{v:.0%}".replace(".", ",") for v in sub["prevalencia"]], textposition="outside", textfont=dict(color=COLOR["texto"], size=11),
            hovertemplate="τ = %{x}<br>%{y:.1%} de los pacientes aún presentes terminan con estancia larga"
                          "<br>AUC del modelo en este estrato: %{customdata[0]:.3f} · n = %{customdata[1]:,.0f}<br><span style='color:#A7B5C9'>" + SERVICIO[servicio] + "</span><extra></extra>",
        ))
    fig.update_xaxes(title="horas desde el ingreso (τ)")
    fig.update_yaxes(tickformat=".0%", range=[0, 0.95])
    fig.update_layout(barmode="group", bargap=0.35, margin=dict(l=44, r=8, t=30, b=40), legend=dict(y=1.02, font=dict(size=11)))
    return fig
