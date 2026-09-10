"""Reconstruct every archived previous-context span without reading annotations/predictions."""
import json
import re
from prepare_beto_context_v2 import ART,OUT,ROOT
import run_beto_first_training_v2 as b
from run_beto_context_v2 import save_same

def main():
    rows=b.read(b.OUT/'canonical-dataset.json')['items']
    parents=[json.loads(s) for s in (ROOT/'outputs/beto-v2/pilot/candidates.jsonl').read_text(encoding='utf-8').splitlines()]
    byparent={r['segment_id']:r for r in parents}
    corrections={r['correction_id']:r for r in b.read(ROOT/'outputs/beto-v2/pilot/visual-corrections.json')}
    entries=[]
    for r in rows:
        if r['role']!='new_AI' or not r.get('context',{}).get('previous'):continue
        previous=r['context']['previous'];pid=r.get('parent_id');loc={}
        if pid:
            parent=byparent[pid];offset=(r.get('parent_offsets') or [0])[0]
            if offset:
                expected=parent['text'][max(0,offset-800):offset]
                loc={'parent_id':pid,'parent_char_span':[max(0,offset-800),offset],'context_block_ids':parent['block_ids'],'context_pages':parent['pages']}
            else:
                sourceparents=[p for p in parents if p['source_id']==r['source_id']];i=sourceparents.index(parent)
                expected=parent['context']['previous'][-800:]
                if i:
                    prev=sourceparents[i-1]
                    assert prev['text']==parent['context']['previous']
                    loc={'parent_id':prev['segment_id'],'parent_char_span':[max(0,len(prev['text'])-800),len(prev['text'])],
                         'context_block_ids':prev['block_ids'],'context_pages':prev['pages']}
        else:
            import fitz
            def clean(t):
                return re.sub(r'\s+',' ',re.sub(r'(?<=\w)-\s*\n\s*(?=[a-záéíóúñü])','',t)).strip()
            correction=corrections[r['correction_id']]
            with fitz.open(ROOT/f"outputs/beto-v2/corpus/{r['source_id']}/source.pdf") as doc:
                block=doc[correction['page']-1].get_text('blocks')[correction['block_index_unsorted']]
            expected=clean(block[4][:correction['raw_offsets'][0]])
            loc={'correction_id':r['correction_id'],'context_pages':[correction['page']],
                 'block_index_unsorted':correction['block_index_unsorted'],'raw_char_span':[0,correction['raw_offsets'][0]]}
        assert previous==expected,r['segment_id']
        entries.append({'segment_id':r['segment_id'],'source_id':r['source_id'],'family_id':r['family_id'],
                        'previous_context_sha256':b.fingerprint(previous),'reconstructed_exactly':True,**loc})
    save_same(ART/'archived-context-locations.json',{'items':entries,'count':len(entries),
        'inputs':{str(p.relative_to(ROOT)):b.filehash(p) for p in [ROOT/'outputs/beto-v2/pilot/candidates.jsonl',ROOT/'outputs/beto-v2/pilot/visual-corrections.json']}})
    print({'archived_contexts_reconstructed':len(entries)})

if __name__=='__main__':main()
