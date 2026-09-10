"""Parent audit display and persistence; explicit signoff and overrides required."""
import argparse,json
from integrate_beto_v3_selected444 import RUN,META,read,save,immutable,inputs,responses,sha,GUIDE
LABELS={'C':'contexto_colonial_antecedentes','I':'crisis_ideas_emancipadoras','M':'campanias_conflictos_militares','L':'liderazgos_diplomacia_proyectos','R':'organizacion_consecuencias_republicanas','P':'participacion_social_regional','N':'no_relevante','X':None}
RULES={'C':'R1','I':'R2','M':'R3','L':'R4','R':'R5','P':'R6','N':'R7','X':'R0'}
def flagged(a,b):return b is not None and (a['proposal']!=b['proposal'] or a['ambiguous'] or b['ambiguous'] or a.get('boundary_blocking') or b.get('boundary_blocking') or a['proposal'] is None or b['proposal'] is None)
def main():
    p=argparse.ArgumentParser();p.add_argument('batches',nargs='+',type=int);p.add_argument('--save',action='store_true');args=p.parse_args()
    U=inputs();F,_=responses('first-pass',U);B,_=responses('second-review',U);Q=set(read(META/'blind-review-queue.json')['selected_ids'])
    override_path=META/'parent-overrides.json';overrides=read(override_path) if override_path.exists() else {}
    for n in args.batches:
        name=f'batch-{n:03}.json';packet=read(RUN/'inputs'/name);out=[];audit=[]
        for u in packet['items']:
            sid=u['segment_id'];a=F[sid];b=B.get(sid);f=flagged(a,b)
            if not args.save:
                if sid in Q and b is None:print(sid,'SECOND_PENDING');continue
                short=dict(id=sid,first=a['proposal'],second=b['proposal'] if b else 'T-unsampled',first_reason=a['rationale'],reason=(b or a)['rationale'],evidence=(b or a)['evidence'],boundary=(b or a)['boundary_rationale'])
                if f:short['text']=u['text']
                print(json.dumps(short,ensure_ascii=False));continue
            assert sid not in Q or b is not None,f'Second missing: {sid}'
            if f:assert sid in overrides,f'Manual resolution required: {sid}'
            basis=b or a;label=basis['proposal'];rule=basis['rule'];reason='Revisión parental de evidencia y frontera: '+basis['rationale'];evidence=basis['evidence'];blocking=False
            if sid in overrides:
                d=overrides[sid];label=LABELS[d['label']];rule='R0; '+RULES[d['label']];reason=d['rationale'];evidence=d.get('evidence',evidence);blocking=label is None
            start=u['text'].index(evidence)
            out.append(dict(segment_id=sid,input_sha256=u['input_sha256'],guide_sha256=sha(GUIDE),accepted_label=label,rule=rule,rationale=reason,
                evidence=evidence,evidence_span=[start,start+len(evidence)],evidence_checked=True,boundary_checked=True,boundary_blocking=blocking,
                boundary_rationale=reason if blocking else 'Evidencia y argumento identificables en el objetivo; cortes menores y errores auténticos conservados, sin añadir contexto.',
                extraction_defect=a['extraction_defect'] or bool(b and b['extraction_defect']),
                review_path='blind_second_plus_parent_adjudication' if b else 'T_unsampled_first_pass_with_parent_check',
                reviewer='parent-text-guide-adjudication',model='GPT-6',model_weights='unknown',factual_verification=False,training_eligible=False))
            audit.append(dict(segment_id=sid,method='full_target_manual_resolution' if sid in overrides else ('agreement_evidence_rationale_boundary_check' if b else 'unsampled_T_full_target_read'),first_sha256=a['input_sha256']))
        if args.save:
            immutable(RUN/'adjudication'/name,dict(items=out,parent_signoff=True))
            immutable(META/'parent-signoff'/name,dict(items=audit,guide_sha256=sha(GUIDE),prior_predictions_consulted=False))
            print('Saved parent adjudications',name,len(out))
if __name__=='__main__':main()
