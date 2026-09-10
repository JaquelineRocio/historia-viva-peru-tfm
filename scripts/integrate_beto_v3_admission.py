"""Versioned admission events; never rewrites completed recovery datasets."""
import argparse, hashlib, json, re, os
from collections import Counter
from pathlib import Path
from beto_v3_admission_accounting import ROOT, ART, OUT, read, sha, expected_ledger, record_response_events, verify, immutable
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)

def new_rows(rows, responses, decisions):
    return [{**u,'first_pass':responses['first-pass'].get(u['segment_id']),
             'second_review':responses['second-review'].get(u['segment_id']),
             'adjudication':decisions.get(u['segment_id']),
             'accepted_label':decisions.get(u['segment_id'],{}).get('accepted_label'),
             'training_eligible':False,
             'reference_status':'accepted_reference' if decisions.get(u['segment_id'],{}).get('accepted_label') else 'pending_resolution',
             'source_admission':'public_original_audio_decoded_sampled_ASR; no expert fidelity certification'} for u in rows]

def verify_checkpoint_history(previous, rows, decisions, parent, archive=False):
    for checkpoint in sorted((ART/'checkpoints').glob('*')):
        if not checkpoint.is_dir():continue
        summary=read(checkpoint/'summary.json')
        old_decisions=read(checkpoint/'adjudication-decisions.json') if (checkpoint/'adjudication-decisions.json').exists() else {}
        assert len(old_decisions)==summary['adjudications'], 'Missing frozen historical adjudications'
        assert all(decisions.get(sid)==d for sid,d in old_decisions.items()), 'Previous adjudication removed or changed'
        old_responses={'first-pass':{},'second-review':{}}
        for receipt in read(checkpoint/'response-manifest.json')['response_files']:
            path=ROOT/receipt['path'];assert sha(path)==receipt['sha256'], 'Checkpointed response changed'
            for response in read(path)['items']:
                assert response['segment_id'] not in old_responses[receipt['stage']]
                old_responses[receipt['stage']][response['segment_id']]=response
        dataset={'parent':str(parent.relative_to(ROOT)),'parent_sha256':sha(parent),
                 'items':previous+new_rows(rows,old_responses,old_decisions)}
        serialized=(json.dumps(dataset,ensure_ascii=False,indent=2)+'\n').replace('\n',os.linesep).encode()
        digest=hashlib.sha256(serialized).hexdigest()
        assert digest==read(checkpoint/'dataset-manifest.json')['sha256'], 'Historical dataset cannot be reconstructed exactly'
        if (checkpoint/'dataset.json').exists():assert read(checkpoint/'dataset.json')==dataset
        elif archive:
            # Preserve the exact bytes attested by the old manifest before replacement.
            with (checkpoint/'dataset.json').open('xb') as handle:handle.write(serialized)

