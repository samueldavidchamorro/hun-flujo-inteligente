"""Sección 05 · Resultados e impacto (OPTIMIZAR), y sección 06 · Cierre."""
from __future__ import annotations

from dash import html

from plataforma.componentes import chip, grafico, panel, seccion, segmento
from plataforma.datos.indicadores import cifras, es
from plataforma.graficos import resultados as g


def _kpi(valor: float, decimales: int, sufijo: str, etiqueta: str, antes: str, detalle: str, clase: str = "",
         pista: tuple[float, float, float, str, str] | None = None, nombre: str = "", interpretacion: str = "") -> html.Div:
    """KPI animado: 40_scroll.js cuenta desde 0 hasta data-contar (respeta reduced-motion).

    pista = (valor antes, valor después, máximo de la escala, rótulo antes, rótulo después): barra comparativa.
    """
    barra = None
    if pista:
        a, b, maximo, rot_a, rot_b = pista
        barra = html.Div([
            html.Div(className="kpi-pista", children=[
                html.I(className="antes", style={"width": f"{100 * a / maximo:.1f}%"}),
                html.I(className="despues", style={"width": f"{100 * b / maximo:.1f}%"}, **{"data-pista": "1"}),
            ]),
            html.Div([html.Span(rot_a), html.Span(rot_b)], className="kpi-pista-leyenda"),
        ])
    return html.Div(className=f"kpi revelar {clase}".strip(), children=[
        html.Div(nombre, className="kpi-nombre") if nombre else None,
        html.Div(className="kpi-valor", children=[
            html.Span(es(valor, decimales), **{"data-contar": f"{valor:.6f}", "data-decimales": str(decimales)}),
            html.Small(sufijo),
        ]),
        html.Div(etiqueta, className="kpi-etiqueta"),
        barra,
        html.Div(antes, className="kpi-antes"),
        html.Div(detalle, className="kpi-detalle"),
        html.Div(interpretacion, className="kpi-interpretacion") if interpretacion else None,
    ])


def _operacion() -> html.Div:
    """Línea base operativa: espera, uso de camas, disponibilidad y eficiencia por turno (M3, M4)."""
    from plataforma.datos import cargar
    esp = cargar.tabla("m3/tablas/esperas_transiciones.csv")
    obs_hosp = esp[(esp["desde"] == "urgencias_observacion") & (esp["hacia"] == "hospitalizacion")].iloc[0]
    bloq = cargar.tabla("m3/tablas/bloqueo_urg_hosp_por_ocupacion.csv")
    anio = cargar.tabla("m3/tablas/colas_por_anio.csv")
    h = anio[anio["servicio"] == "hospitalizacion"].set_index("anio")
    return html.Div(id="operacion", className="operacion", children=[
        html.Div(className="bloque-cabecera revelar", children=[
            html.Div([html.Span("Línea base operativa", className="numero-sub"),
                      html.H3("Espera, uso de camas y disponibilidad", className="subtitulo")]),
            html.P("El estado actual que la política de alertas busca anticipar. Son mediciones de la operación real "
                   "(2023–2026), no simulaciones: el modelo no cambia estos números por sí solo, cambia cuándo se entera el hospital."),
        ]),
        html.Div(className="espera-fichas revelar", children=[
            html.Div(className="espera-ficha", children=[
                html.Span("Llegada a urgencias → cama de hospitalización", className="numero-sub"),
                html.B(f"{es(bloq['mediana_h'].min(), 0)}–{es(bloq['mediana_h'].max(), 0)} h"),
                html.P("mediana según la ocupación hospitalaria al llegar"),
            ]),
            html.Div(className="espera-ficha", children=[
                html.Span("El 25 % que más espera", className="numero-sub"),
                html.B(f"{es(bloq['p75_h'].iloc[0], 0)} → {es(bloq['p75_h'].iloc[-1], 0)} h"),
                html.P("P75 con el hospital menos y más lleno (deciles 1 y 10)"),
            ]),
            html.Div(className="espera-ficha", children=[
                html.Span("Observación → hospitalización", className="numero-sub"),
                html.B(f"{es(obs_hosp['espera_p90_h'], 1)} h"),
                html.P(f"P90 del hueco entre etapas ({es(obs_hosp['n'], 0)} traslados); la mediana es 0 h"),
            ]),
            html.Div(className="espera-ficha", children=[
                html.Span("Utilización hospitalaria", className="numero-sub"),
                html.B(f"{es(h.loc[2023, 'rho'] * 100, 0)} → {es(h.loc[2025, 'rho'] * 100, 0)} %"),
                html.P("ρ = L / c entre 2023 y 2025, con un censo que crece"),
            ]),
        ]),
        html.Div(className="rejilla-3", children=[
            panel("¿Qué tan usadas están las camas?", "M3 · colas_por_anio.csv · barras = horas sobre el 95 %",
                  grafico("g-utilizacion", g.fig_utilizacion()),
                  [html.Strong("Hospitalización trabaja al límite todo el año. "),
                   "La utilización ronda el 90–94 % y entre un cuarto y casi la mitad de las horas supera el 95 % de la capacidad estimada."]),
            panel("¿Cuánto margen queda?", "M3 · capacidad estimada c menos censo medio L",
                  grafico("g-disponibilidad", g.fig_disponibilidad()),
                  [html.Strong("Unos 20–28 lugares en hospitalización. "),
                   "Es el margen frente al pico reciente (P95 de 90 días), no camas físicas vacías: por eso anticipar las altas importa."]),
            panel("¿Qué turno se satura más?", "M4 visual · turnos.csv · fracción de horas saturadas",
                  grafico("g-turnos", g.fig_turnos()),
                  [html.Strong("Hospitalización se satura en la mañana; urgencias, en la tarde de los días hábiles. "),
                   "Ahí es donde una alerta temprana da más margen para mover camas y altas."]),
        ]),
    ])


