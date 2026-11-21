"""Piezas de interfaz reutilizables (Dash html/dcc) del sistema de diseño."""
from __future__ import annotations

from dash import dcc, html

from plataforma.graficos.tema import CONFIG_GRAFICO

ICONO_INFO = html.Span(
    "i", **{"aria-hidden": "true"},
    style={"width": "16px", "height": "16px", "borderRadius": "50%", "border": "1px solid currentColor",
           "display": "inline-grid", "placeItems": "center", "fontSize": "10px", "fontWeight": 700,
           "fontFamily": "var(--fuente-mono)", "flex": "none", "color": "var(--cian)", "marginTop": "2px"},
)


def antetitulo(texto: str) -> html.P:
    return html.P(texto, className="antetitulo revelar")


def seccion(id_: str, numero: str, rotulo: str, titulo, entradilla: str | None, *hijos, clase: str = "") -> html.Section:
    return html.Section(
        id=id_, className=f"seccion {clase}".strip(), **{"data-seccion": id_},
        children=html.Div(className="contenedor", children=[
            html.Span(numero, className="numero-capitulo", **{"aria-hidden": "true"}),
            antetitulo(f"{numero} · {rotulo}"),
            html.H2(titulo, className="titulo-seccion revelar"),
            html.P(entradilla, className="entradilla revelar") if entradilla else None,
            *hijos,
        ]),
    )


ALTOS = {  # alto de los gráficos que llena un callback (deben coincidir con plataforma/graficos)
    "g-variable": 330, "g-shap": 480, "g-efectos": 370, "g-heatmap": 300, "g-atipicos": 230,
    "g-confusion": 300, "g-estrategias": 300,
}


def grafico(id_: str, figura=None, alto: int | None = None) -> dcc.Graph:
    """Gráfico con alto fijo: con responsive=True, Plotly toma el alto del contenedor."""
    alto = alto or (figura.layout.height if figura is not None else None) or ALTOS.get(id_)
    estilo = {"height": f"{alto}px"} if alto else {}
    # Sin figura inicial (la llena un callback) se pasa una figura vacía: con figure=None (el valor por
    # defecto) Dash 4 falla al leer su layout en isResponsive.
    figura = figura if figura is not None else {"data": [], "layout": {"height": alto}}
    return dcc.Graph(id=id_, figure=figura, config=CONFIG_GRAFICO, style=estilo)


def panel(pregunta: str, fuente: str, cuerpo, lectura=None, controles=None, clase: str = "", id_lectura: str | None = None,
          hallazgo=None, interpretacion=None, tipo: str | None = None) -> html.Div:
    """Panel de análisis.

    - Con `hallazgo`, el título es la conclusión que muestra el gráfico y la pregunta queda como antetítulo.
    - `interpretacion` = (qué observamos, hallazgo, por qué importa): bloque de lectura en tres partes.
    - `tipo` = "observado" | "estimado" | "simulado": etiqueta que distingue datos, predicciones y simulaciones.
    """
    titulos = [html.P(pregunta, className="panel-ojo"), html.H4(hallazgo, className="panel-hallazgo")] if hallazgo \
        else [html.P(pregunta, className="panel-pregunta")]
    cabecera = html.Div(className="cabecera-panel", children=[
        html.Div([*titulos, html.P([etiqueta_tipo(tipo) if tipo else None, fuente], className="panel-fuente")]),
        controles,
    ])
    lectura_div = None
    if lectura is not None or id_lectura:
        lectura_div = html.Div(lectura, className="lectura", id=id_lectura) if id_lectura else html.Div(lectura, className="lectura")
    interp = bloque_interpretacion(*interpretacion) if interpretacion else None
    return html.Div(className=f"panel revelar {clase}".strip(), children=[cabecera, cuerpo, lectura_div, interp])


TIPOS = {"observado": "Dato observado", "estimado": "Estimación del modelo", "simulado": "Simulación ilustrativa"}


def etiqueta_tipo(tipo: str) -> html.Span:
    """Distingue datos históricos, predicciones y simulaciones con el mismo código en toda la plataforma."""
    return html.Span(TIPOS[tipo], className=f"tipo-dato tipo-{tipo}")


def bloque_interpretacion(observamos, hallazgo, importa) -> html.Div:
    """Lectura en tres partes debajo de los gráficos clave."""
    partes = [("Qué observamos", observamos), ("Hallazgo", hallazgo), ("Por qué importa", importa)]
    return html.Div(className="interpretacion", children=[
        html.Div([html.Span(t, className="interp-rotulo"), html.P(x)], className="interp-parte") for t, x in partes
    ])


def segmento(id_: str, opciones: list[dict], valor) -> dcc.RadioItems:
    return dcc.RadioItems(id=id_, options=opciones, value=valor, className="segmento", inline=True)


def nota_datos(texto) -> html.Div:
    return html.Div([ICONO_INFO, html.Div(texto)], className="nota-datos revelar")


def estadisticos(pares: list[tuple[str, str]]) -> html.Div:
    return html.Div([html.Div([html.Span(k), html.B(v)], className="estadistico") for k, v in pares],
                    className="estadisticos")


def chip(texto: str, tipo: str = "") -> html.Span:
    return html.Span(texto, className=f"etiqueta {tipo}".strip())
