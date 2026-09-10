"""Incremental, idempotent accounting and integration of the frozen 444 selection."""
import argparse, hashlib, json, random
from collections import Counter
from acquire_beto_v3_gap_batch import ROOT, DEST, ART, read, save
from integrate_beto_v3_gap_reviews import csvout, exact, sha

RUN=DEST/'selected-444'; META=ART/'selected-444'; GLOBAL=ROOT/'artifacts/beto-v3'
GUIDE=ROOT/'docs/beto-v3/guia-etiquetado-v3.md'
def immutable(p,obj):
    if p.exists():assert read(p)==obj,f'Frozen artifact changed: {p}'
    else:save(p,obj)
def inputs():
    units={u['segment_id']:u for p in (DEST/'next-first-pass').glob('batch-*.json') for u in read(p)['items']}
    assert len(units)==444 and Counter(u['partition'] for u in units.values())=={'T':300,'V':144}
    assert set(units)==set(read(META/'before/next-annotation-selection.json')['selected_ids'])
    originals={u['segment_id']:u for p in DEST.glob('*/annotation/units.json') for u in read(p)['items']}
    receipts={r['source_id']:r for p in DEST.glob('*/receipt.json') for r in [read(p)]}
    for sid,u in units.items():
        assert u==originals[sid] and u['partition']==receipts[u['source_id']]['role']
        assert u['tokens_with_specials']<=384 and not u['would_truncate_tokens'] and not u['training_eligible']
    for p in sorted((RUN/'inputs').glob('batch-*.json')):
        packet=read(p);assert hashlib.sha256(packet['guide'].encode()).hexdigest()==sha(GUIDE)
        for u in packet['items']:
            assert set(u)=={'segment_id','text','input_sha256','guide_sha256'}
            assert all(units[u['segment_id']][k]==v for k,v in u.items())
    return units
def responses(stage,units):
    rows={};paths=[];labels=set(read(GLOBAL/'protocol.json')['labels'])
    packet_dir=RUN/('inputs' if stage=='first-pass' else 'blind-inputs')
    for p in sorted((RUN/stage).glob('batch-*.json')):
        b=read(p);q=read(packet_dir/p.name);assert b['blind_context'] is True
        assert hashlib.sha256(q['guide'].encode()).hexdigest()==sha(GUIDE)
        for u in q['items']:
            assert set(u)=={'segment_id','text','input_sha256','guide_sha256'}
            assert all(units[u['segment_id']][k]==v for k,v in u.items())
        assert len(b['items'])==len(q['items']) and {u['segment_id'] for u in b['items']}=={u['segment_id'] for u in q['items']}
        for r in b['items']:
            sid=r['segment_id'];assert sid not in rows;exact(units[sid],r,sha(GUIDE))
            assert r['proposal'] in labels|{None} and r['alternative'] in labels|{None}
            assert all(isinstance(r[k],bool) for k in ['ambiguous','extraction_defect','boundary_issue','boundary_blocking'])
            if stage=='first-pass':assert r['accepted_label'] is None and not r['training_eligible']
            rows[sid]=r
        paths.append(p)
    return rows,paths
def baseline():
    for x in read(META/'before/manifest.json'):
        assert sha(ROOT/x['snapshot'])==x['sha256']
        if x['path'].endswith(('all-development-units.json','review-integration.json')):assert sha(ROOT/x['path'])==x['sha256']
    prior=read(META/'before/review-integration.json')
    for x in prior['input_manifest']:assert sha(ROOT/x['path'])==x['sha256']
    reserve=read(GLOBAL/'reserved-index.json')
    assert sha(ROOT/reserve['inherited_final']['manifest'])==reserve['v2_reserved_manifest_sha256']
    return read(META/'before/all-development-units.json')['items']
