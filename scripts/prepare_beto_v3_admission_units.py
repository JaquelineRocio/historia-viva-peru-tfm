"""Deterministic label-free segmentation/prevalidation of fixed admission windows."""
import json,re,hashlib,argparse
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/beto-v3/admission-01';ART=ROOT/'artifacts/beto-v3/admission-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub(r'\s+',' ',s).strip()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def save(p,d):
 if (ART/'frozen-inputs.json').exists() and p.exists():
  assert read(p)==d, f'Frozen annotation input differs: {p}; preserve reviewed text, create a new version within budget'
  return
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def grams(s):
 w=re.findall(r'\w+',s.lower());return {' '.join(w[i:i+12]) for i in range(len(w)-11)}
def main():
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
 guide=ROOT/'docs/beto-v3/guia-etiquetado-v3.md';plan=ART/'sampling-plan.json';manifest=[];rows=[];missing=[]
 for sid in read(plan)['sources']:
  for wi in range(3):
   p=OUT/sid/'asr'/f'window-{wi}.json'
   if not p.exists() or not read(p).get('complete'):missing.append(str(p.relative_to(ROOT)));continue
   data=read(p);c=data['segments'];n=len(c);cache={}
   def segment(a,b):
    if (a,b) not in cache:
     t=norm(' '.join(x['text'] for x in c[a:b]));cache[a,b]=(t,len(tok(t,truncation=False)['input_ids']))
    return cache[a,b]
   # Five 75s-anchor targets; only add a sixth if no complete <=384-token partition exists.
   best=None
   for k in range(5,9):
    states={(0,0):(0,[])}
    for j in range(1,k+1):
     for b in range(j,n+1):
      if j==k and b!=n:continue
      opts=[]
      for a in range(j-1,b):
       prev=states.get((j-1,a))
       if prev is None:continue
       t,nt=segment(a,b)
       if nt>384 or not t:continue
       boundary=c[b-1]['end'];anchor=data['offset_seconds']+j*data['audio_seconds']/k
       punct=bool(re.search(r'[.!?][\"»”]?$',c[b-1]['text'].strip()))
       score=prev[0]+(boundary-anchor)**2+(0 if punct or b==n else 900)
       opts.append((score,prev[1]+[(a,b)]))
      if opts:states[j,b]=min(opts,key=lambda x:x[0])
    if (k,n) in states:best=states[k,n];break
   assert best is not None,(sid,wi,'Cannot cover cues without truncation')
   ids=[]
   for ui,(a,b) in enumerate(best[1]):
    text,nt=segment(a,b);uid=f'A01-{sid}-w{wi}-u{ui+1:02}';ids.append(uid)
    rows.append({'segment_id':uid,'source_id':sid,'family_id':'video-'+('KHcAIKD38sI' if sid=='N01' else sid),'partition':'V','text':text,'input_sha256':digest(text),'guide_sha256':sha(guide),'source_sha256':data['source_sha256'],'transcript_path':str(p.relative_to(ROOT)),'transcript_sha256':sha(p),'window_index':wi,'cue_indices':list(range(a,b)),'start_sec':c[a]['start'],'end_sec':c[b-1]['end'],'tokens_with_specials':nt,'would_truncate_tokens':0,'boundary_ends_sentence':bool(re.search(r'[.!?][\"»”]?$',c[b-1]['text'].strip())),'training_eligible':False,'reference_status':'unannotated'})
   assert norm(' '.join(r['text'] for r in rows if r['source_id']==sid and r['window_index']==wi))==norm(' '.join(x['text'] for x in c))
   manifest.append({'source_id':sid,'window_index':wi,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'offset_seconds':data['offset_seconds'],'audio_seconds':data['audio_seconds'],'cue_count':n,'units':ids,'all_cues_retained':True,'segmentation_cost':best[0]})
 prior_paths=[ROOT/'outputs/beto-v3/datasets/H-reviewed.json',ROOT/'outputs/beto-v3/recovery-01/all-development-units.json']
 prior=[]
 for p in prior_paths:
  for r in read(p)['items']:
   assert r.get('partition',r.get('split')) not in ['S','test','val']
   prior.append({'segment_id':r['segment_id'],'source_id':r.get('source_id'),'text':r['text']})
 index=defaultdict(set);exact=defaultdict(list)
 for r in prior:
  exact[digest(norm(r['text']))].append(r['segment_id'])
  for g in grams(r['text']):index[g].add(r['segment_id'])
 matches=[];temporal=[];seen={}
 for r in rows:
  hits=defaultdict(list)
  for g in grams(r['text']):
   for target in index.get(g,[]):hits[target].append(g)
  if hits:matches.append({'segment_id':r['segment_id'],'matches':[{'prior_segment_id':t,'shared_12grams':len(gs),'examples':gs[:3]} for t,gs in sorted(hits.items())]})
  if r['input_sha256'] in exact or r['input_sha256'] in seen:matches.append({'segment_id':r['segment_id'],'exact_duplicate':exact.get(r['input_sha256'],[])+seen.get(r['input_sha256'],[])})
  for old in rows:
   if old is r:break
   if old['source_id']==r['source_id'] and max(old['start_sec'],r['start_sec'])<min(old['end_sec'],r['end_sec'])-.001:temporal.append([old['segment_id'],r['segment_id']])
  seen.setdefault(r['input_sha256'],[]).append(r['segment_id'])
  for g in grams(r['text']):index[g].add(r['segment_id'])
 complete=not missing;budget=len(rows)<=31
 report={'plan_sha256':sha(plan),'source_windows':manifest,'missing_windows':missing,'complete_inventory':complete,'units':len(rows),'max_tokens':max((r['tokens_with_specials'] for r in rows),default=0),'annotation_ceiling':31,'budget_pass':budget,'temporal_overlap_pairs':temporal,'text_overlap_findings':matches,'prevalidation_pass':complete and budget and not temporal and not matches,'annotation_entries_spent':0,'S_content_accessed':False,'prior_inputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in prior_paths],'method':'Fixed windows; 5 segments/window minimizing squared time-anchor displacement with sentence-end preference; additional segment only if token cap makes five infeasible. Every cue retained exactly once. Exact text hashes and normalized 12grams screened against H-reviewed + recovery development + earlier candidates. Matches require substantive review before annotation.'}
 save(OUT/'annotation-inventory.json',{'items':rows});save(ART/'prevalidation.json',report)
 if report['prevalidation_pass']:
  sanitized=[{k:r[k] for k in ['segment_id','text','input_sha256','guide_sha256']} for r in rows]
  for bi in range(0,len(rows),8):save(OUT/'annotation-inputs'/f'batch-{bi//8+1:02}.json',{'guide':guide.read_text(encoding='utf-8'),'instruction':'Apply guide to exact text. Return {metadata:{model:"GPT-6 family; exact weights unknown"},items:[{segment_id,input_sha256,proposal:class_or_null,evidence:literal_text,evidence_span:[start,end],rule,alternative:class_or_null,flags:[],rationale}]}. Flags should explicitly identify ambiguity, extraction defects, boundary issues, or blocking boundaries when present. Preserve uncertainty with proposal null when blocking; no labels inherited; evidence_span uses Python codepoint offsets. No histories or other files; do not assign split or training eligibility.','items':sanitized[bi:bi+8]})
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_windows','prior_inputs','method','text_overlap_findings']},ensure_ascii=False));print('Overlap findings',len(matches))
if __name__=='__main__':main()
