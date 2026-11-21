"""Sección 03 · Modelo: gemelo digital 3D + cómo funciona el modelo.

El gemelo (assets/js/30_gemelo.js) lee /api/gemelo, que sirve datos reales de
outputs/ (ver plataforma/datos/gemelo.py). Los controles son HTML normal: el
JavaScript les añade los eventos, Dash no interviene en la animación.
"""
from __future__ import annotations

from dash import html

from plataforma.componentes import chip, grafico, panel, seccion
from plataforma.datos.indicadores import cifras, es
from plataforma.graficos import resultados

ESTADOS = [
    ("var(--verde)", "Disponible"),
    ("var(--azul)", "Ocupada"),
    ("var(--cian)", "En tránsito"),
    ("var(--naranja)", "Alerta: estancia larga prevista"),
    ("var(--rojo)", "Estancia larga sin alerta"),
    ("var(--gris-claro)", "Consultorio (sin estancia)"),
]


def _gemelo() -> html.Div:
    return html.Div(className="gemelo revelar", children=[
        html.Div(id="gemelo-lienzo", className="gemelo-lienzo", **{"data-escenario": "B"}, children=[
            html.Div("Cargando gemelo digital…", className="gemelo-cargando"),
            html.Div(className="gemelo-sin-webgl", children=html.Div([
                html.P("Este navegador no tiene WebGL disponible.", style={"color": "var(--texto)", "fontWeight": 600}),
                html.P("Los indicadores del panel lateral siguen funcionando: salen de los mismos datos."),
            ])),
            html.Div(id="gemelo-etiquetas", className="gemelo-etiquetas", **{"aria-hidden": "true"}),
            html.Div(className="gemelo-reloj", children=[html.Span("Lun 00:00", id="gemelo-reloj", className="reloj"),
                                                         html.Span("semana típica", className="etiqueta")]),
            html.Div(id="gemelo-escenario", className="gemelo-escenario", **{"aria-live": "polite"}),
            html.Div(className="gemelo-leyenda", children=[
                html.Span([html.I(className="punto", style={"background": c}), t]) for c, t in ESTADOS
            ]),
            html.Div(className="gemelo-camara", children=[
                html.Button("Perspectiva", id="cam-perspectiva", className="boton", **{"aria-pressed": "true"}),
                html.Button("Cenital", id="cam-cenital", className="boton", **{"aria-pressed": "false"}),
            ]),
        ]),
        html.Div(className="gemelo-panel", children=[
            html.Div(className="panel", children=[
                html.Div(className="grupo-control", children=[
                    html.P("1 · Política de alerta", className="control-titulo"),
                    html.Div(className="control-fila", children=[
                        html.Button([html.B("A · Regla actual"), html.Small("alerta si p ≥ 0,5")],
                                    id="esc-a", className="boton escenario-boton", **{"aria-pressed": "false"}),
                        html.Button([html.B("B · Política óptima"), html.Small("alerta si p ≥ θ* del servicio")],
                                    id="esc-b", className="boton escenario-boton", **{"aria-pressed": "true"}),
                    ]),
                    html.P(id="que-cambia", className="que-cambia"),
                    html.Div(id="metricas-escenario", className="metricas-escenario", style={"marginTop": "12px"}),
                    html.P(id="nota-escenario", className="nota-pie", style={"marginTop": "10px"}),
                ]),
            ]),
            html.Div(className="panel", children=[
                html.Div(className="grupo-control", children=[
                    html.P("2 · Tiempo · semana típica", className="control-titulo"),
                    html.Div(className="control-fila", children=[
                        html.Button("Iniciar", id="sim-iniciar", className="boton primario"),
                        html.Button("Pausar", id="sim-pausar", className="boton", disabled=True),
                        html.Button("Reiniciar", id="sim-reiniciar", className="boton"),
                    ]),
                    # El control deslizante lo crea 30_gemelo.js (así React no lo reescribe al moverlo desde JS)
                    html.Div(id="sim-hora-contenedor"),
                    html.Div(className="control-fila velocidades", children=[
                        html.Span("Velocidad", className="nota-pie", style={"alignSelf": "center", "marginRight": "4px"}),
                        *[html.Button(f"{v}×", className="boton", **{"data-velocidad": str(v), "aria-pressed": "true" if v == 1 else "false"})
                          for v in (0.5, 1, 2, 4)],
                    ]),
                ]),
                html.Details(className="guia-simulacion", children=[
                    html.Summary("Cómo leer esta simulación"),
                    html.Ul([
                        html.Li("Cada hora muestra la ocupación real promedio de esa franja de la semana (M4); las camas se llenan y vacían para seguirla."),
                        html.Li("Los puntos son llegadas reales por hora (1 punto ≈ 20 visitas) que siguen las probabilidades de transición reales."),
                        html.Li("Al cambiar de A a B, los pacientes son los mismos: solo cambia la regla que decide a quién alertar."),
                        html.Li("Naranja = alerta (estancia larga prevista). Rojo = estancia larga que la regla no detectó: el error que más cuesta."),
                    ]),
                ]),
            ]),
            html.Div(className="panel inspector", children=[
                html.P("3 · Inspector", className="control-titulo"),
                html.Div(id="inspector", children=html.P("Haz clic en una cama o en un paciente para ver su estado.", className="vacio")),
            ]),
        ]),
        html.P("Simulación ilustrativa con tasas reales de ocupación, llegadas y alertas; el plano no es el del HUN.",
               className="nota-gemelo"),
    ])


