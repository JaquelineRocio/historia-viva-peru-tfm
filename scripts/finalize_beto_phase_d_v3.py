"""Close D after its comparison and bounded qualitative report exist."""
from datetime import datetime, timezone
import shutil
import run_beto_phase_c_v3 as r
from report_beto_phase_d_v3 import A, dump, write


def main():
    summary = r.read(A/'comparison.json')
    ledger = r.read(r.ART/'budget-ledger-after-D.json')
    sample = r.read(A/'error-sample.json')
    assert len(summary['results'])==6 and len(sample['sample'])<=12
    assert ledger['new_training_trajectories']==8 and ledger['CD_training_gpu_seconds']<=14400
    assert ledger['new_training_gpu_seconds']<=28800 and ledger['new_unique_annotation_proposals']==999
    assert len(list(r.OUT.glob('seed-*/*/attempt-started.json')))==8
    assert not (r.OUT/'run.lock').exists()
    assert summary['freeze_sha256']==r.filehash(r.FREEZE)
    for entry in ledger['attempts']:
        attempt = r.read(r.pinned(entry))
        assert attempt['status']=='complete' and 'wall_seconds' in attempt
    for row in summary['results']:
        assert r.filehash(r.ROOT/row['result_path'])==row['result_sha256']
    assert (r.ROOT/'docs/beto-v3/phase-d-analysis.md').exists()
    assert (A/'curves-D.png').exists() and (A/'curves-D.pdf').exists()
    frozen, _ = r.frozen_inputs()
    assert frozen['S_closed'] and not summary['S_opened']
    verification = dict(status='passed',checked_utc=datetime.now(timezone.utc).isoformat(),
        six_comparable_runs=True,four_new_trajectories=True,C_results_unchanged=True,
        freeze_sha256=r.filehash(r.FREEZE), S_content_opened=False,
        new_resume_states='All four loaded in CPU by report: epoch, protocol, history, best predictions, optimizer, scheduler, scaler and RNG checked',
        reload_verification='Seed 42 reuses C identical-reload receipts with current checkpoint hash verification; 43/44 freshly reloaded within each run',
        resume_training_or_power_failure_test_executed=False,
        diagnostic_texts_inspected=len(sample['sample']),references_changed=False,
        free_bytes=shutil.disk_usage(r.ROOT).free,
        annotation_units_remaining_development=1,annotation_units_reserved_S=200,
        external_backup_verified=False)
    dump(A/'verification.json', verification)
    state = r.read(r.ART/'development-current.json')
    state.update(status='D_complete_F_recommended_not_executed',updated_utc=datetime.now(timezone.utc).isoformat(),
        C_results='outputs/beto-v3/phase-c/comparison-seed42.json', results='artifacts/beto-v3/phase-d/comparison.json',
        budget_ledger='artifacts/beto-v3/budget-ledger-after-D.json', S_closed=True, final_success_evaluated=False,
        next_intervention=dict(phase='F',option='transcript_only_vs_H_plus_T',executed=False,
                              prospective_V_exception_scope_required=True),
        development_annotation_remaining=1,reserved_S_annotations=200)
    dump(r.ART/'development-current.json',state)
    agg=summary['aggregate']
    lines = ['# BETO V3: fase D completada; S cerrada','',
        '[Seis ejecuciones y métricas por clase/obra](phase-d-results.md) · [Curvas, 12 errores y recomendación](phase-d-analysis.md) · [Runner y comandos](runner-phase-c.md).','',
        'Se reutilizaron R0/R2 de 42 y se completaron sólo R0/R2 × 43/44. R2 mantuvo 20 épocas y scheduler completo; mejores épocas 8/14/9. R0: 4/4/4. H 590, T 426, V 444, etiquetas y representación congeladas; R1/R3 intactas.','',
        '| Magnitud | Media ± DE muestral (3 semillas) |','|---|---:|',
        f"| R0 F1 macro V | {agg['R0']['mean']:.6f} ± {agg['R0']['sample_sd']:.6f} |",
        f"| R2 F1 macro V | {agg['R2']['mean']:.6f} ± {agg['R2']['sample_sd']:.6f} |",
        f"| Diferencia emparejada R2−R0 | {agg['R2_minus_R0']['mean']:+.6f} ± {agg['R2_minus_R0']['sample_sd']:.6f} |", '',
        'Diferencias 42/43/44: +0,156277 / +0,081374 / +0,072132. Mejora en tres semillas y cinco de ocho obras; no uniforme. Cuatro clases R2 quedan bajo 0,50 en media. Train R2 llega a 1,0, con V limitada; se conserva R2 como control de desarrollo, sin afirmar éxito final.','',
        f"Presupuesto: D {ledger['phase_D_wall_seconds']:.2f} s; C–D {ledger['CD_training_gpu_seconds']:.2f}/14.400 s. V3 {ledger['new_training_gpu_seconds']:.2f}/28.800 s; 8/18 trayectorias. ASR 933,00 s sin gasto nuevo; US$0. Anotación 999/1.200: una entrada de desarrollo y 200 reservadas para S.", '',
        'Siguiente intervención recomendada: opción F, sólo T frente a H+T con R2 y tres semillas, sin nuevas anotaciones. No ejecutada. La enmienda 23+23 sólo cubre C–D: documentar su alcance prospectivo para F antes de ajustar. No ampliar automáticamente a T600 ni abrir S.', '',
        'Recargas idénticas verificadas; métricas por época, mejor checkpoint y último estado completo conservados. Espacio: 14,10 GiB antes, 7,55 GiB después. Snapshots locales en `artifacts/beto-v3/phase-d/before/`; pesos en `outputs/beto-v3/phase-c/`. Respaldo externo no verificado.', '',
        'Estado: `artifacts/beto-v3/development-current.json`. Ledger vigente: `artifacts/beto-v3/budget-ledger-after-D.json`, snapshot tras C más recibos D sin duplicación. [Verificación](../../artifacts/beto-v3/phase-d/verification.json). [Incidentes](../../artifacts/beto-v3/phase-d/incidents.md). Cierre: `outputs/venv-ml/Scripts/python.exe -X utf8 scripts/finalize_beto_phase_d_v3.py`.']
    write(r.ROOT/'docs/beto-v3/progress.md','\n'.join(lines)+'\n')
    print('D closed: six results verified, four new fits, S closed, F recommendation only.')


if __name__ == '__main__':
    main()
