"""Recover only document-ordered context; freeze exact paired BETO inputs before fits."""
import bisect
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
import run_beto_first_training_v2 as b

ROOT=b.ROOT
OUT=ROOT/'outputs/beto-v2/context'
ART=ROOT/'artifacts/beto-v2/context'
SOURCES={
'747ca90f-92fc-4d19-aec4-6dfc34c2917e':'artifacts/demo/files/86cd8383-a0d1-40f6-a759-e2c5a2bf37a9.pdf',
'9f60a031-0183-478c-a1f8-a3bdd37d7b0b':'.corpus-downloads/orrego_primeros_anos_republicanos.pdf',
'9154f7f7-86c9-4bad-bcba-47eaf54b93e1':'.corpus-downloads/constitucion_1823.pdf',
'e32181bc-41d0-4400-a76d-eb11fc88bf71':'.corpus-downloads/fonseca_bandoleros_patrotas.pdf',
'9fecbe5a-9fb2-4002-a088-8a2810db938e':'artifacts/demo/files/a181d154-666b-4ca9-b2e3-dcd45d16b3f6.pdf',
'0ea45102-057d-4bff-b527-f36326f66d33':'.corpus-downloads/opheland_mito_independencia.pdf',
'17552e18-8e04-53f8-a48f-b60ed56fbbd0':'outputs/source-candidates-v1/josefa-montes.pdf',
'48262fb6-dee2-531e-b001-536c5928a9ca':'outputs/ideas-source-v1/huerta-2020.pdf',
'11b4365c-87f9-5b8d-802f-a0d2aafc478a':'outputs/source-diversity-v1/contreras-2011.pdf',
'7ef1a1d4-97c6-55cf-990b-3a7b1fbb0f9d':'outputs/source-diversity-v1/hunefeldt-1979.pdf',
'776e9620-a23b-54e8-bf0e-d5a27ed2969a':'outputs/corpus-batch-v2/women/arguedas-2022.pdf',
'08fa49e1-abac-5645-a35e-2d7ec4a8f05d':'outputs/training-batch-v3/hampe/article.pdf',
'1c8bc7af-a9f6-5392-b3ff-6d7433fb010a':'outputs/training-batch-v3/source-moran-2019.pdf',
**{s:f'outputs/beto-v2/corpus/{s}/source.pdf' for s in ['S01','S03','S05','S06','S10','S15','S17']}}

def normalized(text):
    chars=[]; offsets=[]
    for i,c in enumerate(text):
        for a in unicodedata.normalize('NFKD',c.casefold()):
            if a.isalnum():chars.append(a);offsets.append(i)
    return ''.join(chars),offsets

def clean(text):
    text=re.sub(r'(?<=\w)[-\u00ad]\s*\n\s*(?=\w)','',text)
    return ' '.join(text.replace('\u00ad','').split())

def extract(path):
    import fitz
    blocks=[];full=''
    with fitz.open(path) as doc:
        for pi,page in enumerate(doc):
            for bi,block in enumerate(page.get_text('blocks',sort=True)):
                if block[6]!=0 or not block[4].strip():continue
                blocks.append({'page':pi+1,'block':bi,'bbox':list(block[:4]),'page_height':page.rect.height,'start':len(full),'end':len(full)+len(block[4])})
                full+=block[4]+'\n'
    norm,offsets=normalized(full)
    return {'text':full,'normalized':norm,'offsets':offsets,'blocks':blocks}

