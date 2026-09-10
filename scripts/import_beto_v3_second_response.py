"""Lossless import of actual authorized CLI response; add exact quote offsets."""
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/beto-v3/admission-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    raw=OUT/'isolated-second/response-utf8.json';response=read(raw)
    receipt=read(OUT/'isolated-second/receipt-utf8.json')
    assert receipt['exit_code']==0 and receipt['prompt_sha256']==sha(OUT/'isolated-second/prompt.txt')
    events=[json.loads(s) for s in (OUT/'isolated-second/events-utf8.jsonl').read_text(encoding='utf-8').splitlines()]
    assert all(e.get('item',{}).get('type') in (None,'agent_message') for e in events), 'Unexpected tool use in isolated review'
    usage=next(e['usage'] for e in events if e['type']=='turn.completed')
    rows={r['segment_id']:r for r in response['items']};assert len(rows)==len(response['items'])==30
    for packet in sorted((OUT/'annotation-inputs').glob('batch-*.json')):
        result=[]
        for u in read(packet)['items']:
            d=rows[u['segment_id']];assert d['input_sha256']==u['input_sha256']
            assert d['evidence'] in u['text'] and d['evidence']
            a=u['text'].index(d['evidence']);result.append({**d,'evidence_span':[a,a+len(d['evidence'])]})
        dest=OUT/'second-review'/packet.name;dest.parent.mkdir(exist_ok=True)
        data={'model':receipt['model'],'model_weights':'unknown','session':'admission_second_cli_utf8','stage':'second-review',
              'raw_response':str(raw.relative_to(ROOT)),'raw_response_sha256':sha(raw),'input_packet_sha256':sha(packet),
              'provider_usage_complete_session':usage,'usage_note':'Same single session usage repeated for provenance; count it once, not once per batch',
              'items':result}
        if dest.exists():assert read(dest)==data
        else:dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Imported 30 real responses, exact hashes and quotes verified; no new judgments generated')
if __name__=='__main__':main()
