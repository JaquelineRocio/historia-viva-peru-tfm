"""Final provenance, tokenization and full-pool overlap checks; no model inference."""
from process_beto_pilot_v2 import *

def main():
    suffix='-recovered' if '--recovered' in sys.argv else ''
    candidate_file='annotation-candidates-final.jsonl' if suffix else 'annotation-candidates-v2.jsonl'
    rows=[json.loads(x) for x in (OUT/candidate_file).read_text(encoding='utf-8').splitlines()]
    parents={x['segment_id']:x for x in [json.loads(l) for l in (OUT/'candidates.jsonl').read_text(encoding='utf-8').splitlines()]}
    blocks={x['block_id']:x for x in [json.loads(l) for l in (OUT/'layout-blocks.jsonl').read_text(encoding='utf-8').splitlines()]}
    corrected={x['correction_id']:x for x in read(OUT/'visual-corrections.json')}
    manifest=read(ART/'processing-manifest.json'); selection=read(ART/'selection.json')
    for rel,h in manifest['inputs_sha256'].items():assert sha((ROOT/rel).read_bytes())==h,rel
    assert sha((OUT/'annotation-input.json').read_bytes())==selection['input_sha256']
    reserved=set(manifest['reserved_ids_excluded'])
    tok=AutoTokenizer.from_pretrained(ROOT/manifest['tokenizer_path'],local_files_only=True)
    provenance=[]; issues=[]
    for r in rows:
        assert r['source_id'] not in reserved and r['label'] is None and r['split'] is None
        assert r['text_sha256']==sha(r['text'].encode())
        assert r['beto_tokens']==len(tok(r['text'],truncation=False)['input_ids'])
        if r.get('rescued_block_id'):
            b=blocks[r['rescued_block_id']]
            assert re.sub(r'(?<=\w)\u00ad\s*(?=\w)','',b['text'])==r['text']
            assert b['text_original']==r['text_original']
            provenance.append({'segment_id':r['segment_id'],'pages_exact':[b['page']],'rescued_block_id':b['block_id'],'bbox':b['bbox'],'status':'pending_OCR_and_boundaries'})
        elif r.get('correction_id'):
            c=corrected[r['correction_id']]
            assert c['corrected']==r['text'] and c['original']==r['text_original']
            assert sha((ROOT/c['evidence_image']).read_bytes())==c['evidence_sha256']
            provenance.append({'segment_id':r['segment_id'],'pages_exact':[c['page']],'visual_correction':c['correction_id'],'evidence':c['evidence_image']})
        else:
            p=parents[r['parent_id']]; start,end=r.get('parent_offsets',[0,len(p['text'])])
            original=p['text'][start:end]
            assert re.sub(r'(?<=\w)\u00ad\s*(?=\w)','',original)==r['text']
            mapped=[];offset=0
            for bid in p['block_ids']:
                b=blocks[bid]; z=offset+len(b['text'])
                lo=max(start,offset);hi=min(end,z)
                if lo<hi:mapped.append({'block_id':bid,'page':b['page'],'bbox':b['bbox'],'normalized_block_offsets':[lo-offset,hi-offset]})
                offset=z+1
            assert ' '.join(blocks[b]['text'] for b in p['block_ids'])==p['text']
            provenance.append({'segment_id':r['segment_id'],'parent_id':p['segment_id'],'parent_offsets':[start,end],'pages_exact':sorted({b['page'] for b in mapped}),'source_spans':mapped,'roundtrip':'parent slice then declared soft-hyphen transform; source blocks preserved'})
        flags=list(r['quality_flags'])
        if re.search(r'Revista del Archivo|The Maritime|Abstract|ISSN|doi:|Recibido:|Aprobado:',r['text']):flags.append('paratext_or_language_review')
        if r['beto_tokens']<25:flags.append('short_context_dependent_review')
        if flags:issues.append({'segment_id':r['segment_id'],'source_id':r['source_id'],'status':'pending','reasons':sorted(set(flags))})
    # Final text revisions must be included, not merely the coarse 18-span or previous checkpoint.
    old=read(OUT/'duplication-complete-v2.json'); refs={}
    for rel,h in old['historical_files_sha256'].items():
        assert sha((ROOT/rel).read_bytes())==h
        for i,r in enumerate(read(ROOT/rel).get('items',[])):
            t=r.get('text','');n=normalize(t)
            if n:refs.setdefault(n,{'text':t,'versions':[]})['versions'].append({'dataset':rel,'index':i,'record_id':r.get('id'),'resource_id':r.get('resourceId')})
    pool=[{'kind':'historical','key':sha(n.encode()),**r} for n,r in refs.items()]+[{'kind':'candidate','key':r['segment_id'],'text':r['text']} for r in rows]
    inv=defaultdict(set);gs=[];alerts=[];exact_index=defaultdict(set)
    for i,r in enumerate(pool):
        g=grams(r['text']);gs.append(g);n=normalize(r['text']);possible=set(exact_index[n])
        for w in g:possible.update(inv[w])
        if r['kind']=='candidate':
            for j in sorted(possible):
                jac,con=similarities(g,gs[j]);exact=n==normalize(pool[j]['text'])
                if exact or jac>=.25 or con>=.8:
                    relation='text_overlap_pending_review'
                    if pool[j]['kind']=='candidate':
                        a=next(x for x in rows if x['segment_id']==r['key']);b=next(x for x in rows if x['segment_id']==pool[j]['key'])
                        if a.get('parent_id') and a.get('parent_id')==b.get('parent_id'):relation='same_record_alternative_segmentation'
                        elif a['source_id']==b['source_id'] and ('visual' in a['segment_id'] or 'visual' in b['segment_id']):relation='corrected_OCR_and_original_same_work'
                    alerts.append({'candidate_id':r['key'],'other_kind':pool[j]['kind'],'other_id':pool[j]['key'],'versions':pool[j].get('versions',[]),'exact':exact,'jaccard':jac,'containment':con,'relation':relation})
        for w in g:inv[w].add(i)
        exact_index[n].add(i)
    save(OUT/f'provenance-final{suffix}.json',provenance)
    save(OUT/f'quality-queue-final{suffix}.json',{'segments':issues,'sources':read(OUT/'transcripts-preserved.json') and [{'source_id':s,'reason':'rights_review; ASR boundaries and complete video duration unknown','status':'pending','duration_retrieval_attempt':'web open YouTube watch failed, no fallback evasion'} for s in ['V01','V02']],'warning':'absence of automatic flags does not certify extraction quality; only pilot receives semantic review'})
    save(OUT/f'duplication-final{suffix}.json',{'candidates_checked':len(rows),'historical_files_sha256':old['historical_files_sha256'],'historical_unique_texts':len(refs),'historical_versions':'duplication.json/version_groups','alerts':alerts,'method':old['method'],'documentary_dependence':'source-groups-v2.json: provisional original work families; author/publisher/citation not identity','reserved_content_read':False})
    bysource={s:{'pages_processed':manifest['source_stats'][s]['pages_processed'],'candidate_versions':sum(r['source_id']==s for r in rows),'pending_automatic_quality':sum(r['source_id']==s for r in issues),'pilot_selected':sum(x.startswith(s+'-') for x in selection['ids'])} for s in IDS}
    metrics={'candidate_versions':len(rows),'underlying_sentence_candidates':len(rows)-2,'alternative_whole_paragraphs':2,'pending_automatic_quality':len(issues),'without_automatic_quality_flags':len(rows)-len(issues),'source_counts':bysource,'separated_block_counts':dict(Counter(b['kind'] for b in blocks.values())),'tokens':{'min':min(r['beto_tokens'] for r in rows),'max':max(r['beto_tokens'] for r in rows),'over_192':sum(r['beto_tokens']>192 for r in rows),'over_512':sum(r['beto_tokens']>512 for r in rows)},'duplicate_alerts':len(alerts),'duplicate_relations':dict(Counter(a['relation'] for a in alerts)),'historical_alerts':sum(a['other_kind']=='historical' for a in alerts),'checks':{'all_final_texts_tokenized_without_truncation':True,'source_roundtrip':True,'original_input_hashes_unchanged':True,'reserved_excluded':True,'selected_input_unchanged':True,'no_training_no_BETO_inference':True},'script_sha256':sha(Path(__file__).read_bytes())}
    metrics['pending_raw_recovered_blocks']=sum('rescued_block_id' in r for r in rows)
    metrics['underlying_sentence_candidates']=len(rows)-2-metrics['pending_raw_recovered_blocks']
    save(ART/f'checks{suffix}.json',metrics);print(json.dumps(metrics,ensure_ascii=False))
if __name__=='__main__':main()