def main(check_only=False):
    inventory=OUT/'annotation-inventory.json';rows=read(inventory)['items'];units={r['segment_id']:r for r in rows}
    labels=set(read(ROOT/'artifacts/beto-v3/protocol.json')['labels'])
    pre=read(ART/'prevalidation.json');assert pre['prevalidation_pass'] and 0<len(rows)<=31
    assert len(units)==len(rows) and len({r['input_sha256'] for r in rows})==len(rows)
    assert pre['units']==len(rows) and not pre['missing_windows'] and not pre['temporal_overlap_pairs'] and not pre['text_overlap_findings']
    assert sha(ART/'sampling-plan.json')==pre['plan_sha256']
    for receipt in pre['prior_inputs']:
        assert sha(ROOT/receipt['path'])==receipt['sha256'], 'Prior H/development inputs changed'
    guide=ROOT/'docs/beto-v3/guia-etiquetado-v3.md'
    windows={r['path']:r for r in pre['source_windows']};used={path:[] for path in windows}
    for r in rows:
        assert hashlib.sha256(r['text'].encode()).hexdigest()==r['input_sha256']
        assert r['partition']=='V' and r['tokens_with_specials']<=384
        assert sha(ROOT/r['transcript_path'])==r['transcript_sha256']
        assert r['guide_sha256']==sha(guide) and r['training_eligible'] is False
        window=windows[r['transcript_path']];assert window['sha256']==r['transcript_sha256']
        transcript=read(ROOT/r['transcript_path']);assert transcript['complete']
        assert transcript['source_id']==r['source_id']==window['source_id']
        assert transcript['source_sha256']==r['source_sha256']
        indices=r['cue_indices'];assert indices and indices==list(range(indices[0],indices[-1]+1))
        cues=[transcript['segments'][i] for i in indices]
        assert re.sub(r'\s+',' ',' '.join(c['text'] for c in cues)).strip()==r['text'], 'Text differs from authentic cues'
        assert r['start_sec']==cues[0]['start'] and r['end_sec']==cues[-1]['end']
        used[r['transcript_path']]+=indices
    for path,indices in used.items():
        assert indices==list(range(windows[path]['cue_count'])), 'Cues repeated or omitted'
        assert windows[path]['units']==[r['segment_id'] for r in rows if r['transcript_path']==path]
    packets={}
    packet_ids=[]
    for path in sorted((OUT/'annotation-inputs').glob('batch-*.json')):
        packet=read(path);assert packet['guide']==guide.read_text(encoding='utf-8')
        for r in packet['items']:
            assert set(r)=={'segment_id','text','input_sha256','guide_sha256'}
            assert all(units[r['segment_id']][k]==v for k,v in r.items())
            packet_ids.append(r['segment_id'])
        packets[path.name]=packet
    assert packet_ids==[r['segment_id'] for r in rows]
    frozen_inputs=ART/'frozen-inputs.json'
    input_manifest=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [inventory, ART/'prevalidation.json',*sorted((OUT/'annotation-inputs').glob('batch-*.json'))]]
    if check_only:assert read(frozen_inputs)==input_manifest
    else:immutable(frozen_inputs,input_manifest)
    responses={};files=[]
    for stage in ('first-pass','second-review'):
        responses[stage]={}
        for path in sorted((OUT/stage).glob('batch-*.json')):
            packet=read(path)
            assert path.name in packets and {d['segment_id'] for d in packet['items']}=={d['segment_id'] for d in packets[path.name]['items']}
            assert packet.get('stage',stage)==stage and packet['session']
            for d in packet['items']:
                sid=d['segment_id'];assert sid in units and sid not in responses[stage]
                u=units[sid];assert d['input_sha256']==u['input_sha256']
                assert d['proposal'] in labels|{None} and d.get('alternative') in labels|{None}
                assert d['evidence'] and u['text'][slice(*d['evidence_span'])]==d['evidence']
                assert d['rule'] and d['rationale'] and isinstance(d['flags'],list)
                responses[stage][sid]=d
            files.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'stage':stage,'session':packet['session']})
    assert not {r['session'] for r in files if r['stage']=='first-pass'} & {r['session'] for r in files if r['stage']=='second-review'}, 'Review passes share a declared session'
    account={'baseline_sha256':read(ART/'accounting-contract.json')['admission_baseline']['sha256'],'response_files':files}
    indexed={r['path']:r for r in files}
    for event in (ART/'annotation-events').glob('*.json'):
        prior_event=read(event);assert indexed.get(prior_event['path'])==prior_event, 'Previously counted response changed or removed'
    if check_only:assert read(ART/'annotation-accounting.json')==account
    else:
        save(ART/'annotation-accounting.json',account);record_response_events()
        save(ROOT/'artifacts/beto-v3/budget-ledger-current.json',expected_ledger())
    ledger=verify();parent=ROOT/'outputs/beto-v3/recovery-01/all-development-units.json'
    previous=read(parent)['items'];decisions={}
    adjudication=OUT/'adjudication.json'
    if adjudication.exists():
        for d in read(adjudication)['items']:
            sid=d['segment_id'];assert sid not in decisions, 'Duplicate adjudication ID'
            u=units[sid]
            assert sid in responses['first-pass'] and sid in responses['second-review']
            assert d['input_sha256']==u['input_sha256'] and d['accepted_label'] in labels|{None}
            assert u['text'][slice(*d['evidence_span'])]==d['evidence'] and d['evidence']
            assert d['evidence_checked'] and d['boundary_checked'] and d['rationale']
            assert d['accepted_label'] is None or not d['boundary_blocking']
            for stage in responses:
                assert d[stage+'_sha256']==hashlib.sha256(json.dumps(responses[stage][sid],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            decisions[sid]=d
    verify_checkpoint_history(previous,rows,decisions,parent,archive=not check_only)
    new=new_rows(rows,responses,decisions)
    combined=previous+new
    assert len({r['segment_id'] for r in combined})==len(combined)
    assert not any(r['partition']=='S' or r['training_eligible'] for r in combined)
    roles={}
    for r in combined:roles.setdefault(r['family_id'],set()).add(r['partition'])
    assert all(len(v)==1 for v in roles.values())
    from integrate_beto_v3_selected444 import coverage
    gaps,works=coverage(combined)
    accepted=dict(Counter(r['partition'] for r in combined if r.get('accepted_label')))
    blockers=[f"{r['partition']}/{r['class']}: missing {r['missing_examples']} references and {r['missing_works']} works" for r in gaps if r['missing_examples'] or r['missing_works']]
    blockers+=['Source caption/audio fidelity final admission remains incomplete (G13/G16/G18 QA audio HTTP403); H/T/V and S metadata manifest not frozen']
    if len(decisions)<len(rows):blockers.append(f'{len(rows)-len(decisions)} admission adjudications outstanding')
    summary={'version':'admission-01-v1','parent':str((ROOT/'artifacts/beto-v3/recovery-01/current.json').relative_to(ROOT)),
             'first_pass_units':len(responses['first-pass']),'second_review_units':len(responses['second-review']),'adjudications':len(decisions),
             'new_accepted_references':sum(bool(r['accepted_label']) for r in new),'accepted_references':accepted,
             'accepted_30min_references':{p:sum(r['accepted_from_30min_works'] for r in gaps if r['partition']==p) for p in ('T','V')},
             'coverage':{p:{'accepted':accepted[p],'units':sum(r['partition']==p for r in combined),'fraction':accepted[p]/sum(r['partition']==p for r in combined)} for p in ('T','V')},
             'pending_references':sum(not r.get('accepted_label') for r in combined),'annotation_unique':ledger['new_unique_annotation_proposals'],
             'annotation_remaining':ledger['annotation_budget_remaining'],'development_remaining':ledger['annotation_budget_remaining']-200,
             'ASR_gpu_seconds':ledger['ASR_gpu_seconds'],'training_runs':0,'C_ready':False,'S_evaluated':False,'S_content_opened':False,
             'incidental_reserved_search_snippet_seen':True,'reserved_search_snippet_used':False,'services_paid_USD':0,'blockers':blockers,
             'all_development_units':str((OUT/'all-development-units.json').relative_to(ROOT)),
             'sampling_scope':'3 fixed 375-second windows per newly acquired work; no complete-video coverage claim'}
    dataset={'parent':str(parent.relative_to(ROOT)),'parent_sha256':sha(parent),'items':combined}
    summary['all_development_units_sha256']=hashlib.sha256((json.dumps(dataset,ensure_ascii=False,indent=2)+'\n').replace('\n',os.linesep).encode()).hexdigest()
    checkpoint=ART/'checkpoints'/f"{summary['first_pass_units']:03}-{summary['second_review_units']:03}-{summary['adjudications']:03}"
    checkpoint_objects=[('summary.json',summary),('budget-ledger.json',ledger),('response-manifest.json',account),('dataset-manifest.json',{'path':summary['all_development_units'],'sha256':summary['all_development_units_sha256']})]
    # Reject a same-count reinterpretation BEFORE replacing current datasets/reports.
    for name,value in checkpoint_objects:
        if (checkpoint/name).exists():assert read(checkpoint/name)==value, f'Existing checkpoint differs: {checkpoint/name}'
    objects={OUT/'all-development-units.json':dataset,OUT/'pending-resolution.json':{'items':[r for r in combined if not r.get('accepted_label')]},ART/'exact-gaps.json':{'items':gaps},ART/'coverage-by-work.json':{'items':works}}
    for p,d in objects.items():
        if check_only:assert read(p)==d
        else:save(p,d)
    assert summary['all_development_units_sha256']==sha(OUT/'all-development-units.json')
    for p in (ART/'current.json',ROOT/'artifacts/beto-v3/phase-B-summary.json'):
        if check_only:assert read(p)==summary
        else:save(p,summary)
    annotation_progress={**read(ART/'before/annotation-progress.json'),
                         'unique_new_units_with_proposal':summary['annotation_unique'],
                         'remaining_annotation_ceiling':summary['annotation_remaining'],
                         'accepted_references':accepted,'pending':summary['pending_references'],
                         'second_review_units':ledger['phase_B_second_review_units'],
                         'same_model_family':None,
                         'model_identity_note':'Historical passes GPT-6 family; admission second CLI default model identifier not exposed. No claim of different model independence.',
                         'admission01_first_pass':len(responses['first-pass']),
                         'admission01_second_review':len(responses['second-review']),
                         'admission01_adjudications':len(decisions),
                         'current_state':str((ART/'current.json').relative_to(ROOT))}
    annotation_path=ROOT/'artifacts/beto-v3/annotation-progress.json'
    if check_only:assert read(annotation_path)==annotation_progress
    else:save(annotation_path,annotation_progress)
    for name,value in checkpoint_objects:
        if check_only:assert read(checkpoint/name)==value
        else:immutable(checkpoint/name,value)
    if not check_only:
        immutable(checkpoint/'adjudication-decisions.json',decisions)
        immutable(checkpoint/'dataset.json',dataset)
    print(json.dumps({k:summary[k] for k in ['first_pass_units','second_review_units','adjudications','new_accepted_references','annotation_unique','development_remaining','C_ready']}))
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check-only',action='store_true');main(p.parse_args().check_only)
