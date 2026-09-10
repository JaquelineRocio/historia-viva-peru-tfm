"""Persist the parent's manual review-run-01 decisions; no model or classifier calls."""
from integrate_beto_v3_gap_reviews import ROOT,DEST,ART,RUN,META,read,save
L={'M':'campanias_conflictos_militares','C':'contexto_colonial_antecedentes','I':'crisis_ideas_emancipadoras','L':'liderazgos_diplomacia_proyectos','R':'organizacion_consecuencias_republicanas','P':'participacion_social_regional','N':'no_relevante',None:None}
rules={'M':'R3','C':'R1','I':'R2','L':'R4','R':'R5','P':'R6','N':'R7',None:'R0'}
# Explicit text/guide adjudication after reading full targets for every flagged case.
D={
'G01-u017':(None,'No hay proposición en la repetición aislada; requiere nueva evidencia de extracción.'),
'G01-u023':(None,'Despedida contemporánea y relato del Real Felipe quedan yuxtapuestos e incompletos; no hay dominancia única.'),
'G01-u025':('P','La explicación responde por qué extranjeros se incorporaron a los ejércitos mediante procedencia y exilio familiar; no desarrolla conducción política de Canterac.'),
'G01-u026':('P','La organización del mando sirve para defender la procedencia peruana de los participantes, que es el argumento desarrollado; prima R6 sobre R3.'),
'G01-u038':(None,'La conmemoración de 1974 y el significado de Ayacucho son dos núcleos sin enlace que resuelva dominancia.'),
'G01-u044':(None,'Captura y desmoralización militar, y parentescos entre bandos, ocupan dos núcleos; conservar para revisión de frontera.'),
'G01-u045':(None,'Opciones identitarias de los Castilla y cronología de capitulación se yuxtaponen; nombrar presidentes no resuelve R4.'),
'G01-u058':('N','Solicita bibliografía y formula una pregunta sobre masonería; no desarrolla mecanismos de influencia ideológica.'),
'G01-u066':(None,'Correspondencia y autorización política, ocupación militar y método historiográfico se mezclan; el objetivo no permite prioridad estable.'),
'G02-u019':('N','Predominan anuncios y crítica de una narrativa; la explicación de composición social aún no se desarrolla en este objetivo.'),
'G02-u020':('P','Explica composición peruana e identidad de ambos bandos; la transición al motín no desplaza ese núcleo autónomo.'),
'G02-u023':('M','Recuperación de Lima, entrega de fortaleza y repliegue de Bolívar constituyen el argumento; la crisis de nombramiento queda introducida al cierre.'),
'G02-u035':('R','El objeto es el balance de resultados del orden republicano implantado: marginación y explotación se evalúan como consecuencias frente a sus promesas; mantener R5.'),
'G02-u039':(None,'La hipótesis de pacto, parentescos y exhortación divulgativa quedan sin subordinación clara; acuerdo nominal no elimina ambigüedad.'),
'G02-u054':('M','La división interna se propone explícitamente como causa de derrota en Ayacucho; los saludos no impiden reconocer ese argumento completo.'),
'G02-u064':(None,'Falta el objeto de la sugerencia rechazada por el rey; no importarlo del fragmento vecino.'),
'G02-u079':('M','Explica Ayacucho mediante desgaste acumulado e invasión francesa; la abdicación sólo se inicia, sin desarrollo suficiente de legitimidad para R2.'),
'G02-u081':('C','El pasaje desarrolla condiciones económicas coloniales y presiones fiscales como explicación del descontento; la adhesión es su consecuencia, no un análisis autónomo de agencia.'),
'G02-u082':(None,'Recursos y apoyo militar e ideas ilustradas reciben desarrollo separado; el corte impide resolver qué organiza el argumento.'),
'G02-u089':('N','Educación e Inquisición desde Toledo se discuten sin nexo causal desarrollado con la independencia; no heredar alcance del título de la charla.'),
'G02-u092':('N','La defensa general de la nobleza y jurisdicciones coloniales remite al orden remoto sin relación explicada con el proceso en alcance.'),
'G02-u093':('N','Contrasta orden inca y movilidad virreinal general, sin relacionarlos con independencia; no basta mencionar grupos indígenas.'),
'G02-u094':('N','Matrimonios de conquistadores y violencia colonial general no desarrollan relación con la emancipación; no suplir la periodización defectuosa.'),
'G02-u111':(None,'Cierre del naufragio y nueva pregunta sobre consecuencias sociales forman dos bloques incompletos sin prioridad.'),
'G02-u112':('P','Explica las revoluciones por intereses de élites criollas y actores comerciales; la ausencia de proyecto nacional es conclusión, no un diseño político desarrollado.'),
'G02-u115':('N','La comparación actual sobre conocimiento de masonería y el cierre dominan; atribuir un proyecto masónico sin explicar su diseño no basta para R4.'),
'G02-u121':(None,'Disputa de linaje y atribución de influencias masónicas constituyen dos núcleos; mantener ambigüedad, sin resolverla por la identidad del hablante.'),
'G02-u123':('I','El pasaje sí atribuye financiación y propaganda contra la corona hasta 1821 como mecanismo ideológico; su clasificación no valida la cronología ni las atribuciones del expositor.'),
'G02-u127':('P','La enumeración de comandantes y barcos pretende establecer procedencia inglesa frente a argentina/chilena, no explicar operaciones ni logística; corregir incluso el acuerdo R3.'),
'G02-u128':(None,'Encuentro militar, capitulación y proyecto inconcluso se enumeran sin una explicación dominante; no forzar R3.'),
'G02-u129':(None,'Respuesta personal y acusación histórica con orden sin completar; el contenido faltante impide decidir, no corresponde descarte automático R7.'),
'G03-asr-005':('N','Enumera interpretaciones en conflicto para presentar el libro; no explica sustantivamente juntas ni levantamientos.'),
'G03-asr-023':(None,'El objetivo no ubica temporalmente la implantación de monumentos; no transferir la fecha de otro objetivo invisible al clasificador.')}

