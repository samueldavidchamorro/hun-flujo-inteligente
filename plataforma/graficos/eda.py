"""Gráficos del análisis exploratorio (M2, M3, M4 visual). Solo tablas agregadas reales.

Importante: la copia del proyecto no trae los datos por paciente, así que las
distribuciones se dibujan a partir de sus cuantiles (P10…P99, máximo). Se dice
así en cada gráfico: no se simulan histogramas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plataforma.config import COLOR, SERVICIO
from plataforma.datos import cargar
from plataforma.graficos.tema import ESCALA_OCUPACION, FUENTE as FUENTE_TEXTO, base

NOMBRE_TABLA = {"Hospitalización": "hospitalizacion", "Urgencias / observación": "urgencias_observacion"}
COLOR_SERVICIO = {"hospitalizacion": COLOR["azul"], "urgencias_observacion": COLOR["cian"]}

ETIQUETA_VARIABLE = {
    "edad": "Edad (años)",
    "n_mediciones_24h": "Laboratorios en las últimas 24 h",
    "n_mediciones_historia": "Laboratorios en la historia",
    "n_dx_historia": "Diagnósticos registrados en la historia",
    "n_dx_distintos_historia": "Diagnósticos distintos en la historia",
    "n_dx_30d": "Diagnósticos en los últimos 30 días",
    "n_visitas_365d": "Visitas en el último año",
    "n_hospitalizaciones_previas": "Hospitalizaciones previas",
    "horas_desde_ultima_alta_hosp": "Horas desde la última alta hospitalaria",
    "censo_servicio_t_menos_1h": "Censo del servicio en t − 1 h",
    "ocupacion_servicio_t_menos_1h": "Ocupación del servicio en t − 1 h",
    "llegadas_servicio_t_menos_1h": "Llegadas al servicio en t − 1 h",
}

# Conteos a los que M5.4 aplica log1p (rama num_log del ColumnTransformer)
VARIABLES_LOG1P = [
    "n_mediciones_24h", "n_mediciones_historia", "n_dx_historia", "n_dx_distintos_historia",
    "n_dx_30d", "n_visitas_365d", "n_hospitalizaciones_previas", "llegadas_servicio_t_menos_1h",
]


def _nombre(servicio_tabla: str) -> str:
    return NOMBRE_TABLA.get(servicio_tabla, servicio_tabla)


# ---------------------------------------------------------------------------
# 6.1 Univariado
# ---------------------------------------------------------------------------
def opciones_variables() -> list[dict]:
    df = cargar.tabla("m2/tablas/univariado_snapshot_tau0.csv")
    return [{"label": ETIQUETA_VARIABLE.get(v, v), "value": v} for v in df["variable"].unique()]


def resumen_variable(variable: str) -> pd.DataFrame:
    df = cargar.tabla("m2/tablas/univariado_snapshot_tau0.csv")
    return df[df["variable"] == variable]


def fig_variable(variable: str) -> go.Figure:
    """Caja construida con los cuantiles reales (P25, mediana, P75, P99) + máximo, por servicio."""
    df = resumen_variable(variable)
    fig = base(330)
    for _, f in df.iterrows():
        clave = _nombre(f["servicio"])
        fig.add_trace(go.Box(
            name=f["servicio"], y=[f["servicio"]], orientation="h",
            q1=[f["p25"]], median=[f["mediana"]], q3=[f["p75"]],
            lowerfence=[f["p25"]], upperfence=[f["p99"]],
            marker_color=COLOR_SERVICIO[clave], fillcolor="rgba(57,132,255,0.16)" if clave == "hospitalizacion" else "rgba(49,214,232,0.14)",
            line=dict(width=1.6), hoverinfo="skip", showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[f["máx"]], y=[f["servicio"]], mode="markers",
            marker=dict(symbol="diamond", size=9, color=COLOR["naranja"]),
            name="máximo", showlegend=False,
            hovertemplate=f"<b>{f['servicio']}</b><br>máximo: %{{x:,.0f}}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[f["p25"], f["mediana"], f["p75"], f["p99"]], y=[f["servicio"]] * 4, mode="markers",
            marker=dict(size=14, color="rgba(0,0,0,0)"), showlegend=False,
            customdata=[["P25"], ["Mediana"], ["P75"], ["P99"]],
            hovertemplate="%{customdata[0]}: %{x:,.2f}<extra></extra>",
        ))
    log = variable in VARIABLES_LOG1P or variable == "horas_desde_ultima_alta_hosp"
    fig.update_xaxes(type="log" if log else "linear", title=ETIQUETA_VARIABLE.get(variable, variable)
                     + (" · escala log" if log else ""))
    fig.update_layout(margin=dict(l=170, r=20, t=10, b=50))
    return fig


def fig_cuantiles_estancia() -> go.Figure:
    """Perfil de cuantiles de la estancia (LOS) por servicio, con el umbral P75 de entrenamiento."""
    df = cargar.tabla("m2/tablas/los_cuantiles.csv")
    cuantiles = ["p10_h", "p25_h", "p50_h", "p75_h", "p90_h", "p95_h", "p99_h"]
    etiquetas = ["P10", "P25", "P50", "P75", "P90", "P95", "P99"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=list(df["servicio"]), horizontal_spacing=0.1)
    for i, (_, f) in enumerate(df.iterrows(), start=1):
        clave = _nombre(f["servicio"])
        valores = [f[c] for c in cuantiles]
        umbral = f["umbral P75 (train)"]
        fig.add_trace(go.Bar(
            x=etiquetas, y=valores, marker_color=COLOR_SERVICIO[clave], marker_line_width=0,
            opacity=0.9, showlegend=False,
            customdata=np.stack([np.array(valores) / 24, np.array(valores) / umbral], axis=1),
            hovertemplate="<b>%{x}</b>: %{y:,.1f} h (≈ %{customdata[0]:.1f} días)"
                          "<br>%{customdata[1]:.2f} × el umbral de estancia larga<br><span style='color:#A7B5C9'>" + f["servicio"] + "</span><extra></extra>",
        ), row=1, col=i)
        fig.add_hline(y=f["umbral P75 (train)"], line=dict(color=COLOR["naranja"], dash="dot", width=1.4),
                      annotation_text=f"umbral P75 = {f['umbral P75 (train)']:.1f} h".replace(".", ","),
                      annotation_font_color=COLOR["naranja"], annotation_position="top left",
                      row=1, col=i)
        fig.update_yaxes(title_text="horas" if i == 1 else None, row=1, col=i)
    fig.update_layout(height=340, bargap=0.35, margin=dict(l=56, r=16, t=40, b=36))
    for a in fig.layout.annotations[:2]:
        a.font = dict(color=COLOR["texto"], size=13)
    return fig


def fig_estancia_por_mes() -> go.Figure:
    df = cargar.tabla("m2/tablas/los_por_mes.csv").copy()
    df["mes"] = pd.to_datetime(df["mes"])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=[SERVICIO["hospitalizacion"], SERVICIO["urgencias_observacion"]])
    for fila, clave in enumerate(["hospitalizacion", "urgencias_observacion"], start=1):
        sub = df[df["servicio"] == clave]
        for col, nombre, ancho, punteado in (("p75", "P75", 2.2, None), ("p50", "mediana", 1.6, "dot")):
            fig.add_trace(go.Scatter(
                x=sub["mes"], y=sub[col], mode="lines", name=nombre, legendgroup=nombre, customdata=sub["n"],
                showlegend=fila == 1, line=dict(color=COLOR_SERVICIO[clave] if col == "p75" else COLOR["texto_2"],
                                                width=ancho, dash=punteado, shape="spline"),
                hovertemplate="%{x|%b %Y}: %{y:,.1f} h<br>%{customdata:,.0f} estancias en el mes<br><span style='color:#A7B5C9'>" + nombre + "</span><extra></extra>",
            ), row=fila, col=1)
    for fila in (1, 2):
        fig.add_vrect(x0="2023-01-31", x1="2026-04-01", fillcolor=COLOR["azul"], opacity=0.05,
                      line_width=0, row=fila, col=1)
    fig.update_yaxes(title_text="horas")
    fig.update_layout(height=420, margin=dict(l=56, r=16, t=40, b=30))
    for a in fig.layout.annotations:
        a.font = dict(color=COLOR["texto"], size=13)
    return fig


def fig_balance() -> go.Figure:
    df = cargar.tabla("m2/tablas/balance_episodio.csv")
    fig = base(260)
    for particion, color in (("entrenamiento", COLOR["azul"]), ("prueba", COLOR["cian"])):
        sub = df[df["particion"] == particion]
        fig.add_trace(go.Bar(
            y=[SERVICIO[s] for s in sub["servicio"]], x=sub["tasa"] * 100, orientation="h",
            name=particion.capitalize(), marker_color=color, marker_line_width=0,
            customdata=np.stack([sub["positivos"], sub["n"]], axis=1),
            text=[f"{v:.1f} %".replace(".", ",") for v in sub["tasa"] * 100], textposition="outside",
            textfont=dict(color=COLOR["texto"]),
            hovertemplate="%{y} · " + particion + "<br>%{x:.1f} % de estancias largas"
                          "<br>%{customdata[0]:,.0f} de %{customdata[1]:,.0f} episodios<extra></extra>",
        ))
    fig.update_layout(barmode="group", bargap=0.35, margin=dict(l=170, r=40, t=30, b=40))
    fig.update_xaxes(title="% de episodios con estancia > P75 del servicio", range=[0, 34])
    return fig


# ---------------------------------------------------------------------------
# 6.2 Variables importantes
# ---------------------------------------------------------------------------
COLOR_DOMINIO = {
    "admisión": COLOR["azul"], "historia clínica": "#8C7CFF", "presión del servicio": COLOR["cian"],
    "calendario": "#6FA8DC", "laboratorios": "#C3CEDD",
}


def fig_shap(alcance: str = "global", top: int = 12) -> go.Figure:
    if alcance == "global":
        df = cargar.tabla("m7/tablas/m7_3_importancia_shap.csv")
    else:
        df = cargar.tabla("m7/tablas/m7_3_importancia_shap_por_servicio.csv")
        df = df[df["servicio"] == alcance]
    df = df.sort_values("media_abs_shap", ascending=False).head(top).iloc[::-1]
    fig = base(30 * top + 120)
    fig.add_trace(go.Bar(
        y=df["etiqueta"], x=df["porcentaje"], orientation="h",
        marker_color=[COLOR_DOMINIO.get(d, COLOR["gris"]) for d in df["dominio"]], marker_line_width=0,
        customdata=np.stack([df["dominio"], df["media_abs_shap"]], axis=1),
        text=[f"{v:.1f} %".replace(".", ",") for v in df["porcentaje"]], textposition="outside",
        textfont=dict(color=COLOR["texto"], size=11),
        hovertemplate="<b>%{y}</b><br>dominio: %{customdata[0]}<br>media |SHAP| = %{customdata[1]:.3f}"
                      "<br>%{x:.1f} % de la importancia total<extra></extra>",
    ))
    # Leyenda de dominios (trazas vacías: solo explican el color)
    for dominio in [d for d in COLOR_DOMINIO if d in set(df["dominio"])]:
        fig.add_trace(go.Bar(x=[None], y=[None], orientation="h", name=dominio, marker_color=COLOR_DOMINIO[dominio],
                             showlegend=True, hoverinfo="skip"))
    fig.update_layout(margin=dict(l=300, r=50, t=10, b=96), barmode="overlay",
                      legend=dict(orientation="h", y=-0.2, yanchor="top", x=-0.6, xanchor="left", font=dict(size=11),
                                  entrywidthmode="pixels", entrywidth=150))
    fig.update_traces(selector=dict(type="bar"), showlegend=False)
    for tr in fig.data[1:]:
        tr.showlegend = True
    fig.update_xaxes(title="% de la importancia SHAP total (LightGBM)", range=[0, df["porcentaje"].max() * 1.18])
    return fig


def fig_efectos(servicio: str = "hospitalizacion", top: int = 10) -> go.Figure:
    """Tamaño de efecto univariado frente al objetivo (M3): |2·AUC − 1| o V de Cramér, con BH."""
    df = cargar.tabla("m3/tablas/bivariado_target_paciente.csv")
    df = df[df["servicio"] == servicio].sort_values("efecto", ascending=False).head(top).iloc[::-1]
    colores = {"despreciable": COLOR["gris"], "pequeño": COLOR["azul"], "mediano": COLOR["cian"], "grande": COLOR["verde"]}
    fig = base(30 * top + 70)
    fig.add_trace(go.Bar(
        y=[ETIQUETA_VARIABLE.get(v, v.replace("_", " ")) for v in df["variable"]], x=df["efecto"],
        orientation="h", marker_color=[colores.get(m, COLOR["gris"]) for m in df["magnitud"]],
        marker_line_width=0, customdata=np.stack([df["métrica"], df["magnitud"], df["detalle"]], axis=1),
        hovertemplate="<b>%{y}</b><br>%{customdata[0]} = %{x:.3f} (%{customdata[1]})<br>%{customdata[2]}<extra></extra>",
    ))
    fig.update_layout(margin=dict(l=300, r=30, t=10, b=40))
    fig.update_xaxes(title="tamaño de efecto (|2·AUC − 1| o V de Cramér)")
    return fig


# ---------------------------------------------------------------------------
# 6.3 Multivariado
# ---------------------------------------------------------------------------
def fig_heatmap_ocupacion(servicio: str = "hospitalizacion", medida: str = "ocupacion") -> go.Figure:
    datos = cargar.heatmaps_ocupacion()[servicio]
    z = np.array(datos[medida])
    fig = base(300)
    fig.add_trace(go.Heatmap(
        z=z, x=[f"{h:02d}" for h in range(24)], y=datos["dias"], colorscale=ESCALA_OCUPACION,
        xgap=2, ygap=2, colorbar=dict(thickness=10, outlinewidth=0, tickfont=dict(color=COLOR["texto_2"]),
                                      tickformat=".0%"),
        hovertemplate="%{y} %{x}:00<br>" + ("ocupación media" if medida == "ocupacion" else "horas saturadas")
                      + ": %{z:.1%}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(title="hora del día", showgrid=False)
    fig.update_layout(margin=dict(l=46, r=10, t=10, b=44))
    return fig


def fig_bloqueo() -> go.Figure:
    """Espera en urgencias hasta hospitalización frente a la ocupación hospitalaria al llegar (M3)."""
    df = cargar.tabla("m3/tablas/bloqueo_urg_hosp_por_ocupacion.csv")
    fig = base(330)
    for col, nombre, color, ancho in (("p90_h", "P90", COLOR["naranja"], 1.4), ("p75_h", "P75", COLOR["cian"], 2.4),
                                      ("mediana_h", "mediana", COLOR["azul"], 2.0)):
        fig.add_trace(go.Scatter(
            x=df["ocup_media"], y=df[col], mode="lines+markers", name=nombre,
            line=dict(color=color, width=ancho, shape="spline"), marker=dict(size=6),
            customdata=df["decil_ocup"],
            hovertemplate="decil %{customdata} · ocupación %{x:.1%}<br>" + nombre + ": %{y:.1f} h<extra></extra>",
        ))
    fig.update_xaxes(title="ocupación hospitalaria en la hora de llegada (decil)", tickformat=".0%")
    fig.update_yaxes(title="horas en urgencias hasta hospitalizar")
    return fig


def fig_colinealidad() -> go.Figure:
    """Pares de variables con |ρ de Spearman| ≥ 0,7 (M3). Solo existen esos pares en la tabla."""
    df = cargar.tabla("m3/tablas/colinealidad_spearman_07.csv")
    corto = {
        "n_dx_historia": "dx historia", "n_dx_distintos_historia": "dx distintos", "n_dx_30d": "dx 30 días",
        "censo_servicio_t_menos_1h": "censo t−1", "ocupacion_servicio_t_menos_1h": "ocupación t−1",
    }
    variables = list(dict.fromkeys(list(df["var_1"]) + list(df["var_2"])))
    fig = make_subplots(rows=1, cols=2, subplot_titles=list(df["servicio"].unique()), horizontal_spacing=0.06)
    for i, serv in enumerate(df["servicio"].unique(), start=1):
        sub = df[df["servicio"] == serv]
        m = pd.DataFrame(np.nan, index=variables, columns=variables)
        for v in variables:
            m.loc[v, v] = 1.0
        for _, f in sub.iterrows():
            m.loc[f["var_1"], f["var_2"]] = m.loc[f["var_2"], f["var_1"]] = f["rho"]
        etiquetas = [corto.get(v, v) for v in variables]
        texto = m.map(lambda x: "" if pd.isna(x) else f"{x:.2f}".replace(".", ","))
        fig.add_trace(go.Heatmap(
            z=m.values, x=etiquetas, y=etiquetas, zmin=0, zmax=1, colorscale=ESCALA_OCUPACION,
            text=texto.values, texttemplate="%{text}", textfont=dict(size=11, color=COLOR["fondo"]),
            showscale=False, xgap=3, ygap=3, hovertemplate="%{y} · %{x}<br>ρ = %{z:.2f}<extra></extra>",
        ), row=1, col=i)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_yaxes(showticklabels=False, row=1, col=2)
    fig.update_xaxes(showgrid=False, tickangle=-30)
    fig.update_layout(height=340, margin=dict(l=90, r=10, t=36, b=70))
    for a in fig.layout.annotations:
        a.font = dict(color=COLOR["texto"], size=13)
    return fig


def fig_sankey() -> go.Figure:
    s = cargar.sankey()
    etiquetas = [e.replace("<br>", " · ") for e in s["etiquetas"]]
    color_nodo = []
    for e in etiquetas:
        if e.startswith("Llegada"):
            color_nodo.append(COLOR["texto"])
        elif e.startswith("Egreso"):
            color_nodo.append(COLOR["verde"])
        elif e.startswith("Hospitaliz"):
            color_nodo.append(COLOR["azul"])
        elif e.startswith("Urgencias"):
            color_nodo.append(COLOR["cian"])
        elif e.startswith("Ingreso"):
            color_nodo.append("#9B8CFF")
        else:
            color_nodo.append(COLOR["gris"])
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=etiquetas, color=color_nodo, pad=18, thickness=12, line=dict(width=0),
                  hovertemplate="%{label}<extra></extra>"),
        link=dict(source=s["origen"], target=s["destino"], value=s["valor"],
                  color="rgba(57,132,255,0.18)",
                  hovertemplate="%{source.label} → %{target.label}<br>%{value:,.0f} visitas<extra></extra>"),
    ))
    fig.update_layout(height=420, font=dict(color=COLOR["texto"], size=11), margin=dict(l=10, r=10, t=10, b=10))
    return fig


# ---------------------------------------------------------------------------
# 6.4 Atípicos
# ---------------------------------------------------------------------------
def fig_atipicos(variable: str, servicio: str = "Hospitalización") -> go.Figure:
    """Antes / después de log1p con los cuantiles reales.

    log1p es monótona, así que los cuantiles transformados son exactamente
    log1p(cuantil): la comparación es exacta, no aproximada.
    """
    df = resumen_variable(variable)
    f = df[df["servicio"] == servicio].iloc[0]
    puntos = {"P25": f["p25"], "Mediana": f["mediana"], "P75": f["p75"], "P99": f["p99"], "Máximo": f["máx"]}
    fig = make_subplots(rows=1, cols=2, subplot_titles=["Escala original", "Tras log1p (rama num_log de M5.4)"],
                        horizontal_spacing=0.12)
    for col, transformar in ((1, lambda v: v), (2, np.log1p)):
        x = [transformar(v) for v in puntos.values()]
        iqr = x[2] - x[0]
        fig.add_trace(go.Box(
            y=["v"], orientation="h", q1=[x[0]], median=[x[1]], q3=[x[2]], lowerfence=[x[0]], upperfence=[x[3]],
            marker_color=COLOR["azul"], fillcolor="rgba(57,132,255,0.16)", line=dict(width=1.6),
            hoverinfo="skip", showlegend=False,
        ), row=1, col=col)
        fig.add_trace(go.Scatter(
            x=[x[4]], y=["v"], mode="markers", marker=dict(symbol="diamond", size=11, color=COLOR["naranja"]),
            showlegend=False, hovertemplate="máximo: %{x:,.2f}<extra></extra>",
        ), row=1, col=col)
        if iqr > 0:
            limite = x[2] + 1.5 * iqr
            fig.add_vline(x=limite, line=dict(color=COLOR["rojo"], dash="dot", width=1.2), row=1, col=col)
    fig.update_yaxes(showticklabels=False, showgrid=False)
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=36, b=36))
    for a in fig.layout.annotations[:2]:
        a.font = dict(color=COLOR["texto"], size=12)
    return fig


def tabla_colas(servicio: str = "Hospitalización") -> pd.DataFrame:
    """Cola derecha de cada conteo: cuántas veces el máximo supera al P99 y cuántos IQR hay hasta el P99."""
    df = cargar.tabla("m2/tablas/univariado_snapshot_tau0.csv")
    df = df[(df["servicio"] == servicio) & (df["variable"].isin(VARIABLES_LOG1P))].copy()
    df["max_sobre_p99"] = df["máx"] / df["p99"].replace(0, np.nan)
    return df[["variable", "mediana", "p75", "p99", "máx", "% cero", "asimetría", "max_sobre_p99"]]


def fig_dispersion_franjas() -> go.Figure:
    """Dispersión de las 168 franjas día × hora: ocupación media frente a horas saturadas (M4 visual).

    Cada punto es un agregado real (una franja de la semana típica), no un paciente.
    """
    ocup = cargar.heatmaps_ocupacion()
    llegadas = cargar.heatmaps_llegadas()
    fig = base(380)
    for servicio in ("hospitalizacion", "urgencias_observacion"):
        z_o = np.array(ocup[servicio]["ocupacion"]).ravel()
        z_s = np.array(ocup[servicio]["frac_saturada"]).ravel()
        z_l = np.array(llegadas[servicio]).ravel()
        etiquetas = [f"{d} {h:02d}:00" for d in ocup[servicio]["dias"] for h in range(24)]
        tam = 6 + 16 * (z_l - z_l.min()) / max(z_l.max() - z_l.min(), 1e-9)
        fig.add_trace(go.Scatter(
            x=z_o, y=z_s, mode="markers", name=SERVICIO[servicio],
            marker=dict(size=tam, color=COLOR_SERVICIO[servicio], opacity=0.7, line=dict(width=0)),
            customdata=np.stack([etiquetas, z_l], axis=1),
            hovertemplate="<b>%{customdata[0]}</b><br>ocupación media %{x:.1%}<br>horas saturadas %{y:.0%}"
                          "<br>llegadas %{customdata[1]:.1f}/h<br><span style='color:#A7B5C9'>" + SERVICIO[servicio] + "</span><extra></extra>",
        ))
    for u, color in ((0.95, COLOR["azul"]), (0.85, COLOR["cian"])):
        fig.add_vline(x=u, line=dict(color=color, dash="dot", width=1))
    fig.update_xaxes(title="ocupación media de la franja (censo / capacidad estimada)", tickformat=".0%")
    fig.update_yaxes(title="semanas con esa franja saturada", tickformat=".0%", range=[-0.03, 1.03])
    return fig


def _nodos_sankey() -> list[dict]:
    """Nodos del Sankey de M4 con su servicio, paso y conteo (leídos de las etiquetas que generó M4)."""
    import re
    s = cargar.sankey()
    nodos = []
    for etiqueta in s["etiquetas"]:
        m = re.match(r"^(.*?) · paso (\d+)<br>([\d,]+) \(([\d.]+) %\)", etiqueta)
        if m:
            nodos.append({"servicio": m.group(1), "paso": int(m.group(2)), "n": int(m.group(3).replace(",", ""))})
    return nodos


def fig_rutas() -> go.Figure:
    """Versión simple del Sankey: por dónde entra cada visita y cuántas etapas recorre antes de salir.

    Ambas barras usan solo nodos que no se repiten por visita (primer paso y paso del egreso),
    así que ninguna visita se cuenta dos veces.
    """
    nodos = _nodos_sankey()
    total = sum(v for o, v in zip(cargar.sankey()["origen"], cargar.sankey()["valor"]) if o == 0)
    entrada = [n for n in nodos if n["paso"] == 1 and n["servicio"] != "Egreso"]
    entrada.sort(key=lambda n: -n["n"])
    salida = sorted([n for n in nodos if n["servicio"] == "Egreso"], key=lambda n: n["paso"])
    colores_entrada = {"Ambulatorio": "#4A5D7E", "Ingreso a urgencias": "#8C7CFF",
                       "Urgencias / observación": COLOR["cian"], "Hospitalización": COLOR["azul"]}
    colores_salida = [COLOR["verde"], "#1A9C72", "#A7F3D8"]   # el tercero claro: visible fuera de la barra

    def texto_sobre(hex_color: str) -> str:
        """Color de texto con mejor contraste sobre el segmento (oscuro sobre claros, blanco sobre oscuros)."""
        r, g, b = (int(hex_color.lstrip("#")[k:k + 2], 16) / 255 for k in (0, 2, 4))
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
        lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
        contraste_blanco = 1.05 / (lum + 0.05)
        contraste_oscuro = (lum + 0.05) / (0.0037 + 0.05)   # luminancia de #070B14 ≈ 0,0037
        return "#FFFFFF" if contraste_blanco >= contraste_oscuro else COLOR["fondo"]

    fig = base(300)
    filas = ["¿Por dónde entra?", "¿Cuántas etapas recorre?"]
    MIN_DENTRO = 15          # % mínimo para que la etiqueta quepa dentro del segmento
    fuera = {0: [], 1: []}   # etiquetas de segmentos delgados, a la derecha de cada barra

    def agregar(fila, nombre, pct, n, color, extra):
        dentro = pct >= MIN_DENTRO
        etiqueta = f"{nombre} · {pct:.0f} %".replace(".", ",")
        if not dentro:
            valor = f"{pct:.1f} %".replace(".", ",") if pct < 1 else f"{pct:.0f} %"
            fuera[fila].append(f"<span style='color:{color}'>■</span> {nombre} <b>{valor}</b>")
        fig.add_trace(go.Bar(
            y=[filas[fila]], x=[pct], orientation="h", name=nombre,
            marker_color=color, marker_line_width=0,
            text=[etiqueta if dentro else ""], textposition="inside", insidetextanchor="middle",
            textfont=dict(color=texto_sobre(color), size=13, family=FUENTE_TEXTO),
            # Todo el texto en la caja principal: la caja "extra" de Plotly toma el color del segmento y no se lee
            hovertemplate=f"<b>{nombre}</b><br>{n:,} visitas".replace(",", ".") + f" ({pct:.1f} %)".replace(".", ",")
                          + f"<br><span style='color:{COLOR['texto_2']}'>{extra}</span><extra></extra>",
            hoverlabel=dict(bgcolor="#0B1321", bordercolor=color, font=dict(color=COLOR["texto"], size=13)),
        ))

    for n in entrada:
        agregar(0, n["servicio"], n["n"] / total * 100, n["n"], colores_entrada.get(n["servicio"], COLOR["gris"]),
                "primer servicio de la visita")
    for i, n in enumerate(salida):
        k = n["paso"] - 1
        agregar(1, f"{k} etapa" + ("s" if k > 1 else ""), n["n"] / total * 100, n["n"], colores_salida[min(i, 2)],
                "etapas antes del egreso")
    for fila, textos in fuera.items():
        if textos:
            fig.add_annotation(x=100, y=filas[fila], xanchor="left", xshift=10, showarrow=False, align="left",
                               text="<br>".join(textos), font=dict(color=COLOR["texto"], size=12.5, family=FUENTE_TEXTO))
    fig.update_layout(barmode="stack", bargap=0.42, showlegend=False, margin=dict(l=190, r=210, t=10, b=40))
    fig.update_xaxes(range=[0, 100], ticksuffix=" %", title=None, showgrid=False, tickfont=dict(color=COLOR["texto_2"]))
    fig.update_yaxes(autorange="reversed", tickfont=dict(family=FUENTE_TEXTO, size=13, color=COLOR["texto"]))
    return fig
