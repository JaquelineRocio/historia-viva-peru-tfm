# BETO V3 ? revisi?n ciega integrada; fase B en curso

Checkpoint UTC: 2026-09-09T04:39:13.260812+00:00. Revisi?n `phase-b-gap-02/review-run-01` completada bajo autorizaci?n expl?cita y persistente del usuario. No se ampli? la adquisici?n durante esta revisi?n.

Se revisaron las **211 entradas congeladas**, repartidas en 15 lotes entre tres subagentes creados con `fork_turns="none"`. Cada uno recibi? exclusivamente gu?a y objetivos aut?nticos con sus hashes, sin etiquetas previas, predicciones BETO ni historial. Se guardaron las 211 respuestas: **185 acuerdos nominales y 26 discrepancias** entre pasadas. El adjudicador examin? las 32 entradas con discrepancia, ambig?edad o frontera bloqueante; comprob? evidencias y fronteras de los acuerdos y corrigi? tambi?n el acuerdo militar de G02-u127 a participaci?n social por centrarse en procedencia de los participantes.

Se guardaron **251 decisiones finales del lote**: 211 tras segunda revisi?n ciega y 40 T fuera de la muestra de segunda pasada, rele?das por el adjudicador conforme al protocolo. Hay **237 referencias nuevas aceptadas (51 T, 186 V)** y **14 pendientes**. Las etiquetas clasifican el contenido del fragmento, sin certificar las afirmaciones hist?ricas de los expositores ni reparar silenciosamente transcripciones. Los defectos y alternativas de ambas pasadas se conservan. Sesiones de la misma familia GPT-6, pesos desconocidos: consistencia entre sesiones, no independencia entre modelos ni gold experto.

La integraci?n conserva literalmente las **235 unidades heredadas** (hash `344eb020f2fc5b0c34ad1a15f5ce7ec0c48b7d5272220f1f39d65bd5fe44e0eb`) y a?ade 251: **486 unidades inventariadas**. Totales aceptados: **144 T, 285 V y 14 auxiliares**. T contiene 25 referencias de fuentes cortas: para la cuota estricta cuentan **119 T y 285 V de obras ?30 minutos**. Hay 43 pendientes: 29 heredados y 14 nuevos. Ninguna unidad se habilit? para entrenamiento.

**Campa?as militares V: 57 referencias aceptadas de dos obras largas**, G01 y G02; quedan cubiertas las metas de 25 y dos obras. Cobertura resoluble sobre unidades anotadas: T 144/156 = 92,31%; V 285/315 = 90,48%. La cobertura por obra sigue publicada; por ejemplo N07 conserva 14 pendientes de 76. Estas fracciones no certifican cobertura de la totalidad de los v?deos ni admisi?n final de obras.

Carencias vigentes, solo fuentes ?30 minutos; no usar el CSV heredado como estado actual:

| Partici?n / clase | Referencias ?30 min | Meta | Faltan referencias | Faltan obras |
|---|---:|---:|---:|---:|
| T / campanias_conflictos_militares | 13 | 20 | 7 | 1 |
| T / contexto_colonial_antecedentes | 1 | 20 | 19 | 1 |
| T / crisis_ideas_emancipadoras | 6 | 20 | 14 | 1 |
| T / liderazgos_diplomacia_proyectos | 7 | 20 | 13 | 0 |
| T / no_relevante | 69 | 20 | 0 | 0 |
| T / organizacion_consecuencias_republicanas | 6 | 20 | 14 | 0 |
| T / participacion_social_regional | 17 | 20 | 3 | 0 |
| V / campanias_conflictos_militares | 57 | 25 | 0 | 0 |
| V / contexto_colonial_antecedentes | 14 | 25 | 11 | 0 |
| V / crisis_ideas_emancipadoras | 21 | 25 | 4 | 0 |
| V / liderazgos_diplomacia_proyectos | 13 | 25 | 12 | 0 |
| V / no_relevante | 125 | 25 | 0 | 0 |
| V / organizacion_consecuencias_republicanas | 13 | 25 | 12 | 0 |
| V / participacion_social_regional | 42 | 25 | 0 | 0 |

[CSV vigente](../../artifacts/beto-v3/phase-b-gap-02/exact-gaps-30min-works.csv) ? [Cobertura por obra](../../artifacts/beto-v3/phase-b-gap-02/coverage-by-work.csv) ? [Integraci?n](../../artifacts/beto-v3/phase-b-gap-02/review-integration.json).

## Presupuesto acumulado y reservas

- **494/1.200 entradas ?nicas; quedan 706**. Las 211 segundas pasadas y 251 adjudicaciones reutilizan entradas congeladas: no a?aden propuestas ?nicas.
- Segundas revisiones acumuladas: **390 unidades, 29 lotes, 10 sesiones**. Esta revisi?n a?ade 211 unidades, 15 lotes y tres sesiones. El contador hist?rico `phase_B_second_review_calls` representa sesiones, no el n?mero exacto de invocaciones del proveedor. Tokens e invocaciones reales desconocidos.
- ASR acumulado: **833,6825293/28.800 s**; sin nuevo ASR ni inferencia. Entrenamientos V3: **0**, segundos C/D: **0**. Entrenamiento previo exitoso conservado: 2.828,3538435 s; duraci?n previa fallida desconocida.
- **US$0; ning?n servicio ni API de pago contratado**. S permanece cerrada. Todos los roles y reservas heredados se conservan, junto con las seis obras S nuevas registradas solo por metadatos. H y V2 intactos.

## Artefactos y comprobaci?n

