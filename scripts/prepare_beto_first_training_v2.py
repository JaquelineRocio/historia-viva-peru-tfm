"""Freeze a small additional annotation batch from existing readable passages."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/beto-v2/first-training'
IDS = '''S01-seg0005-s00000 S01-seg0005-s02191 S01-seg0007-s01472
S01-seg0007-s04313 S01-seg0007-s06192 S01-seg0007-s05495
S01-seg0008-s00000 S01-seg0010-s02676
S03-seg0005-s00000 S03-seg0017-s00000 S03-seg0019-s00000
S03-seg0022-s00000 S03-seg0062-s00000
S06-seg0008-s00000 S06-seg0010-s00000 S06-seg0022-s00000
S06-seg0035-s00000 S06-seg0040-s00000
S10-seg0010-s00717 S10-seg0012-s00000 S10-seg0015-s00645
S15-seg0010-s00000 S15-seg0017-s00000'''.split()

def main():
    rows = [json.loads(s) for s in (ROOT/'outputs/beto-v2/pilot/annotation-candidates-final.jsonl').read_text(encoding='utf-8').splitlines()]
    old = json.loads((ROOT/'outputs/beto-v2/pilot/annotation-input.json').read_text(encoding='utf-8'))
    byid = {r['segment_id']: r for r in rows}
    assert not set(IDS) & {r['segment_id'] for r in old['items']}
    selected = [byid[i] for i in IDS]
    assert all(r['status']=='usable_candidate' and not r['quality_flags'] for r in selected)
    assert len(IDS)==len(set(IDS)) <= 70
    config = old['config']
    assert config['guide_sha256']==hashlib.sha256((ROOT/'docs/beto-v2/guia-etiquetado-v2.md').read_bytes()).hexdigest()
    payload = dict(config=config, selection='23 additional passages, five works; targeted reading of existing readable material for constitutional sovereignty, colonial structures and boundary contrasts. No label quota; no new sources needed for this bounded batch.', items=[{k:r[k] for k in ('segment_id','source_id','family_id','format','pages','text','context','beto_tokens')} for r in selected])
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/'annotation-input.json').open('x',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    print(len(selected))

if __name__=='__main__': main()
