"""Freeze blind review inputs for completed first passes; no decisions exposed."""
import random,hashlib,json
from acquire_beto_v3_gap_batch import ROOT,ART,DEST,read,save
guide=(ROOT/'docs/beto-v3/guia-etiquetado-v3.md').read_text(encoding='utf-8')
if (ART/'review-integration.json').exists():
    print('Frozen review-run-01 already completed; create a distinct queue for the next lot.')
    raise SystemExit(0)
selected=[];selection=[]
for folder in sorted(DEST.glob('*/annotation')):
    passes=[r for p in sorted((folder/'first-pass').glob('batch-*.json')) for r in read(p)['items']]
    if not passes:continue
    units={r['segment_id']:r for r in read(folder/'units.json')['items']}
    role=next(iter(units.values()))['partition']
    required=[r for r in passes if role=='V' or r['ambiguous'] or r['extraction_defect'] or r['proposal'] is None]
    other=sorted([r for r in passes if r not in required],key=lambda r:r['segment_id'])
    rng=random.Random(42)
    sample=rng.sample(other,(len(other)+4)//5) if role=='T' else []
    ids={r['segment_id'] for r in required+sample}
    selection.append(dict(source_id=folder.parent.name,role=role,required_count=len(required),random_training_sample_count=len(sample),seed=42,selected_ids=sorted(ids)))
    for sid in sorted(ids):
        u=units[sid]
        selected.append({k:v for k,v in u.items() if k in ['segment_id','source_id','family_id','partition','text','input_sha256','guide_sha256','source_sha256','start_sec','end_sec','cue_indices','cue_pieces','source_char_span','tokens_with_specials']})
digest=hashlib.sha256(json.dumps(selected,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
paths=[]
for i in range(0,len(selected),15):
    p=DEST/'blind-review'/digest[:12]/f'batch-{i//15+1:03}.json'
    save(p,{'guide':guide,'items':selected[i:i+15],'required_output':'Per ID proposal/alternative/rule/rationale/literal evidence and span/ambiguity/extraction/boundary flags/model/exposed configuration. No BETO predictions. Do not consult first passes. Do not mark accepted labels.'})
    paths.append(str(p.relative_to(ROOT)))
save(ART/'blind-review-queue.json',dict(input_sha256=digest,units=len(selected),selection=selection,batches=paths,second_reviews_completed=0,independence='requires context without history; no independent review claimed',S_closed=True))
print(len(selected),'blind inputs;',len(paths),'batches')
