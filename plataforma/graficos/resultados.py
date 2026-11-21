"""Gráficos del modelo y de resultados (M6, M7). Solo salidas reales de los módulos."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plataforma.config import COLOR, SERVICIO
from plataforma.datos import cargar
from plataforma.graficos.tema import base

NOMBRE_MODELO = {
    "lightgbm": "LightGBM", "random_forest": "Random Forest", "svm_rbf": "SVM RBF", "cart": "Árbol CART",
    "logreg_lasso": "Regresión logística", "knn": "KNN", "naive_bayes": "Naive Bayes",
}


def fig_modelos() -> go.Figure:
    """AUC OOF global y dentro de servicio × τ de los 7 modelos (M6.4)."""
    df = cargar.tabla("m6/model_benchmark_summary.csv").sort_values("auc_oof")
    nombres = [NOMBRE_MODELO.get(m, m) for m in df["modelo"]]
    fig = base(340)
    fig.add_trace(go.Bar(
        y=nombres, x=df["auc_oof"], orientation="h", name="AUC OOF global",
        marker_color=[COLOR["azul"] if m == "lightgbm" else "rgba(57,132,255,0.35)" for m in df["modelo"]],
        marker_line_width=0, hovertemplate="%{y}<br>AUC global: %{x:.3f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=nombres, x=df["auc_oof_servicio_tau"], mode="markers", name="AUC medio servicio × τ",
        marker=dict(symbol="line-ns", size=18, line=dict(width=3, color=COLOR["cian"])),
        hovertemplate="%{y}<br>AUC servicio × τ: %{x:.3f}<extra></extra>",
    ))
    fig.update_xaxes(range=[0.5, 0.78], title="AUC-ROC (validación cruzada agrupada por paciente)")
    fig.update_layout(margin=dict(l=150, r=20, t=64, b=46), bargap=0.4, legend=dict(y=1.03, font=dict(size=11)))
    return fig


def fig_costo_umbral() -> go.Figure:
    """Costo esperado por 100 snapshots según el umbral (OOF calibrado, desarrollo M7.2), c_FN = 5."""
    df = cargar.tabla("m7/tablas/m7_2_barrido_costo_desarrollo.csv")
    df = df[df["modelo"] == "lightgbm"]
    theta = cargar.json_resultado("m7/m7_2_umbrales_congelados.json")["modelos"]["lightgbm"]["theta_global"]
    fig = base(340)
    fig.add_trace(go.Scatter(
        x=df["umbral"], y=df["costo_por_100"], mode="lines", line=dict(color=COLOR["cian"], width=2.4),
        fill="tozeroy", fillcolor="rgba(49,214,232,0.07)", name="costo esperado",
        hovertemplate="θ = %{x:.2f}<br>costo: %{y:.1f} por 100<extra></extra>",
    ))
    for x, texto, color in ((theta, f"θ* = {theta:.2f}", COLOR["verde"]), (0.5, "θ = 0,5 (regla actual)", COLOR["gris_claro"])):
        y = float(df.loc[(df["umbral"] - x).abs().idxmin(), "costo_por_100"])
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text", text=[texto.replace(".", ",")], textposition="top center",
            textfont=dict(color=color, size=12), marker=dict(size=11, color=color, line=dict(width=2, color=COLOR["fondo"])),
            showlegend=False, hovertemplate=texto + "<br>costo: %{y:.1f}<extra></extra>",
        ))
    fig.add_vline(x=1 / 6, line=dict(color=COLOR["texto_2"], dash="dot", width=1),
                  annotation_text="Bayes 1/6", annotation_font_color=COLOR["texto_2"], annotation_position="bottom right")
    fig.update_xaxes(title="umbral de alerta θ (probabilidad calibrada)", range=[0, 1])
    fig.update_yaxes(title="costo esperado por 100 (c_FN = 5, c_FP = 1)", rangemode="tozero")
    fig.update_layout(showlegend=False)
    return fig


def fig_estrategias(servicio: str = "hospitalizacion") -> go.Figure:
    """Costo por 100 en la prueba temporal única: referencias sin modelo frente a las dos reglas."""
    e = cargar.escenarios_decision("lightgbm")[servicio]
    etiquetas = ["Nunca alertar", "Regla θ = 0,5", "Alertar a todos", "Política θ*"]
    valores = [e["costo_nunca"], e["A"]["costo_100"], e["costo_alertar_todos"], e["B"]["costo_100"]]
    colores = [COLOR["gris"], COLOR["gris_claro"], COLOR["gris"], COLOR["verde"]]
    fig = base(300)
    fig.add_trace(go.Bar(
        x=etiquetas, y=valores, marker_color=colores, marker_line_width=0,
        text=[f"{v:.1f}".replace(".", ",") for v in valores], textposition="outside",
        textfont=dict(color=COLOR["texto"], size=13),
        hovertemplate="%{x}<br>costo: %{y:.1f} por 100 snapshots<extra></extra>",
    ))
    fig.add_annotation(x=3, y=valores[3], ax=1, ay=valores[1], xref="x", yref="y", axref="x", ayref="y",
                       showarrow=True, arrowhead=2, arrowwidth=1.4, arrowcolor=COLOR["verde"], text="")
    fig.add_annotation(x=2.0, y=max(valores) * 1.12, showarrow=False, font=dict(color=COLOR["verde"], size=12),
                       text=f"−{(1 - valores[3] / valores[1]) * 100:.0f} % frente a la regla 0,5".replace(".", ","))
    fig.update_yaxes(title="costo esperado por 100 (c_FN = 5, c_FP = 1)", range=[0, max(valores) * 1.22])
    fig.update_layout(bargap=0.45, margin=dict(l=56, r=10, t=20, b=40))
    return fig


def fig_confusion(servicio: str = "hospitalizacion") -> go.Figure:
    """Qué pasa con 100 snapshots en cada escenario (prueba temporal única de M7.2)."""
    e = cargar.escenarios_decision("lightgbm")[servicio]
    filas = ["Escenario A · θ = 0,5", "Escenario B · θ*"]
    partes = [
        ("tp_100", "Estancia larga detectada", COLOR["verde"]),
        ("fn_100", "Estancia larga no detectada", COLOR["rojo"]),
        ("fp_100", "Alerta preventiva sin estancia larga", COLOR["naranja"]),
        ("tn_100", "Sin alerta, estancia normal", "rgba(137,152,173,0.30)"),
    ]
    fig = base(300)
    for clave, nombre, color in partes:
        valores = [e["A"][clave], e["B"][clave]]
        fig.add_trace(go.Bar(
            y=filas, x=valores, orientation="h", name=nombre, marker_color=color, marker_line_width=0,
            text=[f"{v:.1f}".replace(".", ",") if v >= 4 else "" for v in valores], textposition="inside",
            insidetextanchor="middle", textfont=dict(color=COLOR["fondo"], size=12),
            hovertemplate="%{y}<br>" + nombre + ": %{x:.1f} de cada 100<extra></extra>",
        ))
    fig.update_layout(barmode="stack", bargap=0.35, margin=dict(l=150, r=10, t=10, b=110),
                      legend=dict(orientation="h", y=-0.42, yanchor="top", x=0, font=dict(size=11.5),
                                  traceorder="normal", entrywidthmode="pixels", entrywidth=245))
    fig.update_xaxes(range=[0, 100], title="de cada 100 snapshots de " + SERVICIO[servicio].lower())
    return fig


def fig_calibracion() -> go.Figure:
    """Prevalencia real frente a probabilidad media en prueba, por servicio (M7.2)."""
    df = cargar.tabla("m7/tablas/m7_2_calibracion_prueba.csv")
    df = df[(df["modelo"] == "lightgbm") & (df["servicio"] != "todos")]
    fig = base(340)
    for version, color in (("sin_calibrar", COLOR["gris"]), ("isotonic", COLOR["cian"])):
        sub = df[df["version"] == version]
        fig.add_trace(go.Bar(
            x=[SERVICIO[s] for s in sub["servicio"]], y=sub["p_media"],
            name="probabilidad media · " + ("sin calibrar" if version == "sin_calibrar" else "isotónica"),
            marker_color=color, marker_line_width=0,
            hovertemplate="%{x}<br>prob. media: %{y:.1%}<extra></extra>",
        ))
    sub = df[df["version"] == "isotonic"]
    fig.add_trace(go.Scatter(
        x=[SERVICIO[s] for s in sub["servicio"]], y=sub["prevalencia"], mode="markers", name="prevalencia real",
        marker=dict(symbol="line-ew", size=40, line=dict(width=3, color=COLOR["texto"])),
        hovertemplate="%{x}<br>prevalencia real: %{y:.1%}<extra></extra>",
    ))
    fig.update_yaxes(tickformat=".0%", range=[0, 0.8])
    fig.update_layout(barmode="group", bargap=0.4, margin=dict(l=48, r=10, t=84, b=40), legend=dict(y=1.03, font=dict(size=11)))
    return fig


def fig_auc_estratos() -> go.Figure:
    """AUC de LightGBM dentro de cada servicio × τ (OOF, M7.1)."""
    df = cargar.tabla("m7/tablas/m7_1_por_servicio_tau.csv")
    df = df[df["modelo"] == "lightgbm"]
    fig = base(260)
    fig.add_trace(go.Bar(
        x=df["estrato"].str.replace("urgencias_observacion", "Urgencias").str.replace("hospitalizacion", "Hospitalización"),
        y=df["auc_roc"], marker_color=[COLOR["azul"] if "hosp" in e else COLOR["cian"] for e in df["estrato"]],
        marker_line_width=0, text=[f"{v:.3f}".replace(".", ",") for v in df["auc_roc"]], textposition="outside",
        textfont=dict(color=COLOR["texto"]), hovertemplate="%{x}<br>AUC: %{y:.3f}<extra></extra>",
    ))
    fig.add_hline(y=0.5, line=dict(color=COLOR["texto_2"], dash="dot", width=1),
                  annotation_text="azar", annotation_font_color=COLOR["texto_2"])
    fig.update_yaxes(range=[0.45, 0.8], title="AUC-ROC")
    fig.update_layout(bargap=0.45)
    return fig


def senal_saturacion(top: int = 6) -> dict:
    """Variables en t − 1 con mayor AUC frente a y_target_saturacion (M5.3, entrenamiento)."""
    df = cargar.tabla("m5/tablas/m5_3_auc_saturacion.csv")
    df = df[~df["variable"].str.startswith("REFERENCIA")]
    salida = {}
    for servicio, sub in df.groupby("servicio"):
        sub = sub.assign(fuerza=np.abs(sub["auc"] - 0.5)).sort_values("fuerza", ascending=False).head(top)
        salida[servicio] = sub[["variable", "auc"]].to_dict("records")
    return salida


def fig_senal_saturacion() -> go.Figure:
    datos = senal_saturacion(6)
    fig = base(320)
    for servicio, color in (("hospitalizacion", COLOR["azul"]), ("urgencias_observacion", COLOR["cian"])):
        filas = datos[servicio][::-1]
        fig.add_trace(go.Bar(
            y=[f["variable"].replace("_", " ") for f in filas], x=[f["auc"] for f in filas], orientation="h",
            name=SERVICIO[servicio], marker_color=color, marker_line_width=0,
            hovertemplate="%{y}<br>AUC: %{x:.3f}<br><span style='color:#A7B5C9'>" + SERVICIO[servicio] + "</span><extra></extra>",
        ))
    fig.add_vline(x=0.5, line=dict(color=COLOR["texto_2"], dash="dot", width=1))
    fig.update_xaxes(range=[0, 1], title="AUC frente a saturación en t + 4 h (una sola variable)")
    fig.update_layout(barmode="group", margin=dict(l=190, r=20, t=30, b=46), bargap=0.3)
    return fig


def fig_utilizacion() -> go.Figure:
    """Utilización ρ = L / c por año y fracción de horas sobre el 95 % (M3 · colas_por_anio)."""
    df = cargar.tabla("m3/tablas/colas_por_anio.csv")
    fig = base(320)
    for servicio, color in (("hospitalizacion", COLOR["azul"]), ("urgencias_observacion", COLOR["cian"])):
        sub = df[df["servicio"] == servicio]
        fig.add_trace(go.Bar(
            x=sub["anio"].astype(str), y=sub["frac_095"], name=f"{SERVICIO[servicio]} · horas ≥ 95 %",
            marker_color=color, opacity=0.35, marker_line_width=0, yaxis="y2",
            hovertemplate="%{x}: %{y:.0%} de las horas sobre el 95 %<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=sub["anio"].astype(str), y=sub["rho"], name=f"{SERVICIO[servicio]} · utilización ρ",
            mode="lines+markers", line=dict(color=color, width=2.6), marker=dict(size=8),
            hovertemplate="%{x}: ρ = %{y:.1%}<extra></extra>",
        ))
    fig.update_layout(
        barmode="group", bargap=0.35, margin=dict(l=56, r=56, t=70, b=36), legend=dict(y=1.04, font=dict(size=10)),
        yaxis=dict(title="utilización ρ = L / c", tickformat=".0%", range=[0.6, 1.0]),
        yaxis2=dict(title="horas sobre el 95 %", tickformat=".0%", overlaying="y", side="right", range=[0, 1.6],
                    showgrid=False, tickfont=dict(color=COLOR["texto_2"])),
    )
    return fig


def fig_disponibilidad() -> go.Figure:
    """Lugares libres en promedio: capacidad estimada c menos censo medio L, por año (M3)."""
    df = cargar.tabla("m3/tablas/colas_por_anio.csv")
    fig = base(300)
    for servicio, color in (("hospitalizacion", COLOR["azul"]), ("urgencias_observacion", COLOR["cian"])):
        sub = df[df["servicio"] == servicio]
        libres = sub["c"] - sub["L"]
        fig.add_trace(go.Bar(
            x=sub["anio"].astype(str), y=libres, name=SERVICIO[servicio], marker_color=color, marker_line_width=0,
            text=[f"{v:.0f}" for v in libres], textposition="outside", textfont=dict(color=COLOR["texto"]),
            customdata=np.stack([sub["c"], sub["L"]], axis=1),
            hovertemplate="%{x}<br>c = %{customdata[0]:.0f} · L = %{customdata[1]:.0f}<br>libres: %{y:.0f}<extra></extra>",
        ))
    fig.update_yaxes(title="lugares libres en promedio (c − L)", rangemode="tozero")
    fig.update_layout(barmode="group", bargap=0.35, margin=dict(l=56, r=10, t=40, b=36))
    return fig


def fig_turnos() -> go.Figure:
    """Fracción de horas saturadas por turno, en días hábiles y no hábiles (M4 visual · turnos)."""
    df = cargar.tabla("m4_visual/tablas/turnos.csv")
    orden = ["mañana", "tarde", "noche"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=[SERVICIO["hospitalizacion"], SERVICIO["urgencias_observacion"]],
                        shared_yaxes=True, horizontal_spacing=0.06)
    for i, servicio in enumerate(("hospitalizacion", "urgencias_observacion"), start=1):
        for no_habil, nombre, color in ((False, "día hábil", COLOR["azul"] if i == 1 else COLOR["cian"]),
                                        (True, "no hábil", COLOR["gris"])):
            sub = df[(df["servicio"] == servicio) & (df["no_habil"] == no_habil)].set_index("turno").loc[orden]
            fig.add_trace(go.Bar(
                x=orden, y=sub["frac_sat"], name=nombre, legendgroup=nombre, showlegend=i == 1,
                marker_color=color, marker_line_width=0,
                hovertemplate="%{x} · " + nombre + "<br>%{y:.0%} de las horas saturadas<extra></extra>",
            ), row=1, col=i)
    fig.update_yaxes(tickformat=".0%", range=[0, 0.8])
    fig.update_layout(height=300, barmode="group", bargap=0.3, margin=dict(l=48, r=10, t=56, b=30),
                      legend=dict(y=1.12, font=dict(size=10)))
    for a in fig.layout.annotations:
        a.font = dict(color=COLOR["texto"], size=12)
    return fig
