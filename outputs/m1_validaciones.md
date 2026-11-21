# M1 · Validaciones del dataset maestro

## CHECK_snapshot_no_posterior_al_fin

```
 count_star()
            0
```

## CHECK_target_no_trivial

```
 count_star()
            0
```

## CHECK_episodio_con_persona

```
 count_star()
            0
```

## CHECK_snapshot_id_unico

```
 (count_star() - count(DISTINCT snapshot_id))
                                            0
```

## CHECK_umbral_solo_entrenamiento

```
 count_star()
            0
```

## CHECK_capacidad_sin_futuro

```
 count_star()
            0
```

## CHECK_dx_sin_futuro

```
 count_star()
            0
```

## CHECK_mediciones_sin_futuro

```
 count_star()
            0
```

## CHECK_censo_sin_propio_paciente

```
 count_star()
            0
```

## CHECK_target_saturacion_sin_horizonte_completo

```
 count_star()
            0
```

## RESUMEN_parametros

```
  fecha_corte_datos inicio_periodo_estable fin_periodo_estable   fin_entrenamiento snapshots_horas  percentil_los  umbral_ocupacion_urgencias  umbral_ocupacion_hospitalizacion  ventana_capacidad_dias  horizonte_horas  percentil_capacidad  tolerancia_vinculo_h  gap_union_subprocesos_h  dias_riesgo_truncamiento              construido_en
2026-07-17 18:41:56    2023-01-31 00:23:38          2026-04-01 2025-07-13 19:59:00           0,2,6           0.75                        0.85                              0.95                      90                4                 0.95                    12                      1.0                        30 2026-11-10 18:00:51.512882
```

## RESUMEN_episodios

```
             servicio  n_episodios  n_personas  frac_entrenamiento  los_p50_h  umbral_p75_h  tasa_positivos  frac_origen_urgencias  n_riesgo_truncamiento
      hospitalizacion        49423       36723               0.726       70.8         141.6           0.260                  0.972                  924.0
urgencias_observacion       493320      203638               0.736        0.0           8.9           0.255                  0.000                 8548.0
```

## RESUMEN_snapshots

```
             servicio  horas_desde_ingreso      n  n_estables  tasa_positivos  prom_dx  frac_sin_mediciones_24h  prom_censo_t1
      hospitalizacion                    0  49416     44416.0           0.260    232.0                    0.412          278.2
      hospitalizacion                    2  49223     44247.0           0.261    244.8                    0.361          280.5
      hospitalizacion                    6  48879     43936.0           0.263    256.1                    0.366          283.1
urgencias_observacion                    0 241463    216827.0           0.521    106.1                    0.969          227.0
urgencias_observacion                    2 212616    191539.0           0.592    116.0                    0.761          236.2
urgencias_observacion                    6 164934    148968.0           0.763    136.6                    0.350          243.9
```

## RESUMEN_ocupacion

```
             servicio          fuente_capacidad  umbral_ocupacion  capacidad_media  n_horas  n_horas_estables  censo_prom  censo_max  ocupacion_media  tasa_entren  tasa_prueba
      hospitalizacion proxy_movil_p95_censo_90d              0.95            311.7    31051           25579.0       284.3      378.0            0.928        0.383         0.38
urgencias_observacion proxy_movil_p95_censo_90d              0.85            311.1    31051           25579.0       224.2      639.0            0.743        0.263         0.27
```

## RESUMEN_calidad

```
               tabla                                                                chequeo  n_afectados  n_total    pct
    visit_occurrence                                  fin = inicio (LOS 0 en toda la tabla)      1706001  1706001 100.00
    visit_occurrence                                                   visit_concept_id = 0            2  1706001   0.00
    visit_occurrence               tipo LOINC 3045729 como visita (no es un concepto Visit)        17858  1706001   1.05
        visit_detail                                            fin < inicio o fechas nulas            0  3281613   0.00
        visit_detail vínculo a visita incoherente (empieza > tolerancia antes de su visita)       954735  3281613  29.09
        visit_detail                                hospitalización con vínculo incoherente        31524   108601  29.03
        visit_detail                                         hospitalización con duración 0         3533   108601   3.25
        visit_detail                                                     duración > 90 días           38  3281613   0.00
condition_occurrence                     person_id distinto al de su visita (mal vinculado)      7186749 38636063  18.60
condition_occurrence                                               condition_concept_id = 0     14605421 38636063  37.80
condition_occurrence                                                sin visit_occurrence_id       823429 38636063   2.13
condition_occurrence                                  fecha posterior a 2026-08-13 (futura)           82 38636063   0.00
         measurement                     person_id distinto al de su visita (mal vinculado)      7115665 16575888  42.93
         measurement                                             measurement_concept_id = 0      8876114 16575888  53.55
         measurement                                                    sin value_as_number      6373242 16575888  38.45
              person                                                   year_of_birth < 1900           87   912205   0.01
              person                                                  gender_concept_id = 0          129   912205   0.01
procedure_occurrence   procedure_date nulo (tabla no utilizable en el tiempo; no se extrae)         <NA>     <NA>    NaN
```
