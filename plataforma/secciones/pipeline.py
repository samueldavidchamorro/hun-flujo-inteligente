"""Bloque 2.5 del EDA · De datos crudos a dataset listo para el modelo (pipeline interactivo).

El contenido de cada etapa resume lo que hicieron M1 y M5 (docs/M1_*.md,
modulo_5/README.md). Las cifras se toman de esos documentos y de outputs/.
"""
from __future__ import annotations

from dash import html

from plataforma.datos import cargar
from plataforma.datos.indicadores import es


def _calidad(tabla: str, chequeo_empieza: str) -> float:
    df = cargar.tabla("m2/tablas/calidad.csv")
    fila = df[(df["tabla"] == tabla) & (df["chequeo"].str.startswith(chequeo_empieza))].iloc[0]
    return float(fila["pct"])


def _faltante(variable: str) -> tuple[float, float]:
    df = cargar.tabla("m2/tablas/faltantes_snapshot.csv").set_index(cargar.tabla("m2/tablas/faltantes_snapshot.csv").columns[0])
    return float(df.loc[variable, "Hospitalización"]), float(df.loc[variable, "Urgencias / observación"])


def etapas() -> list[dict]:
    svd = cargar.tabla("m5/tablas/svd_varianza.csv")
    var_svd = float(svd["varianza_acumulada"].iloc[-1])
    salida = cargar.tabla("m5/tablas/m5_4_variables_salida.csv")
    f_hosp, f_urg = _faltante("horas_desde_ultima_alta_hosp")
    return [
        {
            "nombre": "Datos crudos",
            "titulo": "Tablas OMOP, leídas sin tocar el servidor",
            "resumen": "PostgreSQL uhn_i, esquema uninorte_omop, vía VPN. El servidor es de solo lectura: "
                       "se extrae con SELECT a parquet y todo se procesa en local con DuckDB.",
            "cifras": [("1,71 M", "visitas (visit_occurrence)"), ("3,28 M", "subprocesos (visit_detail)"),
                       ("38,6 M", "diagnósticos")],
            "hecho": "Extracción de person, visit_occurrence, visit_detail, condition_occurrence, measurement "
                     "y concept, solo con las columnas que usa el ETL (M1 y M5.0). procedure_occurrence no se "
                     "extrae: su fecha está vacía.",
            "porque": "El servidor no admite escritura y la VPN es lenta (~14.000 filas/s). Trabajar en local permite "
                      "repetir el ETL sin volver a extraer.",
            "variables": "Tablas completas; 16,6 M mediciones de laboratorio.",
            "cambio": "Del servidor a parquets locales (data/raw/), sin transformar.",
            "aporte": "Es la materia prima de las dos tareas: estancia del paciente y ocupación del servicio.",
        },
        {
            "nombre": "Limpieza",
            "titulo": "La estancia real estaba en otra tabla",
            "resumen": f"En el {es(_calidad('visit_occurrence', 'fin = inicio'), 0)} % de las visitas el fin es igual al inicio. "
                       "La estancia se reconstruye con visit_detail y se descartan los vínculos rotos.",
            "cifras": [(es(_calidad('visit_detail', 'vínculo a visita incoherente'), 1) + " %", "subprocesos con vínculo incoherente"),
                       (es(_calidad('condition_occurrence', 'person_id distinto'), 1) + " %", "diagnósticos de otra persona"),
                       ("4", "servicios reales")],
            "hecho": "Episodios desde visit_detail (columna los_h). Eventos con vínculo incoherente fuera "
                     "(vinculo_coherente). Solo el periodo estable 2023-01-31 → 2026-04-01.",
            "porque": "visit_occurrence_id apunta a la visita de otra persona en una parte de los registros. "
                      "Fuera del periodo estable la carga de datos cambia (censo subestimado y saltos).",
            "variables": "los_h, servicio, vinculo_coherente, en_periodo_estable, en_riesgo_truncamiento.",
            "cambio": "Tablas episodio, snapshot (τ = 0, 2, 6 h) y ocupacion_servicio_hora (M1).",
            "aporte": "Sin esta corrección toda estancia mediría 0 h y el objetivo no existiría.",
        },
        {
            "nombre": "Valores faltantes",
            "titulo": "Un faltante también es información",
            "resumen": f"«Horas desde la última alta» falta en el {es(f_hosp, 0)} % (hospitalización) y el {es(f_urg, 0)} % "
                       "(urgencias): no es un error, es que el paciente nunca estuvo hospitalizado.",
            "cifras": [("24", "banderas MNAR y de laboratorio"), ("20", "laboratorios con bandera has_measurement"),
                       ("10", "pares de sinónimos fusionados")],
            "hecho": "Banderas estructurales (sin_mediciones_24h, sin_mediciones_historia, sin_dx_historia, "
                     "nunca_hospitalizado) y has_measurement_X para los 20 laboratorios más frecuentes (M5.1). "
                     "Imputación por mediana (numéricas) o «Desconocido» (categóricas) dentro del Pipeline.",
            "porque": "La ausencia no es aleatoria (MNAR). La imputación se ajusta solo con entrenamiento para no "
                      "filtrar información de la prueba.",
            "variables": "horas_desde_ultima_alta_hosp, n_mediciones_*, n_dx_*, has_measurement_*.",
            "cambio": "+24 columnas binarias; ningún nulo llega al modelo.",
            "aporte": "El modelo distingue «sin datos» de «valor bajo».",
        },
        {
            "nombre": "Valores atípicos",
            "titulo": "Se conservan los extremos y se transforma la escala",
            "resumen": "No se recortó ningún valor. Los conteos con asimetría de 1,4 a 17 pasan por log1p, "
                       "y los modelos finales son de árboles, que no dependen de la escala.",
            "cifras": [("10", "conteos con log1p"), ("0", "filas eliminadas por atípicas"), ("38", "subprocesos > 90 días, conservados")],
            "hecho": "Rama num_log del ColumnTransformer: mediana → log1p → StandardScaler (M5.4). "
                     "La estancia de 0 h en urgencias se mantiene: es un registro puntual real.",
            "porque": "Los extremos son pacientes con historias clínicas largas, justo los de más riesgo. "
                      "Recortarlos borraría señal.",
            "variables": "n_dx_historia, n_dx_30d, n_visitas_365d, n_mediciones_*, llegadas, hospitalizaciones previas.",
            "cambio": "Mismas filas; escala comparable para modelos lineales, KNN y SVM.",
            "aporte": "Comparación justa entre las 7 familias de modelos de M6.",
        },
        {
            "nombre": "Ingeniería de variables",
            "titulo": "Historia clínica, calendario y presión del servicio",
            "resumen": f"3.625 códigos de diagnóstico se condensan en 50 componentes SVD ({es(var_svd * 100, 1)} % de la varianza). "
                       "Se añaden variables cíclicas, festivos de Colombia y la ocupación del servicio en t − 1.",
            "cifras": [("50", "componentes SVD de diagnósticos"), ("14", "variables de ocupación t − 1"), ("8/8", "verificaciones anti-fuga")],
            "hecho": "TruncatedSVD sobre TF-IDF de códigos (M5.2), seno/coseno de hora y día, turno, festivos y puentes, "
                     "ocupación media/máxima/tendencia en ventanas de 3 a 24 h con shift(1) antes de cada ventana (M5.3).",
            "porque": "Solo se usan eventos de la misma persona con fecha anterior a τ. La SVD se reajusta en cada pliegue.",
            "variables": "dx_codigos, hour_sin/cos, dow_sin/cos, es_festivo, tras_festivo, srv_ocupacion_*, srv_llegadas_*.",
            "cambio": "63 columnas de entrada listas para el preprocesador.",
            "aporte": "La presión del servicio y el perfil de diagnósticos están entre las variables de mayor peso SHAP.",
        },
        {
            "nombre": "Selección de variables",
            "titulo": "Fuera lo duplicado, lo vacío y lo que viene del futuro",
            "resumen": "No se duplican variables idénticas, los procedimientos quedan fuera (fecha vacía) y "
                       "ninguna columna y_* entra como predictor.",
            "cifras": [("ρ = 1,00", "srv_ocupacion_t1 = ocupación de M1 → una sola"), ("0", "columnas y_* como entrada"),
                       (str(len(salida)), "variables tras el preprocesador")],
            "hecho": "Se descartan srv_ocupacion_t1, srv_censo_t1 y srv_llegadas_t1 (idénticas a las de M1). "
                     "hora_del_dia y dia_semana se sustituyen por sus versiones cíclicas. procedure_date está vacío.",
            "porque": "Las variables duplicadas reparten la importancia y confunden la interpretación. "
                      "Las y_* son la etiqueta: usarlas sería fuga.",
            "variables": "Se conservan los conteos colineales de diagnósticos para los árboles; la SVD resume el resto.",
            "cambio": f"63 columnas de entrada → {len(salida)} tras OneHot, log1p y SVD.",
            "aporte": "Un modelo más estable y explicable por dominio clínico (SHAP agrupado).",
        },
        {
            "nombre": "Dataset listo",
            "titulo": "Listo para entrenar, validar y probar una sola vez",
            "resumen": "Partición temporal en 2025-07-13 y validación cruzada agrupada por paciente: "
                       "ningún paciente aparece a la vez en entrenamiento y validación.",
            "cifras": [("541.260", "snapshots de entrenamiento estable"), ("148.673", "snapshots de prueba"), ("5", "pliegues StratifiedGroupKFold")],
            "hecho": "Pipeline sin ajustar (pipeline_m5_4_plantilla.joblib) que M6 completa con cada modelo. "
                     "Los pliegues son los mismos para todos los modelos.",
            "porque": "La validación cruzada estratificada simple mezclaría snapshots del mismo paciente y sobrestimaría el AUC.",
            "variables": "Entrada: 63 columnas. Objetivo: y_target_los_largo.",
            "cambio": "Dataset final: X (snapshot × variables), y, grupos = person_id.",
            "aporte": "Es la entrada de LightGBM, de la calibración y de la política de alertas θ* de la sección siguiente.",
        },
    ]