def main():
    F={u['segment_id']:u for p in DEST.glob('*/annotation/first-pass/batch-*.json') for u in read(p)['items']}
    F={k:v for k,v in F.items() if k.startswith(('G01-','G02-','G03-'))}
    U={u['segment_id']:u for p in DEST.glob('*/annotation/units.json') for u in read(p)['items']}
    B={u['segment_id']:u for p in sorted((RUN/'second-review').glob('batch-*.json')) for u in read(p)['items']}
    assert len(F)==251 and len(B)==211
    decisions=[];flagged=[];agreements=[];unsampled=[]
    for sid,a in sorted(F.items()):
        b=B.get(sid);u=U[sid];basis=b or a
        special=bool(b and (a['proposal']!=b['proposal'] or a['ambiguous'] or b['ambiguous'] or b.get('boundary_blocking')))
        if special:assert sid in D;flagged.append(sid)
        if sid in D:
            code,reason=D[sid];label=L[code];rule='R0; '+rules[code]
            # Preserve an actual exact evidence chosen by the relevant reviewed rationale.
            if sid in ['G02-u035','G02-u081','G02-u115']:basis=a
        else:
            assert not special
            if b:assert a['proposal']==b['proposal'];agreements.append(sid)
            else:assert not a['ambiguous'] and not a['extraction_defect'];unsampled.append(sid)
            label=basis['proposal'];rule=basis['rule']
            reason=('Comprobadas evidencia y frontera del acuerdo: ' if b else 'Relectura del objetivo T no muestreado: ')+basis['rationale']
        if sid=='G02-u127':
            evidence='argentinos y bien este chilenos los los no'
        else:evidence=basis['evidence']
        start=u['text'].index(evidence)
        decisions.append(dict(segment_id=sid,input_sha256=u['input_sha256'],guide_sha256=a['guide_sha256'],accepted_label=label,
            rule=rule,rationale=reason,evidence=evidence,evidence_span=[start,start+len(evidence)],
            boundary_checked=True,evidence_checked=True,boundary_blocking=label is None,
            boundary_rationale='El objetivo conserva argumento o paratexto autónomo pese a cortes y errores no bloqueantes; no se cambió el texto.' if label else reason,
            extraction_defect=bool(a['extraction_defect'] or (b and b['extraction_defect'])),
            review_path='blind_second_plus_parent_adjudication' if b else 'T_unsampled_first_pass_with_parent_check',
            reviewer='parent-text-guide-adjudication',model='GPT-6',model_weights='unknown',
            factual_verification=False,training_eligible=False))
    save(RUN/'adjudications.json',dict(items=decisions,S_closed=True,method='Manual parent decisions, no BETO predictions; same model family, not expert gold'))
    save(META/'adjudication-signoff.json',dict(all_ids=sorted(F),flagged_full_targets_read=flagged,agreement_evidence_rationale_and_boundaries_checked=agreements,
        agreement_overridden_after_target_read=['G02-u127'],T_unsampled_full_targets_read=unsampled,
        manual_decisions_script='scripts/save_beto_v3_gap_adjudications.py',second_review_sessions=['/root/blind_a','/root/blind_b','/root/blind_c'],fork_turns='none',
        note='Parent reviewed every evidence/rationale and boundary flag, full flagged targets, 23 additional agreement targets, and all 40 unsampled T targets. No audio factual verification claimed. Same-model dependence retained.'))
    print('Saved',len(decisions),'adjudications;',len(flagged),'flagged;',len(unsampled),'unsampled T')
if __name__=='__main__':main()
