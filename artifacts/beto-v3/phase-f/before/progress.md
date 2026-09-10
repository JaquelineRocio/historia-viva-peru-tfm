# BETO V3: fase D completada; S cerrada

[Seis ejecuciones y métricas por clase/obra](phase-d-results.md) · [Curvas, 12 errores y recomendación](phase-d-analysis.md) · [Runner y comandos](runner-phase-c.md).

Se reutilizaron R0/R2 de 42 y se completaron sólo R0/R2 × 43/44. R2 mantuvo 20 épocas y scheduler completo; mejores épocas 8/14/9. R0: 4/4/4. H 590, T 426, V 444, etiquetas y representación congeladas; R1/R3 intactas.

| Magnitud | Media ± DE muestral (3 semillas) |
|---|---:|
| R0 F1 macro V | 0.421345 ± 0.039173 |
| R2 F1 macro V | 0.524606 ± 0.008453 |
| Diferencia emparejada R2−R0 | +0.103261 ± 0.046145 |

Diferencias 42/43/44: +0,156277 / +0,081374 / +0,072132. Mejora en tres semillas y cinco de ocho obras; no uniforme. Cuatro clases R2 quedan bajo 0,50 en media. Train R2 llega a 1,0, con V limitada; se conserva R2 como control de desarrollo, sin afirmar éxito final.

Presupuesto: D 3559.11 s; C–D 7205.39/14.400 s. V3 7205.39/28.800 s; 8/18 trayectorias. ASR 933,00 s sin gasto nuevo; US$0. Anotación 999/1.200: una entrada de desarrollo y 200 reservadas para S.

Siguiente intervención recomendada: opción F, sólo T frente a H+T con R2 y tres semillas, sin nuevas anotaciones. No ejecutada. La enmienda 23+23 sólo cubre C–D: documentar su alcance prospectivo para F antes de ajustar. No ampliar automáticamente a T600 ni abrir S.

Recargas idénticas verificadas; métricas por época, mejor checkpoint y último estado completo conservados. Espacio: 14,10 GiB antes, 7,55 GiB después. Snapshots locales en `artifacts/beto-v3/phase-d/before/`; pesos en `outputs/beto-v3/phase-c/`. Respaldo externo no verificado.

Estado: `artifacts/beto-v3/development-current.json`. Ledger vigente: `artifacts/beto-v3/budget-ledger-after-D.json`, snapshot tras C más recibos D sin duplicación. [Verificación](../../artifacts/beto-v3/phase-d/verification.json). [Incidentes](../../artifacts/beto-v3/phase-d/incidents.md). Cierre: `outputs/venv-ml/Scripts/python.exe -X utf8 scripts/finalize_beto_phase_d_v3.py`.