def detalle(indice: int):
    e = etapas()[indice]
    return html.Div(className="detalle-etapa detalle-entrada", key=str(indice), children=[
        html.Div([
            html.Span(f"Etapa {indice + 1} de 7 · {e['nombre']}", className="numero-sub"),
            html.H3(e["titulo"]),
            html.P(e["resumen"], className="resumen"),
            html.Div(className="detalle-cifra", children=[
                html.Div([html.B(v), html.Span(t)]) for v, t in e["cifras"]
            ]),
        ]),
        html.Dl(className="detalle-campos", children=[
            html.Div([html.Dt(k), html.Dd(e[c])], className="detalle-campo") for k, c in (
                ("Qué se hizo", "hecho"), ("Por qué", "porque"), ("Variables", "variables"),
                ("Cambio en los datos", "cambio"), ("Aporte al modelo", "aporte"))
        ]),
    ])


def pipeline() -> html.Div:
    nombres = [e["nombre"] for e in etapas()]
    return html.Div(id="pipeline", className="bloque", children=[
        html.Div(className="bloque-cabecera revelar", children=[
            html.Div([html.Span("2.5", className="numero-sub"),
                      html.H3("De registros sueltos a variables con sentido clínico", className="subtitulo")]),
            html.P("Lo que el análisis anterior obligó a decidir: siete pasos llevaron las tablas del HUN a un dataset "
                   "listo para modelar. Elige una etapa para ver qué se hizo, por qué y qué cambió."),
        ]),
        html.Div(className="pipeline revelar", role="tablist", **{"aria-label": "Etapas del pipeline"}, children=[
            html.Div(className="pipeline-linea", **{"aria-hidden": "true"}),
            *[html.Button(
                [html.Span(f"{i + 1:02d}", className="etapa-nodo"), html.Span(n, className="etapa-nombre")],
                id={"tipo": "etapa", "indice": i}, className="etapa", n_clicks=0, role="tab",
            ) for i, n in enumerate(nombres)],
        ]),
        html.Div(id="detalle-etapa", className="panel revelar", children=detalle(0), **{"aria-live": "polite"}),
        transformacion(),
    ])


