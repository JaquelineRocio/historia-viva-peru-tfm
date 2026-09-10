"""Full caption inventory; timestamp anchors are pending discourse review."""
import hashlib, json, re, sys
from collections import defaultdict
from acquire_beto_v3_gap_batch import ROOT, DEST, ART, read, save
sys.path.insert(0,str(ROOT/'apps/ml'))
from app.segmentation import segment_by_time
from transformers import AutoTokenizer

def main():
    tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
    guide=ROOT/'docs/beto-v3/guia-etiquetado-v3.md';gh=hashlib.sha256(guide.read_bytes()).hexdigest()
    summary=[]
    for path in sorted(DEST.glob('*/cues.json')):
        receipt=read(path.parent/'receipt.json');sid=receipt['source_id'];cues=read(path)
        dest=DEST/sid/'annotation'
        if (dest/'units.json').exists():continue
        groups=defaultdict(list)
        anchors=segment_by_time(cues,window_sec=75,overlap_sec=0)
        for i,c in enumerate(cues):groups[int(c['start']//75)].append((i,c))
        items=[]
        for n,anchor in enumerate(anchors,1):
            selected=groups[int(anchor.start_sec//75)]
            original=' '.join(c['text'].strip() for _,c in selected if c['text'].strip())
            text=re.sub(r'\s+',' ',original).strip();tokens=len(tok(text)['input_ids'])
            items.append(dict(segment_id=f'{sid}-u{n:03}',source_id=sid,family_id=receipt['family_id'],partition=receipt['role'],text_original=original,text=text,input_sha256=hashlib.sha256(text.encode()).hexdigest(),guide_sha256=gh,source_sha256=receipt['captions_sha256'],cue_indices=[i for i,c in selected],start_sec=anchor.start_sec,end_sec=anchor.end_sec,tokens_with_specials=tokens,would_truncate_tokens=max(0,tokens-384),training_eligible=False,accepted_label=None,status='pending_discourse_and_annotation_review'))
        assert sorted(i for u in items for i in u['cue_indices'])==list(range(len(cues)))
        save(dest/'units.json',{'items':items,'segmentation':'production segment_by_time(75,0); full cue inventory; discourse and length review REQUIRED before acceptance'})
        for i in range(0,len(items),15):save(dest/f'blind/batch-{i//15+1:03}.json',{'guide':guide.read_text(encoding='utf-8'),'items':items[i:i+15]})
        gaps=[{'after_cue':i-1,'start':cues[i-1]['start']+cues[i-1]['duration'],'end':c['start']} for i,c in enumerate(cues) if i and c['start']-(cues[i-1]['start']+cues[i-1]['duration'])>15]
        qa=dict(source_id=sid,units=len(items),overlength=sum(u['would_truncate_tokens']>0 for u in items),full_returned_cue_coverage=True,duration_seconds=receipt['duration_seconds'],caption_start=receipt['caption_start'],caption_end=receipt['caption_end'],gaps_over_15s=gaps,literal_fidelity_certified=False,missing_speech_not_inferred_from_caption_gaps=True)
        save(DEST/sid/'caption-quality.json',qa);summary.append(qa);print(sid,len(items),qa['overlength'])
    save(ART/'segmentation-run.json',{'items':summary,'new_annotation_inputs_consumed':0,'S_closed':True})

if __name__=='__main__': main()
