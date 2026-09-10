"""Freeze a purposive varied pilot before annotation; no label-based selection."""
from process_beto_pilot_v2 import *
SELECTED='''S01-seg0005-s00704 S01-seg0005-s02873 S01-seg0005-s04319 S01-seg0012-s00703 S01-seg0014-s00683 S01-seg0019-s00000
S03-seg0006-s00000 S03-seg0009-s00000 S03-seg0015-s00000 S03-seg0037-s00000 S03-seg0042-s00577 S03-seg0044-s00991
S06-seg0005-s00000 S06-seg0016-s00000 S06-seg0020-s00000 S06-seg0032-s00000 S06-seg0036-s00000
S10-seg0003-s00000 S10-seg0005-s00000 S10-seg0010-s00000 S10-seg0014-s00000 S10-seg0034-s00606
S15-seg0007-s00000 S15-seg0008-s00000 S15-seg0025-s00000 S15-seg0057-s00000 S15-seg0061-s00000
S05-visual-p007-01 S05-visual-p007-02 S17-visual-p003-03'''.split()
def main():
    rows=[json.loads(x) for x in (OUT/'candidates-complete-v2.jsonl').read_text(encoding='utf-8').splitlines()]
    tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
    changes=[]
    for r in rows:
        before=r['text'];after=re.sub(r'(?<=\w)\u00ad\s*(?=\w)','',before)
        if after!=before:
            changes.append({'segment_id':r['segment_id'],'before_sha256':sha(before.encode()),'after_sha256':sha(after.encode()),'rule':'remove discretionary soft hyphen and following layout whitespace','original_reference':'candidates-complete-v2.jsonl','changes':list(__import__('difflib').ndiff(before.split(),after.split()))})
            r['text']=after;r['text_sha256']=sha(after.encode());r['transformations']+=['soft_hyphen_layout_join'];r['beto_tokens']=len(tok(after,truncation=False)['input_ids'])
    # Retain longer complete paragraphs as explicit alternative versions, not independent examples.
    parents={r['segment_id']:r for r in [json.loads(x) for x in (OUT/'candidates.jsonl').read_text(encoding='utf-8').splitlines()]}
    for pid in ['S01-seg0012','S01-seg0014']:
        p=parents[pid]; rows.append({**p,'segment_id':pid+'-whole','parent_id':pid,'version_relation':'alternative whole paragraph; do not count alongside sentence derivatives','context':{k:v[-800:] if k=='previous' else v[:800] for k,v in p['context'].items()}})
    # Select longer alternatives instead of their sentence children.
    ids=[x for x in SELECTED if not x.startswith(('S01-seg0012-','S01-seg0014-'))]+['S01-seg0012-whole','S01-seg0014-whole']
    byid={r['segment_id']:r for r in rows}; pilot=[byid[x] for x in ids]
    assert len(pilot)<=70 and all(r['status']=='usable_candidate' for r in pilot)
    config={'model':'GPT-6 (Codex session model; exact provider snapshot unavailable)','prompt_version':'beto-pilot-annotation-v2.0','pass_isolation':'separate fresh contexts; no previous labels or BETO predictions','guide_sha256':sha((ROOT/'docs/beto-v2/guia-etiquetado-v2.md').read_bytes()),'temperature':'not exposed by session runtime','annotation_origin':'AI-assisted; no expert gold'}
    safe=[{k:r[k] for k in ['segment_id','source_id','family_id','format','pages','text','context','beto_tokens']} for r in pilot]
    save(OUT/'annotation-input.json',{'config':config,'items':safe})
    lines(OUT/'annotation-candidates-v2.jsonl',rows);save(OUT/'soft-hyphen-transformations.json',changes)
    save(ART/'selection.json',{'ids':ids,'selection':'purposive before annotation; spans across article bodies and late pages; explicit historical/methodological and institutional/social boundary cases; no predicted labels or quotas','format_limitation':'PDF only; acquired transcripts pending rights and ASR review','count':len(ids),'guide_sha256':config['guide_sha256'],'input_sha256':sha((OUT/'annotation-input.json').read_bytes()),'longer_versions':{'S01-seg0012-whole':'replaces sentence children in pilot','S01-seg0014-whole':'replaces sentence children in pilot'}})
    print(json.dumps({'selected':len(pilot),'tokens':[min(r['beto_tokens'] for r in pilot),max(r['beto_tokens'] for r in pilot)],'candidates':len(rows)}))
if __name__=='__main__':main()