def _nodo(titulo: str, texto: str, clase: str = "", flecha: str = "", extra=None) -> html.Div:
    """Caja del diagrama. flecha = der | izq | abajo indica hacia dónde sale el flujo."""
    return html.Div(className=f"flujo-nodo {clase}".strip(), **({"data-flecha": flecha} if flecha else {}), children=[
        html.B(titulo), html.Span(texto), extra,
    ])


def _diagrama() -> html.Div:
    """Cómo funciona el modelo, de la solicitud a la alerta. Las cifras salen de outputs/."""
    import json

    from plataforma.datos import cargar
    c = cifras()
    hp = json.loads(cargar.tabla("m6/model_benchmark_summary.csv").set_index("modelo").loc["lightgbm", "hiperparametros"])
    salida = len(cargar.tabla("m5/tablas/m5_4_variables_salida.csv"))
    ramas = html.Div(className="flujo-ramas", children=[
        html.Div([html.B("Numéricas"), html.Span("edad, horas, ocupación · 18")], className="flujo-rama"),
        html.Div([html.B("Conteos"), html.Span("diagnósticos, visitas, laboratorios · 10")], className="flujo-rama"),
        html.Div([html.B("Categóricas"), html.Span("servicio, turno, festivos, banderas · 34")], className="flujo-rama"),
        html.Div([html.B("Historia clínica"), html.Span("códigos de diagnóstico → 50 ejes")], className="flujo-rama"),
    ])
    return html.Div(className="flujo revelar", role="img",
                    **{"aria-label": "Flujo del modelo: paciente, preprocesador, LightGBM, calibración, umbral por servicio y alerta"},
                    children=[
        html.Div(className="flujo-marco", children=html.Span("ajustado solo con el entrenamiento de cada partición")),
        _nodo("Paciente al ingreso", "Lo que se sabe a las 0, 2 o 6 h: 63 datos, nunca información del futuro",
              "dato flujo-paciente", "der"),
        _nodo("Preprocesador", f"Ordena y limpia los datos en 4 ramas → {salida} variables", "modelo flujo-pre", "der", ramas),
        _nodo("LightGBM", f"{hp['modelo__n_estimators']} árboles de decisión que votan juntos y dan un puntaje de riesgo",
              "modelo flujo-lgbm", "abajo"),
        _nodo("Calibración", "Convierte el puntaje en una probabilidad real: si dice 30 %, ocurre cerca del 30 % de las veces",
              "modelo flujo-cal", "izq"),
        _nodo("Umbral por servicio",
              f"Avisa desde {es(c['theta_hosp'] * 100, 0)} % en hospitalización y {es(c['theta_urg'] * 100, 0)} % en urgencias: "
              "no avisar cuesta 5 veces más que avisar de más", "decide flujo-umbral", "izq"),
        _nodo("Alerta", "¿Esta estancia superará lo normal de su servicio? Sí / no", "dato flujo-alerta"),
    ])