def aligned(target,doc):
    needle,_=normalized(target)
    if len(needle)<80:return '',None,'target_too_short_for_unique_alignment'
    start=doc['normalized'].find(needle)
    if start<0:return '',None,'no_exact_normalized_full_target_alignment'
    if doc['normalized'].find(needle,start+1)>=0:return '',None,'ambiguous_multiple_locations'
    pos=doc['offsets'][start]
    blocks=doc['blocks'];idx=bisect.bisect_right([x['start'] for x in blocks],pos)-1
    block=blocks[idx];prefix=doc['text'][block['start']:pos]
    def doubtful(x):
        raw=doc['text'][x['start']:x['end']].strip()
        key=normalized(raw)[0]
        repeated=sum(normalized(doc['text'][z['start']:z['end']])[0]==key for z in blocks)>1
        return (repeated or bool(re.match(r'^\d+[.\s]',raw)) or
                (x['bbox'][1]<x['page_height']*.09 and len(raw.split())<25))
    if doubtful(block):return '',None,'target_block_header_or_note_boundary_ambiguous'
    # When a target starts mid-block, take exactly its preceding block prefix.
    # At a block boundary take the immediately preceding textual block, never a label-selected neighbor.
    begin=block['start']
    if len(normalized(prefix)[0])<8:
        if idx==0:return '',None,'document_start'
        if blocks[idx-1]['page']!=block['page'] or doubtful(blocks[idx-1]):
            return '',None,'previous_block_header_note_or_page_boundary_ambiguous'
        begin=blocks[idx-1]['start']
    context=clean(doc['text'][begin:pos])
    if len(context.split())<8:return '',None,'preceding_block_too_short_or_heading'
    loc={'method':'unique_full_target_NFKD_casefold_alphanumeric_match','target_char_start':pos,
         'target_char_end':doc['offsets'][start+len(needle)-1]+1,'context_char_start':begin,'context_char_end':pos,
         'blocks':[x for x in blocks if x['end']>begin and x['start']<pos],
         'target_page':block['page'],'target_block':block['block']}
    return context,loc,None

def encode(tok,text,context):
    original=dict(tok(text,padding='max_length',truncation=True,max_length=384))
    n=sum(original['attention_mask']);target=original['input_ids'][1:n-1]
    cids=tok(context,add_special_tokens=False)['input_ids'] if context else []
    take=min(95,len(cids),max(0,384-len(target)-3))
    if not take:return original,original.copy(),target,[]
    cids=cids[-take:];ids=[tok.cls_token_id]+target+[tok.sep_token_id]+cids+[tok.sep_token_id]
    types=[0]*(len(target)+2)+[1]*(len(cids)+1);n=len(ids)
    transformed={'input_ids':ids+[tok.pad_token_id]*(384-n),'token_type_ids':types+[0]*(384-n),'attention_mask':[1]*n+[0]*(384-n)}
    assert transformed['input_ids'][1:len(target)+1]==target
    assert set(original)==set(transformed)
    return original,transformed,target,cids

