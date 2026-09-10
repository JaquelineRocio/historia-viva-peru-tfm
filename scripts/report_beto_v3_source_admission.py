"""Close documented event relation; retain blocked audio fidelity honestly."""
import json, hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts/beto-v3/admission-01'
BASE=ROOT/'outputs/beto-v3/phase-b-gap-02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 data=ROOT/'outputs/beto-v3/recovery-01/all-development-units.json';items=read(data)['items'];rows=[]
 for sid in sorted({r['source_id'] for r in items if r['source_id'].startswith('G')}):
  folder=BASE/sid;receipt=read(folder/'receipt.json');quality=read(folder/'transcript-quality.json') if (folder/'transcript-quality.json').exists() else {}
  units=[r for r in items if r['source_id']==sid];accepted=[r for r in units if r.get('accepted_label')]
  lead=quality.get('leading_interval_without_captions',0);duration=quality.get('duration_seconds',receipt.get('duration_seconds'));tail=quality.get('trailing_interval_without_captions',0)
  overlap=[r['segment_id'] for r in accepted if (lead>0 and r.get('start_sec',lead)<lead) or (tail>0 and r.get('end_sec',duration-tail)>duration-tail+.001)]
  row={'source_id':sid,'partition':receipt['role'],'duration_seconds':duration,'primary_duration_eligible':duration>=1800,'accepted_references_preserved':len(accepted),'classes':dict(Counter(r['accepted_label'] for r in accepted)),'leading_uncaptioned_seconds':lead,'trailing_uncaptioned_seconds':tail,'accepted_intersecting_uncaptioned_edges':overlap,'receipt_sha256':sha(folder/'receipt.json'),'transcript_quality_sha256':sha(folder/'transcript-quality.json') if quality else None,'literal_audio_fidelity_certified':False,'admission':'unchanged_pending_final_source_fidelity_review'}
  if sid in ['G13','G16','G18']:
   row.update(admission='audio_QA_blocked_HTTP403',audio_attempt_receipts=[str(p.relative_to(ROOT)) for p in sorted((ART/sid).glob('acquisition*.json'))],edge_gap_decision='Missing edge audio is outside accepted targets; no basis to infer silence, append text, change labels, or claim complete-video coverage.')
  if sid=='G17':row.update(admission='event_independence_admitted_audio_ASR_receipts_preserved',audio_decode_receipt=str((folder/'download.json').relative_to(ROOT)))
  rows.append(row)
 report={'scope':'Targeted outstanding admission; existing adjudications reused, no repeat annotation, no S content read by this script','effective_dataset_sha256':sha(data),'annotation_entries_spent':0,'ASR_gpu_seconds_spent':0,'paid_USD':0,'source_decisions':rows,'relation_decisions':[{'sources':['G16','G17'],'roles':['T','T'],'decision':'admit_as_two_distinct_recorded_events_same_speaker','evidence':[{'path':'outputs/beto-v3/phase-b-gap-02/G16/video-details.json','fact':'Official IIHS description: Charles F. Walker, 7 November 2018, Auditorio Gonzalo Aguirre Beltran, Xalapa, Veracruz.'},{'path':'outputs/beto-v3/phase-b-gap-02/G17/source-aac.info.json','fact':'Official Universidad Diego Portales upload_date 20140911, Cathedra Norbert Lechner.'},{'path':'outputs/beto-v3/phase-b-gap-02/G17/asr/cues.json','fact':'Distinct introduction welcomes second annual lecture and describes local masters programme; G16 introduction announces comparative resistance/negotiation talk.'},{'path':'artifacts/beto-v3/phase-b-gap-02/development-overlap.json','fact':'Previously completed exact 12-gram screen found no G16/G17 overlap; reused, not rerun.'}],'limitation':'Speaker, book and subject recur; thematic reuse is not independent historian evidence. Both recordings remain T; no split move. No audio fingerprint claim.'}],'quota_decision':'No accepted reference removed or added by this targeted check. Existing 5 colonial, 3 leadership, 2 republican V shortfalls remain provisional. Whole phase B cannot be certified closed while source fidelity remains unresolved.','limitations':['Network-approved audio requests returned HTTP 403 for G13/G16/G18; no evasion or repeated download attempts.','No ASR ran because the requested audio was unavailable.','Edge nonintersection distinguishes missing coverage from proven corruption; it does not certify the fidelity of captioned speech.']}
 ART.mkdir(parents=True,exist_ok=True);(ART/'source-admission-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'sources':len(rows),'accepted':sum(r['accepted_references_preserved'] for r in rows),'edge_intersections':{r['source_id']:r['accepted_intersecting_uncaptioned_edges'] for r in rows if r['accepted_intersecting_uncaptioned_edges']},'ASR_gpu_seconds':0}))
if __name__=='__main__':main()
