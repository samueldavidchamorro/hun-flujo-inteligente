"""Callbacks de Dash: interacción de los paneles analíticos y del pipeline."""
from __future__ import annotations

import numpy as np
from dash import ALL, Input, Output, callback, ctx, html

from plataforma.componentes import estadisticos
from plataforma.config import SERVICIO
from plataforma.datos import cargar
from plataforma.datos.indicadores import es
from plataforma.graficos import eda
from plataforma.graficos import resultados as g
from plataforma.secciones import pipeline as sec_pipeline

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


@callback(
    Output("g-variable", "figure"), Output("estadisticos-variable", "children"), Output("lectura-variable", "children"),
    Input("sel-variable", "value"),
)
def actualizar_variable(variable):
    df = eda.resumen_variable(variable)
    hosp = df[df["servicio"] == "Hospitalización"].iloc[0]
    urg = df[df["servicio"] == "Urgencias / observación"].iloc[0]
    dec = 2 if variable.startswith("ocupacion") else 0
    pares = [
        ("Mediana hosp.", es(hosp["mediana"], dec)), ("Mediana urg.", es(urg["mediana"], dec)),
        ("P99 hosp.", es(hosp["p99"], dec)), ("% en cero hosp.", es(hosp["% cero"], 1) + " %"),
        ("Asimetría hosp.", es(hosp["asimetría"], 1)), ("Asimetría urg.", es(urg["asimetría"], 1)),
    ]
    asim = max(abs(hosp["asimetría"]), abs(urg["asimetría"]))
    if asim > 3:
        lectura = [html.Strong("Muy asimétrica a la derecha. "),
                   f"El máximo llega a {es(max(hosp['máx'], urg['máx']), 0)} mientras la mediana es "
                   f"{es(hosp['mediana'], dec)} en hospitalización: por eso entra al modelo con log1p (sección 2.4)."]
    elif abs(hosp["mediana"] - urg["mediana"]) > 0.2 * max(abs(hosp["mediana"]), 1e-9):
        lectura = [html.Strong("Los servicios son distintos. "),
                   f"Mediana {es(hosp['mediana'], dec)} en hospitalización frente a {es(urg['mediana'], dec)} en "
                   "urgencias: el modelo necesita saber el servicio para interpretar el valor."]
    else:
        lectura = [html.Strong("Distribución contenida y parecida entre servicios. "),
                   "Entra al modelo con imputación por mediana y estandarización."]
    return eda.fig_variable(variable), estadisticos(pares), lectura


@callback(Output("g-shap", "figure"), Output("lectura-shap", "children"), Input("sel-shap", "value"))
def actualizar_shap(alcance):
    if alcance == "global":
        df = cargar.tabla("m7/tablas/m7_3_importancia_shap.csv")
    else:
        df = cargar.tabla("m7/tablas/m7_3_importancia_shap_por_servicio.csv")
        df = df[df["servicio"] == alcance]
    top = df.sort_values("media_abs_shap", ascending=False).head(3)
    nombres = ", ".join(f"{e.lower()} ({es(p, 0)} %)" for e, p in zip(top["etiqueta"], top["porcentaje"]))
    if alcance == "global":
        lectura = [html.Strong("En el ranking global dominan el servicio y τ, "),
                   "por cómo se define el objetivo (cada servicio tiene su P75 y su prevalencia). "
                   "Las rankings por servicio muestran lo clínico."]
    else:
        lectura = [html.Strong(f"En {alcance.lower()} pesan más: "), nombres + "."]
    return eda.fig_shap(alcance), lectura


@callback(Output("g-efectos", "figure"), Input("sel-efectos", "value"))
def actualizar_efectos(servicio):
    return eda.fig_efectos(servicio)


@callback(
    Output("g-heatmap", "figure"), Output("lectura-heatmap", "children"),
    Input("sel-heatmap-servicio", "value"), Input("sel-heatmap-medida", "value"),
)
def actualizar_heatmap(servicio, medida):
    z = np.array(cargar.heatmaps_ocupacion()[servicio][medida])
    d, h = np.unravel_index(np.argmax(z), z.shape)
    d_min, h_min = np.unravel_index(np.argmin(z), z.shape)
    nombre = "la ocupación media" if medida == "ocupacion" else "la fracción de horas saturadas"
    lectura = [html.Strong(f"Pico: {DIAS[d]} a las {h:02d}:00 ({es(z[d, h] * 100, 0)} %). "),
               f"Valle: {DIAS[d_min]} a las {h_min:02d}:00 ({es(z[d_min, h_min] * 100, 0)} %). ",
               f"En {SERVICIO[servicio].lower()}, {nombre} sigue un ciclo diario marcado: "
               "las alertas deben mirar la hora, no solo el día."]
    return eda.fig_heatmap_ocupacion(servicio, medida), lectura


