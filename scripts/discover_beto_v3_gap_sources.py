"""Bounded metadata-only public search; no captions or reserved content opened."""
import sys
from acquire_beto_v3_gap_batch import ROOT, ART, save
sys.path.insert(0,str(ROOT/'outputs/beto-v3/media-tools'))
import yt_dlp
queries=sys.argv[1:] or ['Perú crisis Cádiz independencia conferencia','primera república peruana 1821 1842 conferencia','independencia Perú mujeres indígenas conferencia']
rows=[]
with yt_dlp.YoutubeDL(dict(quiet=True,extract_flat=True,skip_download=True)) as y:
    for q in queries:
        result=y.extract_info('ytsearch5:'+q,download=False)
        entries=[{k:e.get(k) for k in ['id','title','channel','duration','url']} for e in result['entries']]
        rows.append(dict(query=q,items=entries))
        import hashlib
        save(ART/f'discovery-{hashlib.sha256(str(queries).encode()).hexdigest()[:12]}.json',rows)
        for e in entries:print(e)