- Objetivos sanitizados: `outputs/beto-v3/phase-b-gap-02/review-run-01/batch-001.json` ? `batch-015.json`.
- Respuestas ciegas: `review-run-01/second-review/batch-001.json` ? `batch-015.json`; decisiones: `review-run-01/adjudications.json`.
- [Unidades integradas](../../outputs/beto-v3/phase-b-gap-02/all-development-units.json), [nuevas referencias](../../outputs/beto-v3/phase-b-gap-02/new-reviewed-units.json), [pendientes completos](../../outputs/beto-v3/phase-b-gap-02/pending-resolution.json).
- Comparaci?n, cach? separada, aprobaci?n de adjudicaci?n y snapshots previos: `artifacts/beto-v3/phase-b-gap-02/review-run-01/`. La cach? incluye texto, contexto nulo, gu?a, configuraci?n expuesta, modelo y versi?n del prompt.
- Integrador compatible: `scripts/integrate_beto_v3_gap_reviews.py`. Preserva las primeras pasadas sin etiquetas aceptadas y escribe aceptaci?n en artefactos derivados. Los comandos antiguos de informe/finalizaci?n detectan la integraci?n y verifican el estado vigente sin sustituirlo por cifras antiguas. La cola revisada permanece congelada: los siguientes lotes necesitan una cola distinta.
- Verificaci?n offline aprobada: 1.008 candidatos, 251 primeras evidencias, 211 respuestas y hashes de gu?a/texto, 251 adjudicaciones, l?mites de 384 tokens, presupuesto, separaci?n de roles y reservas. [Prueba de reanudaci?n](../../artifacts/beto-v3/phase-b-gap-02/review-run-01/resume-check.json): repetir integraci?n e informes conserva hashes de ledger y dataset. `check_beto_v3.py --require-C` devuelve **2** por requisitos de datos pendientes; integridad aprobada.

## Trabajo que falta

La revisi?n autorizada de 211 entradas est? completa; ya no existe bloqueo de autorizaci?n. La fase C sigue sin reunir los requisitos: **faltan 181 referencias T largas**, las cuotas de la tabla y la admisi?n final/congelaci?n de fuentes y manifiestos H/T/V/S. No se ejecutaron R0?R3 ni se abri? S.

1. Continuar sobre las transcripciones existentes con la selecci?n fijada de **444 entradas**: 144 V (G09/G14) y 300 T en diez obras. Est? en `next-annotation-selection.json` y `next-first-pass/`. No fue anotada en este checkpoint. Con esa primera pasada quedar?an 262 entradas: margen planificado de 200 S y 62 para cambios; no es una reserva gastada ni permiso para abrir S ahora. Hay 757 candidatos a?n sin primera pasada; no anotarlos todos porque agotar?an el presupuesto con S. Guardar cada lote y crear una nueva cola ciega sin sobrescribir la actual; autorizaci?n de subagentes sin historial sigue vigente.
2. Conservar/resolver con evidencia adicional los 43 pendientes. Nuevos: `G01-u017`, `G01-u023`, `G01-u038`, `G01-u044`, `G01-u045`, `G01-u066`, `G02-u039`, `G02-u064`, `G02-u082`, `G02-u111`, `G02-u121`, `G02-u128`, `G02-u129`, `G03-asr-023`. Falta audio/contexto aut?ntico o segmentaci?n que resuelva cada frontera/alcance. Todo cambio de objetivo exige nuevo hash y contabilizaci?n; no inventar contexto ni imponer etiquetas.
3. Completar calidad y admisi?n por obra: 15 fuentes nuevas largas transcritas (13 subt?tulos reutilizados, dos ASR), 11 T y cuatro V; con las previas, adquisici?n provisional 13 T y seis V. Son cantidades de adquisici?n, no obras admitidas/congeladas. G04?G06 son partes cortas de una ?nica presentaci?n y no cuentan. Revisar huecos de subt?tulos, especialmente comienzos G18 (128,429 s), G13 (49,5 s), G16 (30,75 s); ausencia de cues no demuestra silencio. Audio completo verificado para G01/G02/G03/G17; fidelidad literal y fotogramas no certificados. Mantener revisi?n de reproducciones/fragmentos y relaciones G16/G17; la b?squeda de coincidencias textuales no prueba independencia sem?ntica.
4. Recalcular carencias tras cada lote aceptado; adquirir m?s fuentes solo donde persistan carencias y dentro del presupuesto. Congelar las particiones y ejecutar R0?R3 ?nicamente cuando el control C lo permita; mantener S cerrada.

## Comandos de reanudaci?n desde la ra?z

Verificar el checkpoint sin adquirir, transcribir ni entrenar:

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/integrate_beto_v3_gap_reviews.py --check-only
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/verify_beto_v3_gap_batch.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/check_beto_v3.py --require-C
```

Reconstruir esta integraci?n de forma idempotente, usando las respuestas y adjudicaciones guardadas:

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/integrate_beto_v3_gap_reviews.py
```

Recuperar la selecci?n del pr?ximo lote (selecci?n congelada; no genera etiquetas):

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/select_beto_v3_gap_next_batch.py
Get-Content -Encoding UTF8 artifacts/beto-v3/phase-b-gap-02/next-annotation-selection.json
```

La revisi?n/anotaci?n siguiente exige leer los objetivos y guardar decisiones reales; no existe un comando que sustituya ese trabajo por etiquetas autom?ticas. Este integrador valida espec?ficamente el lote congelado de 251 entradas y su presupuesto de checkpoint; para integrar otro lote debe ampliarse por eventos y manifiestos, conservando este snapshot y el ledger acumulado.
