# Estado V3 — fase B en curso

Último checkpoint: 2026-09-09T04:23:49.525341+00:00.

Se conservan los resultados anteriores: 93 T, 99 V y 14 auxiliares aceptadas; 29 pendientes. De T, 68 referencias provienen de obras ≥30 minutos. Las cuotas oficiales no incluyen propuestas sin segunda revisión.

Nuevo lote `phase-b-gap-02`: 15 fuentes ≥30 minutos con texto adquirido (13 subtítulos públicos reutilizados y dos ASR completos), 251 propuestas de primera pasada, 0 nuevas referencias aceptadas. G01 (RTV San Marcos, 83:45) y G02 (Héroes de Cavite, 164:48) tienen ambas primeras pasadas completas: 29 y 32 propuestas militares respectivamente, todavía sin aceptación. G03 (IEP, 64:15) y G17 (UDP, 91:30) tienen audio AAC decodificado y ASR completo; G03 tiene 52 propuestas, 48 de ellas no relevantes por tratar sobre historiografía y conmemoración posterior a 1842. G01/G02 también tienen audio AAC completo verificado. Se conservaron los fallos Opus de G01/G03. G02 se reanudó una vez tras timeout. No se certificó la fidelidad literal ni la integridad de fotogramas.

Adquisición provisional: 11 T y 4 V nuevas; con las obras largas transcritas anteriores, 13 T y 6 V. Se añadieron cinco obras S con metadatos verificados ≥30 minutos: total 6 nuevas S registradas, además de todas las reservas heredadas. Son cantidades de adquisición, pendientes de admisión final por obra, no particiones congeladas. G04–G06 son partes cortas de una misma presentación y no cuentan. Comparación de 23 obras de desarrollo: solo coincidencia exacta en un saludo del MNAAHP; no acredita ausencia de reproducciones semánticas ni uso de fragmentos.

Presupuesto acumulado: 494/1.200 inputs; quedan 706. ASR: 833.68/28.800 s, llamadas y cargas medidas, sin reserva en curso. Entrenamientos V3: 0; US$0. Uso de tokens del proveedor desconocido. C cerrada y S cerrada.

Trabajo pendiente exacto:

- Ejecutar las 15 revisiones ciegas guardadas: 211 entradas (199 V, 2 ambiguas de G03 y 10 de su muestra T aleatoria). Adjudicar con guía y evidencia, corregir límites discursivos si procede y contabilizar cada entrada que cambie. Ninguna segunda pasada nueva se presenta como realizada.
- Resolver con nueva evidencia los 29 pendientes heredados, conservando el inventario si persiste la ambigüedad.
- Continuar la primera pasada seleccionada: 444 entradas (144 V restantes, 300 T en diez obras, hasta diez por tercio temporal). La selección se fijó sin etiquetas/predicciones nuevas. Después quedarían 262 inputs: margen de planificación de 200 para S y 62 para cambios/revisión. Las 757 candidatas aún no anotadas permanecen inventariadas; no se anotan todas porque excederían el presupuesto con S.
- Revisar intervalos sin subtítulos, especialmente comienzo de G18 (128,429 s), G13 (49,5 s) y G16 (30,75 s); ausencia de subtítulos no demuestra silencio. Completar admisión de fuentes y revisión de fragmentos/reproducciones.
- Integrar únicamente referencias admisibles, recalcular [exact-gaps-30min-works.csv](../../artifacts/beto-v3/phase-b-completion-01/exact-gaps-30min-works.csv), cumplir cantidades/clases/diversidad/cobertura resoluble y congelar H/T/V y manifiesto S antes de R0–R3. S permanece cerrada.

Bloqueo de la revisión ciega: se solicitó autorización explícita para subagentes sin historial porque la configuración de esta sesión prohíbe crearlos sin ella; aún no llegó respuesta. El lote está preparado para revisión. No se ejecutaron R0–R3 ni se modificaron requisitos para completar cuotas.

Artefactos: `artifacts/beto-v3/phase-b-gap-02/checkpoint.json`, `verification.json`, `source-registry-overlay.json`, `source-relation-review.json`, `blind-review-queue.json`, `next-annotation-selection.json`; unidades/pasadas en `outputs/beto-v3/phase-b-gap-02/G*/annotation/`; 15 SRT en `G*/transcript.srt`. Las reservas y el registro anterior se conservan. La verificación nueva comprobó hashes, evidencia literal, conservación de cues, 384 tokens, presupuesto y separación de S. La integridad heredada pasó; `--require-C` sigue devolviendo 2.

Reanudación (desde la raíz; adquisición requiere red):
```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/acquire_beto_v3_gap_batch.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/prepare_beto_v3_gap_units.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/resume_beto_v3_asr.py --base outputs/beto-v3/phase-b-gap-02 --sources G03 G17
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/prepare_beto_v3_asr_units.py --base outputs/beto-v3/phase-b-gap-02 G03 G17
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/prepare_beto_v3_gap_blind_queue.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/select_beto_v3_gap_next_batch.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/verify_beto_v3_gap_batch.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/report_beto_v3_gap_batch.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/check_beto_v3.py --require-C
```

Estos comandos reutilizan resultados; no ejecutan las revisiones ni generan etiquetas automáticamente. Para retomarlas, abrir solo los lotes indicados en `blind-review-queue.json` en contextos sin historial, conservar respuestas y después adjudicar. El finalizador anterior ya protege el contador acumulado frente a disminuciones, pero aún no integra las referencias del lote nuevo. No usarlo como integrador de este lote. Los runners de ASR/segmentación ahora admiten la carpeta nueva; al encontrar transcripciones completas, ASR termina sin cargar modelo ni gastar GPU.