def transformacion() -> html.Div:
    """Diagrama del ColumnTransformer de M5.4: cuatro ramas → 124 variables."""
    salida = len(cargar.tabla("m5/tablas/m5_4_variables_salida.csv"))
    ramas = [
        ("num", "18", "Edad, horas desde ingreso y última alta, ocupación t − 1, cíclicas", "mediana → estandarizar"),
        ("num_log", "10", "Conteos asimétricos: diagnósticos, visitas, mediciones, llegadas", "mediana → log1p → estandarizar"),
        ("cat", "34", "Servicio, sexo, origen, turno, calendario, banderas MNAR y de laboratorio", "«Desconocido» → one-hot"),
        ("clinica", "1", "Códigos de diagnóstico previos a τ, como texto", "conteo binario → TF-IDF → SVD 50"),
    ]
    return html.Div(className="transformacion revelar", children=[
        html.Div(className="transformacion-cabecera", children=[
            html.Span("Pipeline de transformación · M5.4", className="numero-sub"),
            html.H3("Un solo objeto para entrenar, validar y servir", className="subtitulo"),
            html.P("Todo lo que se aprende de los datos (medianas, escalas, categorías, vocabulario y ejes de la SVD) "
                   "se ajusta dentro del Pipeline, solo con entrenamiento. El mismo objeto sirve en la validación cruzada "
                   "y en la API de M8."),
        ]),
        html.Div(className="transformacion-flujo", children=[
            html.Div(className="tf-entrada", children=[html.B("63"), html.Span("columnas de entrada")]),
            html.Div(className="tf-ramas", children=[
                html.Div(className="tf-rama", children=[
                    html.Div([html.Code(n), html.B(k)], className="tf-rama-cabeza"),
                    html.P(d), html.Span(t, className="tf-pasos"),
                ]) for n, k, d, t in ramas
            ]),
            html.Div(className="tf-salida", children=[html.B(str(salida)), html.Span("variables → LightGBM")]),
        ]),
    ])
