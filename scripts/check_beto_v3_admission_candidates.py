"""Candidate metadata admission only; S payloads are never opened."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 paths=['artifacts/beto-v3/source-registry.json','artifacts/beto-v3/phase-b-completion-01/source-registry-final.json','artifacts/beto-v3/phase-b-completion-01/new-source-relations.json','artifacts/beto-v3/phase-b-gap-02/reserve-metadata.json','artifacts/beto-v3/phase-b-gap-02/acquisition-plan.json']
 records=[]
 def walk(x):
  if isinstance(x,dict):
   if x.get('video_id') or x.get('family_id'):records.append(x)
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 for p in paths:walk(read(ROOT/p))
 result=[]
 for sid,vid in [('N01','KHcAIKD38sI'),('-Ma1tt97eFg','-Ma1tt97eFg')]:
  matches=[r for r in records if r.get('video_id')==vid or r.get('family_id')=='video-'+vid]
  conflicts=[r for r in matches if r.get('role',r.get('proposed_role')) not in [None,'V']]
  assert not conflicts
  info=read(ROOT/'outputs/beto-v3/admission-01'/sid/'source.info.json')
  result.append({'source_id':sid,'video_id':vid,'role_preserved':'V','title':info['title'],'official_channel':info['channel'],'upload_date':info['upload_date'],'duration_metadata_seconds':info['duration'],'long_duration_metadata_pass':info['duration']>=1800,'matching_registered_records':len(matches),'conflicting_roles':[],'registered_family':'video-'+vid,'decision':'metadata_and_partition_admitted_pending_decode_and_development_text_overlap','relation_rationale':'Registered TVPeru episode on a different dated subject, no video/family collision with H/T/S metadata. Shared programme branding does not establish one original episode. Reused interview excerpts cannot be ruled out by metadata and require development transcript screening before annotation.','content_comparison_required':True})
 report={'scope':'New V candidate metadata; no S audiovisual/transcript/labels accessed','sources':result,'evidence_files':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths],'paid_USD':0,'ASR_gpu_seconds':0,'annotation_entries':0}
 p=ROOT/'artifacts/beto-v3/admission-01/candidate-metadata-admission.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