@callback(
    Output("g-atipicos", "figure"), Output("lectura-atipicos", "children"), Output("tabla-colas", "children"),
    Input("sel-atipicos", "value"), Input("sel-atipicos-servicio", "value"),
)
def actualizar_atipicos(variable, servicio):
    f = eda.resumen_variable(variable)
    f = f[f["servicio"] == servicio].iloc[0]
    iqr = f["p75"] - f["p25"]
    limite = f["p75"] + 1.5 * iqr
    iqr_log = np.log1p(f["p75"]) - np.log1p(f["p25"])
    limite_log = np.log1p(f["p75"]) + 1.5 * iqr_log
    sobre = "el P99 y el máximo quedan por encima" if f["p99"] > limite else "el P99 queda dentro"
    sobre_log = "el máximo sigue fuera" if np.log1p(f["máx"]) > limite_log else "todo queda dentro"
    lectura = [html.Strong(f"En escala original {sobre} del límite de Tukey ({es(limite, 0)}). "),
               f"Tras log1p {sobre_log}, pero la distancia se comprime: de {es(f['máx'] / max(f['mediana'], 1), 0)} "
               f"veces la mediana a {es(np.log1p(f['máx']) / max(np.log1p(f['mediana']), 1e-9), 1)} veces. "
               "Ninguna fila se eliminó."]
    t = eda.tabla_colas(servicio)
    filas = [html.Tr([
        html.Td(eda.ETIQUETA_VARIABLE.get(r["variable"], r["variable"])),
        html.Td(es(r["mediana"], 0)), html.Td(es(r["p99"], 0)), html.Td(es(r["máx"], 0)),
        html.Td(es(r["asimetría"], 1)), html.Td("—" if np.isnan(r["max_sobre_p99"]) else es(r["max_sobre_p99"], 1) + "×"),
    ], style={"background": "var(--azul-suave)"} if r["variable"] == variable else None) for _, r in t.iterrows()]
    tabla = html.Table(className="tabla", children=[
        html.Thead(html.Tr([html.Th(x) for x in ("Variable", "Mediana", "P99", "Máx", "Asimetría", "Máx / P99")])),
        html.Tbody(filas),
    ])
    return eda.fig_atipicos(variable, servicio), lectura, tabla


@callback(
    Output("detalle-etapa", "children"), Output({"tipo": "etapa", "indice": ALL}, "className"),
    Input({"tipo": "etapa", "indice": ALL}, "n_clicks"),
)
def elegir_etapa(_clics):
    activa = ctx.triggered_id["indice"] if isinstance(ctx.triggered_id, dict) else 0
    clases = ["etapa activa" if i == activa else ("etapa hecha" if i < activa else "etapa") for i in range(7)]
    return sec_pipeline.detalle(activa), clases


@callback(
    Output("g-confusion", "figure"), Output("g-estrategias", "figure"),
    Output("lectura-confusion", "children"), Output("lectura-estrategias", "children"),
    Input("sel-resultado-servicio", "value"),
)
def actualizar_resultados(servicio):
    e = cargar.escenarios_decision("lightgbm")[servicio]
    a, b = e["A"], e["B"]
    if servicio == "hospitalizacion":
        lectura_c = [html.Strong(f"Las estancias largas sin alerta bajan de {es(a['fn_100'])} a {es(b['fn_100'])} por cada 100. "),
                     f"A cambio, las alertas preventivas sin estancia larga suben de {es(a['fp_100'])} a {es(b['fp_100'])}: "
                     "un aviso de más cuesta menos que una cama bloqueada sin planear."]
    else:
        lectura_c = [html.Strong("En urgencias / observación θ* alerta casi a todos. "),
                     f"La prevalencia en prueba es {es(e['prevalencia'] * 100, 0)} %: con costo 5:1, avisar siempre es casi óptimo "
                     "y el modelo apenas cambia la decisión."]
    mejor = min(e["costo_alertar_todos"], e["costo_nunca"])
    ahorro = 1 - b["costo_100"] / mejor
    lectura_e = [html.Strong(f"Política θ*: {es(b['costo_100'])} por 100. "),
                 f"Regla 0,5: {es(a['costo_100'])}. Mejor estrategia sin modelo: {es(mejor)}. "
                 + (f"El modelo ahorra {es(ahorro * 100, 0)} % sobre esa referencia." if ahorro > 0.005
                    else "Aquí el modelo no mejora a la referencia sin modelo.")]
    return g.fig_confusion(servicio), g.fig_estrategias(servicio), lectura_c, lectura_e
