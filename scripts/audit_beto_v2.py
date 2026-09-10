"""Read-only, offline BETO forensic audit. Never trains or overwrites outputs."""
import argparse, collections, csv, hashlib, importlib.metadata, json, os, platform, re, subprocess, sys, unicodedata, zipfile
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()
def canonical(d): return hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def norm(s): return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def save(p,d):
    with p.open('x',encoding='utf-8') as f: json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
def csvsave(p,rows,fields):
    with p.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default='artifacts/beto-v2/audit'); a=ap.parse_args()
    out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT) or (out.exists() and any(out.iterdir())): raise ValueError('Use a NEW directory inside repository')
    out.mkdir(parents=True,exist_ok=True)
    import numpy as np, torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from sklearn.metrics import f1_score,accuracy_score,confusion_matrix,mutual_info_score,normalized_mutual_info_score
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.stats import chi2_contingency
    torch.set_num_threads(4)
    git=['git','-c','safe.directory='+ROOT.as_posix()]
    report={'created_at':datetime.now(timezone.utc).isoformat(),'command':subprocess.list2cmdline([sys.executable,*sys.argv]),'commit':subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip(),'working_tree':subprocess.check_output(git+['status','--porcelain'],text=True),'python':platform.python_version(),'versions':{k:importlib.metadata.version(k) for k in ['torch','transformers','tokenizers','numpy','scikit-learn','scipy','safetensors']},'offline':True,'training_performed':False,'production_verified_live':False}
    checkpoints=[ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',ROOT/'outputs/experiments/beto-u1/beto-lr2e5']
    report['checkpoints']={rel(p):{f.name:sha(f) for f in p.iterdir() if f.is_file()} for p in checkpoints}
    report['checkpoint_metadata']={rel(p):{n:read(p/n) for n in ['labels.json','config.json']} for p in checkpoints}
    tokenizers=[AutoTokenizer.from_pretrained(p,local_files_only=True) for p in checkpoints]
    report['tokenizer_settings']=[{'class':type(t).__name__,'do_lower_case':getattr(t,'do_lower_case',None),'special_tokens':t.special_tokens_map,'truncation_side':t.truncation_side,'padding_side':t.padding_side} for t in tokenizers]
    manifest={}
    paths=[]
    for folder in ['artifacts','outputs','configs','scripts','apps/ml/app','apps/api/src','deploy','notebooks','docs']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and p.suffix in ['.json','.py','.ts','.md','.ipynb','.txt'] and not any(x in p.parts for x in ['venv-ml','venv-ops','tools','node_modules','__pycache__','beto-v2']):
                manifest[rel(p)]=sha(p)
                if p.suffix=='.json' and p.stat().st_size<15000000:
                    try:
                        d=read(p)
                        if isinstance(d,dict) and isinstance(d.get('items'),list) and d['items'] and all(isinstance(r,dict) and isinstance(r.get('text'),str) and isinstance(r.get('label'),str) for r in d['items']): paths.append((p,d))
                    except (ValueError,UnicodeError): pass
    report['input_manifest']=manifest
    report['datasets']=[]; distributions=[]; suspicious=[]; tokens=[]; allunique={}; lengths={}
    for p,d in paths:
        rows=d['items']; labels=d.get('labels') or sorted({r['label'] for r in rows}); name=rel(p)
        counts=collections.Counter((str(r.get('resourceId','UNKNOWN')),r.get('sourceType','UNKNOWN'),r.get('split','UNSPECIFIED'),r['label']) for r in rows)
        for src,fmt,sp in sorted({k[:3] for k in counts}):
            for lab in labels: distributions.append(dict(dataset=name,source=src,format=fmt,split=sp,label=lab,count=counts[src,fmt,sp,lab]))
        for i,r in enumerate(rows):
            text=r['text']; key=hashlib.sha256(text.encode()).hexdigest()
            allunique.setdefault(key,{'text':text,'references':[]})['references'].append({'dataset':name,'index':i,'label':r['label'],'split':r.get('split'),'source':r.get('resourceId')})
            if key not in lengths: lengths[key]=len(tokenizers[0](text,truncation=False,add_special_tokens=True)['input_ids'])
            n=lengths[key]
            tokens.append(dict(dataset=name,index=i,text_sha256=key,label=r['label'],source=r.get('resourceId','UNKNOWN'),format=r.get('sourceType','UNKNOWN'),split=r.get('split','UNSPECIFIED'),tokens=n,**{f'lost_{m}':max(0,n-m) for m in [128,192,256,384,512]}))
        sources=[str(r.get('resourceId','UNKNOWN')) for r in rows]; y=[r['label'] for r in rows]; srcs=sorted(set(sources)); labs=sorted(set(y))
        table=np.array([[sum(s==src and lab==l for s,lab in zip(sources,y)) for l in labs] for src in srcs])
        chi,pvalue,_,_=chi2_contingency(table) if min(table.shape)>1 else (0,1,0,0)
        ns=[lengths[hashlib.sha256(r['text'].encode()).hexdigest()] for r in rows]
        groups=collections.defaultdict(list); rawgroups=collections.defaultdict(list); source_splits=collections.defaultdict(set)
        for i,r in enumerate(rows): groups[norm(r['text'])].append(i);rawgroups[r['text']].append(i);source_splits[str(r.get('resourceId','UNKNOWN'))].add(r.get('split','UNSPECIFIED'))
        report['datasets'].append({'path':name,'file_sha256':sha(p),'canonical_sha256':canonical(d),'n':len(rows),'labels':labels,'split_counts':dict(collections.Counter(r.get('split','UNSPECIFIED') for r in rows)),'source_count':len(srcs),'missing_author':sum(not r.get('author') for r in rows),'missing_source':sum(not r.get('resourceId') for r in rows),'source_overlap':{k:sorted(v) for k,v in source_splits.items() if len(v)>1},'exact_duplicate_groups':[v for v in rawgroups.values() if len(v)>1],'normalized_duplicate_groups':[v for v in groups.values() if len(v)>1],'contradictory_exact_groups':[v for v in groups.values() if len({rows[i]['label'] for i in v})>1],'source_label_association':{'mutual_information_nats':float(mutual_info_score(sources,y)),'normalized_mutual_information':float(normalized_mutual_info_score(sources,y)),'cramers_v':float(np.sqrt(chi/(len(rows)*max(1,min(table.shape)-1)))),'chi_square_p_descriptive_not_iid':float(pvalue)},'tokens':{'min':min(ns),'median':float(np.median(ns)),'max':max(ns),'truncation':{str(m):{'segments':sum(n>m for n in ns),'fraction':sum(n>m for n in ns)/len(ns),'lost_tokens':sum(max(0,n-m) for n in ns)} for m in [128,192,256,384,512]}}})
    print('Datasets',len(paths),'unique texts',len(allunique),flush=True)
    # Similarity is a screening measure, never an automatic label correction.
    keys=list(allunique); texts=[allunique[k]['text'] for k in keys]
    vect=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=60000,dtype=np.float32)
    X=vect.fit_transform(texts); pairs=[]
    for start in range(0,len(texts),128):
        sim=(X[start:start+128]@X.T).tocoo()
        for ii,j,v in zip(sim.row,sim.col,sim.data):
            i=start+int(ii);j=int(j)
            if i<j and v>=0.82:
                li={r['label'] for r in allunique[keys[i]]['references']};lj={r['label'] for r in allunique[keys[j]]['references']}
                pairs.append({'a':keys[i],'b':keys[j],'cosine':float(v),'different_label_sets':li!=lj})
    save(out/'similarity-pairs.json',{'method':'char_wb TFIDF 3-5, min_df=2, max_features=60000, cosine>=0.82; unique raw texts; version overlaps are not split leakage','pairs':pairs,'texts':allunique})
    for k,item in allunique.items():
        t=item['text']; reasons=[]
        if '\ufffd' in t or re.search('Ã.|Â.|â€',t): reasons.append('possible_encoding_noise')
        if '\xad' in t or re.search(r'\w\s*-\s+\w',t): reasons.append('pdf_broken_word')
        if re.search(r'\b(\w+)\s+\1\b',t,re.I): reasons.append('repeated_word_possible_asr')
        if re.search(r'\b(?:ISBN|ISSN|Ibid|op\. cit|bracketleft|bracketright)\b',t,re.I): reasons.append('editorial_or_citation')
        if t and (t[0].islower() or t[-1] not in '.!?;:»”\"'): reasons.append('possible_cut_boundary')
        if len({r['label'] for r in item['references']})>1: reasons.append('same_text_multiple_labels_across_versions')
        if reasons:
            for r in item['references']: suspicious.append(dict(**r,text_sha256=k,reason=';'.join(reasons),status='requires_context_review_not_confirmed_error',text=t))
    for p in pairs:
        if p['different_label_sets']:
            suspicious.append(dict(dataset='cross_dataset_similarity',index='',label='',split='',source='',text_sha256=p['a'],reason='similar_different_labels:'+p['b'],status='requires_context_review_not_confirmed_error',text=allunique[p['a']]['text']))
    report['similarity']={'unique_texts':len(keys),'pairs_above_082':len(pairs),'different_label_pairs':sum(p['different_label_sets'] for p in pairs)}
    csvsave(out/'token-lengths.csv',tokens,list(tokens[0])); csvsave(out/'source-class-distribution.csv',distributions,list(distributions[0])); csvsave(out/'suspicious-labels.csv',suspicious,list(suspicious[0]))
    gold=read(ROOT/'artifacts/datasets/gold-v1-source-aware.json'); rows=gold['items']; labels=gold['labels']; predictions=[]; report['reproduced_metrics']={}
    report['tokenizer_ids_equal_on_gold']=all(tokenizers[0](r['text'])['input_ids']==tokenizers[1](r['text'])['input_ids'] for r in rows)
    # CPU fp32 mirrors deployed beto.infer, without changing the service singleton.
    for ck,tok in zip(checkpoints,tokenizers):
        meta=read(ck/'labels.json'); model=AutoModelForSequenceClassification.from_pretrained(ck,local_files_only=True).eval(); pred=[]
        for start in range(0,len(rows),16):
            enc=tok([r['text'] for r in rows[start:start+16]],padding=True,truncation=True,max_length=meta['max_len'],return_tensors='pt')
            with torch.inference_mode(): probs=model(**enc).logits.softmax(-1)
            vals,ids=probs.max(-1)
            for offset,(idx,conf) in enumerate(zip(ids.tolist(),vals.tolist())):
                i=start+offset;r=rows[i];lab=meta['id2label'][str(idx)];pred.append(lab)
                predictions.append(dict(dataset='artifacts/datasets/gold-v1-source-aware.json',dataset_sha256=sha(ROOT/'artifacts/datasets/gold-v1-source-aware.json'),index=i,split=r['split'],source=r['resourceId'],label=r['label'],prediction=lab,confidence=conf,checkpoint=rel(ck),checkpoint_sha256=report['checkpoints'][rel(ck)]['model.safetensors'],commit=report['commit'],text_sha256=hashlib.sha256(r['text'].encode()).hexdigest()))
            if start%160==0: print(rel(ck),start,'/',len(rows),flush=True)
        report['reproduced_metrics'][rel(ck)]={}
        for split in ['train','val','test']:
            ids=[i for i,r in enumerate(rows) if r['split']==split]; yt=[rows[i]['label'] for i in ids];yp=[pred[i] for i in ids]
            report['reproduced_metrics'][rel(ck)][split]={'n':len(ids),'correct':sum(a==b for a,b in zip(yt,yp)),'f1_macro_seven':f1_score(yt,yp,labels=labels,average='macro',zero_division=0),'accuracy':accuracy_score(yt,yp),'confusion_matrix':confusion_matrix(yt,yp,labels=labels).tolist()}
        del model
    csvsave(out/'predictions-current.csv',predictions,list(predictions[0]))
    report['zip_evidence']={}
    for p in [ROOT/'modelo_vN.zip',ROOT/'artifacts/training/historia-viva-beto-v1-colab.zip']:
        with zipfile.ZipFile(p) as z:
            entries={}
            for n in z.namelist():
                if n.endswith('/'): continue
                h=hashlib.sha256()
                with z.open(n) as f:
                    for b in iter(lambda:f.read(1048576),b''):h.update(b)
                entries[n]=h.hexdigest()
            report['zip_evidence'][rel(p)]={'sha256':sha(p),'entries':entries}
    changed=[p for p,h in manifest.items() if sha(ROOT/p)!=h]
    report['input_preservation']={'changed':changed,'checked':len(manifest)}
    assert not changed
    save(out/'dataset-audit.json',report)
    print(json.dumps(report['reproduced_metrics'],indent=2),flush=True)
if __name__=='__main__': main()
