"""Package actual isolated AI passes and text-grounded adjudication, never gold."""
from process_beto_pilot_v2 import *
from datetime import datetime, timezone

# These are the primary session's actual semantic review notes, not a labeling heuristic.
REVIEW={
'S01-seg0005-s00704':'R5: las herramientas culturales afianzan repúblicas; la transformación lingüística explica esa pedagogía, sin desarrollar un programa emancipador específico.',
'S01-seg0005-s02873':'R5: el hecho es la recepción política de Tocqueville en 1842 para responder a la crisis republicana. No es mera bibliografía ni queda fuera de alcance por una fecha editorial.',
'S01-seg0005-s04319':'R7: el objetivo desarrolla la difusión de Washington en 1851. El contexto muestra continuidad pedagógica, pero no convierte ese episodio posterior en una explicación del proceso hasta 1842. Se resuelve la duda temporal conservando alternativa R5.',
'S01-seg0019-s00000':'R5: el argumento desarrolla funcionamiento fallido y recursos ceremoniales de las instituciones confederales; guerra y caudillos son factores explicativos.',
'S03-seg0006-s00000':'R1: describe jurisdicción, creación y sucesión de mando del departamento colonial, sin operaciones armadas desarrolladas.',
'S03-seg0009-s00000':'R3: Bayona y las juntas introducen las exigencias navales; el desarrollo principal se centra en tareas, presencia y conflicto de fuerzas marítimas, no en doctrinas de soberanía.',
'S03-seg0015-s00000':'R3: secuencia de ataque, captura y evasión territorial. El canje es desenlace incidental de la operación, no diplomacia como argumento principal.',
'S03-seg0037-s00000':'R3: persecución y combate naval narrados de manera completa; contexto identifica la operación.',
'S03-seg0042-s00577':'R4: acuerdo diplomático con obligaciones salariales, reconocimiento, repatriación y ascensos; el objeto naval no lo convierte en relato de batalla.',
'S03-seg0044-s00991':'R1: disputa sobre la obediencia administrativa a audiencias y cédula real dentro del orden colonial; no desarrolla emancipación ni soberanía republicana.',
'S06-seg0005-s00000':'R7: crítica a conmemoraciones y publicaciones actuales sin explicar todavía el acontecimiento histórico; la explicación en el contexto no reemplaza al objetivo.',
'S06-seg0016-s00000':'R3: postura defensiva, captura naval y bloqueo del Callao son el objeto explícito.',
'S06-seg0020-s00000':'R3: duración y bajas de la refriega; el contexto identifica el combate y completa las referencias anafóricas.',
'S06-seg0032-s00000':'R4: el oficio de justificación del virrey responde a consecuencias diplomáticas. La multitud aparece en esa defensa oficial, sin convertir la cita en una explicación autónoma de agencia social.',
'S06-seg0036-s00000':'R6: resuelve quién participó y quién lideró la masacre; las referencias historiográficas posteriores sustentan una controversia histórica concreta, no R7.',
'S10-seg0003-s00000':'R5: implementación y límites de prescripciones escolares, anclados por el caso de 1825 en contexto; no mera propuesta de régimen.',
'S10-seg0005-s00000':'PENDIENTE R0/R5/R7: programa metodológico e hipótesis sustantiva se mezclan para todo el XIX. El contexto incluye la guerra de 1879–1883. No permite establecer con seguridad cuánto de esa hipótesis se refiere a 1780–1842. El acuerdo entre pasadas no resuelve esta ambigüedad.',
'S10-seg0010-s00000':'R5: omisión y alcance del sistema educativo y del sufragio en la temprana república; grupos sociales son destinatarios de política estatal, no actores movilizados en este objetivo.',
'S10-seg0014-s00000':'R7: el acontecimiento es la producción y promoción educativa de 1855/1859, no una cita posterior sobre acontecimientos emancipadores.',
'S10-seg0034-s00606':'R7: la gestión de licencias y adopción de libros sucede en 1847 y después; el objetivo no desarrolla consecuencias para el periodo definido.',
'S15-seg0007-s00000':'R5: norma de 1825 y persistencia jurídica, económica y cotidiana de esclavitud forman una cadena causal institucional. Se resuelve la duda de A por este hilo explicativo; R6 se conserva como alternativa por experiencia material.',
'S15-seg0008-s00000':'R6: pugna entre intereses de hacendados y acciones de esclavos, con persistencia del mercado; la agencia e intereses contrapuestos organizan el párrafo.',
'S15-seg0025-s00000':'R7: justificación de métodos estadísticos, sin interpretación histórica de sus resultados.',
'S15-seg0057-s00000':'R6: experiencia laboral y diferenciación por género y especialización de personas esclavizadas en el periodo de los avisos, identificado en contexto.',
'S15-seg0061-s00000':'R5: explicación económica del precio de esclavos después de la independencia y descarte de una causalidad militar directa. Mencionar historiografía no elimina el contenido histórico.',
'S05-visual-p007-01':'R6: el argumento pregunta por la capacidad de las clases populares para generar alternativas; bandolerismo y rebelión sostienen ese foco social.',
'S05-visual-p007-02':'R6: extensión regional y campesina de la rebelión organiza el pasaje; fechas y ejecuciones explican alcance/duración, sin táctica ni campaña específica como eje.',
'S17-visual-p003-03':'R6: capacidad de presión de esclavizados, violencia de amos y voces de protesta. La referencia constitucional del contexto no desplaza la agencia en el objetivo.',
'S01-seg0012-whole':'R4: legitimidad y apoyos/enemigos del proyecto confederal organizan la explicación. La guerra civil presenta el contexto de disputa del régimen.',
'S01-seg0014-whole':'R4: diseño de soberanía y concentración del Protector; el contexto documenta falta de Constitución final, parlamento y revisión del pacto. Se resuelve la duda de A a favor de proyecto aún disputado, reteniendo R5 como alternativa institucional.'}

