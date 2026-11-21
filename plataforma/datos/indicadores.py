"""Cifras que se citan en los textos de la plataforma, calculadas desde outputs/.

Ninguna cifra de los textos se escribe a mano: si un módulo se vuelve a correr y
cambia un resultado, la plataforma lo refleja sola.
"""
from __future__ import annotations

from functools import lru_cache

from plataforma.datos import cargar


def es(numero: float, decimales: int = 1) -> str:
    """Formato colombiano: coma decimal y punto de miles (1.463.640,5)."""
    texto = f"{numero:,.{decimales}f}"
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


@lru_cache(maxsize=None)
def cifras() -> dict:
    colas = cargar.colas()
    sat = cargar.tabla("m2/tablas/balance_saturacion.csv")
    sat_train = sat[sat["particion"] == "entrenamiento"].set_index("servicio")
    episodios = cargar.tabla("m2/tablas/balance_episodio.csv")
    cuantiles = cargar.tabla("m2/tablas/los_cuantiles.csv").set_index("servicio")
    sankey = cargar.sankey()
    escenarios = cargar.escenarios_decision("lightgbm")
    hosp = escenarios["hospitalizacion"]
    calib = cargar.tabla("m7/tablas/m7_2_calibracion_prueba.csv")
    auc_prueba = float(calib[(calib["modelo"] == "lightgbm") & (calib["version"] == "isotonic")
                             & (calib["servicio"] == "todos")]["auc_roc"].iloc[0])
    bench = cargar.tabla("m6/model_benchmark_summary.csv").set_index("modelo")
    shap = cargar.tabla("m7/tablas/m7_3_importancia_shap.csv")
    bloqueo = cargar.tabla("m3/tablas/bloqueo_urg_hosp_por_ocupacion.csv")
    m4 = cargar.tabla("m4_visual/tablas/efecto_calendario.csv")
    urg_cal = m4[m4["servicio"] == "urgencias_observacion"].set_index("tipo_dia")
    congelados = cargar.json_resultado("m7/m7_2_umbrales_congelados.json")
    auc_sat = cargar.tabla("m5/tablas/m5_3_auc_saturacion.csv").set_index(["servicio", "variable"])["auc"]

    visitas = sum(v for o, v in zip(sankey["origen"], sankey["valor"]) if o == 0)
    costo_a, costo_b = hosp["A"]["costo_100"], hosp["B"]["costo_100"]
    mejor_sin_modelo = min(hosp["costo_alertar_todos"], hosp["costo_nunca"])

    return {
        "visitas": visitas,
        "episodios_hosp": int(episodios[episodios["servicio"] == "hospitalizacion"]["n"].sum()),
        "episodios_urg": int(episodios[episodios["servicio"] == "urgencias_observacion"]["n"].sum()),
        "tasa_larga": float((episodios["positivos"].sum()) / episodios["n"].sum()),
        "ocupacion_hosp": float(colas.loc["hospitalizacion", "rho_aprox"]),
        "ocupacion_urg": float(colas.loc["urgencias_observacion", "rho_aprox"]),
        "horas_saturadas_hosp": float(sat_train.loc["hospitalizacion", "tasa"]),
        "horas_saturadas_urg": float(sat_train.loc["urgencias_observacion", "tasa"]),
        "estancia_p50_hosp": float(cuantiles.loc["Hospitalización", "p50_h"]),
        "umbral_hosp": float(cuantiles.loc["Hospitalización", "umbral P75 (train)"]),
        "umbral_urg": float(cuantiles.loc["Urgencias / observación", "umbral P75 (train)"]),
        "los_cero_urg": float(cuantiles.loc["Urgencias / observación", "% LOS = 0"]),
        "auc_prueba": auc_prueba,
        "auc_oof": float(bench.loc["lightgbm", "auc_oof"]),
        "auc_oof_estrato": float(bench.loc["lightgbm", "auc_oof_servicio_tau"]),
        "theta_hosp": float(congelados["modelos"]["lightgbm"]["theta_por_servicio"]["hospitalizacion"]),
        "theta_urg": float(congelados["modelos"]["lightgbm"]["theta_por_servicio"]["urgencias_observacion"]),
        "sens_a": hosp["A"]["sensibilidad"], "sens_b": hosp["B"]["sensibilidad"],
        "alertas_a": hosp["A"]["alertas_100"], "alertas_b": hosp["B"]["alertas_100"],
        "fn_a": hosp["A"]["fn_100"], "fn_b": hosp["B"]["fn_100"],
        "costo_a": costo_a, "costo_b": costo_b,
        "reduccion_costo": 1 - costo_b / costo_a,
        "costo_alertar_todos": hosp["costo_alertar_todos"],
        "ahorro_vs_sin_modelo": 1 - costo_b / mejor_sin_modelo,
        "n_prueba_hosp": hosp["n"], "n_prueba": escenarios["todos"]["n"],
        "shap_top": shap.sort_values("media_abs_shap", ascending=False).head(3)["etiqueta"].tolist(),
        "bloqueo_p75_bajo": float(bloqueo.iloc[0]["p75_h"]),
        "bloqueo_p75_alto": float(bloqueo.iloc[-1]["p75_h"]),
        "bloqueo_ocup_baja": float(bloqueo.iloc[0]["ocup_media"]),
        "bloqueo_ocup_alta": float(bloqueo.iloc[-1]["ocup_media"]),
        "urg_laboral": float(urg_cal.loc["laboral (mar–vie)", "llegadas_media"]),
        "urg_festivo": float(urg_cal.loc["festivo", "llegadas_media"]),
        "urg_tras_festivo": float(urg_cal.loc["día después festivo", "llegadas_media"]),
        "auc_sat_hosp": float(auc_sat.loc[("hospitalizacion", "ocupacion_t1")]),
        "auc_sat_urg": float(auc_sat.loc[("urgencias_observacion", "ocupacion_t1")]),
        "capacidad_hosp": float(colas.loc["hospitalizacion", "capacidad_media_c"]),
        "lambda_hosp": float(colas.loc["hospitalizacion", "lambda_por_hora"]),
        "w_hosp": float(colas.loc["hospitalizacion", "estancia_media_h"]),
        "l_hosp": float(colas.loc["hospitalizacion", "censo_prom_L"]),
        "little_hosp": float(colas.loc["hospitalizacion", "little_lambda_x_W"]),
    }
