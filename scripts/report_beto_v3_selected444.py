"""Render current selected-444 progress without resetting historical artifacts."""
import csv
from datetime import datetime, timezone
from collections import Counter
from acquire_beto_v3_gap_batch import ROOT, DEST, ART, read

def main():
    if (ROOT/'artifacts/beto-v3/recovery-01/current.json').exists():
        from report_beto_v3_recovery import main as report_recovery
        return report_recovery()
    meta=ART/'selected-444';run=DEST/'selected-444';s=read(meta/'current.json')
    ledger=read(ROOT/'artifacts/beto-v3/budget-ledger-current.json')
    gaps=list(csv.DictReader((meta/'exact-gaps-30min-works.csv').open(encoding='utf-8-sig')))
    first={r['segment_id']:r for p in (run/'first-pass').glob('batch-*.json') for r in read(p)['items']}
    second={r['segment_id']:r for p in (run/'second-review').glob('batch-*.json') for r in read(p)['items']}
    agrees=sum(first[k]['proposal']==r['proposal'] for k,r in second.items())
    new=read(run/'new-reviewed-units.json')['items'];pending=[r['segment_id'] for r in new if r['adjudication'] and not r['accepted_label']]
    names={'campanias_conflictos_militares':'Campañas','contexto_colonial_antecedentes':'Colonial','crisis_ideas_emancipadoras':'Crisis e ideas','liderazgos_diplomacia_proyectos':'Liderazgos','no_relevante':'No relevante','organizacion_consecuencias_republicanas':'República','participacion_social_regional':'Participación'}
    table='| Partición / clase | Aceptadas ≥30 min | Faltan referencias | Faltan obras |\n|---|---:|---:|---:|\n'
    for r in gaps:table+=f"| {r['partition']} / {names[r['class']]} | {r['accepted_from_30min_works']} | {r['missing_examples']} | {r['missing_works']} |\n"
    coverage='; '.join(f"{role}: {r['accepted']}/{r['units']} ({r['fraction']:.2%})" for role,r in s['coverage'].items())
    status='completado' if s['selected444_complete'] else 'en curso'
    text=f'''# BETO V3 — lote seleccionado de 444 entradas {status}; C y S cerradas

Checkpoint UTC: {datetime.now(timezone.utc).isoformat()}. Estado vigente: `artifacts/beto-v3/phase-b-gap-02/selected-444/current.json`.

## Resultados guardados

Selección fija: **300 T y 144 V**, exclusivamente transcripciones existentes. No se adquirieron nuevas fuentes. Primeras pasadas: **{s['first_pass_units']}/444**. Revisiones ciegas guardadas: **{s['second_review_units']}/{s['second_review_target'] if s['second_review_target'] is not None else 'muestra todavía no congelada'}**. Adjudicaciones: **{s['adjudications']}/444**. Acuerdos nominales entre las pasadas: {agrees}; discrepancias: {len(second)-agrees}. El acuerdo por sí solo no equivale a aceptación ni exactitud experta.

Nuevas referencias aceptadas: **{s['accepted_new_references']}**, por partición {s['accepted_new_by_partition']}. Nuevos adjudicados pendientes: **{s['pending_new_adjudicated']}**. Las primeras pasadas mantienen `accepted_label: null`; la aceptación vive en la integración derivada, con evidencia y decisión final. Textos, alternativas, banderas y respuestas originales se conservan.

Totales acumulados aceptados: **{s['accepted_references']}**. Para cuotas de obras ≥30 minutos: **T {s['accepted_30min_references']['T']}, V {s['accepted_30min_references']['V']}**. Las 25 referencias T de obras cortas siguen excluidas de esa cuota. Inventario sin referencia aceptada: **{s['pending_references']}**, incluidos los 43 pendientes heredados y {s['pending_new_adjudicated']} nuevos adjudicados pendientes; restan {444-s['adjudications']} decisiones del lote. Cobertura resoluble sobre unidades anotadas: {coverage}. La cobertura por obra se publica por separado; no equivale a cobertura del vídeo completo.

Se preservan las **486 unidades previas**, su hash y los manifiestos de las revisiones anteriores. Las respuestas se guardan por lote y cada lote adjudicado genera un checkpoint inmutable con decisiones integradas, carencias y presupuesto. El integrador puede reanudarse sin duplicar consumo.

## Carencias actuales

Metas por clase: 20 T, 25 V y dos obras independientes ≥30 minutos; cantidades totales mínimas: T300 y V200. Las cifras de adquisición siguen siendo provisionales hasta la admisión de fuentes.

{table}
[Carencias vigentes CSV](../../artifacts/beto-v3/phase-b-gap-02/selected-444/exact-gaps-30min-works.csv) · [Cobertura por obra](../../artifacts/beto-v3/phase-b-gap-02/selected-444/coverage-by-work.csv).

## Presupuesto y aislamiento

- **{ledger['new_unique_annotation_proposals']}/1.200 entradas únicas; quedan {ledger['annotation_budget_remaining']}**. Repetir pasadas sobre la misma entrada no consume otra unidad. Todo cambio de objetivo/contexto requiere nuevo hash y contabilización.
- Margen de planificación S: 200 entradas, conservado; no es consumo ni autorización para abrir S. Las 444 primeras pasadas dejan el acumulado en 938 y el saldo en 262 (200 S y 62 de margen adicional).
- ASR acumulado sin cambios: **{ledger['ASR_gpu_seconds']:.8f}/28.800 s**. Entrenamientos V3 y segundos C/D: **0**. Entrenamiento previo exitoso: 2.828,3538435 s; fallido previo desconocido, sin ponerlo a cero.
- Segundas revisiones acumuladas: {ledger['phase_B_second_review_units']} unidades, {ledger['phase_B_second_review_batches']} lotes y {ledger['phase_B_second_review_calls']} sesiones. El contador de llamadas histórico representa sesiones; invocaciones reales y tokens del proveedor desconocidos.
- **US$0**, sin servicios ni APIs de pago contratados. Revisores creados sin historial; únicamente objetivos auténticos y guía, sin etiquetas anteriores ni predicciones BETO. Misma familia GPT-6, pesos desconocidos: consistencia entre sesiones, no independencia entre modelos ni gold experto. La autorización persistente del usuario sigue vigente.
- **S cerrada**; H, V2, roles y reservas conservados. Ninguna referencia nueva habilitada para entrenamiento. No se ejecutaron R0–R3.

## Pendientes y condición C

'''
    text+='\n'.join('- '+b for b in s['blockers'])+'\n\n'
    text+='Pendientes adjudicados de este lote: '+(', '.join('`'+sid+'`' for sid in pending) or 'ninguno registrado todavía')+'.\n\n'
    text+='''Los 43 pendientes heredados se conservan sin cambios. Resolver casos de alcance o frontera exige nueva evidencia auténtica; no importar contexto invisible para BETO ni forzar una etiqueta para cubrir cuotas.

Adquisición existente: 15 fuentes largas nuevas transcritas (13 subtítulos y dos ASR), con 13 T y seis V largas provisionales al sumar las previas. Seis nuevas S registradas sólo por metadatos, más todas las reservas heredadas. Falta admisión final de independencia/reproducciones y calidad. G04–G06 son partes cortas de una misma presentación y no cuentan. Revisar huecos de subtítulos, especialmente comienzos G18 (128,429 s), G13 (49,5 s), G16 (30,75 s): ausencia de cues no acredita silencio. G01/G02/G03/G17 tienen audio completo verificado; fidelidad literal y fotogramas no certificados. Conservar revisión de relaciones G16/G17 y todos los recibos originales.

Una vez terminada esta selección, dirigir el margen disponible a carencias persistentes y casos recuperables, preservando el margen S. Priorizar evidencia y transcripciones existentes antes de adquirir fuentes adicionales. Congelar H/T/V/S y ejecutar R0–R3 solamente cuando se cumplan todas las condiciones C; S permanece cerrada.

## Artefactos y reanudación

Entradas sanitizadas, respuestas y adjudicaciones: `outputs/beto-v3/phase-b-gap-02/selected-444/{inputs,first-pass,blind-inputs,second-review,adjudication}/`. Dataset vigente: [all-development-units.json](../../outputs/beto-v3/phase-b-gap-02/selected-444/all-development-units.json). Pendientes: [pending-resolution.json](../../outputs/beto-v3/phase-b-gap-02/selected-444/pending-resolution.json). Snapshots, manifiestos y checkpoints por lote: `artifacts/beto-v3/phase-b-gap-02/selected-444/`. La selección original y los artefactos de `review-run-01` son históricos y no se sobrescriben.

Desde la raíz, contabilizar e integrar sólo respuestas y decisiones reales ya guardadas:

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/integrate_beto_v3_selected444.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/report_beto_v3_selected444.py
```

Comprobar el estado sin adquisición, ASR ni entrenamiento:

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/integrate_beto_v3_selected444.py --check-only
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/verify_beto_v3_gap_batch.py
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/check_beto_v3.py --require-C
```

`--require-C` debe devolver 2 mientras persistan las condiciones de datos pendientes. Los comandos de informe/finalización anteriores reconocen este estado y no restauran cifras antiguas. La anotación/revisión restante requiere decisiones reales; estos comandos no inventan etiquetas.
'''
    if (meta/'verification.json').exists():
        text+='\nVerificación final: [verification.json](../../artifacts/beto-v3/phase-b-gap-02/selected-444/verification.json). Integridad y reanudación idempotente comprobadas; 30 checkpoints conservados, entradas y guía exactas, sin duplicar presupuesto. El control C devolvió 2 por las carencias publicadas.\n'
    recovery_path=ROOT/'artifacts/beto-v3/recovery-01/preparation.json'
    if recovery_path.exists():
        recovery=read(recovery_path)
        text+=f'''
## Continuación: recuperación de pendientes V (`recovery-01`)

Se prepararon **{recovery['prepared_candidates']} candidatos** a partir de los {recovery['pending_V_examined']} pendientes V, conservando íntegramente cada objetivo y añadiendo sólo texto contiguo de su transcripción. Otros {len(recovery['deferred'])} casos quedan para revisión de audio por contenido léxico insuficiente. Selección sin filtrar por clase propuesta ni predicciones; hashes nuevos, procedencia por cue y máximo de 384 tokens comprobados con el tokenizador local. Son candidatos para revisar, no casos resueltos.

Manifestación de procedencia y presupuesto: [preparation.json](../../artifacts/beto-v3/recovery-01/preparation.json). Objetivos ampliados: [candidates.json](../../outputs/beto-v3/recovery-01/candidates.json). Cuatro paquetes sanitizados de hasta diez objetivos en `outputs/beto-v3/recovery-01/inputs/`, sin etiquetas ni decisiones previas.

**0 nuevas anotaciones y 0 referencias aceptadas** en esta preparación. El presupuesto sigue en 938/1.200; si se anotaran todos los candidatos llegaría a {recovery['projected_unique_if_all_annotated']}/1.200 y quedarían {recovery['remaining_if_all_annotated']} entradas, incluidas las 200 de margen S. No se adquirieron fuentes, ejecutaron ASR ni entrenamientos.

Antes de anotar, preparar una integración versionada que contabilice los hashes nuevos: el integrador histórico `selected-444` verifica actualmente un acumulado fijo de 938 y no admite consumo posterior. No modificar sus respuestas ni sus checkpoints. La nueva integración deberá preservar el historial y actualizar los verificadores de presupuesto.

Revisar primero las fronteras y el alcance de los candidatos. Cada candidato registra los IDs existentes con los que se solapa: **no sumarlos directamente a las cuotas ni al F1**. Resolver sustituciones y solapamientos entre candidatos y referencias anteriores antes de integrar; un objetivo ampliado no acredita una ganancia neta. Algunos casos todavía pueden requerir audio o quedar ambiguos.

La anotación y segunda pasada siguen pendientes. Se requiere un contexto sin historial para la revisión ciega; no presentar otra lectura de esta conversación como revisión aislada. En esta sesión no se crearon agentes: las instrucciones vigentes sólo permiten delegarlos cuando el usuario lo pide explícitamente. Pendiente autorización explícita para revisores aislados. C y S continúan cerradas y las carencias aceptadas no cambian.

Verificar la reconstrucción exacta, límites de tokens y reanudación sin escrituras:

```powershell
outputs/venv-ml/Scripts/python.exe -X utf8 scripts/prepare_beto_v3_recovery.py --check-only
```
'''
    (ROOT/'docs/beto-v3/progress.md').write_text(text,encoding='utf-8')
    plan=ROOT/'docs/beto-v3/fase-B-lote-completo.md'
    lines=plan.read_text(encoding='utf-8').splitlines()
    lines[2]=f"> **Estado vigente: `selected-444`, {status}.** Primeras pasadas {s['first_pass_units']}/444; revisiones ciegas {s['second_review_units']}/{s['second_review_target']}; adjudicaciones {s['adjudications']}/444. Referencias nuevas: {s['accepted_new_references']}; pendientes nuevos: {s['pending_new_adjudicated']}. Cuotas largas: T {s['accepted_30min_references']['T']}, V {s['accepted_30min_references']['V']}. Presupuesto {ledger['new_unique_annotation_proposals']}/1.200, US$0. C y S cerradas. [Resultados, carencias y reanudación](progress.md). El resto de esta página conserva el cierre del lote anterior."
    plan.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('progress.md updated from selected-444 checkpoint')
if __name__=='__main__':main()
