"""Compare development text only; reservations checked by identifiers, never content."""
import re, hashlib
from itertools import combinations
from acquire_beto_v3_gap_batch import ROOT, ART, DEST, read, save
def grams(text,n=12):
    words=re.findall(r'\w+',text.lower())
    return {hashlib.sha256(' '.join(words[i:i+n]).encode()).digest() for i in range(max(0,len(words)-n+1))}
old=read(ROOT/'outputs/beto-v3/phase-b-completion-01/all-development-units.json')['items']
works={}
for row in old:
    assert row['partition']!='S'
    works.setdefault(row['source_id'],{'role':row['partition'],'text':[]})['text'].append(row['text'])
new_ids=[]
for receipt in sorted(DEST.glob('*/receipt.json')):
    r=read(receipt);p=receipt.parent/'cues.json'
    if not p.exists():p=receipt.parent/'asr/cues.json'
    if not p.exists():continue
    assert r['role']!='S'
    works[r['source_id']]={'role':r['role'],'text':[x['text'] for x in read(p)]};new_ids.append(r['source_id'])
sets={sid:grams(' '.join(r['text'])) for sid,r in works.items()}
rows=[]
for a,b in combinations(works,2):
    if a not in new_ids and b not in new_ids:continue
    overlap=len(sets[a]&sets[b]);den=min(len(sets[a]),len(sets[b]))
    if overlap:rows.append(dict(a=a,b=b,role_a=works[a]['role'],role_b=works[b]['role'],shared_12grams=overlap,minimum_work_12grams=den,containment=overlap/den if den else 0))
rows.sort(key=lambda r:r['containment'],reverse=True)
reserve=read(ART/'reserve-metadata.json')['sources']
plan=read(ART/'acquisition-plan.json')
assert not {r['video_id'] for r in reserve}&{r['video_id'] for r in plan['sources']}
save(ART/'development-overlap.json',dict(pairs=rows,development_works=len(works),S_content_accessed=False,method='Exact normalized 12-word windows; no semantic/visual/audio fingerprint verification',conclusion='Screen only; low exact overlap does not prove original-work independence. G04-G06 one presentation. G16/G17 require speaker/event comparison. Final source admission pending.'))
print('works',len(works),'nonzero overlaps',len(rows),'max',rows[:3])
