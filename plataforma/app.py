"""HUN · Flujo Inteligente — plataforma interactiva del Data Challenge.

Ejecutar desde la raíz del proyecto:

    python -m plataforma.app

y abrir http://127.0.0.1:8050. Dash sirve el análisis (Python) y la carpeta
assets/ trae el CSS, las escenas Three.js y las animaciones GSAP (JavaScript).
"""
from __future__ import annotations

import dash
from dash import html
from flask import jsonify

from plataforma import callbacks  # noqa: F401  (registra los callbacks)
from plataforma.config import DEBUG, PUERTO
from plataforma.datos import gemelo
from plataforma.secciones.datos import datos
from plataforma.secciones.inicio import inicio, navegacion, planteamiento
from plataforma.secciones.modelo import modelo
from plataforma.secciones.operativa import operativa
from plataforma.secciones.resultados import cierre, pie, resultados

# Librerías de cliente con versión fija (CDN). Se cargan antes que assets/.
SCRIPTS_EXTERNOS = [
    "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js",
    # Postprocesado (resplandor de luces y ventanas). El orden importa: EffectComposer define THREE.Pass.
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/CopyShader.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/LuminosityHighPassShader.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/EffectComposer.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/ShaderPass.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/RenderPass.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/UnrealBloomPass.js",
    # GSAP 3.13: desde esta versión todos los plugins (SplitText incluido) son gratuitos
    "https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js",
    "https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrollTrigger.min.js",
    "https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/SplitText.min.js",
]
ESTILOS_EXTERNOS = [
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@500;600;650;700"
    "&family=JetBrains+Mono:wght@400;500;600&display=swap",
]

app = dash.Dash(
    __name__,
    title="HUN · Flujo Inteligente",
    external_scripts=SCRIPTS_EXTERNOS,
    external_stylesheets=ESTILOS_EXTERNOS,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "Predicción de estancias largas y saturación hospitalaria · HUN"},
        {"name": "theme-color", "content": "#070B14"},
    ],
    update_title=None,
)
server = app.server


@server.route("/api/gemelo")
def api_gemelo():
    """Datos reales agregados que consume el gemelo digital 3D."""
    return jsonify(gemelo.carga_util())


app.layout = html.Div(id="plataforma", children=[
    # Pantalla de carga: la retira 05_cargador.js cuando la escena 3D dibuja su primer cuadro
    html.Div(id="cargador", className="cargador", **{"aria-hidden": "true"}, children=[
        html.Div(className="cargador-marca", children=[html.Span("+", className="marca-icono"),
                                                       html.Span("HUN · Flujo Inteligente")]),
        html.Div(className="cargador-barra", children=html.Span(id="cargador-progreso")),
        html.Span("Inicializando gemelo digital", className="cargador-texto"),
    ]),
    navegacion(),
    html.Main([inicio(), planteamiento(), datos(), modelo(), operativa(), resultados(), cierre()]),
    pie(),
])


if __name__ == "__main__":
    app.run(debug=DEBUG, port=PUERTO, host="127.0.0.1")