def _como_funciona() -> html.Div:
    c = cifras()
    pasos = [
        ("1 · Mirar", "En cuanto el paciente ingresa, y otra vez a las 2 y 6 horas, el modelo toma lo que el hospital ya sabe de él: "
                      "edad, servicio, diagnósticos previos, laboratorios y qué tan lleno está el servicio."),
        ("2 · Estimar", f"Cientos de árboles de decisión combinan esas señales y estiman la probabilidad de que la estancia sea larga. "
                        f"En la prueba con datos que nunca vio separa bien los casos (AUC {es(c['auc_prueba'], 3)})."),
        ("3 · Decidir", f"La probabilidad se compara con un umbral elegido por costo. Con la regla habitual (50 %) solo se detecta el "
                        f"{es(c['sens_a'] * 100, 0)} % de las estancias largas de hospitalización; con el umbral óptimo, el "
                        f"{es(c['sens_b'] * 100, 0)} %."),
    ]
    return html.Div(id="como-funciona", className="como-funciona", children=[
        _diagrama(),
        html.Div(className="pasos-modelo", children=[
            html.Div([html.Span(t, className="numero-sub"), html.P(d)], className="paso-modelo revelar") for t, d in pasos
        ]),
        html.Div(className="panel revelar", children=[
            html.Div(className="rejilla-2", children=[
                html.Div([
                    html.H4("Cómo leer la solución", className="panel-pregunta"),
                    html.P(f"En hospitalización solo una de cada cuatro estancias es larga, así que casi ningún paciente supera el 50 %: "
                           f"por eso la regla habitual se pierde la mayoría. Bajar el umbral a {es(c['theta_hosp'] * 100, 0)} % "
                           "detecta casi todas, a cambio de más alertas preventivas.", className="lectura-texto"),
                    html.P("En urgencias / observación la mayoría de los pacientes ya tiene estancias largas a las 6 h, y con un "
                           "costo 5:1 lo óptimo es prácticamente avisar a todos. El modelo cambia decisiones donde importa: hospitalización.",
                           className="lectura-texto"),
                    html.P("Para la saturación del servicio, la mejor señal anticipada es la ocupación de la hora anterior. "
                           "El modelo de saturación por servicio no está entrenado todavía en el proyecto (queda para M8).",
                           className="lectura-texto", style={"color": "var(--texto-3)"}),
                ]),
                html.Div([
                    html.P("¿Qué variable anticipa la saturación en 4 horas?", className="panel-pregunta"),
                    html.P("M5.3 · m5_3_auc_saturacion.csv · capacidad de cada variable sola para separar (0,5 = azar)",
                           className="panel-fuente"),
                    grafico("g-senal-saturacion", resultados.fig_senal_saturacion()),
                ]),
            ]),
        ]),
    ])


def modelo() -> html.Section:
    return seccion(
        "modelo", "03", "Modelo · Predecir",
        ["Ver el hospital ", html.Em("antes"), " de que se llene."],
        "El modelo convierte lo que se sabe de cada paciente en una probabilidad de estancia larga, y una regla con "
        "costos explícitos convierte esa probabilidad en alerta. Primero, cómo funciona; después, un gemelo digital "
        "que muestra qué cambia en el hospital con cada regla.",
        html.H3("Cómo funciona el modelo", className="subtitulo revelar"),
        html.P("Del ingreso del paciente a la alerta, en seis pasos.", className="revelar",
               style={"color": "var(--texto-2)", "margin": "0 0 28px"}),
        _como_funciona(),
        html.Div(style={"height": "72px"}),
        html.H3("Gemelo digital: la regla actual frente a la política óptima", className="subtitulo revelar"),
        html.P("Ocupación, llegadas y rutas reales por hora de una semana típica, con la política de alertas aplicada a "
               "cada cama. Compara A y B sobre los mismos pacientes.", className="revelar",
               style={"color": "var(--texto-2)", "margin": "0 0 28px"}),
        _gemelo(),
    )
