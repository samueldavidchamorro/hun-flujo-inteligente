"""Navegación fija y sección de inicio (hero con la escena 3D del hospital)."""
from __future__ import annotations

from dash import html

from plataforma.datos.indicadores import cifras, es

SECCIONES = [
    ("inicio", "01", "Inicio"),
    ("datos", "02", "EDA"),
    ("modelo", "03", "Modelo"),
    ("operativa", "04", "Operativa"),
    ("resultados", "05", "Resultados"),
    ("cierre", "06", "Cierre"),
]

FLECHA_ABAJO = html.Span(
    "↓", **{"aria-hidden": "true"}, style={"fontSize": "1.1em", "lineHeight": 1, "display": "inline-block"}
)


def navegacion() -> html.Div:
    return html.Div([
        html.Div(className="progreso", id="progreso", **{"aria-hidden": "true"}),
        html.Nav(className="nav", id="nav", **{"aria-label": "Secciones"}, children=[
            html.A(href="#inicio", className="marca", children=[
                html.Span(className="marca-icono", children=html.Span("+", style={"fontWeight": 700, "fontSize": "18px", "lineHeight": 1})),
                html.Span(["HUN · Flujo Inteligente", html.Small("Data Challenge")]),
            ]),
            html.Ul(className="nav-enlaces", id="nav-enlaces", children=[
                html.Li(html.A([html.Span(n), t], href=f"#{s}", **{"data-ir": s})) for s, n, t in SECCIONES
            ]),
            html.Button("Menú", className="boton nav-menu", id="nav-menu", **{"aria-expanded": "false", "aria-controls": "nav-enlaces"}),
        ]),
    ])


def inicio() -> html.Section:
    c = cifras()
    return html.Section(id="inicio", className="seccion hero", **{"data-seccion": "inicio"}, children=[
        html.Div(id="escena-hero", className="hero-escena", **{"aria-hidden": "true"}),
        html.Div(className="contenedor hero-contenido", children=[
            html.P("Hospital Universidad del Norte · Barranquilla", className="antetitulo hero-entrada"),
            html.H1(className="hero-titulo", children=[
                html.Span(html.Span("Flujo"), className="linea"),
                html.Span(html.Span("hospitalario"), className="linea"),
                html.Span(html.Span("inteligente.", className="acento"), className="linea"),
            ]),
            html.Div(className="hero-pie", children=[
                html.Div([
                    html.P("Transformamos los datos hospitalarios en inteligencia predictiva para anticipar riesgos, "
                           "comprender los cuellos de botella y apoyar mejores decisiones sobre el flujo de pacientes.",
                           className="hero-sub hero-entrada"),
                    html.P(
                        f"Con {es(c['visitas'], 0)} visitas reales y una ocupación hospitalaria del "
                        f"{es(c['ocupacion_hosp'] * 100, 0)} % de su capacidad estimada, el reto no es solo contar camas: "
                        "es saber hoy qué paciente se va a quedar más tiempo y qué servicio se va a llenar en las próximas 4 horas.",
                        className="hero-problema hero-entrada",
                    ),
                    html.Ul(className="hero-retos hero-entrada", children=[
                        html.Li(t) for t in ("Disponibilidad de camas", "Distribución entre servicios",
                                             "Esperas en urgencias", "Cuellos de botella", "Uso de recursos")
                    ]),
                    html.Div(style={"marginTop": "32px"}, className="hero-entrada", children=html.A(
                        [html.Span("Explorar la solución"), FLECHA_ABAJO], href="#datos", className="cta", **{"data-ir": "datos"},
                    )),
                ]),
                html.Div(className="hero-cifras hero-entrada", children=[
                    html.Div([html.B(es(c["visitas"] / 1e6, 2) + " M"), html.Span("visitas analizadas (2023–2026)")], className="hero-cifra"),
                    html.Div([html.B(es(c["tasa_larga"] * 100, 0) + " %"), html.Span("de las estancias supera el P75 de su servicio")], className="hero-cifra"),
                    html.Div([html.B(es(c["horas_saturadas_hosp"] * 100, 0) + " %"), html.Span("de las horas, hospitalización opera por encima del 95 % de su capacidad estimada")], className="hero-cifra"),
                    html.Div([html.B("4"), html.Span("servicios reales: ambulatorio, ingreso a urgencias, observación y hospitalización")], className="hero-cifra"),
                ]),
            ]),
        ]),
        html.Div("Desplázate", className="hero-indicador", **{"aria-hidden": "true"}),
    ])


def planteamiento() -> html.Section:
    """Problema, objetivos y solución: el manifiesto se ilumina palabra por palabra con el scroll."""
    c = cifras()
    manifiesto = (f"Hospitalización opera al {es(c['ocupacion_hosp'] * 100, 0)} % de su capacidad estimada y una de cada "
                  "cuatro estancias supera lo normal de su servicio. La pregunta no es si el hospital se va a llenar, "
                  "sino quién se va a quedar y cuándo.")
    columnas = [
        ("Problema", [
            f"Las camas de hospitalización casi nunca sobran: en promedio quedan unos {es(c['capacidad_hosp'] - c['l_hosp'], 0)} "
            "lugares libres frente a la capacidad estimada.",
            "Una estancia larga no avisa: con la regla de 0,5 solo 1 de cada 7 se detecta a tiempo.",
            "Cuando el hospital está lleno, los pacientes que suben desde urgencias esperan más.",
        ]),
        ("Objetivos", [
            "Predecir, en las primeras 0, 2 y 6 h, si una estancia superará el P75 de su servicio.",
            "Anticipar si urgencias u hospitalización llegarán a su umbral de ocupación en 4 h.",
            "Convertir la predicción en una regla de alerta con costos explícitos.",
        ]),
        ("Solución", [
            "Comprender: 1,46 M de visitas analizadas para ubicar patrones, esperas y cuellos de botella.",
            "Predecir: LightGBM calibrado, validado por paciente y probado una sola vez en el futuro.",
            "Optimizar: un umbral de alerta por servicio que minimiza el costo de errar (5:1), evaluado en un gemelo digital.",
        ]),
    ]
    return html.Section(id="planteamiento", className="seccion planteamiento", **{"data-seccion": "inicio"}, children=[
        html.Div(className="contenedor", children=[
            html.P("01 · Planteamiento", className="antetitulo revelar"),
            html.P([html.Span(p + " ", className="palabra") for p in manifiesto.split(" ")], className="manifiesto"),
            html.Div(className="planteamiento-columnas", children=[
                html.Div(className="planteamiento-col revelar", children=[
                    html.Span(f"0{i + 1}", className="numero-sub"),
                    html.H3(titulo),
                    html.Ul([html.Li(t) for t in items]),
                ]) for i, (titulo, items) in enumerate(columnas)
            ]),
        ]),
    ])
