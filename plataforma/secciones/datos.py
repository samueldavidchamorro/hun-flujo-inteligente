"""Sección 02 · EDA (COMPRENDER): univariado, variables importantes, multivariado, atípicos y decisiones de datos.

Cada panel lleva como título el hallazgo que muestra el gráfico (respaldado por las cifras de outputs/)
y, en los gráficos clave, una interpretación en tres partes: qué observamos, hallazgo, por qué importa.
"""
from __future__ import annotations

import numpy as np
from dash import html

from plataforma.componentes import grafico, panel, seccion, segmento
from plataforma.datos import cargar
from plataforma.datos.indicadores import cifras, es
from plataforma.graficos import eda
from plataforma.secciones.pipeline import pipeline
from plataforma.secciones.recorrido import recorrido

SUBSECCIONES = [
    ("univariado", "2.1", "Univariado"),
    ("importantes", "2.2", "Variables importantes"),
    ("multivariado", "2.3", "Multivariado y flujo"),
    ("atipicos", "2.4", "Atípicos"),
    ("pipeline", "2.5", "Decisiones de datos"),
]

SERVICIOS_TABLA = [{"label": "Hospitalización", "value": "Hospitalización"},
                   {"label": "Urgencias / obs.", "value": "Urgencias / observación"}]


def _cabecera(numero: str, titulo: str, texto: str) -> html.Div:
    return html.Div(className="bloque-cabecera revelar", children=[
        html.Div([html.Span(numero, className="numero-sub"), html.H3(titulo, className="subtitulo")]),
        html.P(texto),
    ])


def _univariado() -> html.Div:
    c = cifras()
    q = cargar.tabla("m2/tablas/los_cuantiles.csv").set_index("servicio")
    p99_dias = q.loc["Hospitalización", "p99_h"] / 24
    return html.Div(id="univariado", className="bloque", children=[
        _cabecera("2.1", "¿Cómo se distribuye cada variable?",
                  "La estancia es la variable central: de ella sale el objetivo. Después, cada variable que el modelo "
                  "conoce en el momento de la evaluación (τ = 0 h), por servicio."),
        html.Div(className="apilar", children=[
            panel(
                "¿Cuánto dura una estancia?",
                "M2 · los_cuantiles.csv · periodo estable",
                grafico("g-cuantiles-estancia", eda.fig_cuantiles_estancia()),
                hallazgo="Hospitalización se mide en días y urgencias en horas: cada servicio necesita su propio umbral de estancia larga",
                tipo="observado",
                interpretacion=(
                    "Los percentiles P10 a P99 de la estancia de cada servicio y, en naranja, el umbral P75 aprendido en entrenamiento.",
                    f"En hospitalización la mediana es {es(c['estancia_p50_hosp'])} h y el 1 % más largo supera los "
                    f"{es(p99_dias, 0)} días; en urgencias / observación el {es(c['los_cero_urg'], 0)} % de los registros dura 0 h.",
                    "Un umbral único en horas mezclaría servicios incomparables. Con el P75 de cada servicio, «estancia larga» "
                    "significa lo mismo en ambos: el cuarto de pacientes que más tiempo ocupa una cama o una camilla.",
                ),
            ),
            html.Div(className="rejilla-12-7", children=[
                panel(
                    "¿La estancia cambia con el tiempo?",
                    "M2 · los_por_mes.csv · la banda azul marca el periodo estable",
                    grafico("g-estancia-mes", eda.fig_estancia_por_mes()),
                    [html.Strong("Por eso la partición es temporal (corte 2025-07-13): "),
                     "el modelo se prueba en un periodo que no vio, con más estancias largas que en entrenamiento."],
                    hallazgo="Las estancias se alargaron entre 2023 y 2025: el P75 de hospitalización sube", tipo="observado",
                ),
                panel(
                    "¿Qué tan frecuentes son las estancias largas?",
                    "M2 · balance_episodio.csv",
                    grafico("g-balance", eda.fig_balance()),
                    ["Es el 25 % por construcción en entrenamiento (es el P75) y un 28 % en prueba: "
                     "la proporción crece con el tiempo, igual que la estancia."],
                    hallazgo="Una de cada cuatro estancias es larga, y en el periodo de prueba son más", tipo="observado",
                ),
            ]),
            panel(
                "Explora cada variable de entrada",
                "M2 · univariado_snapshot_tau0.csv · caja = P25–P75, línea = mediana, bigote = P99, ◆ = máximo",
                html.Div([segmento("sel-variable", eda.opciones_variables(), "n_dx_30d"),
                          grafico("g-variable"), html.Div(id="estadisticos-variable")]),
                id_lectura="lectura-variable", tipo="observado",
            ),
        ]),
    ])


