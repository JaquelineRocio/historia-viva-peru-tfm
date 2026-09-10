"""Validate saved reviews/adjudications, publish measured coverage and closed data gate."""
import json,hashlib,csv,io
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/beto-v3';BASE=OUT/'phase-b-completion-01';ART=ROOT/'artifacts/beto-v3';META=ART/'phase-b-completion-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def archive(p):
 q=p.parent/'before-resume'/p.name
 if p.exists() and not q.exists():q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
def csvout(p,rows):
 if not rows:return
 s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);p.write_bytes(s.getvalue().encode('utf-8-sig'))
def span(row,text):
 a=row['evidence_span'];a=[a['start'],a['end']] if isinstance(a,dict) else a
 assert text[a[0]:a[1]]==row['evidence'] and row['evidence'];return a
def main():
 if (ART/'phase-b-gap-02/review-integration.json').exists():
  from integrate_beto_v3_gap_reviews import main as integrated
  return integrated(check_only=True)
 original=BASE/'units-and-annotations.json';archive(original)
 units=read(BASE/'before-resume/units-and-annotations.json')['items'];index={r['segment_id']:r for r in units}
 for r in units:r.setdefault('reference_status','accepted_first_pass_unsampled_training' if r.get('accepted_label') else 'pending_review')
 guide= digest(ROOT/'docs/beto-v3/guia-etiquetado-v3.md');labels=read(ART/'protocol.json')['labels']
 reviews=[];decisions=[];comparison=[];cache=[]
 for number in range(1,6):
  name=f'batch-{number:03}.json';blind=read(BASE/'review-batches'/name)['items']
  second=read(BASE/'second-review'/name)['items'];adjud=read(BASE/'adjudication'/name)['items']
  assert {r['segment_id'] for r in blind}=={r['segment_id'] for r in second}=={r['segment_id'] for r in adjud}
  ai={r['segment_id']:r for r in adjud}
  for b in second:
   a=index[b['segment_id']];d=ai[b['segment_id']];assert b['input_sha256']==a['input_sha256']==d['input_sha256']
   assert b['guide_sha256']==a['guide_sha256']==guide
   assert hashlib.sha256(a['text'].encode()).hexdigest()==a['input_sha256']
   span(a,a['text']);span(b,a['text']);span(d,a['text'])
   assert b['proposal'] in labels and d['accepted_label'] in labels+[None]
   a['second_review']=b;a['adjudication']=d;a['accepted_label']=d['accepted_label'];a['reference_status']='accepted_adjudicated' if d['accepted_label'] else 'pending_adjudication'
   a['first_pass_status']=a['status'];a['status']=a['reference_status'];a['first_pass_boundary_pending']=a.get('boundary_pending');a['boundary_pending']=d['accepted_label'] is None
   a['annotation_field_note']='proposal, alternative, rule, rationale, ambiguous and extraction_defect retain the original first pass; adjudication and accepted_label determine current reference status'
   a['training_eligible']=False
   comparison.append({'segment_id':a['segment_id'],'partition':a['partition'],'first':a['proposal'],'second':b['proposal'],'label_agreement':a['proposal']==b['proposal'],'first_ambiguous':a['ambiguous'],'second_ambiguous':b['ambiguous'],'accepted_label':d['accepted_label'],'rationale':d['rationale']})
   key={'input_sha256':a['input_sha256'],'guide_sha256':guide,'configuration':b['exposed_configuration'],'prompt_version':b['prompt_version'],'model':b['model']}
   cache.append({'segment_id':a['segment_id'],'cache_key_sha256':hashlib.sha256(json.dumps(key,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'key':key,'response_file':str((BASE/'second-review'/name).relative_to(ROOT))})
  reviews+=second;decisions+=adjud
 assert len(reviews)==len({r['segment_id'] for r in reviews})==69
 save(BASE/'second-review/cache-index.json',{'items':cache,'same_model_family_as_first_pass':True,'independence':'isolated sessions only; not independent model errors','exact_weights':'unknown'})
 save(BASE/'review-comparison.json',{'items':comparison,'agreement_numerator':sum(r['label_agreement'] for r in comparison),'denominator':69,'accuracy_claim':False})
 save(original,{'items':units,'first_pass_snapshot_sha256':digest(BASE/'before-resume/units-and-annotations.json'),'second_review_count':69,'same_model_family':True,'expert_gold':False})
 # New ASR annotations are counted only after actual saved decisions exist.
 new=[]
 for folder in sorted((BASE/'asr-annotation').glob('*')):
  if not (folder/'units.json').exists():continue
  raw=read(folder/'units.json')['items'];first={r['segment_id']:r for p in (folder/'first-pass').glob('batch-*.json') for r in read(p)['items']}
  cues_path=BASE/'new-sources'/folder.name/'asr/cues.json';full=' '.join(c['text'].strip() for c in read(cues_path))
  assert ''.join(r['text_original'] for r in raw)==full
  assert all(r['source_sha256']==digest(cues_path) and r['text']==full[slice(*r['source_char_span'])].strip() and r['tokens_with_specials']<=384 and r['would_truncate_tokens']==0 for r in raw)
  second={r['segment_id']:r for p in (folder/'second-review').glob('batch-*.json') for r in read(p)['items']}
  final={r['segment_id']:r for p in (folder/'adjudication').glob('batch-*.json') for r in read(p)['items']}
  for u in raw:
   u['accepted_label']=None;u['reference_status']='unannotated';u['proposal']=None
   if u['segment_id'] in first:
    a=first[u['segment_id']];assert a['input_sha256']==u['input_sha256'] and a['guide_sha256']==guide and (a['proposal'] in labels or (a['proposal'] is None and (a['ambiguous'] or a['extraction_defect'])));span(a,u['text']);u['first_pass']=a;u['proposal']=a['proposal'];u['reference_status']='pending_review'
   if u['segment_id'] in second:
    b=second[u['segment_id']];assert b['input_sha256']==u['input_sha256'] and b['guide_sha256']==guide and (b['proposal'] in labels or (b['proposal'] is None and (b['ambiguous'] or b['extraction_defect'])));span(b,u['text']);u['second_review']=b
   if u['segment_id'] in final:
    d=final[u['segment_id']];assert d['input_sha256']==u['input_sha256'] and d['accepted_label'] in labels+[None] and u['segment_id'] in first and u['segment_id'] in second;span(d,u['text']);u['adjudication']=d;u['accepted_label']=d['accepted_label'];u['reference_status']='accepted_adjudicated' if d['accepted_label'] else 'pending_adjudication'
   u['status']=u['reference_status']
   new.append(u)
  save(folder/'units-and-annotations.json',{'items':[r for r in new if r['source_id']==folder.name]})
  comparisons=[{'segment_id':r['segment_id'],'first':r['first_pass']['proposal'],'second':r['second_review']['proposal'],'label_agreement':r['first_pass']['proposal']==r['second_review']['proposal'],'accepted_label':r['accepted_label']} for r in new if r['source_id']==folder.name and 'first_pass' in r and 'second_review' in r]
  save(folder/'review-comparison.json',{'items':comparisons,'same_model_family':True,'not_expert_accuracy':True})
  for passname in ['first-pass','second-review']:
   records=[]
   for p in sorted((folder/passname).glob('batch-*.json')):
    for r in read(p)['items']:
     key={'input_sha256':r['input_sha256'],'guide_sha256':r['guide_sha256'],'model':r['model'],'configuration':r.get('exposed_configuration',{'temperature':'unknown','seed':'unknown'}),'prompt_version':r.get('prompt_version','asr-first-v3-1' if passname=='first-pass' else 'asr-blind-review-v3-1')}
     records.append({'segment_id':r['segment_id'],'key':key,'cache_key_sha256':hashlib.sha256(json.dumps(key,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'response_sha256':digest(p),'response_file':str(p.relative_to(ROOT))})
   save(folder/passname/'cache-index.json',{'items':records,'independent_model':False})
 save(BASE/'all-development-units.json',{'items':units+new,'S_content_opened':False,'globally_training_eligible':False})
 save(BASE/'ASR-quality-review.json',{'items':[r for r in new if any(r.get(p,{}).get('boundary_issue') or r.get(p,{}).get('extraction_defect') for p in ['first_pass','second_review'])],'note':'Includes accepted references with nonblocking ASR/boundary defects as well as unresolved cases; never rewrite authentic text silently'})
 allunits=units+new
 coverage=[]
 for label in labels:
  row={'class':label}
  for partition in ['T','V','auxiliary']:
   accepted=[r for r in allunits if r['partition']==partition and r.get('accepted_label')==label]
   row[partition+'_accepted']=len(accepted);row[partition+'_works']=len({r['source_id'] for r in accepted})
   row[partition+'_pending_by_proposal']=sum(r['partition']==partition and not r.get('accepted_label') and r.get('proposal')==label for r in allunits)
  coverage.append(row)
 bywork=[]
 for sid in sorted({r['source_id'] for r in allunits}):
  group=[r for r in allunits if r['source_id']==sid];partition=group[0]['partition']
  for label in labels:bywork.append({'work':sid,'partition':partition,'class':label,'accepted':sum(r.get('accepted_label')==label for r in group),'pending_by_proposal':sum(not r.get('accepted_label') and r.get('proposal')==label for r in group)})
 gaps=[]
 for r in coverage:
  for role,minimum in [('T',20),('V',25)]:gaps.append({'class':r['class'],'partition':role,'accepted':r[role+'_accepted'],'target':minimum,'missing_examples':max(0,minimum-r[role+'_accepted']),'accepted_works':r[role+'_works'],'target_works':2,'missing_works':max(0,2-r[role+'_works'])})
 csvout(META/'coverage-by-class.csv',coverage);csvout(META/'coverage-by-class-work-partition.csv',bywork);csvout(META/'exact-gaps.csv',gaps)
 works=[{'work':sid,'partition':next(r['partition'] for r in allunits if r['source_id']==sid),'units':sum(r['source_id']==sid for r in allunits),'accepted':sum(r['source_id']==sid and r.get('accepted_label') is not None for r in allunits),'pending':sum(r['source_id']==sid and r.get('accepted_label') is None for r in allunits)} for sid in sorted({r['source_id'] for r in allunits})]
 csvout(META/'coverage-by-work.csv',works)
 sources=read(META/'source-registry-final.json');duration_by_id={r.get('video_id',r.get('source_id')):r.get('duration_seconds',0) or 0 for r in sources['existing_sources']}
 duration_by_id.update({r['source_id']:r.get('duration_seconds',0) or 0 for r in sources['new_candidates']})
 for r in works:r['duration_seconds']=duration_by_id.get(r['work'],0);r['at_least_30_minutes']=r['duration_seconds']>=1800;r['resolvable_reference_fraction']=r['accepted']/r['units']
 csvout(META/'coverage-by-work.csv',works)
 work_goals=[{'partition':role,'acquired_transcribed_works':sum(r['partition']==role for r in works),'acquired_transcribed_works_at_least_30min':sum(r['partition']==role and r['at_least_30_minutes'] for r in works),'target_30min_works':target,'missing_30min_works':max(0,target-sum(r['partition']==role and r['at_least_30_minutes'] for r in works))} for role,target in [('T',12),('V',6)]]
 csvout(META/'source-work-targets.csv',work_goals)
 strict_gaps=[]
 for role,minimum in [('T',20),('V',25)]:
  for label in labels:
   accepted_long=[r for r in allunits if r['partition']==role and r.get('accepted_label')==label and duration_by_id.get(r['source_id'],0)>=1800]
   strict_gaps.append({'partition':role,'class':label,'accepted_from_30min_works':len(accepted_long),'target':minimum,'missing_examples':max(0,minimum-len(accepted_long)),'accepted_30min_works':len({r['source_id'] for r in accepted_long}),'missing_works':max(0,2-len({r['source_id'] for r in accepted_long}))})
 csvout(META/'exact-gaps-30min-works.csv',strict_gaps)
 registered_S=[r for r in sources['existing_sources'] if r.get('role')=='S']
 reserve_goal={'registered_new_S_video_works':len(registered_S),'target':6,'missing_registered_works':max(0,6-len(registered_S)),'inherited_reserved_family_count':len(read(ART/'reserved-index.json')['inherited_final']['source_ids']),'S_content_accessed':False}
 save(META/'reserved-work-target.json',reserve_goal)
 csvout(BASE/'annotations.csv',[{'segment_id':r['segment_id'],'source_id':r['source_id'],'partition':r['partition'],'proposal':r.get('proposal'),'accepted_label':r.get('accepted_label'),'status':r['reference_status']} for r in allunits])
 accepted=Counter(r['partition'] for r in allunits if r.get('accepted_label'));pending=[r for r in allunits if not r.get('accepted_label')]
 save(BASE/'pending-resolution.json',{'guide':(ROOT/'docs/beto-v3/guia-etiquetado-v3.md').read_text(encoding='utf-8'),'items':pending})
 external=[{k:r[k] for k in ['segment_id','source_id','family_id','partition','text','input_sha256','guide_sha256','source_sha256','start_sec','end_sec','cue_pieces'] if k in r} for r in pending]
 external_hash=hashlib.sha256(json.dumps(external,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 paths=[]
 for i in range(0,len(external),15):
  p=BASE/'external-review'/external_hash[:12]/f'batch-{i//15+1:03}.json';save(p,{'guide':(ROOT/'docs/beto-v3/guia-etiquetado-v3.md').read_text(encoding='utf-8'),'instructions':'Review exact target with original audio where available; no earlier labels supplied. Preserve unresolved cases.','items':external[i:i+15]});paths.append(str(p.relative_to(ROOT)))
 save(BASE/'external-review/current.json',{'inventory_sha256':external_hash,'units':len(external),'batches':paths})
 blockers=[f'{r["partition"]}/{r["class"]}: missing {r["missing_examples"]} references and {r["missing_works"]} works' for r in gaps if r['missing_examples'] or r['missing_works']]
 for role,target in [('T',300),('V',200)]:
  if accepted[role]<target:blockers.append(f'{role}: {accepted[role]}/{target}; missing {target-accepted[role]} accepted references')
  total=sum(r['partition']==role for r in allunits)
  if accepted[role]/max(1,total)<.9:blockers.append(f'{role}: unique reference coverage {accepted[role]}/{total} = {accepted[role]/max(1,total):.4f}, below operational 0.90 target')
 blockers.extend(f'{r["partition"]}: {r["acquired_transcribed_works_at_least_30min"]}/{r["target_30min_works"]} acquired/transcribed works >=30min; missing {r["missing_30min_works"]}' for r in work_goals if r['missing_30min_works'])
 blockers+=['Final H/T/V/S source-admission and dataset manifests not fully frozen',f'S remains metadata-only: {reserve_goal["registered_new_S_video_works"]}/6 new video works registered; missing {reserve_goal["missing_registered_works"]}']
 if pending:blockers.append(f'{len(pending)} units without a unique accepted reference; retain inventory')
 summary={'version':'phase-b-resume-02','old_units':125,'old_second_reviews':69,'old_accepted':sum(r['accepted_label'] is not None for r in units),'old_pending':sum(r['accepted_label'] is None for r in units),'new_ASR_units':len(new),'new_ASR_first_pass':sum('first_pass' in r for r in new),'new_ASR_second_review':sum('second_review' in r for r in new),'accepted_references':dict(accepted),'pending_references':len(pending),'C_ready':False,'blockers':blockers,'S_content_opened':False,'training_runs':0,'same_model_family_both_passes':True,'old_review_sessions':3,'old_review_batches':5,'old_label_agreements':sum(r['label_agreement'] for r in comparison),'old_label_disagreements':sum(not r['label_agreement'] for r in comparison),'annotation_status_note':'Accepted means usable reference judgment, not training admission or expert gold; pending counts use first proposals only'}
 save(META/'resume-summary.json',summary)
 archive(META/'summary.json');save(META/'summary.json',summary)
 for p in [ART/'phase-B-summary.json',ART/'annotation-progress.json']:archive(p)
 save(ART/'phase-B-summary.json',summary)
 ledger=read(ART/'budget-ledger-current.json');archive(ART/'budget-ledger-current.json')
 new_review_batches=sum(1 for p in (BASE/'asr-annotation').glob('*/second-review/batch-*.json'))
 sessions=[{'agent':'/root/blind_1','inputs':['review-batches/batch-001.json','review-batches/batch-002.json']},{'agent':'/root/blind_2','inputs':['review-batches/batch-003.json','review-batches/batch-004.json']},{'agent':'/root/blind_3','inputs':['review-batches/batch-005.json']}]
 for name,inputs in [('n08_blind',['N08/blind/batch-001.json','N08/blind/batch-002.json']),('n07_blind_a',['N07/blind/batch-001.json','N07/blind/batch-002.json']),('n07_blind_b',['N07/blind/batch-003.json','N07/blind/batch-004.json']),('n07_n03_blind_c',['N07/blind/batch-005.json','N07/blind/batch-006.json','N03/blind/batch-001.json'])]:
  if all((BASE/'asr-annotation'/p.replace('/blind/','/second-review/')).exists() for p in inputs):sessions.append({'agent':'/root/'+name,'inputs':['asr-annotation/'+p for p in inputs]})
 save(META/'review-session-provenance.json',{'model':'GPT-6 (declared system identity); exact backend weights unknown','same_model_family_as_first_pass':True,'fork_turns':'none for all second-review sessions','beto_predictions_supplied':False,'earlier_labels_supplied_to_second_review':False,'sessions':sessions,'adjudication':'Same reviewers then received both passes in their existing contexts; not a third independent model','provider_usage_tokens':None})
 # Later acquisition batches share this cumulative ledger. Rebuilding an older
 # batch must never refund their distinct annotated inputs.
 local_count=133+len({r['input_sha256'] for r in new if 'first_pass' in r})
 ledger.update(new_unique_annotation_proposals=max(ledger['new_unique_annotation_proposals'],local_count),phase_B_second_review_calls=len(sessions),phase_B_second_review_batches=5+new_review_batches,phase_B_second_review_units=69+sum('second_review' in r for r in new),services_paid_USD=0)
 ledger['annotation_count_note']='Conservative inherited 133 distinct annotated inputs plus distinct saved ASR input hashes; reviews of identical frozen inputs do not consume a new-unit quota; actual provider token usage unknown'
 ledger['ASR_accounting_note']='Conservative measured wall seconds of GPU transcription calls plus model loading; includes pilot. In-flight reservations settled after calls; CPU decoding/download time recorded separately'
 ledger['annotation_budget_remaining']=1200-ledger['new_unique_annotation_proposals'];assert ledger['annotation_budget_remaining']>=0 and ledger['ASR_gpu_seconds']<=28800
 save(ART/'budget-ledger-current.json',ledger)
 save(ART/'annotation-progress.json',{'unique_new_units_with_proposal':ledger['new_unique_annotation_proposals'],'accepted_references':dict(accepted),'accepted_for_training':0,'second_review_units':69+sum('second_review' in r for r in new),'same_model_family':True,'pending':len(pending),'V_references_frozen':False,'S_references_frozen':False,'provider_usage_tokens':None,'remaining_annotation_ceiling':ledger['annotation_budget_remaining']})
 verification={'passed':True,'old_blind_reviews_exact_ids_hashes_evidence':69,'old_adjudications_checked':69,'ASR_first_pass_checked':sum('first_pass' in r for r in new),'ASR_second_review_checked':sum('second_review' in r for r in new),'ASR_adjudications_checked':sum('adjudication' in r for r in new),'ASR_source_text_coverage':1.0,'S_closed':True,'no_training_eligible_rows':all(not r['training_eligible'] for r in allunits),'parent_first_pass_snapshot':digest(BASE/'before-resume/units-and-annotations.json'),'all_development_units_sha256':digest(BASE/'all-development-units.json'),'guide_sha256':guide}
 save(META/'resume-verification.json',verification)
 archive(META/'verification.json');save(META/'verification.json',verification)
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
