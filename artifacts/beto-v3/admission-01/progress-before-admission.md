# BETO V3 — recuperación 01; C y S cerradas

Estado vigente: [current.json](../../artifacts/beto-v3/recovery-01/current.json). Historial del lote de 444: [progress-before-recovery-01.md](progress-before-recovery-01.md). Ese lote y sus 30 checkpoints se conservan sin sobrescribir.

## Recuperación ejecutada

De los 38 pendientes V se prepararon 31 objetivos ampliados, conservando todo el texto original y añadiendo exclusivamente transcripción contigua. Siete casos requieren audio por contenido léxico insuficiente. Las entradas tienen procedencia por cue, hashes propios y un máximo de 384 tokens; no contienen contexto generado ni invisible para BETO.

Primeras pasadas: **31/31**. Segundas revisiones: **31/31**. Adjudicaciones: **31/31**. Juicios resueltos: **18**; juicios pendientes: **13**. Acuerdos nominales: 24; discrepancias: 7. La adjudicación comprueba el objetivo completo, evidencia, alcance y fronteras; el acuerdo no acredita verdad experta.

El usuario autorizó explícitamente agentes sin historial. Ambas pasadas se realizaron en sesiones separadas que recibieron sólo los cuatro paquetes sanitizados y la guía. Misma familia GPT-6, pesos y tokens del proveedor desconocidos: consistencia entre sesiones, no independencia entre modelos ni gold experto. El análisis geométrico se realizó aparte y no cuenta como revisión ciega.

## Solapamientos y referencias efectivas

La comprobación de procedencia encontró que **30/31 candidatos se solapan con referencias anteriores aceptadas**. Sólo `N07-asr-042-recovery01` no invade una referencia aceptada; la adjudicación lo dejó pendiente de alcance. Hay siete pares de candidatos solapados. No hay texto de fuente anteriormente sin inventariar en estos candidatos.

Política: preservar las referencias aceptadas anteriores; no recortar vecinos y transferirles etiquetas. Los candidatos con un juicio resuelto que invaden referencias aceptadas quedan guardados como `resolved_but_excluded_overlap`. Un candidato admisible sólo sustituye a su padre pendiente y no puede solaparse con otra referencia aceptada. Los padres originales permanecen en el dataset histórico; los objetivos nuevos nunca heredan automáticamente su etiqueta.

**Ganancia efectiva de esta recuperación: 0 referencias.** Juicios resueltos excluidos por solapamiento: 18. Totales aceptados: **{'T': 426, 'V': 421, 'auxiliary': 14}**; para cuotas de obras ≥30 minutos: **T 401, V 421**. Pendientes del inventario efectivo: **69**. Los 25 T de obras cortas continúan fuera de las cuotas largas.

| Partición / clase | Aceptadas ≥30 min | Faltan referencias | Faltan obras |
|---|---:|---:|---:|
| T / campanias_conflictos_militares | 29 | 0 | 0 |
| T / contexto_colonial_antecedentes | 22 | 0 | 0 |
| T / crisis_ideas_emancipadoras | 24 | 0 | 0 |
| T / liderazgos_diplomacia_proyectos | 29 | 0 | 0 |
| T / no_relevante | 214 | 0 | 0 |
| T / organizacion_consecuencias_republicanas | 21 | 0 | 0 |
| T / participacion_social_regional | 62 | 0 | 0 |
| V / campanias_conflictos_militares | 63 | 0 | 0 |
| V / contexto_colonial_antecedentes | 20 | 5 | 0 |
| V / crisis_ideas_emancipadoras | 75 | 0 | 0 |
| V / liderazgos_diplomacia_proyectos | 22 | 3 | 0 |
| V / no_relevante | 158 | 0 | 0 |
| V / organizacion_consecuencias_republicanas | 23 | 2 | 0 |
| V / participacion_social_regional | 60 | 0 | 0 |

Cobertura resoluble sobre unidades anotadas: T 426/456 (93.42%); V 421/459 (91.72%). No es cobertura del vídeo completo. Cobertura por obra: [coverage-by-work.json](../../artifacts/beto-v3/recovery-01/coverage-by-work.json).

