"""Sección 04 · Inteligencia operativa: resumen de toda la plataforma en tres niveles.

1. ¿Qué está sucediendo?   → datos observados (EDA, M2–M4)
2. ¿Qué podría suceder?     → estimaciones del modelo (M6–M7)
3. ¿Qué decisiones se pueden evaluar? → comparación de políticas en la prueba temporal (M7.2)

No repite los gráficos de detalle: los resume y enlaza a ellos. No recomienda acciones automáticas:
la plataforma evalúa políticas de alerta, no asigna camas ni traslados.
"""
from __future__ import annotations

from dash import html

from plataforma.componentes import chip, etiqueta_tipo, grafico, seccion
from plataforma.datos import cargar
from plataforma.datos.indicadores import cifras, es
from plataforma.graficos import operativa as g


def _mini(valor: str, texto: str, clase: str = "") -> html.Div:
    return html.Div([html.B(valor), html.Span(texto)], className=f"mini-kpi {clase}".strip())


def _cabecera(num: str, titulo: str, sub: str, tipo: str) -> html.Div:
    return html.Div(className="nivel-cabecera", children=[
        html.Span(num, className="nivel-num"),
        html.Div([html.H3(titulo), html.P([etiqueta_tipo(tipo), " ", sub])]),
    ])


def operativa() -> html.Section:
    c = cifras()
    calib = cargar.tabla("m7/tablas/m7_2_calibracion_prueba.csv")
    calib = calib[(calib["modelo"] == "lightgbm") & (calib["version"] == "isotonic")].set_index("servicio")
    esc = cargar.escenarios_decision("lightgbm")["hospitalizacion"]
    bloq = cargar.tabla("m3/tablas/bloqueo_urg_hosp_por_ocupacion.csv")

    politicas = [
        ("Nunca alertar", "0,0 %", "0", es(esc["costo_nunca"]), ""),
        ("Regla actual θ = 0,5", f"{es(esc['A']['sensibilidad'] * 100, 1)} %", es(esc["A"]["alertas_100"], 1), es(esc["A"]["costo_100"]), "actual"),
        ("Alertar a todos", "100 %", "100", es(esc["costo_alertar_todos"]), ""),
        (f"Política θ* = {es(esc['B']['umbral'], 2)}", f"{es(esc['B']['sensibilidad'] * 100, 1)} %", es(esc["B"]["alertas_100"], 1),
         es(esc["B"]["costo_100"]), "optima"),
    ]

    return seccion(
        "operativa", "04", "Inteligencia operativa",
        ["La situación del hospital ", html.Em("en una sola vista.")],
        "Un resumen de toda la plataforma en tres niveles: lo que los datos muestran que sucede, lo que el modelo estima "
        "que podría suceder y las decisiones que se pueden evaluar con esas estimaciones.",
        html.Div(className="operativa-niveles", children=[
            # 1 · Observado
            html.Div(className="nivel revelar", children=[
                _cabecera("1", "¿Qué está sucediendo?", "histórico 2023–2026", "observado"),
                html.Div(className="mini-kpis", children=[
                    _mini(f"{es(c['ocupacion_hosp'] * 100, 0)} %", "ocupación media de hospitalización (capacidad estimada)", "cian"),
                    _mini(f"{es(c['horas_saturadas_hosp'] * 100, 0)} %", "de las horas hospitalización supera el 95 %", "naranja"),
                    _mini(f"{es(c['estancia_p50_hosp'], 0)} h", "estancia mediana en hospitalización", "cian"),
                    _mini(f"{es(bloq['p75_h'].iloc[0], 0)}→{es(bloq['p75_h'].iloc[-1], 0)} h",
                          "espera P75 de urgencias a cama, de hospital vacío a lleno", "naranja"),
                ]),
                html.Div(className="panel", children=[
                    html.P("Ocupación media por hora del día · línea punteada = umbral de saturación", className="panel-fuente"),
                    grafico("g-op-perfil", g.fig_perfil_horario()),
                ]),
                html.A("Ver el análisis completo → 2.3", href="#multivariado", className="enlace-detalle"),
            ]),
            # 2 · Estimado
            html.Div(className="nivel revelar", children=[
                _cabecera("2", "¿Qué podría suceder?", "riesgo estimado por paciente", "estimado"),
                html.Div(className="mini-kpis", children=[
                    _mini(f"{es(calib.loc['hospitalizacion', 'p_media'] * 100, 0)} %",
                          f"probabilidad media estimada en hospitalización (real: {es(calib.loc['hospitalizacion', 'prevalencia'] * 100, 0)} %)", "azul"),
                    _mini(f"{es(calib.loc['urgencias_observacion', 'p_media'] * 100, 0)} %",
                          f"probabilidad media estimada en urgencias (real: {es(calib.loc['urgencias_observacion', 'prevalencia'] * 100, 0)} %)", "azul"),
                    _mini(f"{es(c['theta_hosp'] * 100, 0)} %", "umbral de alerta en hospitalización", "azul"),
                    _mini(f"{es(c['auc_prueba'], 3)}", "AUC en la prueba temporal (0,5 = azar)", "azul"),
                ]),
                html.Div(className="panel", children=[
                    html.P("Proporción observada de estancias largas según el momento de evaluación", className="panel-fuente"),
                    grafico("g-op-riesgo", g.fig_riesgo_tau()),
                ]),
                html.P("Las probabilidades son estimaciones, no hechos: el modelo ordena bien a los pacientes por riesgo, "
                       "pero no anuncia con certeza quién tendrá una estancia larga.", className="nota-pie"),
                html.A("Ver cómo funciona el modelo → 03", href="#como-funciona", className="enlace-detalle"),
            ]),
            # 3 · Decisiones evaluables
            html.Div(className="nivel revelar", children=[
                _cabecera("3", "¿Qué decisiones se pueden evaluar?", "políticas de alerta en hospitalización", "simulado"),
                html.Div(className="panel", children=[
                    html.P(f"Prueba temporal única (n = {es(esc['n'], 0)}) · alertas y costo por cada 100 pacientes · costo 5:1", className="panel-fuente"),
                    html.Div(className="tabla-scroll", children=html.Table(className="tabla tabla-politicas", children=[
                        html.Thead(html.Tr([html.Th(x) for x in ("Política", "Detecta", "Alertas", "Costo")])),
                        html.Tbody([html.Tr([html.Td(a), html.Td(b, className="mono"), html.Td(d, className="mono"), html.Td(e, className="mono")],
                                            className=k) for a, b, d, e, k in politicas]),
                    ])),
                ]),
                html.Div(className="mini-kpis", children=[
                    _mini(f"−{es(c['reduccion_costo'] * 100, 0)} %", "costo esperado frente a la regla actual", "verde"),
                    _mini(f"−{es(c['ahorro_vs_sin_modelo'] * 100, 0)} %", "frente a la mejor estrategia sin modelo", "verde"),
                ]),
                html.P("La plataforma compara políticas de alerta con resultados reales de la prueba; no asigna camas ni "
                       "traslados. La decisión final sigue siendo del equipo clínico y operativo.", className="nota-pie"),
                html.A("Ver resultados e impacto → 05", href="#resultados", className="enlace-detalle"),
            ]),
        ]),
        html.Div(style={"marginTop": "16px"}, children=chip("Observado = datos históricos · Estimado = salida del modelo · "
                                                              "Simulado = evaluación de políticas o escenarios", "")),
    )
