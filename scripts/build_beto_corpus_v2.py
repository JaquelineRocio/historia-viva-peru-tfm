"""Offline compilation of acquired BETO v2 sources; no model or dataset mutation."""
import csv,json,re,sys,subprocess,hashlib,importlib.metadata
from collections import defaultdict,Counter
from datetime import datetime,timezone
from acquire_beto_corpus_v2 import ROOT,BASE,PLAN,read,digest,normalize,grams,similarities

OUT=ROOT/'artifacts/beto-v2/corpus'
VERSION='beto-corpus-v2.2'
PAGES={'S01':[7,12],'S03':[7,11],'S05':[7,11],'S06':[6,9],'S10':[2,5],'S15':[6,8],'S17':[3,7]}
NOTES={
 'S02':'Reused: identical SHA256 in artifacts/reviews/corpus-batch-v2.json; underlying Flora Tristan work and translation rights require separate review.',
 'S04':'Reserved whole work; Hugo Pereyra Plasencia is distinct from Nelson Ernesto Pereyra Chavez. Broad chronology requires scope review.',
 'S05':'OCR defective; collate with page image before annotation. Reprinted in Independencia y revolucion 1780-1840 (1987): group reprints of this essay, not every essay in that collection.',
 'S06':'PDF date discrepancy 2024/2023; institutional citation date 2023-11-30 retained. Shares Callao events with S03, not established text duplication.',
 'S09':'Reserved; landing CC BY 4.0/footer BY 3.0 conflicts with PDF BY-NC-SA 4.0. No redistribution. Author cites her 2016 chapter in the collection containing existing Huamanga chapter: independence pending comparison.',
 'S10':'Whole work spans nineteenth century; selected pages discuss 1825/1827. Adjacent context is not automatically in scope.',
 'S15':'Cites Basadre 1983; citation does not establish duplication. Newspaper excerpts are embedded primary sources; rights and grouping need review.',
 'S17':'Severe OCR; visual collation required. Same author as other works is not proof of same documentary family.',
 'V01':'Public captions, no explicit redistribution license; private local use pending rights review. Historiographic framing may be no_relevante or mixed.',
 'V02':'Public captions, no explicit redistribution license; ASR and mixed historiographic dates require review; do not silently correct 1920 to 1820.',
}
KNOWN={
 '747ca90f-92fc-4d19-aec4-6dfc34c2917e':('Historia de la Republica del Peru, tomo 1','Jorge Basadre Grohmann','artifacts/reviews/boundary-resolution-v3.json'),
 '9fecbe5a-9fb2-4002-a088-8a2810db938e':('Los campesinos de Huamanga y la rebelion de 1814','Nelson Ernesto Pereyra Chavez','artifacts/reviews/boundary-resolution-v3.json'),
 '9154f7f7-86c9-4bad-bcba-47eaf54b93e1':('La Constitucion de 1823 y los inicios de la Republica','Carmen Villanueva','artifacts/reviews/villanueva-boundaries-v1.json'),
 '0ea45102-057d-4bff-b527-f36326f66d33':('El mito de la independencia concedida','Scarlett O Phelan Godoy','artifacts/reviews/corpus-batch-v2.json'),
 '9f60a031-0183-478c-a1f8-a3bdd37d7b0b':('Los primeros anos del Peru republicano','Juan Luis Orrego Penagos','artifacts/reviews/corpus-batch-v2.json'),
 'e32181bc-41d0-4400-a76d-eb11fc88bf71':('Bandoleros o patriotas','Juan Fonseca Ariza','artifacts/reviews/corpus-batch-v2.json'),
}
def write_json(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
def write_lines(path,rows):
    with path.open('x',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
def write_csv(path,rows):
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def clean(s):return re.sub(r'\s+',' ',s).strip()
def main():
    targets=[OUT/'source-registry-v2.csv',BASE/'corpus-unlabeled-v2.jsonl',BASE/'supervised-candidates-v2.jsonl',OUT/'source-groups-v2.json',OUT/'reserved-evaluation-sources-v2.json',OUT/'class-work-author-format-v2.csv',OUT/'verification-v2.json']
    if any(p.exists() for p in targets):raise SystemExit('Existing output preserved; review checkpoint instead of overwriting.')
    plan=read(PLAN);registry=[];groups=[];reserved=[];corpus=[];candidates=[]
    commit=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    evidence={'commit':commit,'command':'outputs/venv-ml/Scripts/python.exe scripts/build_beto_corpus_v2.py','version':VERSION,'acquisition_command':'outputs/venv-ml/Scripts/python.exe scripts/acquire_beto_corpus_v2.py','created_at':datetime.now(timezone.utc).isoformat(),'versions':{x:importlib.metadata.version(x) for x in ['pypdf','requests','youtube-transcript-api']},'python':sys.version,'model_checkpoint':None,'model_used':False,'plan_sha256':digest(PLAN.read_bytes()),'script_sha256':digest(__import__('pathlib').Path(__file__).read_bytes())}
    for s in plan['sources']:
        sid=s['id'];folder=BASE/sid;r=read(folder/'acquisition.json');m=r.get('metadata',{});val=lambda k:' | '.join(m.get(k,[])) or 'UNKNOWN'
        obtained=(folder/'pages.json').exists() or (folder/'cues.json').exists();reuse=sid=='S02';is_reserved=s['role']=='reserved_candidate'
        title=val('citation_title');author=val('citation_author')
        if sid in ['V01','V02']:
            title={'V01':'Las tres interpretaciones sobre la independencia del Peru','V02':'La independencia tardia: la caida del ultimo bastion espanol'}[sid];author={'V01':'Carlos Contreras','V02':'Rolando Rojas'}[sid]
        status='reused_existing' if reuse else ('accepted_reserved_provisional' if is_reserved else 'accepted_unlabeled') if obtained else r['status']
        row={'source_id':sid,'status':status,'reason':NOTES.get(sid,r.get('reason','Content opened and extracted; annotation pending')),'url':s['url'],'title':title,'author':author,'institution':val('citation_publisher') if val('citation_publisher')!='UNKNOWN' else __import__('urllib.parse',fromlist=['urlparse']).urlparse(s['url']).netloc,'date':val('citation_date') if val('citation_date')!='UNKNOWN' else val('citation_publication_date'),'format':'video_transcript' if s['kind']=='video' else 'pdf' if obtained else 'metadata','original_work':title,'edition':val('citation_volume')+'/'+val('citation_issue'),'chapter':'whole article/video; UNKNOWN for unacquired resource','collection':val('citation_journal_title'),'license_conditions':' | '.join(r.get('license_urls',[])) or 'UNKNOWN; no redistribution authorized','content_sha256':r.get('pdf_sha256',r.get('transcript_sha256','')),'landing_sha256':r.get('landing_sha256',''),'role':s['role'],'family_id':'family-'+sid,'relationship_existing':NOTES.get(sid,'No identity established; shared citations are not proof of independence or duplication.'),'topic_provisional':s['topic'],'evidence_path':str((folder/'acquisition.json').relative_to(ROOT)),'commit':commit,'processing_version':VERSION}
        registry.append(row);groups.append({'family_id':row['family_id'],'source_ids':[sid],'original_work':title,'role':s['role'],'grouping_status':'provisional','rationale':row['relationship_existing'],'editions_translations_chapters_must_follow_family':True})
        if is_reserved:reserved.append({'family_id':row['family_id'],'source_id':sid,'obtained':obtained,'status':'candidate_not_final_test','path':str(folder.relative_to(ROOT)),'sha256':row['content_sha256'],'independence_verified':False,'review':row['reason'],'prohibited_uses':['training','augmentation','pseudo_labeling','DAPT','TAPT','BETO_evaluation_during_development']})
        if not obtained or reuse or is_reserved:continue
        units=[]
        if sid in PAGES:
            pages=read(folder/'pages.json')
            for number in PAGES[sid]:
                page=pages[number-1];raw=page['text_original'];units.append({'unit_id':f'{sid}-p{number:03}','page':number,'page_index_base':1,'text_original':raw,'adjacent_context':{'previous':pages[number-2]['text_original'] if number>1 else '', 'next':pages[number]['text_original'] if number<len(pages) else ''},'method':'pypdf.extract_text default; whitespace collapse only'})
        else:
            cues=read(folder/'cues.json')
            for start in range(0,int(max(c['start']+c['duration'] for c in cues))+1,90):
                selected=[(i,c) for i,c in enumerate(cues) if start<=c['start']<start+90]
                if not selected:continue
                a,b=selected[0][0],selected[-1][0]
                units.append({'unit_id':f'{sid}-t{start:04}','start_seconds':cues[a]['start'],'end_seconds':cues[b]['start']+cues[b]['duration'],'text_original':' '.join(c['text'] for _,c in selected),'cue_indices':[a,b],'cues':[c for _,c in selected],'adjacent_context':{'previous':cues[max(0,a-2):a],'next':cues[b+1:b+3]},'method':'public Spanish captions; 90-second bins by cue start; no ASR regeneration'})
        for u in units:
            u.update(source_id=sid,family_id=row['family_id'],text_clean=clean(u['text_original']),source_sha256=row['content_sha256'],processing_version=VERSION,split=None,label=None,usage='unlabeled_review_only',quality_flags=['scope_and_multitopic_review','not_annotation_approved']+(['OCR_visual_collation_required'] if sid in ['S05','S17'] else [])+(['ASR_review','rights_review'] if sid.startswith('V') else []))
            u['text_sha256']=digest(u['text_original'].encode());corpus.append(u)
            # Small review batch. Exact contiguous span; full page and neighboring context remain in corpus.
            if sid.startswith('V') and len([c for c in candidates if c['source_id']==sid])>=2:continue
            matches=list(re.finditer(r'\S+',u['text_original']));end=matches[min(len(matches),220)-1].end() if matches else 0
            raw=u['text_original'][:end]
            candidates.append({'candidate_id':u['unit_id']+'-c01','unit_id':u['unit_id'],'source_id':sid,'family_id':u['family_id'],'label':None,'split':None,'text_original':raw,'text_clean':clean(raw),'offset_start':0,'offset_end':end,'source_sha256':row['content_sha256'],'page':u.get('page'),'start_seconds':u.get('start_seconds'),'end_seconds':u.get('end_seconds'),'context_reference':u['unit_id'],'processing_version':VERSION,'quality_flags':u['quality_flags']+['candidate_boundary_review','may_contain_header_or_footnote'],'annotation_status':'unlabeled_pending_human_review'})
    # Reuse audited distribution, with provenance rather than guessing missing authors.
    matrix=[];dist=ROOT/'artifacts/beto-v2/audit/source-class-distribution.csv'
    for r in csv.DictReader(dist.open(encoding='utf-8-sig')):
        if r['dataset'] not in ['artifacts/datasets/gold-v1-source-aware.json','outputs/corpus-snapshot-v4/reviewed-export.json']:continue
        work,author,ref=KNOWN.get(r['source'],('UNKNOWN','UNKNOWN','unknown; resource ID is not work identity'))
        matrix.append({**r,'work':work,'author':author,'identity_evidence':ref,'identity_status':'verified_previous_review' if work!='UNKNOWN' else 'unknown'})
    write_csv(targets[5],matrix)
    refs=[];ref_hashes={}
    for rel in ['artifacts/datasets/gold-v1-source-aware.json','outputs/corpus-snapshot-v4/reviewed-export.json','artifacts/datasets/evaluation-pilot-v2.json']:
        p=ROOT/rel
        if not p.exists():continue
        ref_hashes[rel]=digest(p.read_bytes());data=read(p)
        for i,x in enumerate(data.get('items',[])):
            t=x.get('text','')
            if t:refs.append((rel,i,normalize(t),grams(t)))
    overlap=[]
    for c in candidates:
        n=normalize(c['text_clean']);g=grams(c['text_clean']);best=(0,0,None,None)
        for rel,i,rn,rg in refs:
            j,contain=similarities(g,rg)
            if j>best[0]:best=(j,contain,rel,i)
            if n==rn or j>=.25 or contain>=.8:overlap.append({'candidate_id':c['candidate_id'],'reference':rel,'item_index':i,'exact':n==rn,'jaccard':j,'containment':contain})
        c['nearest_reference']={'jaccard':best[0],'containment':best[1],'dataset':best[2],'item_index':best[3]}
    new_overlap=[]
    for i,a in enumerate(candidates):
        for b in candidates[i+1:]:
            j,k=similarities(grams(a['text_clean']),grams(b['text_clean']))
            if j>=.25 or k>=.8:new_overlap.append({'a':a['candidate_id'],'b':b['candidate_id'],'jaccard':j,'containment':k})
    reserved_ids={r['source_id'] for r in reserved}
    assert all(c['source_id'] not in reserved_ids and c['label'] is None for c in corpus+candidates)
    for c in candidates:
        u=next(x for x in corpus if x['unit_id']==c['unit_id'])
        assert u['text_original'][c['offset_start']:c['offset_end']]==c['text_original']
    write_csv(targets[0],registry);write_lines(targets[1],corpus);write_lines(targets[2],candidates)
    write_json(targets[3],{'evidence':evidence,'groups':groups,'rule':'Provisional original-work families; editions/translations/chapters follow parent work. Author or publisher alone does not define a family.'})
    write_json(targets[4],{'evidence':evidence,'assignment':'preliminary; no final splits','sources':reserved,'excluded_prior_sets':['original test','external-development-v1','evaluation-pilot-v2']})
    verification={'evidence':evidence,'reference_dataset_hashes':ref_hashes,'distribution_sha256':digest(dist.read_bytes()),'counts':{'registry':len(registry),'statuses':dict(Counter(r['status'] for r in registry)),'unlabeled_units':len(corpus),'annotation_candidates':len(candidates),'reserved_obtained':sum(r['obtained'] for r in reserved)},'lexical_overlap_flags':overlap,'within_batch_overlap_flags':new_overlap,'overlap_scope':'Selected candidate spans vs gold, v4, pilot; 5-word normalized shingles. Not full-work semantic independence proof; external-development not included.','checks':{'reserved_excluded':True,'labels_null':True,'raw_span_roundtrip':True},'outputs_sha256':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in targets[:-1]}}
    write_json(targets[-1],verification);print(json.dumps(verification['counts']))
if __name__=='__main__':main()
