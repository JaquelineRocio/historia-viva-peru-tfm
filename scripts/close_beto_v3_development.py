"""Pre-prediction development admission and immutable freeze; S metadata only."""
import json
import re
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts/beto-v3'
OUT = ROOT / 'outputs/beto-v3'
DEST = ART / 'development-admission-02'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s): return re.sub(r'\s+', ' ', s).strip()
def pin(p): return dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p))
def write(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def audit():
    assert not (ART/'phase-c-freeze.json').exists(), 'Admission already frozen; use runner preflight to verify without rewriting'
    parent = OUT/'admission-01/all-development-units.json'
    allrows = read(parent)['items']
    rows = [dict(r) for r in allrows if r['partition'] in ('T','V') and r.get('accepted_label')]
    registry = read(ART/'phase-b-completion-01/source-registry-final.json')
    metadata = {r.get('source_id',r.get('video_id')):r for r in registry['existing_sources']+registry['new_candidates']}
    for p in (OUT/'phase-b-gap-02').glob('*/receipt.json'):
        r=read(p);metadata[r['source_id']]=r
    sources=[]; problems=[]; gap_hits=[]
    for sid in sorted({r['source_id'] for r in rows}):
        units=[r for r in rows if r['source_id']==sid]
        paths = sorted({ROOT/r['transcript_path'] for r in units if r.get('transcript_path')})
        if not paths:
            choices=[OUT/f'phase-b-gap-02/{sid}/cues.json',OUT/f'phase-b-gap-02/{sid}/asr/cues.json',OUT/f'phase-b-completion-01/new-sources/{sid}/asr/cues.json',OUT/f'acquisition/{sid}/cues.json']
            paths=[next(p for p in choices if p.exists())]
        offset=0
        for p in paths:
            d=read(p);cues=d if isinstance(d,list) else d['segments']
            full=' '.join(c['text'].strip() for c in cues)
            spans=[];pos=0
            for c in cues:
                end=pos+len(c['text'].strip());spans.append((pos,end));pos=end+1
            selected=[r for r in units if not r.get('transcript_path') or ROOT/r['transcript_path']==p]
            duration=metadata.get(sid,{}).get('duration_seconds')
            if sid in ('N01','-Ma1tt97eFg'):
                duration=read(OUT/f'admission-01/{sid}/download.json')['duration_seconds']
            assert duration and duration>0, sid
            ends=[c.get('end',c['start']+c.get('duration',0)) for c in cues]
            gaps=[];covered=cues[0]['start']
            if not isinstance(d,dict) and covered>0:gaps.append(dict(start=0,end=covered,kind='leading'))
            for i,c in enumerate(cues):
                if c['start']-covered>15: gaps.append(dict(start=covered,end=c['start'],kind='internal',before=i-1,after=i))
                covered=max(covered,ends[i])
            if not isinstance(d,dict) and duration>covered:gaps.append(dict(start=covered,end=duration,kind='trailing'))
            for u in selected:
                assert sha(p)==u.get('transcript_sha256',u['source_sha256']),u['segment_id']
                if 'source_char_span' in u:a,z=u['source_char_span']
                else:
                    indices=u['cue_indices'];assert indices==list(range(min(indices),max(indices)+1))
                    a,z=spans[min(indices)][0],spans[max(indices)][1]
                assert norm(full[a:z])==u['text'],u['segment_id']
                u.update(source_char_span=[a+offset,z+offset],duration_seconds=duration,
                         reference_eligible=True,training_eligible=u['partition']=='T',
                         admission_transcript=pin(p))
                for g in gaps:
                    if min(u['end_sec'],g['end'])-max(u['start_sec'],g['start'])>.001:
                        gap_hits.append(dict(segment_id=u['segment_id'],partition=u['partition'],label=u['accepted_label'],gap=g,
                                             before=cues[g['before']]['text'] if 'before' in g else None,
                                             after=cues[g['after']]['text'] if 'after' in g else None))
            sources.append(dict(source_id=sid,transcript=pin(p),duration_seconds=duration,gaps=gaps,
                                accepted=len(selected),audio_listened=False,silence_inferred=False))
            offset+=len(full)+1
    h=read(OUT/'datasets/H-reviewed.json')['items']
    partitions={'H':h,'T':[r for r in rows if r['partition']=='T'],'V':[r for r in rows if r['partition']=='V']}
    for left,right in [('H','T'),('H','V'),('T','V')]:
        for key in ['source_id','family_id','segment_id']:
            overlap={r[key] for r in partitions[left]}&{r[key] for r in partitions[right]}
            if overlap:problems.append(dict(kind=key,left=left,right=right,overlap=sorted(overlap)))
    # Exact normalized 12-word matches identify passages needing a substantive review.
    index=defaultdict(list);matches=defaultdict(set)
    for role,group in partitions.items():
        for u in group:
            words=re.findall(r'\w+',u['text'].lower())
            for gram in set(tuple(words[i:i+12]) for i in range(len(words)-11)):
                for other_role,other_id in index[gram]:
                    if other_role!=role:matches[(other_role,other_id,role,u['segment_id'])].add(' '.join(gram))
                index[gram].append((role,u['segment_id']))
    report=dict(parent=pin(parent),sources=sources,gap_intersections=gap_hits,partition_problems=problems,
                cross_partition_12grams=[dict(pair=list(k),matches=sorted(v)) for k,v in matches.items()],
                counts={k:len(v) for k,v in partitions.items()},S_content_opened=False)
    write(DEST/'audit.json',report)
    write(DEST/'prepared-development.json',{'items':rows})
    print(json.dumps({k:v for k,v in report.items() if k not in ['sources','cross_partition_12grams']},ensure_ascii=False))
    print('12gram pairs',len(matches))
    return report,partitions

def freeze():
    from integrate_beto_v3_admission import main as verify_admission
    verify_admission(check_only=True)
    report, partitions=audit()
    assert not report['partition_problems'] and not report['cross_partition_12grams']
    assert not list((OUT/'phase-c').glob('seed-*/*/result.json'))
    assert not list((OUT/'phase-c').glob('attempts/*.json'))
    reviewed={
        'G01-u003':'Cesión de palabra y bienvenida institucional en ambos extremos.',
        'G01-u016':'Anécdota universitaria y anuncio de video; el hueco no se usa como evidencia histórica.',
        'G02-u001':'Marcador musical y bienvenida al conversatorio de 2024.',
        'G12-u031':'Ceremonia actual de incorporación y entrega de distintivos.',
        'G13-u014':'Dos expresiones de comprobación de pantalla; solo se etiqueta ese texto, no los 39 segundos intermedios.',
        'G13-u054':'Homenaje de otro periodo y felicitación a ponentes; observación historiográfica general.',
        'G14-u051':'Cierre de exposición y apertura de preguntas; sin argumento histórico autónomo.',
        'A01--Ma1tt97eFg-w1-u03':'Contraposición de proyectos y petición de apoyo a Bolívar: evidencia textual de liderazgo conservada. Crédito ASR sospechoso ya marcado en la adjudicación, no utilizado como evidencia.',
        'A01--Ma1tt97eFg-w2-u05':'Programa político atribuido a Sánchez Carrión; evidencia anterior a créditos/URL sospechosos ya marcados, que no determinan la referencia.',
        'A01-N01-w1-u04':'Expulsión de 1767 y secreto de la medida: adjudicación previa por alcance, conservada. No se completa el corte final ni se infiere el contenido del hueco.',
        'A01-N01-w2-u05':'Relación explícita entre reformas borbónicas e independencia; evidencia completa anterior al cierre y crédito ASR sospechoso previamente marcado.'}
    assert {g['segment_id'] for g in report['gap_intersections']}==set(reviewed)
    for g in report['gap_intersections']:
        g.update(decision='retain_existing_text_reference',rationale=reviewed[g['segment_id']],
                 audio_listened=False,missing_speech_inferred=False,
                 scope='Referencia sobre texto de entrada conservado, no etiqueta del audio completo del intervalo. No se certifica fidelidad literal de ASR/subtítulos.')
    report.update(admission_completed=True,decision='Existing text references remain substantively usable; no text/label edits or new annotation inputs.',
                  limitations=['No se escucharon los huecos ni se presume silencio.',
                    'Los huecos externos al muestreo no aportan cobertura; los 11 cruces internos quedan individualizados y revisados sobre el texto disponible.',
                    'Créditos y URL posiblemente espurios del ASR se conservan con las marcas previas; no hay certificación literal de audio ni evaluación de video completo.',
                    'Se hereda la revisión documental de G16/G17 como eventos distintos, ambos T; compartir ponente no acredita independencia de conocimiento histórico.',
                    'No se reanota ni se afirma gold experto. Se mantienen las decisiones de extracción no bloqueante ya adjudicadas.'])
    write(DEST/'audit.json',report)
    original=read(ART/'protocol.json')
    contract=dict(version='development-CD-23-23-v1',authorized_by='User instruction in current session, before observing any V3 F1',
                  recorded_utc=datetime.now(timezone.utc).isoformat(),scope=['C','D'],partition='V',
                  original_operational_goal=25,minimum_overrides={'contexto_colonial_antecedentes':23,'organizacion_consecuencias_republicanas':23},
                  observed_counts={'contexto_colonial_antecedentes':23,'organizacion_consecuencias_republicanas':23},
                  operational_goal_met=False,protocol=pin(ART/'protocol.json'),plan_amendment=pin(ROOT/'docs/beto-v3/development-amendment-23-23.md'),
                  original_budget=original['budget'],original_success=original['evaluation']['targets'],
                  labels=original['labels'],S_closed=True,admission=pin(DEST/'audit.json'),
                  selection='All 426 accepted T and all 444 accepted V, independent of predictions; T300 is the phase name. No balancing or oversampling. 76 pending and 14 auxiliary references excluded.',
                  reference_coverage={'T':426/456,'V':444/489})
    assert contract['reference_coverage']['V']>=original['evaluation']['targets']['resolvable_reference_coverage']
    write(DEST/'development-contract.json',contract)
    legacy=read(ROOT/read(ART/'reserved-index.json')['inherited_final']['manifest'])['sources']
    registry=read(ART/'phase-b-completion-01/source-registry-final.json')
    reserve=legacy+[r for r in registry['existing_sources']+registry['new_candidates'] if r.get('role',r.get('proposed_role'))=='S']+read(ART/'phase-b-gap-02/reserve-metadata.json')['sources']
    ids=set();families=set()
    for r in reserve:
        ids.update(r[k] for k in ['source_id','video_id'] if r.get(k))
        if r.get('family_id'):families.add(r['family_id'])
        if r.get('video_id'):families.add('video-'+r['video_id'])
    for group in partitions.values():
        assert not {r['source_id'] for r in group}&ids
        assert not {r['family_id'] for r in group}&families
    datasets={}
    for name,role in [('H','H'),('T300','T'),('V','V')]:
        p=OUT/f'datasets/{name}.json'
        assert not p.exists(),p
        write(p,dict(frozen=True,partition=role,items=partitions[role],development_contract=pin(DEST/'development-contract.json')))
        datasets[name]=pin(p)
    p=OUT/'datasets/S-manifest.json';assert not p.exists()
    write(p,dict(frozen=True,metadata_only=True,source_ids=sorted(ids),family_ids=sorted(families),S_closed=True))
    datasets['S-manifest']=pin(p)
    write(DEST/'budget-before-C.json',read(ART/'budget-ledger-current.json'))
    result=dict(C_ready=True,blockers=[],admission_completed=True,S_closed=True,
                protocol_sha256=sha(ART/'protocol.json'),representation='normalized_authentic_target_only',
                development_contract=pin(DEST/'development-contract.json'),datasets=datasets,
                admission_evidence=[pin(DEST/'audit.json'),pin(ART/'admission-01/current.json'),pin(ART/'admission-01/source-admission-report.json')],
                budget_ledger=pin(DEST/'budget-before-C.json'))
    write(ART/'phase-c-freeze.json',result)

if __name__=='__main__':
    import sys
    freeze() if '--freeze' in sys.argv else audit()
