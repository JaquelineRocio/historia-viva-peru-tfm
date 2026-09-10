"""Independent delivery integrity checks, including cache, pass evidence and reservation."""
import hashlib,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/beto-v2/pilot'
ART=ROOT/'artifacts/beto-v2/pilot'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    manifest=read(ART/'delivery-manifest.json')
    for rel,h in manifest['outputs_sha256'].items():assert digest(ROOT/rel)==h,rel
    source=read(ART/'processing-manifest.json')
    for rel,h in source['inputs_sha256'].items():assert digest(ROOT/rel)==h,rel
    final=read(OUT/'pilot-annotated.json'); packet=read(OUT/'annotation-input.json');summary=read(ART/'annotation-summary.json')
    items={x['segment_id']:x for x in final['items']};inputs={x['segment_id']:x for x in packet['items']}
    assert set(items)==set(inputs) and len(items)==30
    decisions={x['segment_id']:x for x in read(OUT/'adjudication.json')['items']}
    reserve={x['source_id'] for x in read(ROOT/'artifacts/beto-v2/corpus/reserved-evaluation-sources-v2.json')['sources']}
    for sid,r in items.items():
        assert r['text']==inputs[sid]['text'] and r['context']==inputs[sid]['context']
        assert r['label']==decisions[sid]['final_label']
        assert r['label'] in final['labels']+[None] and r['split'] is None and r['training_eligible'] is False
        assert r['source_id'] not in reserve
        for p in ['pass_a','pass_b']:
            d=decisions[sid][p]
            assert d['text']==r['text'] and d['context']==r['context']
            assert r['text'][d['evidence_start']:d['evidence_end']]==d['evidence']
    assert sum(x['label'] is not None for x in items.values())==summary['accepted_AI_assisted']==29
    assert sum(x['pass_a']['label']==x['pass_b']['label'] for x in decisions.values())==summary['label_agreement_count']==30
    assert sum(x['pass_a']['ambiguity']==x['pass_b']['ambiguity'] for x in decisions.values())==summary['ambiguity_state_agreement_count']==27
    caches=read(OUT/'cache-index.json');assert len(caches)==60
    for c in caches:
        path=ROOT/c['path'];assert digest(path)==c['sha256'];row=read(path)
        payload={'text':row['text'],'context':row['context'],'guide_sha256':packet['config']['guide_sha256'],'configuration':row['config']}
        key=hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        assert key==c['key']==row['cache_key']
    dup=read(OUT/'duplication-final-recovered.json')
    assert not any(x['candidate_id'] in items and x['other_id'] in items for x in dup['alerts'])
    assert {'artifacts/datasets/external-development-v1.json','artifacts/datasets/evaluation-pilot-v2.json'}<=set(dup['historical_files_sha256'])
    allrows=[json.loads(l) for l in (OUT/'annotation-candidates-final.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(allrows)==dup['candidates_checked']==594
    assert all(r['source_id'] not in reserve for r in allrows)
    checks=read(ART/'checks-recovered.json')
    assert checks['pending_automatic_quality']==len(read(OUT/'quality-queue-final-recovered.json')['segments'])==199
    assert checks['without_automatic_quality_flags']==395
    result={'status':'passed','checks':['all_delivery_hashes','source_and_snapshot_hashes_unchanged','all_30_texts_contexts_and_labels_match_frozen_input_and_adjudication','all_60_evidence_offsets_literal','all_60_cache_keys_recomputed','no_reserved_ID_in_594_candidates_or_30_pilot','no_duplicate_alert_pair_inside_pilot','both_required_historical_datasets_in_final_overlap','30_label_agreements_27_state_agreements_29_accepted_1_pending','594_final_records_199_quality_pending_395_without_automatic_flags'],'documents_sha256':{rel:digest(ROOT/rel) for rel in ['docs/beto-v2/03-dataset-piloto.md','docs/beto-v2/guia-etiquetado-v2.md','docs/beto-v2/progress.md']},'validator_sha256':digest(Path(__file__))}
    with (ART/'delivery-validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
