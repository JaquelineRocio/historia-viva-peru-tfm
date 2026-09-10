"""Sentence-complete revision; never replaces the coarse extraction checkpoint."""
from process_beto_pilot_v2 import *

def main():
    parents=[json.loads(x) for x in (OUT/'candidates.jsonl').read_text(encoding='utf-8').splitlines()]
    tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
    rows=[]
    for p in parents:
        text=p['text']; boundaries=[0]
        for m in re.finditer(r'[.!?](?:[”»"])?\d*\s+(?=[¿¡«“"(]*[A-ZÁÉÍÓÚÑ])',text):
            before=text[max(0,m.start()-12):m.start()]
            if re.search(r'\b(?:Sr|Dr|Mr|Sra|Dra|p|pp|vol|núm|nº|etc|fig|al)$',before,re.I):continue
            boundaries.append(m.end())
        boundaries.append(len(text)); start=0
        for end in boundaries[1:]:
            if len(text[start:end].split())<90 and end!=len(text):continue
            raw=text[start:end]; t=raw.strip(); off=start+len(raw)-len(raw.lstrip())
            flags=[x for x in p['quality_flags'] if x=='visual_collation_required']
            if not terminal(t):flags.append('incomplete_end')
            if not re.match(r'^[¿¡«“"(]*[A-ZÁÉÍÓÚÑ0-9]',t):flags.append('possible_incomplete_start')
            if re.search(r'Keywords:|Palabras clave:|FIGURA \d|TABLA \d|Desde el Sur \||\x04',t):flags.append('paratext_or_layout_mixed')
            if not t:start=end;continue
            rows.append({**p,'segment_id':p['segment_id']+f'-s{off:05}','parent_id':p['segment_id'],'text':t,'parent_offsets':[off,off+len(t)],'text_original':None,'original_reference':'candidates.jsonl parent_id and layout-blocks.jsonl block_ids','context':{'previous':text[max(0,off-800):off] or p['context']['previous'][-800:],'next':text[off+len(t):off+len(t)+800] or p['context']['next'][:800]},'beto_tokens':len(tok(t,truncation=False)['input_ids']),'text_sha256':sha(t.encode()),'quality_flags':flags,'status':'pending_extraction' if flags else 'usable_candidate','transformations':p['transformations']+['sentence_boundary_grouping_complete_no_truncation']})
            start=end
    # Visual transcription is restricted to these exact spans on inspected images.
    fixes=[('S05',7,1,'El destino de una revolución,','La independencia comienza', 'El destino de una revolución, más que en las alturas de la clase dominante, se decide en el interior de las clases populares. El bandolerismo que asola los valles y caminos de la costa, los frecuentes motines rurales en la sierra, la persistencia de la rebelión de Juan Santos Atahualpa, son signos no sólo de un malestar social, sino de un profundo descontento, de una falta de resignación que se propala en espacios muy diferentes y que recorre todo el siglo XVIII. Pero lo que nos interesa es saber si esta violencia popular fue capaz de producir alguna alternativa frente al colonialismo y la aristocracia limeña.'),
    ('S05',7,1,'La independencia comienza','Hay una evidente','La independencia comienza en 1780. El levantamiento tupamarista sorprende a cualquier estudioso de los movimientos campesinos, por el dilatado escenario de la lucha, desde el Cusco hasta el altiplano, con una irradiación que llegará hasta Huarochirí, en la sierra de Lima y Salta, Jujuy y Tarapacá por el sur. Mientras, por ejemplo, las “guerras campesinas” (1525) de Alemania duraron unos seis meses, los acontecimientos en el Cusco comenzaran en noviembre de 1780, pero no terminan en abril del año siguiente con el ajusticiamiento de Túpac Amaru, sino que duran hasta 1782 después del asedio de La Paz por Catari. En definitiva todo el espacio quechua y aymara hablante fue convulsionado.'),
    ('S17',3,1,'Es el','Ella,','Es el momento en el que los grandes hacendados no obtienen mas esclavos, lo que implicaba que deberían de pensar dos veces si azotaban al esclavo hasta matarlo. La vida del esclavo —su única arma— se convirtió en un mecanismo de chantaje más efectivo. Es el momento en que en Lima se suscitan voces como las de Rosa, una mulata “blanca”, mujer de un negro albañil.')]
    corrections=[]
    for i,(sid,pageno,block,begin,end,corrected) in enumerate(fixes):
        doc=fitz.open(BASE/sid/'source.pdf'); b=doc[pageno-1].get_text('blocks')[block]; raw=b[4]; a=raw.index(begin); z=raw.index(end,a+len(begin)); original=raw[a:z]
        ident=f'{sid}-visual-p{pageno:03}-{i+1:02}'
        image=OUT/f'{sid}-p{pageno}.png'
        corr={'correction_id':ident,'source_id':sid,'page':pageno,'block_index_unsorted':block,'bbox':b[:4],'raw_offsets':[a,z],'original':original,'corrected':corrected,'evidence_image':image.relative_to(ROOT).as_posix(),'evidence_sha256':sha(image.read_bytes()),'reviewer':'GPT-6 Codex current session; exact provider snapshot unavailable','scope':'only displayed span; neighboring OCR not certified','reason':'visual collation of OCR substitutions and punctuation; printed historical wording retained','diff':list(__import__('difflib').ndiff(clean(original).split(),corrected.split()))}
        corrections.append(corr)
        rows.append({'segment_id':ident,'source_id':sid,'family_id':'family-'+sid,'format':'pdf','text':corrected,'text_original':original,'pages':[pageno],'source_sha256':sha((BASE/sid/'source.pdf').read_bytes()),'context':{'previous':clean(raw[:a]),'next':clean(raw[z:]),'quality':'adjacent context uncorrected OCR'},'beto_tokens':len(tok(corrected,truncation=False)['input_ids']),'text_sha256':sha(corrected.encode()),'quality_flags':[],'status':'usable_candidate','label':None,'split':None,'transformations':['visual_correction'],'correction_id':ident})
    lines(OUT/'candidates-complete-v2.jsonl',rows);save(OUT/'visual-corrections.json',corrections)
    # Re-run comparison on every refined text including corrected OCR against all historical versions.
    old=read(OUT/'duplication.json'); refs={}; guards={}
    for rel in old['historical_files']:
        path=ROOT/rel
        if not path.exists():continue
        guards[rel]=sha(path.read_bytes())
        for i,r in enumerate(read(path).get('items',[])):
            t=r.get('text','');n=normalize(t)
            if n:refs.setdefault(n,{'text':t,'versions':[]})['versions'].append({'dataset':rel,'index':i,'record_id':r.get('id'),'resource_id':r.get('resourceId')})
    pool=[{'kind':'historical','key':sha(n.encode()),**r} for n,r in refs.items()]+[{'kind':'candidate','key':r['segment_id'],'text':r['text']} for r in rows]
    inv=defaultdict(set); gs=[]; alerts=[]; exact_index=defaultdict(set)
    for i,r in enumerate(pool):
        g=grams(r['text']); gs.append(g);n=normalize(r['text']); possible=set(exact_index[n])
        for w in g:possible.update(inv[w])
        if r['kind']=='candidate':
            for j in sorted(possible):
                jac,con=similarities(g,gs[j]); exact=n==normalize(pool[j]['text'])
                if exact or jac>=.25 or con>=.8:alerts.append({'candidate_id':r['key'],'other_kind':pool[j]['kind'],'other_id':pool[j]['key'],'versions':pool[j].get('versions',[]),'exact':exact,'jaccard':jac,'containment':con,'relation':'text_overlap_requires_review; corrected versions can share parent work'})
        for w in g:inv[w].add(i)
        exact_index[n].add(i)
    save(OUT/'duplication-complete-v2.json',{'historical_files_sha256':guards,'historical_unique_texts':len(refs),'candidates_checked':len(rows),'method':old['method'],'alerts':alerts,'version_groups_reference':'duplication.json','work_dependencies_reference':'artifacts/beto-v2/corpus/source-groups-v2.json','reserved_content_read':False})
    print(json.dumps({'count':len(rows),'statuses':dict(Counter(r['status'] for r in rows)),'alerts':len(alerts)},ensure_ascii=False))
if __name__=='__main__':main()
