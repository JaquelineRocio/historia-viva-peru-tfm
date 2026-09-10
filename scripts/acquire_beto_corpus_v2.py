"""Resumable institutional-source acquisition for BETO v2; no models or labels.
Reuses the repository's PDF reader and lexical normalization/overlap helpers.
"""
import argparse,hashlib,html,importlib.metadata,json,re,sys
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import requests
from pypdf import PdfReader
from prepare_agn_pilot import normalize,grams,similarities
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/beto-v2/corpus'
PLAN=ROOT/'artifacts/beto-v2/corpus/acquisition-plan.json'
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
class Page(HTMLParser):
    def __init__(self,s):
        super().__init__();self.meta={};self.links=[];self.text=[];self.feed(s)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta':self.meta.setdefault(a.get('name',a.get('property','')),[]).append(a.get('content',''))
        if tag in ['a','iframe']:self.links.append(a.get('href',a.get('src','')))
    def handle_data(self,d):self.text.append(d)
def fetch(url,path):
    if path.exists():return path.read_bytes()
    r=requests.get(url,timeout=30,headers={'User-Agent':'Academic corpus research; public access only'},verify=True)
    r.raise_for_status()
    if len(r.content)>40000000:raise ValueError('File exceeds 40 MB acquisition limit')
    with path.open('xb') as f:f.write(r.content)
    save(path.with_suffix(path.suffix+'.receipt.json'),{'url':url,'resolved_url':r.url,'status':r.status_code,'sha256':digest(r.content),'bytes':len(r.content),'acquired_at':datetime.now(timezone.utc).isoformat()})
    return r.content
def acquire(s):
    folder=BASE/s['id'];folder.mkdir(parents=True,exist_ok=True)
    resultpath=folder/'acquisition.json'
    if resultpath.exists():print(s['id'],'cached',flush=True);return
    r={**s,'acquired_at':datetime.now(timezone.utc).isoformat(),'status':'blocked','checkpoint':'started','processing_version':'beto-corpus-v2.1','command':sys.argv,'versions':{p:importlib.metadata.version(p) for p in ['requests','pypdf']}}
    try:
        if s['id'] in ['S11','S18']:raise ValueError(s['reason'])
        b=fetch(s['url'],folder/'landing.html');p=Page(b.decode('utf-8',errors='replace'));r['landing_sha256']=digest(b);r['metadata']=p.meta
        r['license_urls']=sorted(set(html.unescape(x) for x in p.links if 'creativecommons.org/licenses/' in x))
        r['linked_video_urls']=sorted(set(x for x in p.links if ('youtube.com/watch' in x or 'youtube.com/embed' in x or 'youtu.be/' in x)))
        r['checkpoint']='landing_saved'
        if s['kind']=='video':
            vids=[]
            for u in r['linked_video_urls']:
                m=re.search(r'(?:v=|embed/|youtu.be/)([A-Za-z0-9_-]{11})',u)
                if m:vids.append(m.group(1))
            vids=list(dict.fromkeys(vids));r['video_ids']=vids
            if not vids:raise ValueError('No direct institutional video URL exposed; event page is not transcript')
            if len(vids)>2:raise ValueError('Multiple video links require manual selection; no blind collection')
            # Public Spanish subtitles only; no audio download, proxy, cookies, paid fallback.
            from youtube_transcript_api import YouTubeTranscriptApi
            vid=s.get('video_id',vids[0]);transcripts=YouTubeTranscriptApi().list(vid)
            try:t=transcripts.find_manually_created_transcript(['es','es-ES','es-419'])
            except Exception:t=transcripts.find_generated_transcript(['es','es-ES','es-419'])
            cues=t.fetch().to_raw_data();save(folder/'cues.json',cues)
            r.update(status='transcript_obtained_rights_review',video_id=vid,cues=len(cues),is_generated=t.is_generated,transcript_sha256=digest((folder/'cues.json').read_bytes()),checkpoint='transcript_saved')
        elif s['kind']=='article':
            if not r['license_urls']:raise ValueError('No explicit reuse license on landing; full-text acquisition deferred')
            urls=p.meta.get('citation_pdf_url',[])
            if not urls:
                urls=[urljoin(s['url'],u.replace('/article/view/','/article/download/')) for u in p.links if re.search(r'/article/(?:view|download)/[^/]+/[^/]+',u) or '/bitstreams/' in u and u.endswith('/download')]
            if not urls:raise ValueError('No public PDF link exposed')
            url=html.unescape(s.get('pdf_url') or urls[0]);pdf=fetch(url,folder/'source.pdf')
            if not pdf.startswith(b'%PDF'):raise ValueError('Public file is not a PDF')
            pages=[{'page':i+1,'text_original':pg.extract_text() or ''} for i,pg in enumerate(PdfReader(folder/'source.pdf').pages)]
            if not (folder/'pages.json').exists():save(folder/'pages.json',pages)
            r.update(status='obtained_pending_content_review',pdf_url=url,pdf_sha256=digest(pdf),pages=len(pages),characters=sum(len(x['text_original']) for x in pages),checkpoint='pages_extracted')
        else:r.update(status=s.get('initial_status','candidate'),reason=s.get('reason','Metadata only; content and permissions pending'),checkpoint='metadata_saved')
    except Exception as e:r['reason']=str(e)[:1600];r['error_type']=type(e).__name__
    save(resultpath,r);print(s['id'],r['status'],r.get('pages',r.get('reason','')),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='*');args=ap.parse_args()
    for source in read(PLAN)['sources']:
        if args.ids is None or source['id'] in args.ids:acquire(source)
