# M4 · Resumen y validaciones (parte SQL, Persona 1)
- ✓ `CHECK_una_salida_por_subproceso` = 0
- ✓ `CHECK_una_llegada_y_un_egreso_por_visita` = 0
- ✓ `CHECK_probabilidades_suman_1` = 0
- ✓ `CHECK_festivos_por_anio_17_18` = 0
- ✓ `CHECK_heatmap_168_celdas_por_servicio` = 0

## resumen_colas (ley de Little: censo_prom_L ≈ little_lambda_x_W)

```
             servicio  lambda_por_hora  estancia_media_h  mu_por_hora  estancia_p50_h  estancia_p90_h  n_subprocesos  censo_prom_L  little_lambda_x_W  capacidad_media_c  rho_aprox
          ambulatorio           51.445             0.000          NaN           0.000           0.000        1427228           NaN                0.0                NaN        NaN
      hospitalizacion            3.586            80.506       0.0124          45.729         187.358          99483         289.5              288.7              311.9      0.926
    urgencias_ingreso           16.100             0.355       2.8189           0.054           0.097         446657           NaN                5.7                NaN        NaN
urgencias_observacion           38.364             5.828       0.1716           1.178          12.476        1064329         224.0              223.6              301.2      0.742
```

## matriz_transicion (top 25)

```
                desde                 hacia      n   prob  espera_p50_h  espera_p75_h  espera_p90_h  frac_solapada  duracion_desde_p50_h
            (llegada)           ambulatorio 957806 0.6544           NaN           NaN           NaN            NaN                   NaN
          ambulatorio              (egreso) 946972 0.9862           NaN           NaN           NaN            NaN                 0.000
urgencias_observacion              (egreso) 390593 0.5372           NaN           NaN           NaN            NaN                 0.000
            (llegada)     urgencias_ingreso 355577 0.2429           NaN           NaN           NaN            NaN                   NaN
urgencias_observacion urgencias_observacion 293497 0.4037         0.000         0.000         0.000          0.010                 2.186
    urgencias_ingreso urgencias_observacion 273768 0.7698        -0.000        -0.000        -0.000          0.974                 0.062
            (llegada) urgencias_observacion 149348 0.1020           NaN           NaN           NaN            NaN                   NaN
    urgencias_ingreso              (egreso)  81740 0.2299           NaN           NaN           NaN            NaN                 0.000
      hospitalizacion              (egreso)  44245 0.6395           NaN           NaN           NaN            NaN                52.157
urgencias_observacion       hospitalizacion  42924 0.0590         0.000         0.000        18.210          0.000                 7.642
      hospitalizacion       hospitalizacion  24885 0.3597         0.000         0.000         0.000          0.044                24.696
          ambulatorio urgencias_observacion  10520 0.0110         0.067         0.088         0.135          0.000                 0.000
          ambulatorio           ambulatorio   2303 0.0024         1.272         7.625       120.322          0.000                 0.000
            (llegada)       hospitalizacion    909 0.0006           NaN           NaN           NaN            NaN                   NaN
          ambulatorio       hospitalizacion    396 0.0004        35.559       150.343       331.321          0.000                 0.000
    urgencias_ingreso       hospitalizacion    101 0.0003        15.934        42.011       277.293          0.000                 0.044
urgencias_observacion           ambulatorio     77 0.0001        78.543       307.703      1175.655          0.052                 0.000
          ambulatorio     urgencias_ingreso     33 0.0000       287.667       434.769      1619.689          0.000                 0.000
      hospitalizacion           ambulatorio     28 0.0004       -25.153        -3.679        98.521          0.750                39.233
      hospitalizacion urgencias_observacion     25 0.0004         0.000         0.000         0.000          0.240                 0.316
      hospitalizacion     urgencias_ingreso      8 0.0001       -69.339       -10.196        -8.506          1.000                70.940
    urgencias_ingreso           ambulatorio      7 0.0000       289.010       339.609       863.552          0.000                 0.000
urgencias_observacion     urgencias_ingreso      7 0.0000       406.766      2195.128      3618.584          0.143                 0.000
```

## rutas_frecuentes (top 15)

```
                                                                  ruta  n_pasos  n_visitas   frac
                                                ambulatorio → (egreso)        1     946877 0.6469
                  urgencias_ingreso → urgencias_observacion → (egreso)        2     247319 0.1690
                                      urgencias_observacion → (egreso)        1     134512 0.0919
                                          urgencias_ingreso → (egreso)        1      81732 0.0558
urgencias_ingreso → urgencias_observacion → hospitalizacion → (egreso)        3      26364 0.0180
                    urgencias_observacion → hospitalizacion → (egreso)        2      14798 0.0101
                        ambulatorio → urgencias_observacion → (egreso)        2       8780 0.0060
      ambulatorio → urgencias_observacion → hospitalizacion → (egreso)        3       1710 0.0012
                                            hospitalizacion → (egreso)        1        877 0.0006
                              ambulatorio → hospitalizacion → (egreso)        2        384 0.0003
                        urgencias_ingreso → hospitalizacion → (egreso)        2        101 0.0001
    urgencias_ingreso → urgencias_observacion → ambulatorio → (egreso)        3         32 0.0000
                        urgencias_observacion → ambulatorio → (egreso)        2         24 0.0000
    ambulatorio → urgencias_ingreso → urgencias_observacion → (egreso)        3         20 0.0000
          ambulatorio → urgencias_observacion → ambulatorio → (egreso)        3         16 0.0000
```

## efecto festivo en llegadas diarias

```
             servicio  laboral  fin_de_semana  festivo  dia_despues_festivo
          ambulatorio   1768.2          173.0      5.4               1640.1
      hospitalizacion     91.6           76.6     63.9                 82.3
    urgencias_ingreso    420.4          315.4    328.2                471.9
urgencias_observacion    998.6          762.8    758.2               1067.2
```

## cobertura de transiciones

```
 visitas  transiciones  en_periodo_estable  frac_mismo_servicio
 1620451       3947329           3575769.0                0.089
```
