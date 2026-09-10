"""Preselect remaining T inputs within the shared annotation/S allowance."""
import random,hashlib,json
from acquire_beto_v3_gap_batch import ROOT,ART,DEST,read,save
path=ART/'next-annotation-selection.json'
if path.exists():
    print('Selection cached; do not resample after seeing labels')
    raise SystemExit(0)
ledger=read(ROOT/'artifacts/beto-v3/budget-ledger-current.json')
selected=[];by_source=[]
for p in sorted(DEST.glob('*/annotation/units.json')):
    units=read(p)['items']
    done={r['segment_id'] for q in (p.parent/'first-pass').glob('batch-*.json') for r in read(q)['items']}
    remaining=[r for r in units if r['segment_id'] not in done]
    if not remaining:continue
    sid=p.parent.parent.name;role=units[0]['partition']
    if role=='V':chosen=remaining
    else:
        # Up to ten units in each temporal third, sampled without labels.
        rng=random.Random('gap-next-v1:'+sid);chosen=[]
        for third in range(3):
            group=remaining[len(remaining)*third//3:len(remaining)*(third+1)//3]
            chosen+=rng.sample(group,min(10,len(group)))
        chosen.sort(key=lambda r:r['start_sec'])
    selected+=chosen;by_source.append({'source_id':sid,'role':role,'candidate_count':len(remaining),'selected_count':len(chosen)})
remaining_after=ledger['annotation_budget_remaining']-len({r['input_sha256'] for r in selected})
assert remaining_after>=200,'Preserve room for S; do not annotate an oversized queue'
save(path,dict(selection_version='gap-next-v1',basis='All remaining V; T up to 10 per temporal third via fixed source-specific seed. No predictions or new labels inspected to select. Full transcript inventory retained.',sources=by_source,selected_ids=[r['segment_id'] for r in selected],inputs=len(selected),not_yet_annotated=True,annotation_ceiling=1200,current_consumed=ledger['new_unique_annotation_proposals'],projected_consumed=ledger['new_unique_annotation_proposals']+len(selected),remaining_after=remaining_after,S_planning_allowance=200,other_revision_headroom=remaining_after-200,S_content_opened=False))
guide=(ROOT/'docs/beto-v3/guia-etiquetado-v3.md').read_text(encoding='utf-8')
for i in range(0,len(selected),15):save(DEST/f'next-first-pass/batch-{i//15+1:03}.json',{'guide':guide,'items':selected[i:i+15]})
print(len(selected),'selected;',remaining_after,'inputs remain after future first pass')
