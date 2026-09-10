"""Screen development transcripts for shared authentic text; never open reserve text."""
import re,json,unicodedata,hashlib
from collections import defaultdict
from pathlib import Path
from prepare_agn_pilot import normalize
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/beto-v3';BASE=OUT/'phase-b-completion-01';META=ROOT/'artifacts/beto-v3/phase-b-completion-01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def words(t):return normalize(t).split()
def grams(t,n=8):
 w=words(t);return {tuple(w[i:i+n]) for i in range(len(w)-n+1)}
def main():
 existing=defaultdict(list)
 for r in read(OUT/'datasets/H-reviewed.json')['items']:
  text=r.get('text',r.get('text_original',''));existing['H:'+str(r.get('source_id',r.get('family_id'))) ].append(text)
 for r in read(BASE/'before-resume/units-and-annotations.json')['items']:existing[r['partition']+':'+r['source_id']].append(r['text'])
 for sid in ['N08','N07','N03']:
  path=BASE/'new-sources'/sid/'asr/cues.json'
  if path.exists():existing[('V' if sid=='N07' else 'T' if sid=='N08' else 'auxiliary')+':'+sid]=[c['text'] for c in read(path)]
 sets={k:grams(' '.join(v)) for k,v in existing.items()};results=[]
 for sid in ['N08','N07','N03']:
  key=next((k for k in sets if k.endswith(':'+sid)),None)
  if not key:continue
  comparisons=[]
  for other,g in sets.items():
   if other==key:continue
   shared=sets[key]&g
   comparisons.append({'other_work':other,'shared_8grams':len(shared),'fraction_of_new_source':len(shared)/max(1,len(sets[key])),'fraction_of_other_work':len(shared)/max(1,len(g)),'examples':[' '.join(x) for x in sorted(shared)[:5]]})
  comparisons.sort(key=lambda r:r['shared_8grams'],reverse=True)
  results.append({'source_id':sid,'new_source_8grams':len(sets[key]),'top_matches':comparisons[:10],'manual_review_candidates':[r for r in comparisons if r['shared_8grams']>=3]})
 result={'method':'Exact normalized eight-word overlap screening; absence does not prove independence; quotations require manual interpretation','reserved_content_accessed':False,'H_and_current_T_V_compared':True,'items':results}
 (META/'new-transcript-overlap.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps([{'source':r['source_id'],'max_shared_8grams':r['top_matches'][0]['shared_8grams'] if r['top_matches'] else 0,'manual_candidates':len(r['manual_review_candidates'])} for r in results]))
if __name__=='__main__':main()