def _importantes() -> html.Div:
    return html.Div(id="importantes", className="bloque", children=[
        _cabecera("2.2", "¿Qué variables pesan más en la predicción?",
                  "Dos evidencias distintas: la importancia SHAP del modelo final (M7.3) y el tamaño de efecto "
                  "de cada variable por separado frente al objetivo (M3), con corrección de Benjamini-Hochberg."),
        html.Div(className="rejilla-2", children=[
            panel(
                "¿En qué se apoya el modelo LightGBM?",
                "M7.3 · m7_3_importancia_shap*.csv · color = dominio clínico",
                grafico("g-shap"),
                id_lectura="lectura-shap",
                hallazgo="La historia clínica pesa en ambos servicios; en hospitalización, también la presión del servicio",
                tipo="estimado",
                controles=segmento("sel-shap", [
                    {"label": "Global", "value": "global"},
                    {"label": "Hospitalización", "value": "Hospitalización"},
                    {"label": "Urgencias", "value": "Urgencias / observación"},
                ], "Hospitalización"),
            ),
            panel(
                "¿Qué variable, sola, separa mejor las estancias largas?",
                "M3 · bivariado_target_paciente.csv · gris = efecto despreciable",
                grafico("g-efectos"),
                ["Con cientos de miles de filas todo p-valor sale < 0,001, por eso se reporta el tamaño de efecto. "
                 "La señal está repartida entre muchas variables: por eso hace falta un modelo multivariable."],
                hallazgo="Ninguna variable sola basta: el efecto más fuerte es apenas «pequeño»", tipo="observado",
                controles=segmento("sel-efectos", [
                    {"label": "Hospitalización", "value": "hospitalizacion"},
                    {"label": "Urgencias", "value": "urgencias_observacion"},
                ], "hospitalizacion"),
            ),
        ]),
    ])


def _interp_dispersion() -> tuple:
    h = cargar.heatmaps_ocupacion()
    o_h, f_h = (np.array(h["hospitalizacion"][k]).ravel() for k in ("ocupacion", "frac_saturada"))
    o_u, f_u = (np.array(h["urgencias_observacion"][k]).ravel() for k in ("ocupacion", "frac_saturada"))
    r = min(np.corrcoef(o_h, f_h)[0, 1], np.corrcoef(o_u, f_u)[0, 1])
    return (
        "Cada punto es una franja de la semana típica (día × hora): su ocupación media frente a cuántas semanas terminó saturada.",
        f"La relación es casi lineal (correlación ≥ {es(r, 2)}). En hospitalización todas las franjas viven entre el "
        f"{es(o_h.min() * 100, 0)} % y el {es(o_h.max() * 100, 0)} %; urgencias va del {es(o_u.min() * 100, 0)} % al {es(o_u.max() * 100, 0)} %.",
        "La ocupación reciente es la señal más simple para anticipar saturación; por eso la ocupación en t − 1 es la mejor "
        "variable aislada para la tarea de saturación (sección 03).",
    )


