"""Offline, append-only development extraction. No classifier inference or training."""
import json, re, hashlib, csv, sys, unicodedata
from pathlib import Path
from collections import Counter, defaultdict
import fitz
from transformers import AutoTokenizer
from prepare_agn_pilot import normalize, grams, similarities

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/beto-v2/corpus'
OUT=ROOT/'outputs/beto-v2/pilot'
ART=ROOT/'artifacts/beto-v2/pilot'
IDS=['S01','S03','S05','S06','S10','S15','S17']
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
def lines(p,x):
    with p.open('x',encoding='utf-8') as f:
        for a in x:f.write(json.dumps(a,ensure_ascii=False)+'\n')
def clean(t):
    # Mechanical layout changes, never lexical OCR repair.
    return re.sub(r'\s+',' ',re.sub(r'(?<=\w)-\s*\n\s*(?=[a-záéíóúñü])','',t)).strip()
def terminal(t): return bool(re.search(r'[.!?][”"»\)\]]?\s*\d*$',t))
def main():
    OUT.mkdir(parents=True,exist_ok=True); ART.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'candidates.jsonl').exists(), 'Existing outputs preserved'
    reg={x['source_id']:x for x in csv.DictReader((ROOT/'artifacts/beto-v2/corpus/source-registry-v2.csv').open(encoding='utf-8'))}
    reserve=read(ROOT/'artifacts/beto-v2/corpus/reserved-evaluation-sources-v2.json')
    reserved={x['source_id'] for x in reserve['sources']}
    tokpath=ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware'
    tok=AutoTokenizer.from_pretrained(tokpath,local_files_only=True)
    blocks=[]; candidates=[]; stats={}; inputs={}; issues=[]
    def guard(p):inputs[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    guard(ROOT/'docs/beto-v2/guia-etiquetado-v2.md')
    guard(ROOT/'artifacts/beto-v2/corpus/reserved-evaluation-sources-v2.json')
    for sid in IDS:
        assert sid not in reserved and reg[sid]['role']=='annotation_pool'
        for name in ['pages.json','source.pdf','acquisition.json']:guard(BASE/sid/name)
        doc=fitz.open(BASE/sid/'source.pdf'); body=[]; bibliography=False
        for pi,page in enumerate(doc):
            dd=page.get_text('dict',sort=True)
            sizes=Counter(round(s['size'],1) for b in dd['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] for _ in s['text'])
            main_size=sizes.most_common(1)[0][0] if sizes else 0
            for bi,b in enumerate(dd['blocks']):
                if 'lines' not in b:continue
                raw='\n'.join(''.join(s['text'] for s in l['spans']) for l in b['lines'])+'\n'
                t=clean(raw); spans=[s for l in b['lines'] for s in l['spans']]
                size=sum(len(s['text'])*s['size'] for s in spans)/max(1,sum(len(s['text']) for s in spans))
                kind='body'
                if re.fullmatch(r'(?:referencias(?: bibliográficas)?|bibliografía|fuentes y bibliografía)',t,re.I):bibliography=True
                if bibliography:kind='bibliography'
                elif b['bbox'][1]<page.rect.height*.065 or b['bbox'][3]>page.rect.height*.965 or re.fullmatch(r'[\d\s]+',t):kind='header_footer'
                elif size<main_size*.9 and (b['bbox'][1]>page.rect.height*.55 or re.match(r'^\d+\s',t)):kind='note'
                elif len(t.split())<9 and not terminal(t):kind='heading'
                row={'block_id':f'{sid}-p{pi+1:03}-b{bi:03}','source_id':sid,'page':pi+1,'bbox':b['bbox'],'text_original':raw,'text':t,'kind':kind,'method':'PyMuPDF dict sort=True; newline-hyphen join; whitespace collapse','body_font_size':main_size,'block_font_size':size}
                blocks.append(row)
                if kind=='body':body.append(row)
        # Assemble full layout paragraphs; continue unfinished paragraphs across blocks/pages.
        pending=[]
        def emit(parts):
            if not parts:return
            text=' '.join(x['text'] for x in parts)
            flags=[]
            if not terminal(text):flags.append('incomplete_end')
            if not re.match(r'^[¿¡«“"(]*[A-ZÁÉÍÓÚÑ0-9]',text):flags.append('possible_incomplete_start')
            if sid in ['S05','S17']:flags.append('visual_collation_required')
            if len(parts)>3:flags.append('layout_boundary_review')
            if not text:return
            candidates.append({'segment_id':f'{sid}-seg{sum(x["source_id"]==sid for x in candidates)+1:04}','source_id':sid,'family_id':reg[sid]['family_id'],'format':'pdf','text':text,'text_original':'\n'.join(x['text_original'] for x in parts),'block_ids':[x['block_id'] for x in parts],'pages':sorted({x['page'] for x in parts}),'source_sha256':reg[sid]['content_sha256'],'transformations':['layout_block_extraction','body_separation_heuristic','line_end_hyphen_join','whitespace_collapse','paragraph_continuity_join'] if len(parts)>1 else ['layout_block_extraction','body_separation_heuristic','line_end_hyphen_join','whitespace_collapse'],'quality_flags':flags,'status':'pending_extraction' if flags else 'usable_candidate','label':None,'split':None})
        for b in body:
            pending.append(b)
            if terminal(b['text']):emit(pending);pending=[]
        emit(pending)
        stats[sid]={'pages_processed':len(doc),'layout_blocks':sum(x['source_id']==sid for x in blocks),'candidates':sum(x['source_id']==sid for x in candidates),'license':reg[sid]['license_conditions']}
    # Cues retained verbatim; no fabricated video duration or sentence punctuation.
    video=[]
    for sid in ['V01','V02']:
        guard(BASE/sid/'cues.json');guard(BASE/sid/'acquisition.json')
        cues=read(BASE/sid/'cues.json'); a=read(BASE/sid/'acquisition.json')
        video.append({'source_id':sid,'video_id':a['video_id'],'video_duration_seconds':None,'duration_status':'not_in_acquisition_metadata','caption_start_seconds':min(c['start'] for c in cues),'caption_end_seconds':max(c['start']+c['duration'] for c in cues),'capture':'all_returned_cues; full_video_coverage_unverified','work_extent':'extract_of_conference' if sid=='V02' else 'interview_video','cues':cues,'status':'pending_permissions_and_ASR_sentence_boundaries','reason':'acquisition records explicitly require rights review; excluded from annotation'})
        issues.append({'source_id':sid,'status':'pending','reason':'rights_review; video_duration_unknown; ASR_sentence_boundaries_unverified','cue_count':len(cues)})
    for sid in IDS:
        rows=[x for x in candidates if x['source_id']==sid]
        for i,c in enumerate(rows):c['context']={'previous':rows[i-1]['text'] if i else '', 'next':rows[i+1]['text'] if i+1<len(rows) else ''}
    for c in candidates:
        c['text_sha256']=sha(c['text'].encode());c['beto_tokens']=len(tok(c['text'],truncation=False,add_special_tokens=True)['input_ids'])
        if c['quality_flags']:issues.append({'segment_id':c['segment_id'],'source_id':c['source_id'],'status':'pending','reason':c['quality_flags']})
    lines(OUT/'candidates.jsonl',candidates);lines(OUT/'layout-blocks.jsonl',blocks)
    save(OUT/'transcripts-preserved.json',video);save(OUT/'extraction-issues.json',issues)
    # All audited historical versions, collapsed by normalized text; labels never read.
    report=(ROOT/'docs/beto-v2/01-auditoria.md').read_text(encoding='utf-8')
    paths=sorted(set(re.findall(r'\| ((?:artifacts|outputs)/[^ |]+\.json) \|',report)))
    refs={}
    for rel in paths:
        p=ROOT/rel
        if not p.exists():continue
        guard(p)
        for i,r in enumerate(read(p).get('items',[])):
            t=r.get('text',''); n=normalize(t)
            if n:refs.setdefault(n,{'text':t,'versions':[]})['versions'].append({'dataset':rel,'index':i,'record_id':r.get('id'),'resource_id':r.get('resourceId')})
    # Inverted shingle index avoids quadratic comparisons without dropping possible overlap.
    pool=[{'kind':'historical','key':sha(n.encode()),'text':r['text'],'versions':r['versions']} for n,r in refs.items()]
    pool += [{'kind':'candidate','key':c['segment_id'],'text':c['text']} for c in candidates]
    inv=defaultdict(set); gs=[]; alerts=[]
    for i,r in enumerate(pool):
        g=grams(r['text']);gs.append(g);possible=set()
        for w in g:possible.update(inv[w])
        if r['kind']=='candidate':
            for j in sorted(possible):
                jac,con=similarities(g,gs[j]); exact=normalize(r['text'])==normalize(pool[j]['text'])
                if exact or jac>=.25 or con>=.8:alerts.append({'candidate_id':r['key'],'other_kind':pool[j]['kind'],'other_id':pool[j]['key'],'versions':pool[j].get('versions',[]),'exact':exact,'jaccard':jac,'containment':con})
        for w in g:inv[w].add(i)
    save(OUT/'duplication.json',{'method':'existing normalized 5-word shingles; Jaccard >= .25 or containment >= .8; no semantic independence claim','historical_files':paths,'historical_unique_texts':len(refs),'version_groups':[{'text_hash':sha(n.encode()),'versions':r['versions']} for n,r in refs.items() if len(r['versions'])>1],'alerts':alerts})
    save(ART/'processing-manifest.json',{'source_stats':stats,'candidate_count':len(candidates),'statuses':dict(Counter(c['status'] for c in candidates)),'reserved_ids_excluded':sorted(reserved),'reserved_content_read':False,'inputs_sha256':inputs,'tokenizer_files':{p.name:sha(p.read_bytes()) for p in tokpath.glob('*') if p.suffix=='.json' or p.name=='vocab.txt'},'tokenizer_path':tokpath.relative_to(ROOT).as_posix(),'token_count_includes_special_tokens':True,'truncation':False,'pymupdf_version':fitz.VersionBind,'python':sys.version,'script_sha256':sha(Path(__file__).read_bytes()),'duplication_alerts':len(alerts),'training':False,'BETO_predictions':False})
    print(json.dumps({'sources':stats,'candidates':len(candidates),'statuses':dict(Counter(c['status'] for c in candidates)),'duplication_alerts':len(alerts)},ensure_ascii=False))
if __name__=='__main__':main()
