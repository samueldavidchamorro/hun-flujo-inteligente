"""Datos que alimentan el gemelo digital 3D (se sirven en /api/gemelo).

Qué es real y qué es ilustrativo (se muestra igual en la interfaz):

REAL (de outputs/):
  - Ocupación media y fracción de horas saturadas por día × hora (M4 visual).
  - Llegadas medias por día × hora de los 4 servicios (M4 visual).
  - Probabilidades de transición entre servicios (M4).
  - Capacidad proxy c, λ y estancia media por servicio (M1/M3).
  - Tasas por 100 snapshots del escenario A (θ = 0,5) y B (θ* por servicio)
    en la prueba temporal única de M7.2.

ILUSTRATIVO (no existe en los datos):
  - El plano del hospital: el HUN no entregó planos.
  - El número de camas dibujadas: se muestran N camas que representan c/N lugares
    del proxy de capacidad (no se conoce el número real de camas).
  - Qué cama concreta recibe una alerta: el modelo da tasas, no trayectorias.
    La animación sortea los casos con las tasas reales de cada escenario.
"""
from __future__ import annotations

from functools import lru_cache

from plataforma.config import SERVICIO
from plataforma.datos import cargar

# Camas dibujadas por zona (decisión visual; cada una representa c/N lugares)
CAMAS_DIBUJADAS = {"hospitalizacion": 36, "urgencias_observacion": 30}

# docs/M1_contrato_datos.md: umbral_ocupacion = 0,95 hospitalización, 0,85 urgencias
UMBRAL_SATURACION = {"hospitalizacion": 0.95, "urgencias_observacion": 0.85}


def _redondear(matriz, n=3):
    return [[round(float(v), n) for v in fila] for fila in matriz]


@lru_cache(maxsize=None)
def carga_util() -> dict:
    ocup = cargar.heatmaps_ocupacion()
    llegadas = cargar.heatmaps_llegadas()
    colas = cargar.colas()
    transicion = cargar.matriz_transicion()
    escenarios = cargar.escenarios_decision("lightgbm")

    servicios = {}
    for clave, nombre in SERVICIO.items():
        fila = colas.loc[clave]
        datos = {
            "nombre": nombre,
            "lambda_h": float(fila["lambda_por_hora"]),
            "estancia_media_h": float(fila["estancia_media_h"]),
            "llegadas": _redondear(llegadas[clave]),
        }
        if clave in ocup:
            c = float(fila["capacidad_media_c"])
            n = CAMAS_DIBUJADAS[clave]
            datos.update(
                {
                    "capacidad_proxy": round(c, 1),
                    "censo_medio": float(fila["censo_prom_L"]),
                    "rho": float(fila["rho_aprox"]),
                    "camas_dibujadas": n,
                    "lugares_por_cama": round(c / n, 1),
                    "umbral_saturacion": UMBRAL_SATURACION[clave],
                    "ocupacion": _redondear(ocup[clave]["ocupacion"]),
                    "frac_saturada": _redondear(ocup[clave]["frac_saturada"]),
                    "escenarios": escenarios[clave],
                }
            )
        servicios[clave] = datos

    return {
        "dias": ocup["hospitalizacion"]["dias"],
        "servicios": servicios,
        "transiciones": {
            desde: {hacia: float(p) for hacia, p in fila.items()}
            for desde, fila in transicion.iterrows()
        },
        "escenarios_global": escenarios["todos"],
        "modelo": "LightGBM calibrado (isotónica), umbrales congelados en M7.2",
        "costos": {"c_fn": 5.0, "c_fp": 1.0},
    }