def resultados() -> html.Section:
    c = cifras()
    return seccion(
        "resultados", "05", "Resultados · Optimizar",
        ["Menos estancias largas ", html.Em("sin aviso.")],
        f"Todo lo que sigue sale de la prueba temporal única de M7.2: {es(c['n_prueba'], 0)} snapshots posteriores al "
        "corte de entrenamiento, evaluados una sola vez con umbrales congelados de antemano.",
        html.Div(className="kpis", children=[
            _kpi(c["sens_b"] * 100, 1, "%", "de las estancias largas de hospitalización reciben alerta",
                 f"Regla actual (θ = 0,5): {es(c['sens_a'] * 100, 1)} %", f"Con la política θ* = {es(c['theta_hosp'], 2)}, mismos pacientes.", "verde",
                 pista=(c["sens_a"] * 100, c["sens_b"] * 100, 100, "gris = regla 0,5", "color = θ*"),
                 nombre="Detección · hospitalización",
                 interpretacion="Mide cuántas estancias largas se anticipan. No es ahorro ni exactitud: es cobertura de la alerta."),
            _kpi(c["reduccion_costo"] * 100, 0, "%", "menos costo esperado que la regla θ = 0,5",
                 f"{es(c['costo_a'])} → {es(c['costo_b'])} por cada 100 pacientes", "Costo con c_FN = 5 y c_FP = 1 (M7.2).",
                 pista=(c["costo_a"], c["costo_b"], c["costo_a"], "costo regla 0,5", "costo θ*"),
                 nombre="Frente a la regla actual",
                 interpretacion="Compara dos usos del mismo modelo: cambiar el umbral basta para reducir el costo a la mitad."),
            _kpi(c["ahorro_vs_sin_modelo"] * 100, 0, "%", "menos costo que la mejor estrategia sin modelo",
                 f"Alertar a todos: {es(c['costo_alertar_todos'])} por 100", "Referencia sin modelo más barata en hospitalización.", "cian",
                 pista=(c["costo_alertar_todos"], c["costo_b"], c["costo_a"], "sin modelo", "con modelo"),
                 nombre="Frente a decidir sin modelo",
                 interpretacion="Es el valor que aporta predecir: lo que se ahorra frente a avisar a todos sin mirar el riesgo."),
            _kpi(c["auc_prueba"], 3, "", "AUC-ROC de LightGBM calibrado en la prueba",
                 f"Validación cruzada: {es(c['auc_oof'], 3)}", f"Dentro de servicio × τ: {es(c['auc_oof_estrato'], 3)} (OOF).",
                 pista=(0.5, c["auc_prueba"], 1.0, "azar = 0,5", "modelo"),
                 nombre="Capacidad de ordenar el riesgo",
                 interpretacion="Probabilidad de que un paciente con estancia larga reciba más riesgo que uno sin ella. 1 = perfecto."),
        ]),
        html.Div(className="rejilla-2", children=[
            panel(
                "¿Qué pasa con 100 pacientes en cada escenario?",
                "M7.2 · m7_2_umbrales_prueba.csv · prueba temporal única",
                grafico("g-confusion"),
                id_lectura="lectura-confusion",
                controles=segmento("sel-resultado-servicio", [
                    {"label": "Hospitalización", "value": "hospitalizacion"},
                    {"label": "Urgencias / obs.", "value": "urgencias_observacion"},
                ], "hospitalizacion"),
            ),
            panel(
                "¿Cuánto cuesta cada estrategia?",
                "M7.2 · costo esperado por 100 snapshots · prueba",
                grafico("g-estrategias"),
                id_lectura="lectura-estrategias",
            ),
        ]),
        html.Div(style={"height": "20px"}),
        html.Div(className="rejilla-3", children=[
            panel(
                "¿Dónde está el umbral óptimo?",
                "M7.2 · barrido de umbral en OOF calibrado (desarrollo)",
                grafico("g-costo-umbral", g.fig_costo_umbral()),
                [html.Strong("La curva es casi plana hasta 0,3 y se dispara después. "),
                 "Con un falso negativo 5 veces más caro, subir el umbral a 0,5 ahorra pocas alertas y deja escapar "
                 "muchas estancias largas: el costo pasa de unos 44 a 96 por cada 100."],
            ),
            panel(
                "¿Qué modelo gana?",
                "M6.4 · model_benchmark_summary.csv · 7 familias, mismos pliegues",
                grafico("g-modelos", g.fig_modelos()),
                [html.Strong("LightGBM gana a los otros 6 "), "(DeLong por conglomerados de paciente, M7.4). "
                 "Frente a Random Forest la diferencia es significativa pero pequeña (ΔAUC = 0,005)."],
            ),
            panel(
                "¿Las probabilidades son creíbles?",
                "M7.2 · m7_2_calibracion_prueba.csv · LightGBM",
                grafico("g-calibracion", g.fig_calibracion()),
                [html.Strong("Casi: la calibración isotónica se ajustó en desarrollo, "),
                 "y en la prueba la prevalencia subió (28 % hospitalización). El modelo la subestima unos puntos: "
                 "hay que recalibrar periódicamente en producción."],
            ),
        ]),
        _operacion(),
        html.Div(className="impacto revelar", children=[
            html.Div([
                chip("Impacto potencial · no observado", "ilustrativo"),
                html.H3("Qué puede hacer el hospital con una alerta temprana"),
                html.P("Estos beneficios son potenciales: la evaluación es retrospectiva sobre datos históricos. "
                       "Demostrar una reducción real de esperas o estancias exige un piloto en la operación."),
            ]),
            html.Ul(className="impacto-lista", children=[
                html.Li([html.B("Planificar capacidad"), "Saber en las primeras horas qué pacientes probablemente ocuparán la cama varios días."]),
                html.Li([html.B("Gestionar disponibilidad"), "Preparar altas y traslados con anticipación en el servicio que opera al 93 % de su capacidad estimada."]),
                html.Li([html.B("Anticipar acumulaciones"), "La espera de urgencias a cama crece cuando hospitalización está llena: liberar camas a tiempo ayuda aguas abajo."]),
                html.Li([html.B("Decidir con costos explícitos"), "El umbral se elige con una relación de costos (5:1) que el hospital puede revisar y ajustar."]),
            ]),
        ]),
        html.Div(className="resumen-ejecutivo", children=[
            html.Div(className="panel revelar", children=[
                html.H4("Para la dirección médica"),
                html.P(f"Con la política θ*, 9 de cada 10 estancias largas de hospitalización se identifican en las primeras "
                       f"horas del ingreso, frente a 1 de cada 7 con la regla de 0,5. Eso da días de margen para planear camas y altas."),
            ]),
            html.Div(className="panel revelar", children=[
                html.H4("Para operaciones"),
                html.P("Hospitalización opera cerca de su capacidad estimada y se satura sobre todo en la mañana; urgencias / "
                       "observación se llena en la tarde, con el pico el martes entre las 14 y las 17 h. Identificar estos cuellos de botella permite asignar recursos con "
                       "información en lugar de intuición."),
            ]),
            html.Div(className="panel revelar", children=[
                html.H4("El costo de la decisión"),
                html.P(f"Más detección implica más alertas: {es(c['alertas_b'], 0)} de cada 100 pacientes de hospitalización "
                       f"reciben una, frente a {es(c['alertas_a'], 0)} con la regla actual. La política elige ese equilibrio "
                       "con un costo explícito (5:1) que el hospital puede ajustar."),
            ]),
        ]),
    )


