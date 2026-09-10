"""Build immutable phase-A artifacts from V2; never read reserved corpus text."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'artifacts/beto-v3'
OUT = ROOT/'outputs/beto-v3'
DOC = ROOT/'docs/beto-v3'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    data = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Frozen artifact differs: '+str(path))
    else:
        with path.open('xb') as f:
            f.write(data)

def prepare():
    source = ROOT/'outputs/beto-v2/first-training/canonical-dataset.json'
    canonical = read(source)
    original = canonical['items']
    assert len(original) == 591 and len({r['segment_id'] for r in original}) == 591
    reserved = canonical['reserved_final']['source_ids']
    assert not set(reserved) & {r['source_id'] for r in original}
    assert all(r['training_eligible'] for r in original)
    protocol_v2 = read(ROOT/'artifacts/beto-v2/first-training/protocol.json')
    # Copies are additive. Final H must be re-frozen after V/S work-overlap checks.
    rows = [{**r, 'v3_role':'H', 'reference_status':'inherited_not_exhaustively_verified',
        'parent_dataset_sha256':sha(source)} for r in original]
    write(OUT/'datasets/H-initial.json', {'version':'H-initial-v3', 'items':rows,
        'status':'frozen_initial_base_pending_video_family_exclusions', 'corrections':[],
        'parent':str(source.relative_to(ROOT)), 'parent_sha256':sha(source)})
    write(ART/'historical-changes.json', {'changes':[], 'policy':'Only documentary evidence; no automatic relabeling from predictions'})
    guide_source = ROOT/'docs/beto-v2/guia-etiquetado-v2.md'
    guide = guide_source.read_text(encoding='utf-8')
    guide += '''

## Aplicación V3 (prevalece sobre las instrucciones de flujo V2)

Se conservan R0–R7, las siete categorías y el alcance 1780–1842. No hay cambio de tarea.
En V3 se permite asignar fuentes a T/V/S y entrenar únicamente tras congelar datos y referencias.
La entrada inicial es únicamente el objetivo auténtico normalizado; no se añade contexto generado
ni contexto invisible para BETO. Máximo 384 tokens con especiales, truncamiento registrado.
Una mención constitucional no decide R2/R5: distinguir ruptura de legitimidad y funcionamiento
institucional. Un nombre no decide R4. Distinguir proyecto disputado R4 de implantación R5;
agencia social R6 de desarrollo militar R3 o norma como objeto R5. La fecha aislada no decide R7.
Cada pasada conserva entrada exacta, hash, evidencia, regla, alternativa y banderas.
En V/S se revisan todas las referencias antes de predicciones; en T todos los ambiguos y un 20%
aleatorio de aceptados. Si las sesiones usan el mismo modelo, declarar su dependencia.
Los casos sin referencia única quedan en el inventario y fuera del F1, con cobertura publicada.
Las referencias asistidas por IA no son gold experto. No se usa no_relevante para incertidumbre.
'''
    write(DOC/'guia-etiquetado-v3.md', guide.encode('utf-8'))
    write(ART/'guide-compatibility.json', {'parent_sha256':sha(guide_source),
        'v3_sha256':sha(DOC/'guia-etiquetado-v3.md'), 'substantive_task_change':False,
        'changes':['Explicit boundary questions consistent with R0-R7',
                   'V2 workflow prohibition on splits replaced by V3 freeze gates',
                   'Annotator input equals classifier input; target only']})
    write(ART/'reserved-index.json', {'inherited_final':canonical['reserved_final'],
        'inherited_evaluations':canonical['historical_evaluations'],
        'new_S_status':'pending_distinct_video_works', 'text_accessed':False,
        'v2_reserved_manifest_sha256':sha(ROOT/canonical['reserved_final']['manifest']),
        'prohibited_development_uses':['train','annotation_training_examples','inference','TAPT','MLM','context_retrieval']})
    config = {'version':'beto-v3.1', 'status':'preregistered_data_not_ready',
        'labels':canonical['labels'], 'scope':[1780,1842], 'base_model':protocol_v2['base_model'],
        'revision':protocol_v2['revision'], 'base_hashes':protocol_v2['base_hashes'],
        'versions':protocol_v2['versions'], 'max_length':384, 'representation':'normalized_authentic_target_only',
        'recipe':{'microbatch':2,'gradient_accumulation':8,'effective_batch':16,'optimizer':'AdamW',
            'weight_decay':.01,'clip_norm':1.,'precision':'AMP float16','warmup_ratio':.1,
            'scheduler':'linear; fresh horizon for each trajectory','class_weights':'inverse_frequency_train_only',
            'loss_normalization':'sum_weighted_CE / sum_weights_effective_batch'},
        'recipes':{'R0':{'data':['H'],'lr':2e-5,'epochs':4},
            'R1':{'data':['H','T300'],'lr':2e-5,'epochs':4},
            'R2':{'data':['H','T300'],'lr':2e-5,'epochs':20},
            'R3':{'data':['H','T300'],'lr':1e-5,'epochs':20}},
        'selection':{'initial_seed':42,'confirmation_seeds':[43,44],
            'checkpoint':'maximum validation macro F1; earliest epoch breaks ties',
            'candidate':'best R1-R3; within 0.005 prefer lower measured cost',
            'E_gate':{'paired_delta_mean_min':.02,'positive_seeds_min':2,'coverage_errors_required':True},
            'F':'at most one: transcript_only (3 fits) OR TAPT (500 updates / 1 hour + 3 fits)',
            'delivery_seed':42,'final_epochs':'median best development epochs',
            'S':'one final phase after recipe/data/reference freeze; never seed selection'},
        'budget':{'new_annotation_units':1200,'historical_review_units':60,'T_max':600,
            'new_trajectories':18,'supervised_fits':17,'MLM_trajectories':1,
            'CD_gpu_seconds':14400,'total_training_gpu_seconds':28800,'ASR_gpu_seconds':28800,
            'phase_fits':{'C':4,'D':4,'E':3,'F':4,'G':3}, 'failures_count':True,
            'scope':'All new V3 phases cumulatively; V2 prior use recorded separately without claiming it is zero'},
        'evaluation':{'labels_explicit':True,'zero_division':0,'primary':'pooled macro F1 over V units',
            'targets':{'macro_f1':.70,'minimum_class_f1':.50,'beats_matched_tfidf':True,
                'resolvable_reference_coverage':.90}, 'bootstrap_unit':'original video/work',
            'coverage_goals':{'T300_per_class':20,'T300_works_per_class':2,'V_S_per_class':25,'V_S_works_per_class':2}},
        'data_gate':['H/T/V/S family disjointness and reproduction checks',
            'real timestamped transcripts with duration/integrity checks',
            'seven class support on T and V, annotation review complete',
            'references and representation hashed before predictions'],
        'tfidf':protocol_v2['baselines'], 'plan_sha256':sha(DOC/'plan-beto-f1-070.md'),
        'guide_sha256':sha(DOC/'guia-etiquetado-v3.md')}
    write(ART/'protocol.json', config)
    # No predictions are used to select this bounded additional historical sample.
    previous_path = ROOT/'outputs/beto-v2/stability/reviewed-cases.json'
    previous = read(previous_path)
    previous_ids = {r['segment_id'] for r in previous}
    sample = sorted([r for r in rows if r['segment_id'] not in previous_ids and r['role']=='historical_train'],
        key=lambda r: hashlib.sha256(('beto-v3-A-sample:'+r['segment_id']).encode()).hexdigest())[:10]
    write(OUT/'historical-review-input.json', {'selection':'first ten by SHA256(beto-v3-A-sample:ID), excluding prior reviewed',
        'prior_reviewed_ids':sorted(previous_ids), 'total_unique_review_ceiling_used_if_completed':len(previous_ids|{r['segment_id'] for r in sample}),
        'status':'pending_documentary_review', 'items':[{k:r[k] for k in ['segment_id','source_id','family_id','text','label','provenance']} for r in sample]})
    results = []
    curves = []
    for path in sorted((ROOT/'outputs/beto-v2').glob('**/result.json')):
        result = read(path)
        if result.get('status') != 'complete':
            continue
        results.append({'path':str(path.relative_to(ROOT)), 'sha256':sha(path),
            'seconds':result['seconds'],'best_epoch':result['best_epoch'],
            'f1_macro':result['metrics']['combined']['f1_macro'],
            'v3_reuse':'diagnostic_only_different_data_and_validation'})
        for h in result['history']:
            curves.append({'run':str(path.parent.relative_to(ROOT)), 'epoch':h['epoch'],
                'weighted_train_loss':h.get('weighted_train_loss'), 'train_f1_eval':None,
                'val_f1':h['f1_macro'],'optimizer_updates':h['optimizer_updates'],
                'amp_skips':h['amp_skips'],'checkpoint_available':(path.parent/f"checkpoint-{h['epoch']}").exists(),
                'resume_available':(path.parent/f"resume-epoch-{h['epoch']}.pt").exists()})
    context_events = [json.loads(line) for line in (ROOT/'outputs/beto-v2/context/execution-events.jsonl').read_text(encoding='utf-8').splitlines()]
    context = {'completed_runs':len(list((ROOT/'outputs/beto-v2/context').glob('**/result.json'))),
        'events':[ {k:e[k] for k in ['at_utc','status','error_type','error'] if k in e} for e in context_events],
        'manifest_sha256':sha(ROOT/'artifacts/beto-v2/context/manifest.json'),
        'decision':'preserve context extraction; do not restart isolated V2 experiment',
        'failed_gpu_seconds':None,'failed_time_note':'V2 events do not expose start/end durations; unknown, not zero'}
    write(ART/'prior-executions.json', {'runs':results,'phase07':context,
        'known_successful_training_seconds':sum(r['seconds'] for r in results),
        'complete_prior_gpu_total':None,'limitation':'Failure time not fully recoverable from old event logs'})
    write(ART/'prior-curves.json', curves)
    write(ART/'budget-ledger-initial.json', {'scope':'V3 cumulative across resumes', 'training_gpu_seconds':0,
        'CD_gpu_seconds':0,'ASR_gpu_seconds':0,'new_trajectories':0,'new_unique_annotated_units':0,
        'prior_usage':'prior-executions.json','updates':'append outputs/beto-v3/budget-events.jsonl; never reset this baseline'})
    write(ART/'phase-A-summary.json', {'H_rows':len(rows),'H_class_counts':dict(Counter(r['label'] for r in rows)),
        'H_families':len({r['family_id'] for r in rows}),'old_runs':len(results),'old_curve_epochs':len(curves),
        'phase07_complete_runs':context['completed_runs'],'corrections':0,
        'status':'base_prepared; train inference and sample review pending; final H awaits V/S family freeze'})
    print(json.dumps(read(ART/'phase-A-summary.json')))

if __name__ == '__main__':
    DOC.mkdir(parents=True, exist_ok=True)
    plan = DOC/'plan-beto-f1-070.md'
    if not plan.exists():
        write(plan, Path('D:/plan-beto-f1-070.md').read_bytes())
    prepare()
