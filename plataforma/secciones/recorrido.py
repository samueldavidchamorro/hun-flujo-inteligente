"""Recorrido del paciente (EDA 2.3): diagrama horizontal con transiciones y cuellos de botella reales.

Cada cifra sale de outputs/:
  - Probabilidad de cada transición: m4_visual/tablas/matriz_transicion_prob.csv
  - Visitas: sankey_flujo (nodo de llegada)
  - Duración de cada etapa (subprocesos): m3/tablas/duracion_por_etapa.csv
  - Utilización ρ y horas sobre el 95 %: m3/tablas/resumen_colas_p1.csv, m2/tablas/balance_saturacion.csv
  - Espera observación → hospitalización: m3/tablas/esperas_transiciones.csv y bloqueo_urg_hosp_por_ocupacion.csv

Regla de clasificación (no basta la ocupación alta):
  cuello de botella  = ocupación media ≥ 90 %  Y  P90 de estancia > 24 h  Y  la espera para entrar crece con la ocupación
  punto de acumulación = ≥ 20 % de horas saturadas  pero estancias cortas (P90 ≤ 24 h)
  fluido             = estancia P90 < 1 h (registro o paso puntual)
"""
from __future__ import annotations

from dash import html

from plataforma.datos import cargar
from plataforma.datos.indicadores import cifras, es


def _pct(p: float) -> str:
    return f"{es(p * 100, 1)} %"


def _horas(h: float) -> str:
    if h < 1:
        return f"{es(h * 60, 0)} min"
    if h < 48:
        return f"{es(h, 1)} h"
    return f"{es(h / 24, 1)} días"


def datos_recorrido() -> dict:
    t = cargar.matriz_transicion()
    dur = cargar.tabla("m3/tablas/duracion_por_etapa.csv").set_index("servicio")
    colas = cargar.colas()
    sat = cargar.tabla("m2/tablas/balance_saturacion.csv")
    sat = sat[sat["particion"] == "entrenamiento"].set_index("servicio")["tasa"]
    esp = cargar.tabla("m3/tablas/esperas_transiciones.csv")
    obs_hosp = esp[(esp["desde"] == "urgencias_observacion") & (esp["hacia"] == "hospitalizacion")].iloc[0]
    bloq = cargar.tabla("m3/tablas/bloqueo_urg_hosp_por_ocupacion.csv")
    espera_crece = float(bloq["p75_h"].iloc[-1]) > float(bloq["p75_h"].iloc[0])

    def clasificar(servicio: str) -> str:
        p90 = float(dur.loc[servicio, "p90_h"])
        rho = colas.loc[servicio, "rho_aprox"]
        frac = float(sat.get(servicio, 0.0))
        if p90 < 1:
            return "fluido"
        if rho == rho and rho >= 0.90 and p90 > 24 and espera_crece:
            return "cuello"
        if frac >= 0.20 and p90 <= 24:
            return "acumulacion"
        return "neutro"

    return {"t": t, "dur": dur, "colas": colas, "sat": sat, "obs_hosp": obs_hosp, "bloq": bloq, "clasificar": clasificar}


ESTADOS = {"fluido": "Flujo ágil", "acumulacion": "Punto de acumulación", "cuello": "Cuello de botella", "neutro": "Sin presión"}


def _nodo(titulo, valor, pie, estado=None, salida=None, extremo=False):
    clases = ["rc-nodo"] + (["extremo"] if extremo else []) + ([estado] if estado in ("cuello", "acumulacion") else [])
    return html.Div(className=" ".join(clases), **({"data-salida": salida} if salida else {}), children=[
        html.Span(ESTADOS[estado], className=f"rc-estado {estado}") if estado else None,
        html.H5(titulo),
        html.Div(valor, className="rc-vol") if valor else None,
        html.Span(pie, className="rc-pie") if pie else None,
    ])


def recorrido() -> html.Div:
    """Versión simple: cinco etapas, un dato por etapa y la probabilidad real de cada paso."""
    d = datos_recorrido()
    t, dur, colas, c = d["t"], d["dur"], d["colas"], cifras()
    est = {s: d["clasificar"](s) for s in ("urgencias_ingreso", "urgencias_observacion", "hospitalizacion")}
    nodos = [
        _nodo("Llegada", f"{es(c['visitas'] / 1e6, 2)} M", "visitas", extremo=True,
              salida=_pct(t.loc["(llegada)", "urgencias_ingreso"])),
        _nodo("Admisión", _horas(dur.loc["urgencias_ingreso", "p50_h"]), "de registro",
              est["urgencias_ingreso"], salida=_pct(t.loc["urgencias_ingreso", "urgencias_observacion"])),
        _nodo("Urgencias · observación", _pct(colas.loc["urgencias_observacion", "rho_aprox"]), "de ocupación media",
              est["urgencias_observacion"], salida=_pct(t.loc["urgencias_observacion", "hospitalizacion"])),
        _nodo("Hospitalización", _pct(colas.loc["hospitalizacion", "rho_aprox"]), "de ocupación media",
              est["hospitalizacion"], salida=_pct(t.loc["hospitalizacion", "(egreso)"])),
        _nodo("Egreso", None, "alta o traslado", extremo=True),
    ]
    return html.Div(className="recorrido", children=html.Div(nodos, className="recorrido-pista"))