def cierre() -> html.Section:
    c = cifras()
    return html.Section(id="cierre", className="seccion cierre", **{"data-seccion": "cierre"}, children=[
        html.Div(id="escena-cierre", className="cierre-escena", **{"aria-hidden": "true"}),
        html.Div(className="contenedor", children=[
            html.P("06 · Conclusiones", className="antetitulo revelar"),
            html.H2(["Lo que deja ", html.Em("este trabajo.")], className="titulo-seccion revelar"),
            html.Div(className="conclusiones", children=[
                html.Div(className="conclusion revelar", children=[
                    html.Span("01 · Hallazgos", className="numero-sub"),
                    html.H3("El hospital tiene patrones claros"),
                    html.P(f"Hospitalización opera al {es(c['ocupacion_hosp'] * 100, 0)} % de su capacidad estimada y se satura en la mañana; "
                           f"urgencias cae a {es(c['urg_festivo'], 0)} llegadas en festivos y sube a {es(c['urg_tras_festivo'], 0)} al día siguiente; "
                           "un hospital lleno alarga la espera en urgencias."),
                ]),
                html.Div(className="conclusion revelar", children=[
                    html.Span("02 · Aporte del modelo", className="numero-sub"),
                    html.H3("Predicción calibrada y una regla explícita"),
                    html.P(f"LightGBM calibrado (AUC {es(c['auc_prueba'], 3)} en la prueba) y la política θ* con costo 5:1 elevan la detección "
                           f"de estancias largas de {es(c['sens_a'] * 100, 0)} % a {es(c['sens_b'] * 100, 0)} % en hospitalización."),
                ]),
                html.Div(className="conclusion revelar", children=[
                    html.Span("03 · Beneficio operativo", className="numero-sub"),
                    html.H3("Días de margen para planear camas"),
                    html.P("La alerta llega en las primeras horas del ingreso, cuando aún se puede planear el alta, el traslado "
                           "y la cama del siguiente paciente, justo en los turnos que más se saturan."),
                ]),
                html.Div(className="conclusion revelar", children=[
                    html.Span("04 · Valor para el hospital", className="numero-sub"),
                    html.H3("Una base lista para producción"),
                    html.P(f"{es(c['ahorro_vs_sin_modelo'] * 100, 0)} % menos costo esperado que la mejor estrategia sin modelo, con un "
                           "pipeline anti-fuga que sirve tal cual en la API de M8. Faltan las camas reales y el modelo de saturación."),
                ]),
            ]),
            html.P(className="lema revelar", children=[
                html.Span("De los datos a la predicción."),
                html.Span("De la predicción a mejores decisiones."),
                html.Span("Hacia un flujo hospitalario más eficiente."),
            ]),
        ]),
    ])


def pie() -> html.Footer:
    return html.Footer(className="pie", children=html.Div(className="contenedor", children=[
        html.Span("Data Challenge HUN · Hospital Universidad del Norte"),
        html.Span("Fuentes: outputs/ de M2–M7 · sin datos por paciente"),
    ]))