def main():
    packet=read(OUT/'annotation-input.json'); config=packet['config']; inp={x['segment_id']:x for x in packet['items']}
    passes={p:json.loads((OUT/f'pass-{p.lower()}.json').read_text(encoding='utf-8-sig')) for p in ['A','B']}
    labels=read(ROOT/'artifacts/datasets/gold-v1-source-aware.json')['labels']
    if isinstance(labels,dict):labels=list(labels)
    assert set(REVIEW)==set(inp)
    annotated={};cache_index=[]
    for name,p in passes.items():
        assert len(p['items'])==len(inp) and {r['segment_id'] for r in p['items']}==set(inp)
        annotated[name]={}
        for r in p['items']:
            target=inp[r['segment_id']]
            assert r['label'] in labels and r.get('alternative_label') in labels+[None]
            assert r['family_id']==target['family_id']
            assert r['evidence'] in target['text']
            a=target['text'].index(r['evidence']);b=a+len(r['evidence'])
            assert r.get('evidence_start',a)==a and r.get('evidence_end',b)==b
            payload={'text':target['text'],'context':target['context'],'guide_sha256':config['guide_sha256'],'configuration':{**config,'pass':name}}
            key=sha(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
            record={**r,'text':target['text'],'context':target['context'],'evidence_start':a,'evidence_end':b,'model':config['model'],'prompt_version':config['prompt_version'],'cache_key':key,'pass':name,'annotation_origin':'AI-assisted, not expert gold','config':payload['configuration']}
            cachepath=OUT/'cache'/name/(key+'.json');save(cachepath,record)
            cache_index.append({'pass':name,'segment_id':r['segment_id'],'key':key,'path':cachepath.relative_to(ROOT).as_posix(),'sha256':sha(cachepath.read_bytes())})
            annotated[name][r['segment_id']]=record
    candidates={x['segment_id']:x for x in [json.loads(l) for l in (OUT/'annotation-candidates-final.jsonl').read_text(encoding='utf-8').splitlines()]}
    provenance={x['segment_id']:x for x in read(OUT/'provenance-final-recovered.json')}
    final=[];adjud=[]
    for sid,target in inp.items():
        a=annotated['A'][sid];b=annotated['B'][sid];pending=sid=='S10-seg0005-s00000'
        assert a['label']==b['label'], 'Unexpected label disagreement requires actual review, never automatic acceptance'
        decision={'segment_id':sid,'family_id':target['family_id'],'pass_a':a,'pass_b':b,'final_label':None if pending else a['label'],'provisional_label':a['label'],'alternative_label':a['alternative_label'],'status':'pending_ambiguity' if pending else 'accepted_AI_assisted','rationale':REVIEW[sid],'reviewer':config['model'],'adjudication_prompt_version':'beto-adjudication-v2.0','guide_sha256':config['guide_sha256'],'evidence':a['evidence'],'evidence_start':a['evidence_start'],'evidence_end':a['evidence_end'],'human_expert_review':False,'confidence_used_as_acceptance_criterion':False}
        adjud.append(decision)
        final.append({**candidates[sid],'label':decision['final_label'],'provisional_label':a['label'],'alternative_label':a['alternative_label'],'annotation_status':decision['status'],'annotation_origin':'AI-assisted, not expert gold','split':None,'training_eligible':False,'pages_exact':provenance[sid]['pages_exact'],'pass_a_cache_key':a['cache_key'],'pass_b_cache_key':b['cache_key'],'adjudication_reference':sid})
    agreement=sum(annotated['A'][s]['label']==annotated['B'][s]['label'] for s in inp)
    states=sum(annotated['A'][s]['ambiguity']==annotated['B'][s]['ambiguity'] for s in inp)
    accepted=[x for x in final if x['label'] is not None]
    stats={'n':len(inp),'label_agreement_count':agreement,'label_agreement_rate':agreement/len(inp),'ambiguity_state_agreement_count':states,'ambiguity_state_agreement_rate':states/len(inp),'label_disagreements':[],'ambiguity_state_disagreements':[s for s in inp if annotated['A'][s]['ambiguity']!=annotated['B'][s]['ambiguity']],'reviewed_ambiguous_union':[s for s in inp if annotated['A'][s]['ambiguity']!='clear' or annotated['B'][s]['ambiguity']!='clear'],'accepted_AI_assisted':len(accepted),'pending_ambiguity':len(final)-len(accepted),'provisional_class_distribution':{l:sum(x['provisional_label']==l for x in final) for l in labels},'accepted_class_distribution':{l:sum(x['label']==l for x in final) for l in labels},'by_source':dict(Counter(x['source_id'] for x in final)),'by_format':dict(Counter(x['format'] for x in final)),'model_independence':False,'isolation':'two fresh sessions instructed to read only guide and frozen input; attestations returned; same model, shared filesystem, not OS-level access isolation','limitations':['purposive sample, not random performance estimate','same-model consistency, no expert gold','no transcript labels pending rights and ASR review','no BETO predictions, training or evaluation'],'prior_runtime_failures':'both initial sessions returned usage-limit error without annotations; explicit user continuation followed by successful retries; no paid external service started'}
    save(OUT/'adjudication.json',{'items':adjud});save(OUT/'pilot-annotated.json',{'labels':labels,'annotation_origin':'AI-assisted; no expert gold','items':final});save(ART/'annotation-summary.json',stats);save(OUT/'cache-index.json',cache_index)
    save(OUT/'ambiguity-queue.json',[x for x in adjud if x['status']=='pending_ambiguity'])
    # Final hashes bind source checkpoints, scripts, guide, actual pass bytes and derived artifacts.
    paths=list(OUT.rglob('*'))+list(ART.glob('*'))+[ROOT/'docs/beto-v2/guia-etiquetado-v2.md']+list((ROOT/'scripts').glob('*beto_pilot_v2.py'))+[ROOT/'scripts/recover_beto_ocr_blocks_v2.py']
    save(ART/'delivery-manifest.json',{'created_at':datetime.now(timezone.utc).isoformat(),'outputs_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in paths if p.is_file()},'source_inputs_reference':'processing-manifest.json','checks_reference':'checks-recovered.json','annotation_input_sha256':sha((OUT/'annotation-input.json').read_bytes()),'pass_a_sha256':sha((OUT/'pass-a.json').read_bytes()),'pass_b_sha256':sha((OUT/'pass-b.json').read_bytes()),'guide_sha256':config['guide_sha256'],'complete_pilot_executed':True,'training_executed':False,'production_modified':False})
    print(json.dumps(stats,ensure_ascii=False))
if __name__=='__main__':main()
