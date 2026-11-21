# Plataforma · HUN Flujo Inteligente

Presentación interactiva del Data Challenge: análisis exploratorio, pipeline de variables, gemelo digital 3D del flujo, modelo y resultados. **Todas las cifras salen de `outputs/`** (M2–M7); no hace falta `data/` ni la VPN.

## Ejecutar

Desde la raíz del proyecto (`JupyterHUN-main/`):

```bash
pip install -r plataforma/requirements.txt
python -m plataforma.app
```

Abrir <http://127.0.0.1:8050>. Necesita internet para las librerías de cliente (Three.js r128, GSAP 3.13.0 con SplitText, fuentes); sin red el análisis funciona y el 3D muestra su aviso.

| Variable de entorno | Defecto | Uso |
|---|---|---|
| `HUN_PLATAFORMA_PUERTO` | 8050 | puerto |
| `HUN_PLATAFORMA_DEBUG` | 0 | `1` activa recarga y depuración de Dash |
| `HUN_OUTPUTS` | `<raíz>/outputs` | carpeta de resultados |

Durante una presentación: **→** pasa a la sección siguiente y **←** a la anterior; **↑ ↓** desplazan la página como siempre; las teclas **1–6** saltan directo a una sección (Inicio, EDA, Modelo, Operativa, Resultados, Cierre). Las animaciones están activas por defecto (también con "reducir movimiento" del sistema); `?movimiento=0` en la URL las desactiva.

## Estructura

| Ruta | Responsabilidad |
|---|---|
| `app.py` | Dash, layout y ruta `/api/gemelo` |
| `config.py` | rutas, paleta, variables de entorno |
| `datos/cargar.py` | lectura de `outputs/` (CSV, JSON y los datos dentro de los HTML de M4 visual) |
| `datos/indicadores.py` | cifras citadas en los textos, calculadas (ninguna escrita a mano) |
| `datos/gemelo.py` | datos del gemelo 3D y qué es real / ilustrativo |
| `graficos/` | tema Plotly oscuro, gráficos de EDA y de resultados |
| `secciones/` | layout de cada sección: inicio, EDA (`datos.py`, `pipeline.py`, `recorrido.py`), modelo, inteligencia operativa (`operativa.py`), resultados y cierre |
| `secciones/recorrido.py` | recorrido del paciente con transiciones reales y regla explícita de cuellos de botella |
| `graficos/operativa.py` | gráficos compactos del panel de inteligencia operativa |
| `callbacks.py` | interacción de los paneles y del pipeline |
| `assets/css/` | sistema de diseño: tokens (paleta v1.2 con contraste AA), base, secciones, pulido y `40_v12.css` (paneles con hallazgo, interpretación, tipo de dato, recorrido, operativa) |
| `assets/js/10_campus3d.js` | edificio 3D del inicio y del cierre |
| `assets/js/30_gemelo.js` | gemelo digital: camas, pacientes, escenarios, inspector |
| `assets/js/40_scroll.js` | navegación, revelado con GSAP ScrollTrigger, contadores |

## Qué es real y qué es ilustrativo

- **Real:** ocupación y llegadas por día × hora (M4 visual), transiciones entre servicios (M4), λ, W, L y capacidad proxy (M1/M3), tasas por 100 de la regla θ = 0,5 y de la política θ* en la prueba temporal única (M7.2), métricas, SHAP y calibración (M6, M7).
- **Ilustrativo (y así se rotula en pantalla):** el plano y el edificio (no hay planos del HUN), la cantidad de camas dibujadas (cada una ≈ c/N lugares de la capacidad estimada) y qué paciente concreto tiene alerta o estancia larga (se sortea con las tasas reales; el mismo paciente en A y en B).

## Pendiente (no se inventó)

- **Camillas:** no hay datos de camillas ni de traslados. El "flujo de camillas" se representa con camas y pacientes en tránsito.
- **Modelo de saturación por servicio:** no está entrenado en el proyecto. Se muestra la señal disponible (AUC de la ocupación en t − 1, M5.3). Cuando exista, basta con añadir sus tasas a `datos/gemelo.py`.
- **Camas reales:** con `config/capacidad_camas.csv` (ver `docs/M1_contrato_datos.md`) la ocupación dejaría de ser un proxy.

## Convenciones de diseño (v1.2)

- **Semántica de color:** azul = interactivo · cian = dato / información · verde = favorable · naranja = advertencia · rojo = crítico · gris = neutral. El escenario A (regla actual) es gris; el B (política óptima) es verde.
- **Tipo de dato:** cada panel lleva una etiqueta "Dato observado", "Estimación del modelo" o "Simulación ilustrativa".
- **Paneles:** el título es el hallazgo; la pregunta queda como antetítulo. Los gráficos clave terminan en "Qué observamos · Hallazgo · Por qué importa".
- **Modo captura:** `?captura=<id>` muestra solo ese bloque, sin pantalla de carga (para generar imágenes de documentación).