def account(first,second,firstfiles,secondfiles):
    base=read(META/'before/budget-ledger-current.json');ledger=read(GLOBAL/'budget-ledger-current.json')
    new=len({r['input_sha256'] for r in first.values()})
    expected=base['new_unique_annotation_proposals']+new
    assert ledger['new_unique_annotation_proposals']<=expected<=1200
    assert ledger['ASR_gpu_seconds']==base['ASR_gpu_seconds'] and ledger['new_training_trajectories']==0
    assert ledger['services_paid_USD']==0 and not ledger['paid_services_used']
    ledger.update(new_unique_annotation_proposals=expected,annotation_budget_remaining=1200-expected,
        gap_02_unique_annotation_inputs=base['gap_02_unique_annotation_inputs']+new,
        selected444_first_pass_units=len(first),selected444_second_review_units=len(second),
        selected444_first_pass_batches=len(firstfiles),selected444_second_review_batches=len(secondfiles),
        phase_B_second_review_units=base['phase_B_second_review_units']+len(second),
        phase_B_second_review_batches=base['phase_B_second_review_batches']+len(secondfiles))
    sessions=read(META/'review-sessions.json') if (META/'review-sessions.json').exists() else {'first':[],'second':[]}
    ledger['selected444_first_review_sessions']=len(sessions['first'])
    ledger['selected444_second_review_sessions']=len(sessions['second'])
    ledger['phase_B_second_review_calls']=base['phase_B_second_review_calls']+len(sessions['second'])
    ledger['annotation_count_note']='Conservative inherited usage plus distinct frozen phase-B input hashes; identical-input reviews/adjudications add no unique input. All prior spend retained.'
    save(GLOBAL/'budget-ledger-current.json',ledger)
    for p in firstfiles:
        immutable(META/'first-pass-events'/p.name,dict(response_file=str(p.relative_to(ROOT)),sha256=sha(p),units=len(read(p)['items']),new_unique_inputs=len(read(p)['items'])))
    for stage,files in [('first-pass',firstfiles),('second-review',secondfiles)]:
        cache=[]
        for p in files:
            for r in read(p)['items']:
                key=dict(text_sha256=r['input_sha256'],context=None,guide_sha256=r['guide_sha256'],configuration=r['exposed_configuration'],model=r['model'],prompt_version=r['prompt_version'])
                cache.append(dict(segment_id=r['segment_id'],key=key,cache_key_sha256=hashlib.sha256(json.dumps(key,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),response_file=str(p.relative_to(ROOT)),response_file_sha256=sha(p)))
        save(META/(stage+'-cache.json'),dict(items=cache))
    return ledger
def freeze_blind():
    units=inputs();first,files=responses('first-pass',units);assert len(first)==444
    selected=[];selection=[]
    for source in sorted({u['source_id'] for u in units.values()}):
        group=sorted([sid for sid,u in units.items() if u['source_id']==source]);role=units[group[0]]['partition']
        required=[sid for sid in group if role=='V' or any(first[sid][k] for k in ['ambiguous','extraction_defect','boundary_blocking']) or first[sid]['proposal'] is None]
        other=[sid for sid in group if sid not in required]
        sample=random.Random(42).sample(other,(len(other)+4)//5) if role=='T' else []
        chosen=sorted(required+sample);selected+=chosen
        selection.append(dict(source_id=source,partition=role,required=required,random_T_sample=sample,seed=42))
    packet_paths=[]
    for start in range(0,len(selected),15):
        p=RUN/'blind-inputs'/f'batch-{start//15+1:03}.json'
        immutable(p,dict(guide=GUIDE.read_text(encoding='utf-8'),items=[{k:units[sid][k] for k in ['segment_id','text','input_sha256','guide_sha256']} for sid in selected[start:start+15]]))
        packet_paths.append(str(p.relative_to(ROOT)))
    q=dict(units=len(selected),selected_ids=selected,selection=selection,batches=packet_paths,
        first_pass_manifest=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files],S_closed=True)
    immutable(META/'blind-review-queue.json',q)
    print(json.dumps(dict(blind_units=len(selected),batches=len(packet_paths),unsampled_T=444-len(selected))))
def coverage(rows):
    registry=read(GLOBAL/'phase-b-completion-01/source-registry-final.json')
    dur={r.get('video_id',r.get('source_id')):r.get('duration_seconds',0) or 0 for r in registry['existing_sources']}
    dur.update({r['source_id']:r.get('duration_seconds',0) or 0 for r in registry['new_candidates']})
    dur.update({r['source_id']:r['duration_seconds'] for p in DEST.glob('*/receipt.json') for r in [read(p)]})
    gaps=[];labels=read(GLOBAL/'protocol.json')['labels']
    for role,target in [('T',20),('V',25)]:
        for label in labels:
            group=[r for r in rows if r['partition']==role and r.get('accepted_label')==label and dur.get(r['source_id'],0)>=1800]
            works=len({r['family_id'] for r in group})
            gaps.append(dict(partition=role,**{'class':label},accepted_from_30min_works=len(group),target=target,missing_examples=max(0,target-len(group)),accepted_30min_works=works,missing_works=max(0,2-works)))
    workrows=[]
    for sid in sorted({r['source_id'] for r in rows}):
        group=[r for r in rows if r['source_id']==sid];n=sum(bool(r.get('accepted_label')) for r in group)
        workrows.append(dict(work=sid,partition=group[0]['partition'],duration_seconds=dur.get(sid,0),units=len(group),accepted=n,pending=len(group)-n,resolvable_reference_fraction=n/len(group)))
    return gaps,workrows
def build_rows(old,units,first,second,decisions):
    receipts={r['source_id']:r for p in DEST.glob('*/receipt.json') for r in [read(p)]}
    new=[]
    for sid in sorted(first):
        u=units[sid];a=first[sid];d=decisions.get(sid);b=second.get(sid);row=dict(u)
        row.update(first_pass=a,second_review=b,adjudication=d,proposal=a['proposal'],accepted_label=d['accepted_label'] if d else None,
            training_eligible=False,reference_status=('accepted_reference' if d['accepted_label'] else 'pending_resolution') if d else 'pending_review',
            source_admission='pending_final_work_admission',original_family_id=u['family_id'])
        row['family_id']='video-'+receipts[u['source_id']]['video_id'];new.append(row)
    allrows=old+new;families={}
    assert len({r['segment_id'] for r in allrows})==len(allrows)
    for r in allrows:
        assert r['partition']!='S' and not r['training_eligible']
        families.setdefault(r['family_id'],set()).add(r['partition'])
    assert all(len(v)==1 for v in families.values())
    return allrows,new
def publish(old,units,first,second,decisions,ledger,batch=None):
    rows,new=build_rows(old,units,first,second,decisions);gaps,works=coverage(rows)
    accepted=Counter(r['partition'] for r in rows if r.get('accepted_label'))
    gains=Counter(r['partition'] for r in new if r.get('accepted_label'))
    longs={role:sum(r['accepted_from_30min_works'] for r in gaps if r['partition']==role) for role in ['T','V']}
    q=read(META/'blind-review-queue.json') if (META/'blind-review-queue.json').exists() else None
    blockers=[f"{r['partition']}/{r['class']}: missing {r['missing_examples']} references and {r['missing_works']} works from >=30-minute sources" for r in gaps if r['missing_examples'] or r['missing_works']]
    fractions={}
    for role,target in [('T',300),('V',200)]:
        total=sum(r['partition']==role for r in rows);fractions[role]=dict(accepted=accepted[role],units=total,fraction=accepted[role]/total)
        if longs[role]<target:blockers.append(f'{role}: {longs[role]}/{target} accepted long-source references; missing {target-longs[role]}')
        if accepted[role]/total<.9:blockers.append(f'{role}: resolvable reference coverage {accepted[role]}/{total} below 0.90')
    if len(decisions)<444:blockers.append(f'Selected material: {444-len(decisions)} final decisions outstanding')
    blockers+=['Final source independence/reproduction admission and frozen H/T/V/S manifests outstanding',
        'Caption/audio fidelity and missing-cue intervals require final admission review; S remains closed']
    report=dict(version='selected-444-v1',first_pass_units=len(first),second_review_units=len(second),second_review_target=q['units'] if q else None,
        adjudications=len(decisions),selected444_complete=len(decisions)==444,accepted_new_references=sum(gains.values()),accepted_new_by_partition=dict(gains),
        accepted_references=dict(accepted),accepted_30min_references=longs,pending_references=sum(not r.get('accepted_label') for r in rows),
        pending_new_adjudicated=sum(not d['accepted_label'] for d in decisions.values()),coverage=fractions,
        C_ready=False,blockers=blockers,S_content_opened=False,training_runs=0,services_paid_USD=0,
        annotation_unique=ledger['new_unique_annotation_proposals'],annotation_remaining=ledger['annotation_budget_remaining'],
        same_model_family_both_passes=True,model_weights='unknown',reference_note='AI-assisted references, not expert gold or training admission',
        source_admission_pending=True,provisional_acquired_30min_works={'T':13,'V':6},new_registered_S_works=6)
    save(RUN/'all-development-units.json',dict(parent=str((META/'before/all-development-units.json').relative_to(ROOT)),parent_sha256=sha(META/'before/all-development-units.json'),items=rows))
    save(RUN/'new-reviewed-units.json',dict(items=new));save(RUN/'pending-resolution.json',dict(items=[r for r in rows if not r.get('accepted_label')]))
    csvout(META/'exact-gaps-30min-works.csv',gaps);csvout(META/'coverage-by-work.csv',works)
    report['all_development_units_sha256']=sha(RUN/'all-development-units.json')
    parent_overlay=ART/'source-registry-overlay.json'
    overlay=read(parent_overlay)
    overlay.update(parent_overlay=str(parent_overlay.relative_to(ROOT)),parent_overlay_sha256=sha(parent_overlay),S_closed=True,
        integrated_reference_dataset=str((RUN/'all-development-units.json').relative_to(ROOT)),final_source_admission=False)
    for source in overlay['sources']:
        group=[r for r in rows if r['source_id']==source['source_id']]
        source['first_pass_units']=len(group)
        source['accepted_reference_units']=sum(bool(r.get('accepted_label')) for r in group)
        source['pending_reference_units']=sum(not r.get('accepted_label') for r in group)
        source['training_eligible']=False
    save(META/'source-registry-overlay.json',overlay)
    report['source_registry_overlay']=str((META/'source-registry-overlay.json').relative_to(ROOT))
    report['label_agreements']=sum(first[sid]['proposal']==b['proposal'] for sid,b in second.items())
    report['label_disagreements']=len(second)-report['label_agreements']
    report['T_unsampled_parent_checked']=sum(d['review_path']=='T_unsampled_first_pass_with_parent_check' for d in decisions.values())
    if batch:
        checkpoint=META/'checkpoints'/batch
        immutable(checkpoint/'summary.json',report);immutable(checkpoint/'exact-gaps.json',dict(items=gaps))
        immutable(checkpoint/'budget-ledger.json',ledger)
        immutable(checkpoint/'integrated-decisions.json',dict(items=list(decisions.values())))
    save(META/'current.json',report);save(GLOBAL/'phase-B-summary.json',report)
    save(GLOBAL/'annotation-progress.json',dict(unique_new_units_with_proposal=ledger['new_unique_annotation_proposals'],accepted_references=dict(accepted),accepted_for_training=0,
        second_review_units=ledger['phase_B_second_review_units'],same_model_family=True,pending=report['pending_references'],V_references_frozen=False,S_references_frozen=False,
        provider_usage_tokens=None,remaining_annotation_ceiling=ledger['annotation_budget_remaining'],selected444_first_pass=len(first),selected444_second_review=len(second)))
    return report
def main(check_only=False):
    # Later lots own the cumulative ledger; this lot becomes read-only history.
    if not check_only and read(GLOBAL/'budget-ledger-current.json').get('recovery01_unique_annotation_inputs', 0):
        return main(check_only=True)
    old=baseline();units=inputs();first,ff=responses('first-pass',units);second,sf=responses('second-review',units)
    queue=read(META/'blind-review-queue.json') if (META/'blind-review-queue.json').exists() else None
    if queue:
        for x in queue['first_pass_manifest']:assert sha(ROOT/x['path'])==x['sha256']
    decisions={};batches=[];labels=set(read(GLOBAL/'protocol.json')['labels'])
    for p in sorted((RUN/'adjudication').glob('batch-*.json')):
        data=read(p);packet=read(RUN/'inputs'/p.name)
        assert len(data['items'])==len(packet['items']) and {r['segment_id'] for r in data['items']}=={r['segment_id'] for r in packet['items']}
        for d in data['items']:
            sid=d['segment_id'];assert sid not in decisions;exact(units[sid],d,sha(GUIDE))
            assert d['accepted_label'] in labels|{None};assert d['evidence_checked'] and d['boundary_checked']
            if d['accepted_label']:assert not d['boundary_blocking']
            if sid in queue['selected_ids']:assert sid in second and d['review_path']=='blind_second_plus_parent_adjudication'
            else:assert units[sid]['partition']=='T' and d['review_path']=='T_unsampled_first_pass_with_parent_check'
            decisions[sid]=d
        batches.append(p)
    if check_only:
        report=read(META/'current.json');ledger=read(GLOBAL/'budget-ledger-current.json')
        if ledger.get('recovery01_unique_annotation_inputs', 0):
            from beto_v3_recovery_accounting import account
            account(check_only=True)
            ledger=read(GLOBAL/'recovery-01/before/budget-ledger-current.json')
        assert ledger['new_unique_annotation_proposals']==494+len({r['input_sha256'] for r in first.values()})
        assert ledger['annotation_budget_remaining']==1200-ledger['new_unique_annotation_proposals']
        assert ledger['phase_B_second_review_units']==390+len(second)
        rows,new=build_rows(old,units,first,second,decisions)
        assert read(RUN/'all-development-units.json')['items']==rows
        assert sha(RUN/'all-development-units.json')==report['all_development_units_sha256']
        for x in read(META/'input-manifest.json')['items']:assert sha(ROOT/x['path'])==x['sha256']
        assert ledger['services_paid_USD']==0 and not ledger['paid_services_used'] and ledger['new_training_trajectories']==0
        gaps,works=coverage(rows)
        assert report['accepted_30min_references']=={role:sum(r['accepted_from_30min_works'] for r in gaps if r['partition']==role) for role in ['T','V']}
        overlay=read(META/'source-registry-overlay.json')
        assert sha(ROOT/overlay['parent_overlay'])==overlay['parent_overlay_sha256']
        assert overlay['reserved_sources']==read(ART/'source-registry-overlay.json')['reserved_sources'] and overlay['S_closed']
        for p in batches:assert read(META/'checkpoints'/p.stem/'integrated-decisions.json')['items'][-len(read(p)['items']):]==read(p)['items']
        assert report['adjudications']==len(decisions) and report['first_pass_units']==len(first) and report['second_review_units']==len(second)
        print(json.dumps(dict(integrity='passed',first=len(first),second=len(second),adjudications=len(decisions),preserved_parent_units=len(old),S_closed=True)))
        return report
    ledger=account(first,second,ff,sf)
    running={}
    for p in batches:
        running.update({d['segment_id']:d for d in read(p)['items']})
        checkpoint=META/'checkpoints'/p.stem/'summary.json'
        if not checkpoint.exists():publish(old,units,first,second,running,ledger,p.stem)
    report=publish(old,units,first,second,decisions,ledger)
    manifest_paths=sorted((RUN/'inputs').glob('batch-*.json'))+sorted((RUN/'blind-inputs').glob('batch-*.json'))+ff+sf+batches+sorted((META/'parent-signoff').glob('batch-*.json'))
    manifest_paths += [p for p in [META/'parent-overrides.json',META/'blind-review-queue.json',META/'review-sessions.json'] if p.exists()]
    save(META/'input-manifest.json',dict(items=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in manifest_paths]))
    print(json.dumps({k:report[k] for k in ['first_pass_units','second_review_units','adjudications','accepted_new_by_partition','annotation_unique','annotation_remaining','C_ready']}))
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check-only',action='store_true');p.add_argument('--freeze-blind',action='store_true');args=p.parse_args()
    if args.freeze_blind:freeze_blind()
    else:main(args.check_only)
