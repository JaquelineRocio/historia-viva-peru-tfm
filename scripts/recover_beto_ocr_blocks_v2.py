"""Recover page-spanning OCR blocks falsely categorized by edge-position heuristic."""
from process_beto_pilot_v2 import *
def main():
    rows=[json.loads(x) for x in (OUT/'annotation-candidates-v2.jsonl').read_text(encoding='utf-8').splitlines()]
    blocks=[json.loads(x) for x in (OUT/'layout-blocks.jsonl').read_text(encoding='utf-8').splitlines()]
    tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
    recovered=[]
    for b in blocks:
        if b['kind']!='header_footer' or len(b['text'])<=250:continue
        sid=b['source_id'];t=re.sub(r'(?<=\w)\u00ad\s*(?=\w)','',b['text'])
        sourceblocks=[x for x in blocks if x['source_id']==sid];i=sourceblocks.index(b)
        row={'segment_id':b['block_id']+'-recovered','source_id':sid,'family_id':'family-'+sid,'format':'pdf','text':t,'text_original':b['text_original'],'source_sha256':sha((BASE/sid/'source.pdf').read_bytes()),'pages':[b['page']],'rescued_block_id':b['block_id'],'context':{'previous':sourceblocks[i-1]['text'][-800:] if i else '', 'next':sourceblocks[i+1]['text'][:800] if i+1<len(sourceblocks) else ''},'quality_flags':['visual_collation_required','page_edge_false_header','sentence_continuity_pending'],'status':'pending_extraction','label':None,'split':None,'text_sha256':sha(t.encode()),'beto_tokens':len(tok(t,truncation=False)['input_ids']),'transformations':['layout_block_extraction','line_end_hyphen_join','whitespace_collapse','soft_hyphen_layout_join','restore_false_header_as_pending_raw_unit']}
        rows.append(row);recovered.append({'block_id':b['block_id'],'old_kind':b['kind'],'new_kind':'pending_OCR_body_or_notes','reason':'long text block touches page edge; positional header classification unsafe','segment_id':row['segment_id']})
    lines(OUT/'annotation-candidates-final.jsonl',rows);save(OUT/'recovered-blocks.json',recovered)
    print(json.dumps({'recovered_pending_blocks':len(recovered),'total_candidate_versions':len(rows)}))
if __name__=='__main__':main()
