# HUN · Flujo Inteligente — dashboard del Data Challenge HUN

Presentación interactiva (Dash + Three.js + GSAP) con los resultados de los módulos M2–M7 del Data Challenge del Hospital Universidad del Norte.

- `plataforma/`: la aplicación (ver `plataforma/README.md`).
- `outputs/`: **solo resultados agregados** (tablas y figuras). No hay datos de pacientes, modelos ni credenciales.

Local: `pip install -r requirements.txt` y `python -m plataforma.app` → http://127.0.0.1:8050

Despliegue: Render (plan gratuito) con `render.yaml` (`gunicorn plataforma.app:server`).
