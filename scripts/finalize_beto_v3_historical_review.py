"""Apply only the documented phase-A extraction decisions; preserve all originals."""
import hashlib
from collections import Counter
from prepare_beto_v3 import ART, OUT, ROOT, read, sha, write

def main():
    initial=read(OUT/'datasets/H-initial.json')
    evidence={r['segment_id']:r for r in read(OUT/'historical-source-collation.json')}
    # Exact substrings of inherited text. No spelling restoration or generated context.
    cuts={
        'historical-v4-0715':(None,'josé bernardo dE TAGLE', 'Remove portrait sidebar heading appended after narrative'),
        'historical-v4-0120':(None,'No en vano', 'Remove incomplete next sentence and appended page footnotes'),
        'historical-v4-0768':('En la mañana',None, 'Remove header, duplicated pull quote and incomplete preceding sentence'),
        'historical-v4-0507':('Proseguir y ganar',None, 'Remove image caption and incomplete preceding quotation'),
        'historical-v4-0189':(None,'Sin embargo', 'Remove interrupted next sentence and unrelated footnote continuation'),
        'historical-v4-0351':(None,'21) John Fisher', 'Remove appended footnotes 21 and 22'),
    }
    decisions=[]
    rows=[]
    for old in initial['items']:
        sid=old['segment_id']
        row=dict(old)
        if sid in cuts:
            start,end,reason=cuts[sid]
            text=old['text']
            a=text.index(start) if start else 0
            z=text.index(end) if end else len(text)
            row['text']=text[a:z].strip()
            row['text_sha256']=hashlib.sha256(row['text'].encode()).hexdigest()
            row['reference_status']='extraction_collated_label_inherited'
            decisions.append({'segment_id':sid,'action':'extract_contiguous_original_span',
                'before':{'text':text,'label':old['label'],'sha256':old['text_sha256']},
                'after':{'text':row['text'],'label':row['label'],'sha256':row['text_sha256']},
                'original_char_span':[a,z],'source':evidence[sid]['source'],
                'source_page':evidence[sid]['page_1_based'],'reason':reason,'model_predictions_used':False})
        elif sid=='historical-v4-0043':
            decisions.append({'segment_id':sid,'action':'exclude_to_pending',
                'before':{'text':old['text'],'label':old['label'],'sha256':old['text_sha256']},
                'after':None,'source':evidence[sid]['source'],'source_page':evidence[sid]['page_1_based'],
                'reason':'Unit mixes conclusion of historiographic discussion, next incomplete section and bibliographic notes; no unique corrected target/reference frozen',
                'model_predictions_used':False})
            continue
        elif sid in evidence:
            decisions.append({'segment_id':sid,'action':'retain_inherited',
                'source':evidence[sid]['source'],'source_page':evidence[sid]['page_1_based'],
                'reason':'Source collated. R2/R4 boundary remains open for 0130 and 0125; no automatic reference change. 0811 is coherent diplomacy.',
                'model_predictions_used':False})
        rows.append(row)
    assert len(rows)==590
    assert all(r['text'] for r in rows)
    write(ART/'historical-review-decisions.json',{'reviewer':'GPT-6 Codex; exact backend unknown',
        'guide_sha256':sha(ROOT/'docs/beto-v3/guia-etiquetado-v3.md'), 'new_reviewed':10,
        'prior_reviewed_unique':20,'total_reviewed_unique':30,'decisions':decisions,
        'no_estimated_corpus_error_rate':True})
    write(OUT/'datasets/H-reviewed.json',{'version':'H-reviewed-v3-01','items':rows,
        'parent_sha256':sha(OUT/'datasets/H-initial.json'),
        'decisions_sha256':sha(ART/'historical-review-decisions.json'),
        'status':'frozen_reviewed_base; final comparison H still requires V/S work exclusions',
        'class_counts':dict(Counter(r['label'] for r in rows))})
    print('H-reviewed: 590 units; six exact-span extraction corrections, one pending exclusion; labels unchanged')

if __name__=='__main__':
    main()