def _multivariado() -> html.Div:
    c = cifras()
    return html.Div(id="multivariado", className="bloque", children=[
        _cabecera("2.3", "¿Qué patrones aparecen al cruzar variables?",
                  "Cuándo se llena cada servicio, cómo afecta la ocupación a la espera, qué variables son redundantes "
                  "y por dónde se mueven los pacientes."),
        html.Div(className="apilar", children=[
            panel(
                "¿Cuándo se llena cada servicio?",
                "M4 visual · heatmap_saturacion · ocupación = censo / capacidad proxy (P95 de 90 días)",
                grafico("g-heatmap"),
                id_lectura="lectura-heatmap",
                hallazgo="Cada servicio se llena a horas distintas: urgencias en la tarde, hospitalización en la mañana",
                tipo="observado",
                controles=html.Div([
                    segmento("sel-heatmap-servicio", [
                        {"label": "Hospitalización", "value": "hospitalizacion"},
                        {"label": "Urgencias / obs.", "value": "urgencias_observacion"},
                    ], "urgencias_observacion"),
                    segmento("sel-heatmap-medida", [
                        {"label": "Ocupación", "value": "ocupacion"},
                        {"label": "Horas saturadas", "value": "frac_saturada"},
                    ], "ocupacion"),
                ], className="control-fila"),
            ),
            panel(
                "¿Una franja más ocupada se satura más a menudo?",
                "M4 visual · 168 franjas día × hora por servicio · tamaño = llegadas por hora · líneas = umbral de saturación",
                grafico("g-dispersion", eda.fig_dispersion_franjas()),
                hallazgo="Cuanto más ocupada está una franja, más semanas termina saturada", tipo="observado",
                interpretacion=_interp_dispersion(),
            ),
            html.Div(className="rejilla-2", children=[
                panel(
                    "¿Un hospital lleno retiene pacientes en urgencias?",
                    "M3 · bloqueo_urg_hosp_por_ocupacion.csv · visitas que entran por urgencias y terminan hospitalizadas",
                    grafico("g-bloqueo", eda.fig_bloqueo()),
                    hallazgo="Con el hospital lleno, quienes suben desde urgencias esperan más", tipo="observado",
                    interpretacion=(
                        "Horas desde la llegada a urgencias hasta la cama de hospitalización, según la ocupación hospitalaria al llegar.",
                        f"El P75 pasa de {es(c['bloqueo_p75_bajo'])} h a {es(c['bloqueo_p75_alto'])} h entre el decil menos "
                        "y el más ocupado; la mediana cambia poco.",
                        "La ocupación de hospitalización se transmite hacia urgencias: liberar camas a tiempo arriba acorta la espera abajo.",
                    ),
                ),
                panel(
                    "¿Qué variables dicen lo mismo?",
                    "M3 · colinealidad_spearman_07.csv · solo los pares con |ρ| ≥ 0,7",
                    grafico("g-colinealidad", eda.fig_colinealidad()),
                    ["Los conteos de diagnósticos son redundantes entre sí, y el censo con la ocupación. "
                     "M5 condensa los diagnósticos con una SVD y no duplica la ocupación de t − 1."],
                    hallazgo="Varias variables repiten la misma información", tipo="observado",
                ),
            ]),
            panel(
                "¿Cómo se mueve un paciente por el hospital?",
                "M4 · matriz de transición real · M3 · duración por etapa, esperas y colas",
                recorrido(),
                hallazgo="La presión se concentra en hospitalización; urgencias acumula pacientes en las tardes",
                tipo="observado",
            ),
            panel(
                "¿Por dónde pasan todas las visitas?",
                "M4 · rutas de visita reales · cada visita se cuenta una sola vez por barra",
                grafico("g-rutas", eda.fig_rutas()),
                ["Las pocas visitas que pasan por observación y hospitalización son las que ocupan camas durante días."],
                hallazgo="Dos de cada tres visitas son ambulatorias, y cuatro de cada cinco salen tras una sola etapa", tipo="observado",
            ),
        ]),
    ])


def _atipicos() -> html.Div:
    return html.Div(id="atipicos", className="bloque", children=[
        _cabecera("2.4", "¿Qué se hizo con los valores extremos?",
                  "Decisión del proyecto: no se recortó ni se eliminó ningún valor. Los extremos son pacientes reales "
                  "con historias largas. Los conteos asimétricos pasan por log1p (M5.4) y los modelos finales son de árboles."),
        html.Div(className="rejilla-2", children=[
            panel(
                "Antes y después de la transformación log1p",
                "M2 · cuantiles reales · línea roja = Q3 + 1,5·IQR (regla de Tukey)",
                html.Div([segmento("sel-atipicos", [o for o in eda.opciones_variables() if o["value"] in eda.VARIABLES_LOG1P],
                                   "n_dx_30d"), grafico("g-atipicos")]),
                id_lectura="lectura-atipicos",
                hallazgo="Los extremos se conservan: log1p los acerca al resto sin borrarlos", tipo="observado",
                controles=segmento("sel-atipicos-servicio", SERVICIOS_TABLA, "Hospitalización"),
            ),
            panel(
                "¿Qué tan larga es la cola de cada conteo?",
                "M2 · univariado_snapshot_tau0.csv",
                html.Div(id="tabla-colas", className="tabla-scroll"),
                [html.Strong("Máx / P99"), " mide cuánto se aleja el extremo del 1 % superior. Recortar en el P99 "
                 "borraría a los pacientes con más historia clínica, que son justo los de más riesgo."],
                hallazgo="Algunos conteos llegan a 10–14 veces su P99", tipo="observado",
            ),
        ]),
    ])


def datos() -> html.Section:
    return seccion(
        "datos", "02", "EDA · Comprender",
        ["Lo que los datos ", html.Em("realmente"), " dicen."],
        "Antes de predecir hay que comprender. Cinco preguntas: cómo se distribuye cada variable, cuáles importan, qué "
        "patrones aparecen al cruzarlas (incluido el recorrido del paciente y sus cuellos de botella), qué hacer con los "
        "extremos y cómo todo eso se convirtió en variables para el modelo.",
        html.Nav(className="subnav", **{"aria-label": "Subsecciones del análisis"}, children=[
            html.A([html.Span(n), t], href=f"#{i}", **{"data-sub": i}) for i, n, t in SUBSECCIONES
        ]),
        _univariado(), _importantes(), _multivariado(), _atipicos(), pipeline(),
    )
