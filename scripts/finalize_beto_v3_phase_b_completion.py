"""Validate phase-B data, export blind review batches and update current status."""
import csv
import json
from collections import Counter, defaultdict

from prepare_beto_v3 import ROOT, OUT, ART, DOC, read, sha, write
from complete_beto_v3_phase_b import DEST, META, digest, csv_write
from beto_v3_phase_b_decisions import LABELS

def replace_with_archive(path, data, archive):
    if not archive.exists() and path.exists():write(archive,path.read_bytes())
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    if (META/'resume-verification.json').exists():
        from finalize_beto_v3_resume import main as resume
        return resume()
    units=read(DEST/'units-and-annotations.json')['items']
    summary=read(META/'summary.json')
    old=read(OUT/'video-unit-candidates.json')['items']
    review=read(DEST/'review-input-blind.json')['items']
    oldhash=read(OUT/'datasets/H-initial.json')['parent_sha256']
    assert sha(ROOT/'outputs/beto-v2/first-training/canonical-dataset.json')==oldhash
    assert len({r['segment_id'] for r in units})==len(units)==125
    parent_dispositions=[]
    for sid in sorted({r['source_id'] for r in units}):
        source_path=OUT/'acquisition'/sid/'cues.json'
        cues=read(source_path)
        source=' '.join(c['text'].strip() for c in cues)
        rows=sorted([r for r in units if r['source_id']==sid],key=lambda r:r['source_char_span'][0])
        assert ''.join(r['text_original'] for r in rows)==source,'Dropped or duplicated transcription text'
        assert rows[0]['source_char_span'][0]==0 and rows[-1]['source_char_span'][1]==len(source)
        for left,right in zip(rows,rows[1:]):assert left['source_char_span'][1]==right['source_char_span'][0]
        cursor=0
        for parent in [r for r in old if r['source_id']==sid]:
            a=source.index(parent['text_original'],cursor);z=a+len(parent['text_original']);cursor=z
            children=[r for r in rows if r['source_char_span'][0]<z and r['source_char_span'][1]>a]
            assert children
            parent_dispositions.append({'parent_candidate_id':parent['segment_id'],'source_id':sid,'source_char_span':[a,z],
                'result_unit_ids':[r['segment_id'] for r in children],
                'split_across_units':len(children)>1,'joined_with_neighbor':any(len(r['parent_candidate_ids'])>1 for r in children),
                'crop_or_transfer':'Boundary fragments transferred to adjacent unit, never discarded',
                'text_coverage_fraction':1.0})
    assert len(parent_dispositions)==123
    for row in units:
        assert row['partition'] in {'T','V'} and row['proposal'] in LABELS.values()
        assert digest(row['text'])==row['input_sha256']
        assert row['text']==row['text_original'].strip()
        assert row['would_truncate_tokens']==0 and row['tokens_with_specials']<=384
        a,z=row['evidence_span'];assert row['text'][a:z]==row['evidence']
        assert row['second_review'] is None and not row['training_eligible']
        if row['accepted_label']:
            assert row['partition']=='T' and not row['review_reasons'] and not row['ambiguous'] and not row['extraction_defect']
    mandatory={r['segment_id'] for r in units if r['review_reasons']}
    assert mandatory=={r['segment_id'] for r in review}
    assert all('proposal' not in r and 'rationale' not in r and 'accepted_label' not in r for r in review)
    assert {r['segment_id'] for r in units if r['partition']=='V'}<=mandatory
    assert not (OUT/'acquisition/zb5zntF2kAs/cues.json').exists()
    reserved=read(ART/'reserved-index.json')
    assert sha(ROOT/reserved['inherited_final']['manifest'])==reserved['v2_reserved_manifest_sha256']
    guide=(DOC/'guia-etiquetado-v3.md').read_text(encoding='utf-8')
    for i in range(0,len(review),15):
        write(DEST/f'review-batches/batch-{i//15+1:03}.json',{'guide':guide,
            'instructions':'Fresh review in a separate call/session without first-pass decisions or BETO predictions. Label only the exact target. Flag ambiguous or defective cases. Return a decision for every ID.',
            'response_fields':['segment_id','input_sha256','guide_sha256','proposal','alternative','rule','evidence','rationale','ambiguous','extraction_defect','model','exposed_configuration'],
            'items':review[i:i+15]})
    coverage=list(csv.DictReader((META/'coverage-by-class-work-partition.csv').open(encoding='utf-8-sig')))
    class_summary=[]
    for label in LABELS.values():
        totals={'class':label}
        for partition in ['T','V']:
            group=[r for r in units if r['partition']==partition and r['proposal']==label]
            totals[partition+'_accepted']=sum(r['accepted_label'] is not None for r in group)
            totals[partition+'_pending']=sum(r['accepted_label'] is None for r in group)
            totals[partition+'_works_proposed']=len({r['source_id'] for r in group})
        class_summary.append(totals)
    csv_write(META/'coverage-by-class.csv',class_summary,list(class_summary[0]))
    works=[]
    for sid in sorted({r['source_id'] for r in units}):
        group=[r for r in units if r['source_id']==sid]
        works.append({'work':sid,'partition':group[0]['partition'],'units':len(group),
            'accepted':sum(r['accepted_label'] is not None for r in group),'pending':sum(r['accepted_label'] is None for r in group)})
    csv_write(META/'coverage-by-work.csv',works,list(works[0]))
    write(META/'parent-candidate-dispositions.json',parent_dispositions)
    sources=read(META/'source-registry-final.json')
    assert len(sources['new_candidates'])==8 and sources['S_closed']
    media=sum(s['status']=='public_video_accessible_transcription_pending' for s in sources['new_candidates'])
    verification={'passed':True,'all_123_parents_accounted':True,'full_source_text_preserved':True,
        'evidence_and_hashes_valid':True,'all_units_at_most_384_tokens':True,
        'all_required_reviews_exported_blind':True,'S_unchanged_and_closed':True,
        'no_BETO_predictions_or_training':True,'new_sources':8,'accessible_direct_videos':media,
        'new_captions_acquired':sum('captions_sha256' in r for r in sources['new_candidates'])}
    write(META/'verification.json',verification)
    ledger=read(ART/'budget-ledger-current.json')
    ledger.update(new_unique_annotation_proposals=summary['cumulative_distinct_annotated_inputs'],
        annotation_budget_remaining=1200-summary['cumulative_distinct_annotated_inputs'],
        services_paid_USD=0,phase_B_second_review_calls=0,
        annotation_count_note='Conservative distinct input-text hashes: 12 old + 121 newly annotated; four exact reuse cases')
    replace_with_archive(ART/'budget-ledger-current.json',ledger,META/'budget-ledger-before.json')
    status=read(ART/'status.json')
    status.update(phase='B_full_existing_candidate_first_pass_complete_review_pending',
        B='125 units from all 123 candidates; 56 first-pass T references, 69 pending review; eight added source candidates',
        C_to_G='not_started; independent review, coverage and final splits still pending',
        phase_B_completion_summary='artifacts/beto-v3/phase-b-completion-01/summary.json',
        current_units='outputs/beto-v3/phase-b-completion-01/units-and-annotations.json',
        current_sources='artifacts/beto-v3/phase-b-completion-01/source-registry-final.json',
        usage=ledger,blockers=['69 reviews pending: separate review call not executed',
            'V still has one annotated work and no colonial or military proposals',
            'T has 85 units, only one colonial proposal and several classes below acquisition targets',
            'Three newly located accessible videos require timed ASR pilot and full transcription QA'],
        completed_artifacts={**status.get('completed_artifacts',{}),'processed_parent_candidates':123,
            'corrected_units':125,'first_pass_annotation_proposals_current':125,'accepted_training_references':56,
            'pending_reviews':69,'additional_source_candidates':8,'accessible_new_video_files':media},
        resume_check='outputs/venv-ml/Scripts/python.exe -X utf8 scripts/finalize_beto_v3_phase_b_completion.py')
    replace_with_archive(ART/'status.json',status,META/'status-before.json')
    rows=['| Clase | T aceptadas | T pendientes | V aceptadas | V pendientes |', '| --- | ---: | ---: | ---: | ---: |']
    rows += [f"| {r['class']} | {r['T_accepted']} | {r['T_pending']} | {r['V_accepted']} | {r['V_pending']} |" for r in class_summary]
    report=['# Fase B: procesamiento completo del lote existente','',
        'Se revisaron los **123 candidatos completos**, incluyendo introducciones, transiciones y créditos. La segmentación resultante contiene **125 unidades (85 T y 40 V)**. Los movimientos de límite, uniones y divisiones están documentados por offsets de texto, cues y candidatos de origen. No se descartó contenido ni se reconstruyeron nombres/fechas de forma conjetural. Todas las entradas tienen como máximo 384 tokens. Los tiempos conservan la precisión de los subtítulos; un recorte dentro de un cue no inventa un tiempo por palabra.','',
        'Todas las unidades tienen una propuesta real de primera pasada, evidencia literal y regla. Se reutilizaron **4 de las 12 propuestas anteriores** con texto y guía idénticos; los otros ocho inputs antiguos se conservan, pero no se trasladaron etiquetas a textos cambiados. Los casos ambiguos o con ASR/límites irresolubles siguen pendientes.','',
        '**56 referencias T** quedaron aceptadas por primera pasada fuera de la muestra de revisión. **69 quedan pendientes**: las 40 V y 29 T. Entre estas últimas están los ambiguos/defectuosos y los 14 sorteados entre 70 T restantes (20%, semilla 20260909). No se ejecutó ni se simuló una llamada aislada de segunda revisión: la lectura actual es una sola pasada. Se exportaron 5 lotes de hasta 15 entradas, con guía e inputs exactos, sin propuestas anteriores, para esa revisión separada. Estas referencias no son gold experto y ninguna unidad está habilitada globalmente para entrenar.','',
        *rows,'',
        'Los pendientes se agrupan por su **propuesta**, no por una etiqueta adjudicada. La tabla completa por clase, obra y partición es `coverage-by-class-work-partition.csv`; también hay resúmenes por clase y obra. V carece de propuestas coloniales y militares, y sigue representada por una sola obra. No se rebajaron los requisitos del plan.','',
        '## Ocho fuentes adicionales','',
        '| ID / rol propuesto | Fuente y carencia | Resultado comprobado |','| --- | --- | --- |',
    ]
    for source in sources['new_candidates']:
        result='Video directo accesible por HEAD 200; sin transcripción' if source['status']=='public_video_accessible_transcription_pending' else ('Sin subtítulos; duración 51:11' if source['source_id']=='N01' else ('HTTP 403' if '403' in source.get('error','') else 'Convocatoria sin grabación única expuesta'))
        report.append(f"| {source['source_id']} / {source['proposed_role']} | [{source['title']}]({source['url']}) — {source['gap']} | {result} |")
    report += ['',
        'Se continuó con otras fuentes tras cada bloqueo. N03, N07 y N08 exponen archivos de video públicos accesibles; no requieren que la usuaria los aporte. Están registrados para descarga y piloto ASR local antes de transcribirlos completos. N03 dura 18 minutos, por debajo de la meta de 30; se declara sin ampliar artificialmente su duración. No se ha verificado aún la integridad audiovisual de esos archivos ni su independencia por contenido: permanecen fuera de las particiones finales. Se conserva también la limitación de concentración por canal.','',
        'Si se dispone de archivos propios autorizados, son especialmente útiles un **SRT/VTT español completo de Reformas Borbónicas (N01)** para antecedentes coloniales de V, y un **SRT/VTT o audio/video original de Batalla de Ayacucho (N02)** para campañas militares de V. Los enlaces exactos están en la tabla; no sirven resúmenes ni transcripciones sin procedencia. No son necesarios para terminar el procesamiento del lote que aquí se entrega.','',
        '## Archivos y reanudación','',
        '- Unidades, procedencia y anotaciones: `outputs/beto-v3/phase-b-completion-01/units-and-annotations.json` y `annotations.csv`.',
        '- Revisión pendiente: `review-input-blind.json` y `review-batches/batch-001.json` a `batch-005.json`; obtener una decisión independiente por ID, conservar modelo/configuración expuestos y adjudicar sin predicciones de BETO.',
        '- Trazabilidad: `artifacts/beto-v3/phase-b-completion-01/segmentation-changes.json` y `parent-candidate-dispositions.json`.',
        '- Registro ampliado: `source-registry-final.json`, con reservas heredadas, roles provisionales, URLs y recibos de acceso.',
        '',
        '**Servicios pagados: US$0.** Entrenamientos/ASR nuevos: 0. Consumo conservador de anotación: 133 inputs distintos acumulados de 1.200, quedan 1.067. Revisión y nuevas transcripciones todavía pendientes; S permanece cerrada y no se calculó F1 ni se entrenó.','',
        'Reproducción y comprobación:', '```powershell',
        'outputs/venv-ml/Scripts/python.exe -X utf8 scripts/complete_beto_v3_phase_b.py',
        'outputs/venv-ml/Scripts/python.exe -X utf8 scripts/finalize_beto_v3_phase_b_completion.py',
        '```','',
        'El primer comando reutiliza el lote congelado. El segundo comprueba cobertura de texto, evidencias, revisión, reservas y actualiza el estado. Las adquisiciones son reproducibles mediante `acquire_beto_v3_phase_b_sources.py` y `probe_beto_v3_phase_b_media.py`, que reutilizan sus recibos. Los archivos anteriores quedan archivados.']
    write(DOC/'fase-B-lote-completo.md',('\n'.join(report)+'\n').encode('utf-8'))
    archive=META/'progress-before.md'
    if not archive.exists():write(archive,(DOC/'progress.md').read_bytes())
    header='''# BETO V3: estado actual

Fase B: procesados los 123 candidatos; 125 unidades con propuestas y evidencia. Hay 56 referencias T aceptadas en primera pasada y 69 casos pendientes de revisión separada (40 V y 29 T). Reutilizadas cuatro anotaciones exactas. Ningún entrenamiento nuevo; S cerrada; servicios pagados US$0.

Se buscaron ocho fuentes adicionales a partir de las carencias calculadas. Tres videos de PUCP tienen enlace directo accesible; requieren piloto ASR y revisión. No se obtuvo ningún nuevo archivo de subtítulos. V aún carece de clases coloniales y militares y de diversidad de obras suficiente.

El detalle vigente, tablas y comandos están en [fase-B-lote-completo.md](fase-B-lote-completo.md). Datos: `outputs/beto-v3/phase-b-completion-01/`. Registro y controles: `artifacts/beto-v3/phase-b-completion-01/`. Estado y presupuesto acumulados: `artifacts/beto-v3/status.json` y `budget-ledger-current.json`.

F1 macro 0,70 no se ha evaluado en V3. Pendiente: segunda revisión real, adjudicación, nuevas transcripciones y congelación de particiones conforme al plan. El estado previo se conserva en `artifacts/beto-v3/phase-b-completion-01/progress-before.md`.
'''
    (DOC/'progress.md').write_text(header,encoding='utf-8')
    print(json.dumps(verification,ensure_ascii=False))

if __name__=='__main__':main()
