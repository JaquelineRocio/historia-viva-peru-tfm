"""Persist actual Codex first-pass decisions on the two inherited oral works.

These are assistant-authored decisions, not a simulated API call. No second
model/passage is claimed. Pending boundaries remain ineligible for training.
"""
import hashlib
from collections import Counter
from prepare_beto_v3 import ART, OUT, ROOT, read, sha, write

SOCIAL='participacion_social_regional'
IDEAS='crisis_ideas_emancipadoras'
MILITARY='campanias_conflictos_militares'
NO='no_relevante'
REPUBLIC='organizacion_consecuencias_republicanas'

DECISIONS={
 'HuT0aI_mDqM':[
    (0,13,SOCIAL,REPUBLIC,'R6','aprenden los valores cívicos','La experiencia de guerra forma conciencia y libertades de las personas; no se describen operaciones militares.',False,False),
    (13,14,NO,None,'R7','[Música]','Interludio musical sin desarrollo histórico.',False,False),
    (14,41,SOCIAL,MILITARY,'R0/R6','los peruanos no habrían luchado','Contrasta agencia peruana y fuerzas extranjeras; la dominancia entre participación y explicación historiográfica requiere revisión.',True,False),
    (41,66,IDEAS,NO,'R2','revoluciones liberales','Desarrolla liberalismo y liberación colonial, pero la última oración termina en el cue siguiente; recuperar límite antes de aceptar.',False,True),
    (66,100,IDEAS,SOCIAL,'R0/R2/R6','las Cortes de Cádiz','Combina crisis imperial y conciencia social; los cues inicial/final incluyen palabras de unidades vecinas.',True,True),
    (100,121,NO,None,'R7','los centenarios tienen la función','Reflexión actual sobre conmemoración y responsabilidad académica, sin desarrollar un hecho dentro del alcance.',False,False),
 ],
 'lrV0mu1iZCI':[
    (0,20,NO,None,'R7','problemas iniciales con la conexión','Presentación, comprobación técnica y agradecimientos del congreso.',False,False),
    (20,40,NO,SOCIAL,'R7','recuperación documental','Presenta un debate y trabajo documental; la formulación del argumento histórico queda cortada al final.',False,True),
    (40,51,SOCIAL,REPUBLIC,'R6','indígenas negros esclavos se unifican','Desarrolla la unión de sectores sociales como explicación histórica; la fecha transcrita 1920 es sospechosa y exige cotejo de audio.',False,True),
    (51,74,NO,SOCIAL,'R7','aprovechada por los militares en el 71','El centro es el uso político de una interpretación en 1971; el último cue mezcla la transición hacia otro autor.',False,True),
    (74,104,SOCIAL,MILITARY,'R0/R6','unificación de sectores sociales','Contrasta la débil movilización local y la intervención externa; no adjudicar por nombres de generales.',True,False),
    (104,124,IDEAS,NO,'R0','construyen una propia narrativa','La exposición anuncia narrativas de actores históricos y termina a mitad de frase; información insuficiente para aceptar referencia.',True,True),
 ]}

def main():
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'apps/ml/storage/models/beto-v1-gold-source-aware',local_files_only=True)
    items=[]
    for vid,decisions in DECISIONS.items():
        cue_path=OUT/'acquisition'/vid/'cues.json'
        cues=read(cue_path)
        covered=[]
        for number,(a,z,label,alternative,rule,evidence,reason,ambiguous,defective) in enumerate(decisions,1):
            selected=cues[a:z]
            text=' '.join(c['text'].strip() for c in selected)
            assert evidence in text
            covered.extend(range(a,z))
            input_hash=hashlib.sha256(text.encode()).hexdigest()
            items.append({'segment_id':f'{vid}-disc{number:02}','source_id':vid,'family_id':'video-'+vid,
                'v3_role':'T','source_sha256':sha(cue_path),'cue_span':[a,z],
                'start_sec':min(c['start'] for c in selected),'end_sec':max(c['start']+c['duration'] for c in selected),
                'text_original':text,'text':text,'input_sha256':input_hash,'context':'',
                'tokens_with_specials':len(tok(text,truncation=False)['input_ids']),
                'proposal':label,'alternative':alternative,'rule':rule,'evidence':evidence,
                'evidence_span':[text.index(evidence),text.index(evidence)+len(evidence)],
                'reason':reason,'ambiguous':ambiguous,'extraction_defect':defective,
                'insufficient_information':ambiguous or defective,
                'status':'pending_boundary_or_adjudication' if ambiguous or defective else 'first_pass_only',
                'training_eligible':False,'model':'GPT-6 Codex, current session; backend weights unknown',
                'configuration':{'temperature':'unknown','seed':'unknown'},
                'guide_sha256':sha(ROOT/'docs/beto-v3/guia-etiquetado-v3.md'),
                'pass':1,'second_pass':None,'historical_expert_review':False})
        assert covered==list(range(len(cues)))
    write(OUT/'annotation/pilot-first-pass.json',{'items':items,'origin':'Actual assistant decisions encoded in this script',
        'limitations':['Same conversational model; no independent second pass executed',
            'No accepted evaluation references; neither video is V or S',
            'Defective and ambiguous targets remain ineligible; no forced no_relevante labels']})
    write(ART/'annotation-progress.json',{'unique_new_units_with_proposal':len(items),
        'first_pass_only_resolvable':sum(r['status']=='first_pass_only' for r in items),
        'pending_boundary_or_adjudication':sum(r['status']!='first_pass_only' for r in items),
        'accepted_for_training':0,'V_references_frozen':False,'S_references_frozen':False,
        'second_model_calls':0,'provider_usage_tokens':None,'usage_note':'Not exposed; no invented estimate',
        'remaining_annotation_ceiling':1200-len(items)})
    print(Counter(r['status'] for r in items))

if __name__=='__main__':
    main()
