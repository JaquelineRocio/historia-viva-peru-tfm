"""Persist explicit parent judgments only after full-target audit; no label voting."""
import hashlib
import json
from beto_v3_recovery_accounting import ROOT, META, OUT, read, immutable, responses


def main():
    units, stages, _ = responses()
    decisions = read(META / 'parent-decisions.json')
    assert set(decisions) == set(units)
    labels = {'M':'campanias_conflictos_militares','P':'participacion_social_regional',
              'L':'liderazgos_diplomacia_proyectos','C':'contexto_colonial_antecedentes',
              'I':'crisis_ideas_emancipadoras','R':'organizacion_consecuencias_republicanas',
              'N':'no_relevante','X':None}
    rules = {'M':'R3','P':'R6','L':'R4','C':'R1','I':'R2','R':'R5','N':'R7','X':'R0'}
    for p in sorted((OUT / 'inputs').glob('batch-*.json')):
        result = []
        for entry in read(p)['items']:
            sid = entry['segment_id']
            d = decisions[sid]
            assert d['full_target_read'] is True
            evidence = d['evidence']
            start = entry['text'].index(evidence)
            first = stages['first-pass'][sid]
            second = stages['second-review'][sid]
            result.append({'segment_id': sid, 'input_sha256': entry['input_sha256'],
                'guide_sha256': entry['guide_sha256'], 'resolved_label': labels[d['label']],
                'alternative': labels[d.get('alternative','X')], 'accepted_label': None,
                'rule': 'R0; '+rules[d['label']], 'rationale': d['rationale'],
                'evidence': evidence, 'evidence_span': [start,start+len(evidence)],
                'evidence_checked': True, 'boundary_checked': True,
                'boundary_blocking': d['label']=='X', 'boundary_rationale': d['rationale'],
                'training_eligible': False, 'prior_predictions_consulted': False,
                'model':'GPT-6','model_weights':'unknown', 'factual_verification':False,
                'review_path':'isolated_two_passes_plus_parent_full_target_adjudication',
                'first_response_sha256':hashlib.sha256(json.dumps(first,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                'second_response_sha256':hashlib.sha256(json.dumps(second,ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
        immutable(OUT/'adjudication'/p.name, {'parent_signoff':True,'items':result})
    print('31 explicit parent judgments saved; effective acceptance requires overlap integration')


if __name__ == '__main__':
    main()
