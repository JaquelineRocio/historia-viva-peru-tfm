"""Reuse temporal anchors, move boundaries to complete ASR sentences, preserve all text."""
import sys,re,hashlib,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/ml'))
from app.segmentation import segment_by_time
from transformers import AutoTokenizer
BASE=ROOT/'outputs/beto-v3/phase-b-completion-01'
def sha(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 global BASE
 parser=argparse.ArgumentParser()
 parser.add_argument('--base',type=Path,default=BASE)
 parser.add_argument('sources',nargs='*')
 args=parser.parse_args();BASE=args.base.resolve()
 assert BASE.is_relative_to(ROOT/'outputs/beto-v3')
 tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
 guide=(ROOT/'docs/beto-v3/guia-etiquetado-v3.md').read_text(encoding='utf-8')
 gh=hashlib.sha256((ROOT/'docs/beto-v3/guia-etiquetado-v3.md').read_bytes()).hexdigest()
 for sid in args.sources or ['N08','N07','N03']:
  folder=(BASE/'new-sources'/sid) if (BASE/'new-sources').exists() else BASE/sid
  path=folder/'asr/cues.json'
  if not path.exists():continue
  dest=BASE/'asr-annotation'/sid if (BASE/'new-sources').exists() else folder/'annotation'
  if (dest/'units.json').exists():continue
  cues=json.loads(path.read_text(encoding='utf-8'));source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
  anchors=segment_by_time(cues,window_sec=75,overlap_sec=0)
  full=' '.join(c['text'].strip() for c in cues); spans=[];pos=0
  for i,c in enumerate(cues):
   n=len(c['text'].strip());spans.append((pos,pos+n,i));pos+=n+1
  # Move only at observed punctuation; timestamps retain parent-cue precision.
  sentence_ends=[m.end() for m in re.finditer(r'[.!?](?:[”"»])?(?:\s+|$)',full)]
  if not sentence_ends or sentence_ends[-1]!=len(full):sentence_ends.append(len(full))
  bounds=[0]; changes=[]
  for anchor in anchors[1:]:
   original=next((a for a,z,i in spans if cues[i]['start']>=anchor.start_sec),len(full))
   choices=[e for e in sentence_ends if e>bounds[-1]]
   if not choices:continue
   b=min(choices,key=lambda e:abs(e-original))
   if b<len(full):bounds.append(b);changes.append({'original_anchor_char':original,'new_boundary_char':b})
  bounds.append(len(full)); refined=[0]
  for endpoint in sorted(set(bounds))[1:]:
   while len(tok(full[refined[-1]:endpoint].strip())['input_ids'])>384:
    options=[e for e in sentence_ends if refined[-1]<e<endpoint and len(tok(full[refined[-1]:e].strip())['input_ids'])<=384]
    if not options:break
    refined.append(max(options))
   refined.append(endpoint)
  items=[]
  for n,(a,z) in enumerate(zip(refined,refined[1:]),1):
   text=full[a:z].strip();selected=[(x,y,i) for x,y,i in spans if x<z and y>a]; tokens=len(tok(text)['input_ids'])
   items.append({'segment_id':f'{sid}-asr-{n:03}','source_id':sid,'family_id':f'candidate-{sid}',
    'partition':json.loads((folder/'receipt.json').read_text(encoding='utf-8')).get('role', 'V' if sid=='N07' else ('T' if sid=='N08' else 'auxiliary')),
    'source_char_span':[a,z],'text_original':full[a:z],'text':text,'input_sha256':sha(text),'guide_sha256':gh,
    'source_sha256':source_hash,'cue_pieces':[{'cue_index':i,'cue_char_start':max(a,x)-x,'cue_char_end':min(z,y)-x} for x,y,i in selected],
    'start_sec':cues[selected[0][2]]['start'],'end_sec':cues[selected[-1][2]]['end'],
    'tokens_with_specials':tokens,'would_truncate_tokens':max(0,tokens-384),'training_eligible':False,
    'status':'pending_discourse_and_annotation_review','primary_duration_eligible':json.loads((folder/'download.json').read_text())['primary_duration_eligible']})
  assert ''.join(r['text_original'] for r in items)==full
  save(dest/'units.json',{'items':items,'source_sha256':source_hash,'guide_sha256':gh,'segmentation':'production segment_by_time(75,0), nearest authentic sentence boundary; 384-token splits at sentence ends only','changes':changes,'full_transcript_text_coverage':1.0})
  for i in range(0,len(items),15):save(dest/f'blind/batch-{i//15+1:03}.json',{'guide':guide,'items':items[i:i+15]})
  print(sid,len(items),'overlength',sum(r['would_truncate_tokens']>0 for r in items))
if __name__=='__main__':main()
