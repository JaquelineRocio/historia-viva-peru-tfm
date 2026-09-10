"""Publish all requested metrics and cumulative compute from immutable C receipts."""
import csv
import io
import json
from datetime import datetime, timezone
import run_beto_phase_c_v3 as runner

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value,encoding='utf-8')

def main():
    summary=runner.report_results()
    freeze,rows=runner.frozen_inputs()
    prior=runner.read(runner.pinned(freeze['budget_ledger']))
    attempts=[runner.read(p) for p in (runner.OUT/'attempts').glob('*.json')]
    assert all(a['status']=='complete' for a in attempts)
    ledger={**prior,'new_training_trajectories':prior['new_training_trajectories']+4,
            'CD_training_gpu_seconds':prior['CD_training_gpu_seconds']+summary['compute_seconds_all_attempts'],
            'new_training_gpu_seconds':prior['new_training_gpu_seconds']+summary['compute_seconds_all_attempts'],
            'accounting_method':'Pre-C immutable snapshot plus each settled C attempt exactly once; conservative wall time includes loading, evaluation and reload.',
            'prior_ledger':freeze['budget_ledger'], 'attempts':[dict(path=str(p.relative_to(runner.ROOT)),sha256=runner.filehash(p)) for p in (runner.OUT/'attempts').glob('*.json')],
            'S_content_opened':False}
    assert ledger['CD_training_gpu_seconds']<=14400 and ledger['new_training_gpu_seconds']<=28800
    write(runner.ART/'budget-ledger-after-C.json',json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
    labels=runner.LABELS
    lines=['# BETO V3: comparación C, semilla 42','',
           'Se completaron R0–R3 sobre la misma V congelada. S permanece cerrada. Son resultados de desarrollo, no éxito final ni confirmación multisemilla.',
           '', 'La enmienda previa a F1 admite 23 coloniales y 23 republicanas para C–D; ambas quedan por debajo de la meta operativa de 25. Se conservan siete clases, etiquetas, fuentes, presupuestos y criterios finales.',
           '',f"H: {len(rows['H'])}; T300: {len(rows['T300'])} (nombre de fase); V: {len(rows['V'])}. Cobertura resoluble V: 444/489 = 90,80 %. T/V sin truncamientos; H conserva tres truncamientos a 384 tokens.",
           '', '| Receta | F1 macro V | Accuracy | TF-IDF comparable | Época elegida / total | Tiempo real acumulado (s) |',
           '|---|---:|---:|---:|---:|---:|']
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(['model','class','precision','recall','f1','support'])
    for row in summary['results']:
        m=row['metrics'];lines.append(f"| {row['recipe']} | {m['f1_macro']:.6f} | {m['accuracy']:.6f} | {row['tfidf_metrics']['f1_macro']:.6f} | {row['best_epoch']} / {row['epochs']} | {row['cumulative_attempt_wall_seconds']:.2f} |")
    lines+=['',f"Tiempo acumulado de los cuatro ajustes, incluidas cargas y recargas: {summary['compute_seconds_all_attempts']:.2f} s de 14.400 s para C–D. ASR acumulado sin gasto nuevo: {prior['ASR_gpu_seconds']:.2f} s. Anotación: 999/1.200; quedan 201 (1 desarrollo y 200 reservadas para S).",'',
            f"Candidata para D según la regla predefinida: **{summary['candidate']}**. No se ejecutaron las semillas 43/44 ni se abrió S."]
    models=[(r['recipe'],r['metrics']) for r in summary['results']]
    for name in ['H','H-T300']:
        baseline=runner.read(runner.OUT/f'baselines/{name}/baselines.json')
        lines+=['',f"TF-IDF {name}: F1 macro {baseline['tfidf']['f1_macro']:.6f}, accuracy {baseline['tfidf']['accuracy']:.6f}, {baseline['seconds']:.3f} s. Mayoría: F1 macro {baseline['majority']['f1_macro']:.6f}."]
        models.extend([(f'TF-IDF {name}',baseline['tfidf']),(f'Mayoría {name}',baseline['majority'])])
    for name,m in models:
        lines+=['',f'## {name}: métricas por clase','', '| Clase | Precisión | Recall | F1 | Soporte |','|---|---:|---:|---:|---:|']
        for label in labels:
            v=m['per_class'][label]
            lines.append(f"| {label} | {v['precision']:.6f} | {v['recall']:.6f} | {v['f1-score']:.6f} | {int(v['support'])} |")
            writer.writerow([name,label,v['precision'],v['recall'],v['f1-score'],int(v['support'])])
    lines+=['','## Checkpoints y trazabilidad','']
    for row in summary['results']:
        lines.append(f"- {row['recipe']}: `{row['checkpoint']}`. Recarga con predicciones idénticas; hashes en `result.json`. Curvas train/V, pérdida y actualizaciones por época en el mismo resultado.")
    lines+=['','## Límites de admisión','',
            'Once referencias cruzan intervalos internos sin cues >15 s. Cada cruce está registrado en `development-admission-02/audit.json` con la evidencia textual y decisión. Los huecos externos al muestreo no aportan cobertura. No se afirma escucha ni silencio; tampoco fidelidad literal de ASR o video completo. Se conservan defectos no bloqueantes ya adjudicados, incluidos créditos/URL ASR sospechosos. Las referencias son asistidas por IA, no gold experto.',
            '', 'No hubo coincidencias normalizadas de 12 palabras entre H/T/V ni identidades de fuente/obra compartidas; se comprobó la exclusión de identidades S mediante metadatos. Este análisis textual no certifica ausencia de toda reproducción audiovisual.',
            '', 'Los snapshots de admisión anteriores se conservan como historia. Estado vigente: `artifacts/beto-v3/development-current.json`; ledger vigente de entrenamiento: `artifacts/beto-v3/budget-ledger-after-C.json`. El antiguo `budget-ledger-current.json` conserva el cierre de anotación pre-C para verificar sus checkpoints.',
            '',f"Freeze SHA-256: `{summary['freeze_sha256']}`."]
    write(runner.ROOT/'docs/beto-v3/phase-c-results.md','\n'.join(lines)+'\n')
    write(runner.ART/'development-admission-02/metrics-per-class.csv',output.getvalue())
    state=dict(status='C_complete_D_not_executed',updated_utc=datetime.now(timezone.utc).isoformat(),C_ready=True,S_closed=True,
               freeze_sha256=summary['freeze_sha256'],candidate=summary['candidate'],results=str((runner.OUT/'comparison-seed42.json').relative_to(runner.ROOT)),
               budget_ledger='artifacts/beto-v3/budget-ledger-after-C.json',final_success_evaluated=False)
    write(runner.ART/'development-current.json',json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    old=runner.ROOT/'docs/beto-v3/progress.md'
    archive=runner.ROOT/'docs/beto-v3/progress-before-phase-C.md'
    if not archive.exists():archive.write_bytes(old.read_bytes())
    write(old,'# BETO V3: fase C completada; S cerrada\n\n'+
          '[Resultados, métricas por clase, tiempos y checkpoints](phase-c-results.md). '+
          '[Enmienda C–D de 23+23 previa a F1](development-amendment-23-23.md). '+
          '[Progreso anterior e incidentes conservados](progress-before-phase-C.md).\n\n'+
          f"R0–R3 completos, semilla 42; candidata para D: {summary['candidate']}. H 590, T 426 y V 444 congelados. S no se abrió ni evaluó. Presupuestos y criterios de éxito finales originales conservados.\n\n"+
          'Estado vigente: `artifacts/beto-v3/development-current.json`. Ledger acumulado: `artifacts/beto-v3/budget-ledger-after-C.json`. Los cierres anteriores de admisión siguen verificables y no se reescriben.\n')

if __name__=='__main__':main()