## Presupuesto y condiciones C

- **969/1.200 entradas únicas; quedan 231**, incluidas 200 de margen S y 31 de margen adicional.
- Las 31 entradas ampliadas cuentan una vez cada una; sus revisiones repetidas no duplican consumo. El integrador cuenta hashes con respuestas reales en cualquiera de las dos pasadas y conserva el consumo anterior completo.
- Segundas revisiones acumuladas: 838 unidades, 61 lotes y 14 sesiones. Las sesiones no equivalen a invocaciones observables del proveedor.
- ASR acumulado: 833.68252930/28.800 s; sin ASR nuevo. Entrenamientos V3 y C/D: 0. Entrenamiento previo exitoso: 2.828,3538435 s; fallido previo desconocido, sin ponerlo a cero.
- US$0; S cerrada; H, V2, roles y reservas preservados. No se ejecutaron R0–R3 ni se habilitaron datos para entrenamiento.

- V/contexto_colonial_antecedentes: missing 5 references and 0 works from >=30-minute sources
- V/liderazgos_diplomacia_proyectos: missing 3 references and 0 works from >=30-minute sources
- V/organizacion_consecuencias_republicanas: missing 2 references and 0 works from >=30-minute sources
- Final source independence/reproduction admission and frozen H/T/V/S manifests outstanding
- Caption/audio fidelity and missing-cue intervals require final admission review; S remains closed

## Próximo paso

El [inventario de texto V disponible](../../artifacts/beto-v3/recovery-01/remaining-existing-V.json) comprueba las seis fuentes V activas: **459 unidades y 344.133 caracteres no blancos ya cubiertos; cero texto auténtico sin anotar**. N07 coincide con sus 908 segmentos ASR completos y el último objetivo alcanza el final de la transcripción. Los huecos temporales de subtítulos se registran aparte y no acreditan silencio ni aportan texto disponible. Otras cuatro candidatas V carecen de transcripción local; N03 sigue en cuarentena auxiliar y no cumple los 30 minutos.

No sumar los juicios solapados para cubrir las carencias. Para nuevas referencias disjuntas hacen falta una resegmentación completa con nueva revisión de los vecinos afectados o material auténtico adicional dentro del margen de desarrollo. No gastar las 200 entradas de S ni forzar casos ambiguos. La autorización para revisores aislados sigue vigente; no hace falta pedirla otra vez.

Antes de congelar H/T/V/S queda la admisión final de independencia/reproducciones y fidelidad. Revisar huecos de subtítulos, especialmente G18 (128,429 s), G13 (49,5 s) y G16 (30,75 s); ausencia de cues no acredita silencio. Conservar la revisión de relaciones G16/G17 y todos los recibos originales. Las 15 fuentes nuevas largas y las cantidades de obras siguen siendo provisionales hasta esa admisión. C sólo puede abrirse cuando se cumplan todas sus condiciones.

## Artefactos y reanudación

- [Candidatos y revisiones integradas](../../outputs/beto-v3/recovery-01/reviewed-candidates.json).
- [Dataset efectivo](../../outputs/beto-v3/recovery-01/all-development-units.json) y [pendientes](../../outputs/beto-v3/recovery-01/pending-resolution.json).
- [Auditoría de solapamientos](../../artifacts/beto-v3/recovery-01/overlap-audit.json), [manifiesto de respuestas](../../artifacts/beto-v3/recovery-01/response-manifest.json) y [verificación](../../artifacts/beto-v3/recovery-01/verification.json).
- Paquetes, primeras pasadas, segundas revisiones y adjudicaciones en `outputs/beto-v3/recovery-01/{inputs,first-pass,second-review,adjudication}/`.

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/integrate_beto_v3_recovery.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/report_beto_v3_recovery.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/prepare_beto_v3_recovery.py --check-only
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/integrate_beto_v3_recovery.py --check-only
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/verify_beto_v3_gap_batch.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/check_beto_v3.py --require-C
```

El último comando debe devolver 2 mientras C siga cerrada. Los integradores/informes históricos reconocen la continuación y no reinician presupuesto ni restauran cifras anteriores. Las decisiones sólo se integran desde respuestas auténticas guardadas.
