"""Persist actual per-unit decisions, verify literal evidence, account unique inputs."""
import sys, hashlib
from acquire_beto_v3_gap_batch import ROOT, DEST, ART, read, save
LABELS={'C':'contexto_colonial_antecedentes','I':'crisis_ideas_emancipadoras','M':'campanias_conflictos_militares','L':'liderazgos_diplomacia_proyectos','R':'organizacion_consecuencias_republicanas','P':'participacion_social_regional','N':'no_relevante'}
RULES=dict(zip('CIMLRPN',['R1','R2','R3','R4','R5','R6','R7']))
LABELS['X']=None
RULES['X']='R0 pending_extraction'
def main():
    sid,batch=sys.argv[1:3];dest=DEST/sid/'annotation'
    decisions=read(dest/f'decisions-{batch}.json')['items'];units={r['segment_id']:r for r in read(dest/'units.json')['items']}
    result=[]
    for d in decisions:
        u=units[d['segment_id']];e=d['evidence'];start=u['text'].index(e)
        result.append(dict(segment_id=u['segment_id'],input_sha256=u['input_sha256'],guide_sha256=u['guide_sha256'],proposal=LABELS[d['label']],alternative=LABELS.get(d.get('alternative')),rule='R0; '+RULES[d['label']],evidence=e,evidence_span=[start,start+len(e)],rationale=d['rationale'],ambiguous=d.get('ambiguous',False),extraction_defect=d.get('extraction_defect',False),boundary_issue=d.get('boundary_issue','cue_indices' in u),extraction_note=d.get('extraction_note','Temporal cue anchors require discourse boundary adjudication; unpunctuated automatic captions retained.' if 'cue_indices' in u else 'Authentic ASR text retained; sentence and quality review pending.'),model='GPT-6',model_weights='unknown',exposed_configuration={'temperature':'unknown','seed':'unknown'},prompt_version='gap-first-v3-1',accepted_label=None,training_eligible=False))
    ledger_path=ROOT/'artifacts/beto-v3/budget-ledger-current.json';ledger=read(ledger_path)
    baseline=ART/'budget-before-gap-02.json'
    if not baseline.exists():save(baseline,ledger)
    inherited=read(baseline)
    hashes={r['input_sha256'] for p in DEST.glob('*/annotation/first-pass/batch-*.json') for r in read(p)['items']}
    hashes.update(r['input_sha256'] for r in result)
    assert inherited['new_unique_annotation_proposals']+len(hashes)<=1200
    save(dest/f'first-pass/batch-{batch}.json',{'items':result,'exact_input_file':str((dest/'units.json').relative_to(ROOT)),'reference_status':'proposals_only_pending_blind_review_and_boundaries'})
    ledger['new_unique_annotation_proposals']=max(ledger['new_unique_annotation_proposals'],inherited['new_unique_annotation_proposals']+len(hashes))
    ledger['annotation_count_note']='Conservative inherited 133 inputs + 110 original ASR inputs + distinct phase-b-gap-02 input hashes. Repeated reviews of identical inputs do not consume another unit; changed inputs count separately. Provider tokens unknown.'
    ledger['annotation_budget_remaining']=1200-ledger['new_unique_annotation_proposals']
    ledger['gap_02_unique_annotation_inputs']=len(hashes);save(ledger_path,ledger)
    print(sid,batch,len(result),'cumulative',ledger['new_unique_annotation_proposals'])
if __name__=='__main__':main()