def prepare():
    from transformers import AutoTokenizer
    p,byid=b.inputs();rows=list(byid.values());assert len(rows)==591
    assert not (ART/'protocol.json').exists(),'Frozen manifest already exists; use runner to verify/reuse'
    tok=AutoTokenizer.from_pretrained(b.BASE,revision=b.REV,local_files_only=True)
    families=b.read(ROOT/'artifacts/beto-v2/first-training/families.json')['works']
    reserve=b.read(ROOT/'artifacts/beto-v2/corpus/reserved-evaluation-sources-v2.json')
    reserved={x['source_id'] for x in reserve['sources']}
    docs={};sources={}
    for sid,path in SOURCES.items():
        assert sid not in reserved and sid in families
        docs[sid]=extract(ROOT/path)
        sources[sid]={'path':path,'sha256':b.filehash(ROOT/path),'family_id':families[sid]['family_id'],'title':families[sid]['title']}
    manifest=[];encoded={}
    for r in rows:
        sid=r['source_id'];assert sources[sid]['family_id']==r['family_id']
        context,loc,reason=aligned(r['text'],docs[sid])
        archived=(r.get('context') or {}).get('previous','')
        # Archived context has a documented parent/block and exact source hash.
        # Its boundaries are inherited unchanged; historical rows use full-target alignment.
        if archived and r['role']=='new_AI':
            assert r['source_sha256']==sources[sid]['sha256']
            context=archived
            loc={'method':'archived_previous_context','archive':r['provenance']['candidate'],'record_id':r['segment_id'],
                 'parent_id':r.get('parent_id'),'parent_offsets':r.get('parent_offsets'),'target_block_ids':r.get('block_ids'),
                 'target_pages':r['pages_exact'],'correction_id':r.get('correction_id'),
                 'derivation_scripts':['scripts/refine_beto_pilot_v2.py','scripts/select_beto_pilot_v2.py']}
            reason=None
        original,transformed,target,cids=encode(tok,r['text'],context)
        changed=original!=transformed
        fold=next(f['id'] for f in p['folds'] if r['segment_id'] in f['validation'])
        item={k:r[k] for k in ['segment_id','source_id','family_id','role','label','text_sha256']}
        item.update(fold=fold,source=sources[sid],context_location=loc,context_found=bool(context),changed=changed,
                    absence_reason=reason if not context else (None if changed else 'no_space_after_preserving_target'),
                    target_token_ids=target,context_token_ids=cids,target_tokens=len(target),context_tokens=len(cids),
                    original_input_sha256=b.fingerprint(original),transformed_input_sha256=b.fingerprint(transformed),
                    context_text_sha256=b.fingerprint(context) if context else None)
        manifest.append(item);encoded[r['segment_id']]={'original':original,'transformed':transformed,'context':context,'target_text':r['text']}
    # Fold checks apply to every row; a source has exactly one family/validation fold.
    for fold in p['folds']:
        b.validate([byid[i] for i in fold['train_B']],[byid[i] for i in fold['validation']])
    for sid in SOURCES:
        assert len({m['fold'] for m in manifest if m['source_id']==sid})==1
    coverage={}
    for field in ['role','family_id','fold','label']:
        coverage[field]={value:{'total':len(xs),'found':sum(x['context_found'] for x in xs),'incorporated':sum(x['changed'] for x in xs)}
            for value in sorted({x[field] for x in manifest}) for xs in [[x for x in manifest if x[field]==value]]}
    sample=[]
    # One per recovered source, capped at 10 by stable SHA256 ranking, without predictions or labels.
    for sid in sorted(SOURCES):
        candidates=[m for m in manifest if m['source_id']==sid and m['context_found']]
        if candidates:sample.append(min(candidates,key=lambda m:b.fingerprint('alignment-audit-v1:'+m['segment_id'])))
    sample=sorted(sample,key=lambda m:b.fingerprint('alignment-audit-v1:'+m['segment_id']))[:10]
    b.save(OUT/'inputs.json',encoded)
    b.save(OUT/'alignment-sample.json',[{**m,'context':encoded[m['segment_id']]['context'],'target':byid[m['segment_id']]['text']} for m in sample])
    b.save(ART/'manifest.json',{'items':manifest,'coverage':coverage,'absence_reasons':dict(Counter(m['absence_reason'] for m in manifest if not m['changed']))})
    b.save(OUT/'extracted-documents.json',{sid:{k:v for k,v in doc.items() if k not in ['normalized','offsets']} for sid,doc in docs.items()})
    protocol={'created_at_utc':datetime.now(timezone.utc).isoformat(),'condition':'B_context','reference':'B','closed_hypothesis':'B_weights_A',
        'rule':'Original B target tokens first; prior authentic passage last min(95,384-target_tokens-3) tokens second; exact original fallback.',
        'base_revision':b.REV,'pilot_seed':42,'additional_seeds':[43,44],'maximum_new_runs':9,
        'expansion_gate':{'minimum_mean_combined_delta':.01,'minimum_improved_folds':2,'minimum_mean_historical_delta':0,'minimum_historical_families_with_context':2},
        'recovery':'All 591 rows; archived prior context first, otherwise unique complete normalized target match in same local PDF. No fuzzy/label-guided alignment. Block prefix or immediately preceding block.',
        'internet_originals_retrieved':0,'additional_OCR_pages':0,'sources':sources,'coverage':coverage,
        'original_protocol_sha256':b.filehash(b.ART/'protocol.json'),
        'frozen_hashes':{str(path.relative_to(ROOT)).replace('\\','/'):b.filehash(path) for path in [OUT/'inputs.json',OUT/'alignment-sample.json',ART/'manifest.json',OUT/'extracted-documents.json',ROOT/'scripts/prepare_beto_context_v2.py',ROOT/'scripts/run_beto_first_training_v2.py']}}
    b.save(ART/'protocol.json',protocol)
    print({'total':591,'found':sum(m['context_found'] for m in manifest),'changed':sum(m['changed'] for m in manifest),'coverage':coverage,'absence_reasons':Counter(m['absence_reason'] for m in manifest if not m['changed'])},flush=True)

if __name__=='__main__':prepare()
