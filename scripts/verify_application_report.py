"""Verifica la síntesis desde registros guardados; sin entrenar ni abrir V/S."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'docs/aprendizaje/informe-aplicacion-entrenamiento-produccion.md'
OUT = ROOT / 'artifacts/informe-aplicacion/verificacion.json'
inputs = {}
checks = []


def read(relative):
    path = ROOT / relative
    raw = path.read_bytes()
    inputs[relative] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw.decode('utf-8'))


def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)


audit = read('artifacts/experiments/course-u1/beto/dataset-audit.json')
check('Snapshot académico: 596/81/137, total 814',
      audit['split_counts'] == {'train': 596, 'val': 81, 'test': 137})
check('Distribuciones por clase suman los splits registrados', all(
    sum(audit['class_distribution'][s].values()) == n
    for s, n in audit['split_counts'].items()))
check('Auditoría guardada: sin solapamiento de fuente/texto exacto',
      audit['source_overlap'] == audit['exact_text_overlap'] == 0)

for backend, winner, expected in [('beto', 'beto-lr2e5', 0.31066),
                                  ('tfidf', 'tfidf-c4', 0.36300)]:
    selection = read(f'artifacts/experiments/course-u1/{backend}/selection.json')
    report = read(f'artifacts/experiments/course-u1/{backend}/report.json')
    best = max(selection['trials'], key=lambda x: x['validation']['f1_macro'])
    check(f'{backend}: ganador por validación y F1 test coinciden',
          selection['selected'] == best['id'] == report['selected'] == winner
          and math.isclose(report['test']['f1_macro'], expected, abs_tol=1e-8))

d = read('artifacts/beto-v3/phase-d/comparison.json')
r2 = next(r for r in d['results'] if r['recipe'] == 'R2' and r['seed'] == 42)
m = r2['metrics']
cm = m['confusion_matrix']
n = sum(map(sum, cm))
correct = sum(cm[i][i] for i in range(7))
f1 = []
for i, label in enumerate(m['per_class']):
    tp = cm[i][i]
    support = sum(cm[i])
    predicted = sum(row[i] for row in cm)
    precision = tp / predicted if predicted else 0
    recall = tp / support if support else 0
    score = 2 * tp / (support + predicted) if support + predicted else 0
    recorded = m['per_class'][label]
    check(f'R2: precisión/recall/F1/soporte de {label}',
          all(math.isclose(a, b, abs_tol=1e-12) for a, b in [
              (precision, recorded['precision']), (recall, recorded['recall']),
              (score, recorded['f1-score']), (support, recorded['support'])]))
    f1.append(score)
check('R2: 275/444 y macro-F1 reconstruidos desde matriz guardada',
      n == 444 and correct == 275
      and math.isclose(correct / n, m['accuracy'], abs_tol=1e-12)
      and math.isclose(statistics.mean(f1), m['f1_macro'], abs_tol=1e-12))
scores = [r['metrics']['f1_macro'] for r in d['results'] if r['recipe'] == 'R2']
check('R2: media y desviación muestral de tres semillas',
      len(scores) == 3
      and math.isclose(statistics.mean(scores), d['aggregate']['R2']['mean'])
      and math.isclose(statistics.stdev(scores), d['aggregate']['R2']['sample_sd']))
run = read('outputs/beto-v3/phase-c/seed-42/R2/result.json')
best = max(run['history'], key=lambda x: x['f1_macro'])
check('R2: 20 épocas, seleccionada 8, recarga idéntica registrada',
      len(run['history']) == 20 and best['epoch'] == run['best_epoch'] == 8
      and run['reload_predictions_identical'] is True)
check('R2: métricas de la trayectoria coinciden con comparación',
      math.isclose(best['f1_macro'], m['f1_macro'], abs_tol=1e-12))

release = read('configs/production-model.json')
parity = read('outputs/model-releases/beto-iba2_1r6-verification.json')
check('Manifiesto R2 con revisión fijada, siete hashes y contrato del paquete',
      release['revision'] == '31a3887ee6906c6778a4853bc76df7b7e2198282'
      and release['repo_id'] == parity['release']['repo_id']
      and release['max_len'] == 384
      and len(release['files']) == 7
      and release['files'] == parity['release']['files']
      and release['labels'] == parity['release']['labels'])
check('Paridad histórica registrada en cinco entradas sintéticas',
      parity['verification']['passed'] and parity['verification']['texts'] == 5
      and parity['verification']['tokenization_equal'])
functional = read('artifacts/experiments/course-u1/evidence/model-functional.json')
smoke = read('artifacts/experiments/course-u1/evidence/production-smoke-post-push.json')
pdf = read('artifacts/experiments/course-u1/evidence/source-flow-reviewed.json')
check('Tres pruebas históricas ML aprobadas en entorno local',
      functional['passed'] and len(functional['cases']) == 3
      and all(c['passed'] for c in functional['cases'])
      and functional['environment'] == 'local-in-process-fastapi')
check('Seis checks históricos de producción aprobados',
      smoke['passed'] and len(smoke['checks']) == 6
      and all(c['status'] == 'passed' for c in smoke['checks']))
check('PDF conserva fallo inicial y recuperación; no se oculta incidencia',
      pdf['passed'] is False and pdf['verification_passed_after_retry'] is True
      and pdf['review_result']['reviewedLabelKey'] == 'no_relevante')

body = REPORT.read_text(encoding='utf-8')
check('Informe UTF-8 sin carácter de sustitución ni mojibake detectado',
      '\ufffd' not in body and 'Ã' not in body and 'Â' not in body)
links = re.findall(r'\]\(([^)]+)\)', body)
missing = [s for s in links if not s.startswith(('https:', 'http:'))
           and (REPORT.parent / s).resolve() != OUT
           and not (REPORT.parent / s).exists()]
check('Todos los enlaces locales de evidencia existen', not missing)
check('Cinco pruebas funcionales documentadas', all(f'### PF-0{i}.' in body for i in range(1, 6)))
check('Todos los registros leídos conservan sus bytes', all(
    hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in inputs.items()))
OUT.parent.mkdir(parents=True, exist_ok=True)
receipt = {
    'created_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Verificación documental y aritmética; no ejecución de pruebas funcionales nuevas',
    'passed': all(c['passed'] for c in checks),
    'checks': checks,
    'input_sha256': inputs,
    'report_sha256': hashlib.sha256(REPORT.read_bytes()).hexdigest(),
    'report_words': len(body.split()),
    'local_links_checked': len(links),
    'new_training': 0, 'new_inferences': 0, 'new_annotations': 0,
    'remote_checks_executed': False, 'V_dataset_opened': False, 'S_opened': False,
    'budget_ledger_modified': False,
    'notes': ['Las matrices y métricas se leen de resultados guardados.',
              'No se hashean ni abren los archivos de datos V o S.',
              'Los hashes identifican registros leídos, no verifican pesos remotos.'],
}
OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': receipt['passed'], 'checks': len(checks),
                  'words': receipt['report_words'], 'receipt': str(OUT)}, ensure_ascii=False))
