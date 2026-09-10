"""Bounded source collation for the ten preregistered historical cases."""
import re
import unicodedata
from collections import Counter

import fitz
from prepare_beto_v3 import ROOT, OUT, ART, read, sha, write

def grams(text):
    words=re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()).split()
    return {' '.join(words[i:i+5]) for i in range(max(0,len(words)-4))}

def main():
    sample=read(OUT/'historical-review-input.json')['items']
    manifest={r['segment_id']:r for r in read(ROOT/'artifacts/beto-v2/context/manifest.json')['items']}
    documents={}
    results=[]
    for row in sample:
        source=manifest[row['segment_id']]['source']
        path=ROOT/source['path']
        assert sha(path)==source['sha256']
        if str(path) not in documents:
            doc=fitz.open(path)
            documents[str(path)]=[page.get_text(sort=True) for page in doc]
        target=grams(row['text'])
        ranked=sorted(enumerate(documents[str(path)]),key=lambda pair:len(target&grams(pair[1])),reverse=True)
        page_index,text=ranked[0]
        record={**row,'source':source,'page_1_based':page_index+1,
            'matching_5grams':len(target&grams(text)),'target_5grams':len(target),
            'page_text_original':text,'source_verification':'PDF bytes hash and target/page lexical collation; no visual QA claim'}
        results.append(record)
    write(OUT/'historical-source-collation.json',results)
    print([(r['segment_id'],r['page_1_based'],r['matching_5grams']) for r in results])

if __name__=='__main__':
    main()
