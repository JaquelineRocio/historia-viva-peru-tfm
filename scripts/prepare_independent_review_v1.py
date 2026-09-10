"""Freeze an AI-reviewed, unevaluated seven-class pilot; preserve all prior data."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/independent-review-v1'
ART = ROOT / 'artifacts/reviews/independent-review-v1'
DATASET = ROOT / 'artifacts/datasets/evaluation-pilot-v2.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def guard(path):
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=digest(path))


def words(text):
    text = unicodedata.normalize('NFKD', text.casefold()).replace('\u00ad', '')
    return re.findall(r'\w+', ''.join(c for c in text if not unicodedata.combining(c)))


def main():
    assert not DATASET.exists() and not (ART / 'report.json').exists(), 'No overwrite'
    inherited = read(ROOT / 'artifacts/experiments/beto-learning-rate-v1/protocol.json')['input_guards']
    for g in inherited: assert digest(ROOT / g['path']) == g['sha256'], g['path']
    snapshot_path = ROOT / 'outputs/corpus-snapshot-v3/reviewed-export.json'
    snapshot = read(snapshot_path)
    labels = snapshot['labels']
    training = [(i, r) for i, r in enumerate(snapshot['items']) if r['split'] == 'train']
    evaluation_hash = text_hash(json.dumps([r for r in snapshot['items'] if r['split'] != 'train'], sort_keys=True, ensure_ascii=False))
    original = {r['id']: r for r in read(OUT / 'selected-draft.json')['items']}
    corrected = read(OUT / 'corrected-candidates.json')['items']
    blind_key = {r['selection_id']: r for r in read(OUT / 'evaluation-key.json')}
    peer = {r['id']: r for r in read(OUT / 'blind-evaluation-review.json')['items']}
    sources = {r['id']: r for r in read(OUT / 'acquired.json')}
    check = read(OUT / 'blind-correction-check.json')
    # All input versions remain archived; reviewer judgments refer to original texts.
    accepted, quarantined, decisions = [], [], []
    overrides = {
        'E12': ('crisis_ideas_emancipadoras', 'Se acepta la lectura del agente: el argumento evalúa la penetración de principios de soberanía y representación, no una demanda colectiva concreta.'),
        'E19': ('campanias_conflictos_militares', 'Se acepta la lectura militar: base, mando, capitulación y cautiverio. La aparición de Santa Cruz no basta para convertir la unidad en liderazgo político.'),
        'E20': ('campanias_conflictos_militares', 'Se acepta la lectura militar: después de los ascensos predominan preparación de efectivos, movimiento de la División Peruana, toma de provincias y desacato de repliegue.')}
    holds = {
        'E02': 'Párrafo completo pero dicha visita y el alcance temporal necesitan contexto; no se completa con una frase inventada.',
        'E04': 'Párrafo completo pero no identifica la visita ni su tiempo; queda como contexto de fuente, fuera de la puntuación del piloto.',
        'E07': 'Constitución y ciudadanía sin identificación suficiente dentro de la unidad exacta; el cotejo confirma Cádiz, pero esa información no llega al clasificador.',
        'E08': 'Desacuerdo sustantivo ideas/participación: impacto constitucional y agencia indígena tienen peso comparable. No forzar una etiqueta para cumplir cupo.'}
    for r in corrected:
        ident = r['id']; key = blind_key[ident]; second = peer[key['blind_id']]
        assert key['text_sha256'] == text_hash(original[ident]['text']) == r['reviewed_original_sha256']
        assert r['text_sha256'] == text_hash(r['text']) and 120 <= len(r['text'].split()) <= 250
        s = sources[r['source']]
        chosen = overrides.get(ident, (r['proposed_label'], 'Coinciden la propuesta inicial y la revisión ciega; se conserva el tema dominante indicado por el agente.'))
        state = 'quarantine' if ident in holds else 'accepted_ai_adjudicated'
        if state != 'quarantine': assert second['usability'] == 'usable' and chosen[0] == second['label']
        item = dict(id=ident, text=r['text'], label=None if ident in holds else chosen[0],
            source_id=r['source'], resourceId=str(uuid.uuid5(uuid.NAMESPACE_URL, s['landing_url'])),
            sourceType='pdf', role='additional_evaluation_pilot_never_train', source_url=s['landing_url'],
            source_author=s['author'], source_title=s['title'], pdf_pages=r['pdf_pages'],
            printed_pages=[s['first_page']+n-1 for n in r['pdf_pages']],
            document_group=s['group'], text_sha256=r['text_sha256'], words=len(r['text'].split()),
            review_status=state, license='CC BY 4.0; publisher declaration; attribution retained',
            extraction_changes='Whitespace and line-break normalization; see archived extraction-corrections.json for the seven corrected texts.')
        (quarantined if ident in holds else accepted).append(item)
        decisions.append(dict(id=ident, blind_id=key['blind_id'], first_label=r['proposed_label'],
            peer_label=second['label'], peer_usability=second['usability'], final_label=item['label'],
            status=state, rationale=holds.get(ident, chosen[1]), peer_rationale=second['reason']))
    assert len(accepted) == 22 and len(quarantined) == 4 and set(x['label'] for x in accepted) == set(labels)
    assert len({x['text_sha256'] for x in accepted+quarantined}) == 26
    assert not {x['resourceId'] for x in accepted} & {r['resourceId'] for _, r in training}
    # Compare only TRAIN; old validation/test texts are never used to select examples.
    lookup = {8: set(), 20: set()}
    for _, r in training:
        w = words(r['text'])
        for n in lookup: lookup[n].update(tuple(w[j:j+n]) for j in range(len(w)-n+1))
    overlap = []
    for r in accepted+quarantined:
        w = words(r['text'])
        matches = {str(n): sorted(' '.join(w[j:j+n]) for j in range(len(w)-n+1) if tuple(w[j:j+n]) in lookup[n]) for n in lookup}
        assert not any(matches.values()), r['id']
        overlap.append(dict(id=r['id'], shared_spans_with_train=matches))
    # Counter prevents concatenated numeric-range regression in the delivered text.
    for r in accepted+quarantined:
        assert not any(s in r['text'] for s in ('pp. 6667', 'pp. 2627', '(18171822)'))
    training_key = {r['id']: r for r in read(OUT / 'training-key.json')}
    train_peer = read(OUT / 'blind-training-review.json')['items']
    train_decisions = []
    for r in train_peer:
        key = training_key[r['id']]; row = snapshot['items'][key['snapshot_index']]
        assert row['split'] == 'train' and text_hash(row['text']) == key['text_sha256']
        train_decisions.append(dict(**key, reviewer_label=r['label'], reviewer_usability=r['usability'],
            action='proposal_only_no_dataset_change', reason=r['reason'], completeness_issues=r['completeness_issues']))
    policy = dict(status='frozen_ai_adjudicated_additional_pilot_not_final_independent_test',
        model_predictions_performed=False, human_review=False,
        purpose='Seven-class pilot of new complete units; reference labels from first AI proposal, blind AI agent review and explicit adjudication.',
        independence='New selected texts and works not present in current TRAIN; no 8/20-word overlaps detected. Full documentary independence is not certified. Escanilla cites previously reused Sala2011; the three RIRA2023 articles share a dossier and Escanilla cites Guarisco2011.',
        use='Never train on these sources or their reproduced documents. If scored later, report as additional development, not an untouched final test. Any further selection based on these scores makes reuse explicit.',
        metrics='Report all seven classes, per-class support/precision/recall/F1, confusion matrix and per-source results. Corpus is purposive and small; no population accuracy or automatic-use readiness claim.',
        stop='No model training or prediction in this block. Four quarantined texts must not enter scored metrics.',
        coverage_limits='Only PDF academic prose; two collection groups, four works; three negatives are bibliography, one predominantly twentieth/twenty-first century. No broad representativeness; missing variety and sparse 1830-1842 coverage.')
    write(DATASET, dict(schema_version=1, dataset='evaluation-pilot-v2', labels=labels, policy=policy, items=accepted))
    write(ART / 'quarantine.json', dict(status='not_for_training_or_scoring', items=quarantined))
    write(ART / 'adjudication.json', dict(review_method='AI_first_proposal_blind_agent_then_adjudication_not_human_gold', items=decisions))
    write(ART / 'training-review.json', dict(status='proposals_only_current619_unchanged', items=train_decisions))
    for name in ('blind-training-review.json','blind-evaluation-review.json','blind-correction-check.json','extraction-corrections.json'):
        shutil.copyfile(OUT / name, ART / name)
    write(ART / 'dependency-review.json', dict(method='Read selected excerpts and source citations; normalized TRAIN-only lexical screen.',
        compared_train_rows=619, exact_source_ids_disjoint=True, full_source_independence=False,
        group_decisions=[
            'Choque2024: Arica visit1793-1796; O’Phelan2012 is not TRAIN O’Phelan1985; Hugo Contreras is not Carlos Contreras. Shared surname is not identical work.',
            'Escanilla2023: bibliography p125 explicitly cites Sala2011 El Trienio Liberal, already used in external development. Keep all new units out of train and do not claim final-test independence.',
            'Escanilla2023 cites Guarisco2011 and both authors reuse their lines of inquiry. Guarisco2023 and Alvarado2023 are in the same dossier; conservatively one collection group.',
            'Escanilla Huerta is not María Claudia Huerta Vera, author of TRAIN Huerta2020. Guarisco huertas and Alvarado salada/Salazar are lexical false positives for author queries.',
            'Alvarado2023 uses Miller2009 elsewhere, a primary-work family present in TRAIN Fonseca/Hünefeldt. The selected body excerpts do not quote Miller. This does not certify absence of paraphrases or every shared primary document.',
            'Common constitutions, institutions and secondary citations are not automatically duplicated passages; no8/20wordmatches found in any of26selected texts. This lexical check is not proof of semantic independence.'],
        overlaps=overlap, original_test_used_for_selection=False, external_texts_used_for_selection=False))
    guards = {g['path']: g for g in inherited}
    for path in [Path(__file__),snapshot_path,ART/'source-reservation.json']+[OUT/name for name in ('selected-draft.json','corrected-candidates.json','blind-training.json','blind-evaluation.json','blind-evaluation-corrected.json','blind-training-review.json','blind-evaluation-review.json','blind-correction-check.json','extraction-corrections.json','training-key.json','evaluation-key.json','acquired.json','inventory.json','select.py','inventory.py','acquire.py','correct_extraction.py','overlap.json')]:
        guards[path.relative_to(ROOT).as_posix()] = guard(path)
    for s in sources:
        for name in ('article.pdf','landing.html','pages.json'): guards[(OUT/s/name).relative_to(ROOT).as_posix()] = guard(OUT/s/name)
    from sklearn.metrics import cohen_kappa_score, confusion_matrix
    initial = [d['first_label'] for d in decisions]; other = [d['peer_label'] for d in decisions]
    report = dict(status=policy['status'], created_at_utc=datetime.now(timezone.utc).isoformat(),
        dataset=guard(DATASET), evaluation_candidates=26, accepted=22, quarantined=4,
        class_counts=dict(Counter(x['label'] for x in accepted)), sources=len(sources), collection_groups=2,
        blind_review_coverage='100% of26newcandidates and12selectedTRAINpassages, not 100% ofTRAIN',
        pre_adjudication_agreement=dict(agree=sum(a==b for a,b in zip(initial,other)), total=26,
            cohen_kappa=cohen_kappa_score(initial,other,labels=labels), labels=labels,
            confusion_matrix=confusion_matrix(initial,other,labels=labels).tolist(),
            interpretation='Descriptive AI-to-AI agreement; small purposive sample, not human reliability, no per-class reliability claim.'),
        training_review=dict(rows=12, label_agreement_with_existing=sum(x['old_label']==x['reviewer_label'] for x in train_decisions),
            usable=sum(x['reviewer_usability']=='usable' for x in train_decisions), requires_context=sum(x['reviewer_usability']=='requires_context' for x in train_decisions), changes_applied=0),
        reviewer_exposure='Agent did not read first labels, keys or predictions. Agent disclosed accidental first-page/title/abstract exposure in two new sources while inspecting page JSON; full source-metadata blindness is not claimed.',
        source_pages_visually_checked=27, visual_renderer='PDFium/pypdfium2 5.13.0 installed only in local outputs vendor directory',
        extraction_corrections=dict(texts=7, replacement_rules=11, original_versions_retained=True),
        no_model_inference=True, no_training=True, old_corpus_unchanged=True, human_review=False,
        full_documentary_independence=False, policy=policy, input_guards=list(guards.values()))
    write(ART / 'report.json', report)
    # Human-readable packet: text and attribution first, IA judgments explicitly marked.
    lines=['# Piloto adicional de evaluación — revisión asistida por IA', '',
        '22 unidades aceptadas; siete clases. No es prueba final plenamente independiente ni gold humano. No se ejecutaron modelos.', '',
        'Las cuatro unidades en cuarentena están archivadas fuera del conjunto puntuable. Las fuentes se reservan completas fuera de entrenamiento.', '']
    for r in accepted:
        d=next(d for d in decisions if d['id']==r['id'])
        lines += [f"## {r['id']} — {r['label']}", '', r['text'], '',
            f"Fuente: {r['source_author']}. [{r['source_title']}]({r['source_url']}). Páginas impresas {', '.join(map(str,r['printed_pages']))}; PDF {', '.join(map(str,r['pdf_pages']))}. CC BY 4.0; normalización de extracción documentada.", '',
            '**Dictamen IA:** '+d['peer_rationale'], '']
    (OUT / 'revision-piloto.md').write_text('\n'.join(lines),encoding='utf-8')
    for g in guards.values(): assert digest(ROOT / g['path']) == g['sha256'], g['path']
    now_snapshot = read(snapshot_path)
    assert evaluation_hash == text_hash(json.dumps([r for r in now_snapshot['items'] if r['split'] != 'train'],sort_keys=True,ensure_ascii=False))
    assert len([r for r in now_snapshot['items'] if r['split']=='train']) == 619
    assert read(DATASET)['items'] == accepted
    assert sum(report['class_counts'].values()) == 22
    write(ART / 'verification.json', dict(status='passed', guarded_inputs=len(guards),
        accepted_rows_checked=22, quarantined_rows_checked=4, original_review_identities_checked=38,
        seven_labels_supported=True, selected_texts_unique=True, accepted_length_range=[min(r['words'] for r in accepted),max(r['words'] for r in accepted)],
        train619_and_evaluation218_unchanged=True, no_8_or_20_word_overlap_with_train=True,
        agreement_recomputed_with_sklearn=True, report_sha256=digest(ART/'report.json'), dataset_sha256=digest(DATASET)))
    print(json.dumps({k:report[k] for k in ('accepted','quarantined','class_counts','pre_adjudication_agreement','training_review')},ensure_ascii=False))


if __name__ == '__main__': main()
