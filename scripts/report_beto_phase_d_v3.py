"""Read-only validation of six runs; derived D reports and cumulative ledger."""
import csv
import io
import json
import statistics as stats
from collections import Counter
from datetime import datetime, timezone
import shutil
import run_beto_phase_c_v3 as r

A = r.ART/'phase-d'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(value, encoding='utf-8')
    tmp.replace(path)


def dump(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def csvfile(name, header, rows):
    buf = io.StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    write(A/name, buf.getvalue())


def describe(values):
    return dict(mean=stats.mean(values), sample_sd=stats.stdev(values), n=len(values))


def main():
    freeze, datasets = r.frozen_inputs()
    val = datasets['V']
    prior = r.read(A/'before/budget-ledger-after-C.json')
    assert r.filehash(A/'before/budget-ledger-after-C.json') == r.filehash(r.ART/'budget-ledger-after-C.json')
    old_paths = {str((r.ROOT/e['path']).resolve()) for e in prior['attempts']}
    for entry in prior['attempts']:
        r.pinned(entry)
    for original in r.read(r.OUT/'comparison-seed42.json')['results']:
        assert r.filehash(r.OUT/'seed-42'/original['recipe']/'result.json') == original['result_sha256'], 'C result changed'
    attempts = [(p, r.read(p)) for p in sorted((r.OUT/'attempts').glob('*.json'))]
    new = [(p,a) for p,a in attempts if str(p.resolve()) not in old_paths]
    assert all('wall_seconds' in a for _,a in attempts), 'Unsettled attempt'
    assert {(a['recipe'],a['seed']) for _,a in new} == {(x,s) for x in ('R0','R2') for s in (43,44)}
    results = []
    class_rows, work_rows, epoch_rows = [], [], []
    for seed in (42,43,44):
        for recipe in ('R0','R2'):
            dest = r.OUT/f'seed-{seed}'/recipe
            config = r.read(dest/'config.json')
            execution = config['execution']
            data, lr, epochs = r.EXPECTED[recipe]
            train = [row for group in data for row in datasets[group]]
            assert execution['seed'] == seed and execution['recipe'] == recipe
            assert execution['lr'] == lr and execution['epochs'] == epochs
            assert execution['train_rows_hash'] == r.fingerprint(train)
            assert execution['validation_rows_hash'] == r.fingerprint(val)
            assert execution['freeze_sha256'] == r.filehash(r.FREEZE)
            assert {k:v for k,v in config.items() if k != 'execution'} == r.read(r.ART/'protocol.json')
            result = r.verify_result(dest, config, val)
            assert result['reload_predictions_identical'] and len(result['history']) == epochs
            assert result['best_epoch'] == max(result['history'], key=lambda h:h['f1_macro'])['epoch']
            assert result['steps_per_epoch'] == r.math.ceil(len(train)/16)
            assert result['warmup_steps'] == max(1,int(result['steps_per_epoch']*epochs*.1))
            work = r.by_work(val, [p['predicted'] for p in result['predictions']])
            assert work == r.read(dest/'by-work.json')
            if seed != 42:
                assert [p.name for p in dest.glob('resume-epoch-*.pt')] == [f'resume-epoch-{epochs}.pt']
                assert [p.name for p in dest.glob('checkpoint-*')] == [f"checkpoint-{result['best_epoch']}"]
                assert r.read(dest/'history.json') == result['history']
                import torch
                state = torch.load(dest/f'resume-epoch-{epochs}.pt',map_location='cpu',weights_only=False)
                assert state['epoch']==epochs and state['protocol_hash']==r.fingerprint(config)
                assert state['history']==result['history'] and state['best_epoch']==result['best_epoch']
                assert state['best_pred']==[p['predicted'] for p in result['predictions']]
                assert all(k in state for k in ('model','optimizer','scheduler','scaler','python_rng','numpy_rng','torch_rng','cuda_rng'))
                assert state['scheduler']['last_epoch']==sum(h['optimizer_updates'] for h in result['history'])
                del state
            wall = sum(a['wall_seconds'] for _,a in attempts if a['recipe']==recipe and a.get('seed',42)==seed)
            row = dict(recipe=recipe, seed=seed, best_epoch=result['best_epoch'], epochs=epochs,
                metrics=result['metrics']['combined'], by_work=work, wall_seconds=wall,
                result_path=str((dest/'result.json').relative_to(r.ROOT)), result_sha256=r.filehash(dest/'result.json'),
                checkpoint=str((dest/f"checkpoint-{result['best_epoch']}").relative_to(r.ROOT)),
                config_sha256=r.filehash(dest/'config.json'), class_weights=result['class_weights'],
                steps_per_epoch=result['steps_per_epoch'], warmup_steps=result['warmup_steps'], reload_predictions_identical=True,
                history=result['history'], predictions=result['predictions'])
            results.append(row)
            for label, m in row['metrics']['per_class'].items():
                class_rows.append([recipe,seed,label,m['precision'],m['recall'],m['f1-score'],m['support']])
            for family,m in work.items():
                work_rows.append([recipe,seed,family,m['n'],m['f1_macro'],m['accuracy']])
            for h in result['history']:
                epoch_rows.append([recipe,seed,h['epoch'],h['weighted_train_loss'],h['train_metrics_eval']['f1_macro'],h['f1_macro'],h['optimizer_updates'],h['amp_skips']])
    lookup = {(x['recipe'],x['seed']):x for x in results}
    for recipe in ('R0','R2'):
        assert all(lookup[recipe,s]['class_weights']==lookup[recipe,42]['class_weights'] for s in (43,44))
    paired = [dict(seed=s, delta=lookup['R2',s]['metrics']['f1_macro']-lookup['R0',s]['metrics']['f1_macro']) for s in (42,43,44)]
    aggregate = {recipe:describe([lookup[recipe,s]['metrics']['f1_macro'] for s in (42,43,44)]) for recipe in ('R0','R2')}
    aggregate['R2_minus_R0'] = describe([p['delta'] for p in paired])
    baselines = {name:r.read(r.OUT/'baselines'/name/'baselines.json')['tfidf'] for name in ('H','H-T300')}
    class_summary = {}
    work_summary = {}
    for label in r.LABELS:
        class_summary[label] = {recipe:{metric:describe([lookup[recipe,s]['metrics']['per_class'][label][metric] for s in (42,43,44)]) for metric in ('precision','recall','f1-score')} for recipe in ('R0','R2')}
        class_summary[label]['paired_f1_delta'] = describe([lookup['R2',s]['metrics']['per_class'][label]['f1-score']-lookup['R0',s]['metrics']['per_class'][label]['f1-score'] for s in (42,43,44)])
    for family in results[0]['by_work']:
        work_summary[family] = {recipe:describe([lookup[recipe,s]['by_work'][family]['f1_macro'] for s in (42,43,44)]) for recipe in ('R0','R2')}
        work_summary[family]['paired_delta'] = describe([lookup['R2',s]['by_work'][family]['f1_macro']-lookup['R0',s]['by_work'][family]['f1_macro'] for s in (42,43,44)])
    weak = [l for l in r.LABELS if class_summary[l]['R2']['f1-score']['mean'] < .5]
    persistent = []
    for i, row in enumerate(val):
        preds = {f"{recipe}/{seed}":lookup[recipe,seed]['predictions'][i]['predicted'] for recipe in ('R0','R2') for seed in (42,43,44)}
        if all(preds[f'R2/{s}'] != row['label'] for s in (42,43,44)):
            persistent.append(dict(segment_id=row['segment_id'],family_id=row['family_id'],truth=row['label'],predictions=preds))
    # Deterministic round-robin by weak class; limit reading text to <=12 persistent errors.
    pools = {label:sorted([e for e in persistent if e['truth']==label],key=lambda e:(e['family_id'],e['segment_id'])) for label in weak}
    sample = []
    while len(sample)<12 and any(pools.values()):
        for label in weak:
            if pools[label] and len(sample)<12:
                sample.append(pools[label].pop(0))
    byid = {row['segment_id']:row for row in val}
    for item in sample:
        row = byid[item['segment_id']]
        item['text'] = row['text']
        item['input_sha256'] = row['text_sha256']
        item['source_id'] = row['source_id']
        item['source_char_span'] = row.get('source_char_span')
    dump(A/'error-sample.json',dict(selection='Up to 12 R2 errors in all three seeds, round-robin mean-F1<.50 classes, family/ID order; diagnostic, no relabeling',persistent_count=len(persistent),sample=sample))
    new_seconds = sum(a['wall_seconds'] for _,a in new)
    ledger = {**prior, 'new_training_trajectories':prior['new_training_trajectories']+4,
        'CD_training_gpu_seconds':prior['CD_training_gpu_seconds']+new_seconds,
        'new_training_gpu_seconds':prior['new_training_gpu_seconds']+new_seconds,
        'prior_ledger':dict(path=str((A/'before/budget-ledger-after-C.json').relative_to(r.ROOT)),sha256=r.filehash(A/'before/budget-ledger-after-C.json')),
        'attempts':prior['attempts']+[dict(path=str(p.relative_to(r.ROOT)),sha256=r.filehash(p)) for p,_ in new],
        'phase_D_wall_seconds':new_seconds,
        'accounting_method':'Immutable after-C snapshot plus only D receipts, once each. D wall includes preflight, loading, saving and reload; CPU report work excluded.',
        'S_content_opened':False}
    assert ledger['CD_training_gpu_seconds'] <= 14400 and ledger['new_training_gpu_seconds'] <= 28800
    dump(r.ART/'budget-ledger-after-D.json',ledger)
    summary = dict(results=results, paired_differences=paired, aggregate=aggregate, tfidf_baselines=baselines, per_class_summary=class_summary,
        by_work_summary=work_summary, persistent_R2_errors=persistent, S_opened=False,
        freeze_sha256=r.filehash(r.FREEZE), free_bytes_after=shutil.disk_usage(r.ROOT).free,
        selection_gate_numeric=aggregate['R2_minus_R0']['mean']>=.02 and sum(p['delta']>0 for p in paired)>=2,
        budget_ledger='artifacts/beto-v3/budget-ledger-after-D.json')
    dump(A/'comparison.json',summary)
    csvfile('metrics-per-class.csv',['recipe','seed','class','precision','recall','f1','support'],class_rows)
    csvfile('metrics-per-work.csv',['recipe','seed','family','n','f1_macro_seven_classes','accuracy'],work_rows)
    csvfile('curves.csv',['recipe','seed','epoch','weighted_train_loss','train_f1','V_f1','updates','amp_skips'],epoch_rows)
    csvfile('paired-differences.csv',['seed','R2_minus_R0'],[[p['seed'],p['delta']] for p in paired])
    lines = ['# BETO V3: fase D, confirmación entre semillas','',
        'Se reutilizaron R0/R2 de 42 y se completaron exactamente cuatro ajustes nuevos: R0/R2 × 43/44. '+
        'H 590, T 426 y V 444; representación, etiquetas y criterios congelados. R2 conserva 20 épocas y scheduler de 20 épocas. S permanece cerrada.', '',
        '| Receta | Semilla | F1 macro V | Mejor época / total | Tiempo real (s) |',
        '|---|---:|---:|---:|---:|']
    for row in results:
        lines.append(f"| {row['recipe']} | {row['seed']} | {row['metrics']['f1_macro']:.6f} | {row['best_epoch']} / {row['epochs']} | {row['wall_seconds']:.2f} |")
    lines += ['', '| Semilla | R2−R0 |','|---|---:|']
    lines += [f"| {p['seed']} | {p['delta']:+.6f} |" for p in paired]
    lines += ['', '| Magnitud | Media | Desviación estándar muestral |','|---|---:|---:|']
    lines += [f"| {name} | {v['mean']:.6f} | {v['sample_sd']:.6f} |" for name,v in aggregate.items()]
    lines += ['', f"Baselines reutilizados sobre la misma V: TF-IDF H = {baselines['H']['f1_macro']:.6f}; TF-IDF H+T = {baselines['H-T300']['f1_macro']:.6f}. "+
        f"La media R2−TF-IDF H+T es {aggregate['R2']['mean']-baselines['H-T300']['f1_macro']:+.6f}. No se ajustaron baselines nuevos."]
    lines += ['', 'Tres semillas por receta; desviación estándar con divisor n−1. Las diferencias son emparejadas. '+
        'Las épocas y las obras no son réplicas adicionales de semillas. La variación entre semillas no estima por sí sola incertidumbre por nuevas fuentes. '+
        'Estos resultados siguen siendo de desarrollo: R2 y sus checkpoints se seleccionan con V.', '',
        '## Métricas por clase','',
        'Media ± desviación estándar muestral de F1 entre semillas; soporte fijo de V.', '',
        '| Clase | Soporte | R0 | R2 | Δ F1 medio R2−R0 |','|---|---:|---:|---:|---:|']
    for label, values in class_summary.items():
        a,b=values['R0']['f1-score'],values['R2']['f1-score']
        lines.append(f"| {label} | {int(results[0]['metrics']['per_class'][label]['support'])} | {a['mean']:.4f} ± {a['sample_sd']:.4f} | {b['mean']:.4f} ± {b['sample_sd']:.4f} | {values['paired_f1_delta']['mean']:+.4f} |")
    lines += ['', 'Precisión, recall, F1 y soporte para cada una de las seis ejecuciones: '+
        '[metrics-per-class.csv](../../artifacts/beto-v3/phase-d/metrics-per-class.csv). '+
        'Medias y desviaciones de precisión/recall/F1 y matrices de confusión: [comparison.json](../../artifacts/beto-v3/phase-d/comparison.json).', '',
        '## Métricas por obra','',
        'F1 macro con las siete clases explícitas y cero cuando no hay soporte/predicción; '+
        'por ello una obra sin las siete clases tiene un techo inferior a uno. Comparar recetas dentro de la misma obra. '+
        'El resultado principal es el F1 sobre V agrupada, no la media de estas obras.', '',
        '| Obra/familia | n | R0 media ± DE | R2 media ± DE | Δ medio |', '|---|---:|---:|---:|---:|']
    for family,values in work_summary.items():
        a,b=values['R0'],values['R2']
        lines.append(f"| {family} | {results[0]['by_work'][family]['n']} | {a['mean']:.4f} ± {a['sample_sd']:.4f} | {b['mean']:.4f} ± {b['sample_sd']:.4f} | {values['paired_delta']['mean']:+.4f} |")
    lines += ['', '[Seis métricas por obra](../../artifacts/beto-v3/phase-d/metrics-per-work.csv); '+
        'el JSON completo también incluye precisión, recall, F1 por clase y matriz de confusión de cada obra.', '',
        '## Curvas y conservación','',
        '![Curvas de las seis ejecuciones](../../artifacts/beto-v3/phase-d/curves-D.png)', '',
        '[Curvas CSV](../../artifacts/beto-v3/phase-d/curves.csv) · [Figura PDF](../../artifacts/beto-v3/phase-d/curves-D.pdf) · '+
        '[Curvas existentes de C](../../artifacts/beto-v3/phase-d/curves-C.png). Cada `result.json` conserva todas las métricas por época.', '',
        '| Receta/semilla | Train F1 final | V F1 final | Pérdida final | Actualizaciones / omisiones AMP |', '|---|---:|---:|---:|---:|']
    for row in results:
        h=row['history'];last=h[-1]
        lines.append(f"| {row['recipe']}/{row['seed']} | {last['train_metrics_eval']['f1_macro']:.6f} | {last['f1_macro']:.6f} | {last['weighted_train_loss']:.6f} | {sum(e['optimizer_updates'] for e in h)} / {sum(e['amp_skips'] for e in h)} |")
    lines += ['', 'Todos los mejores checkpoints tienen recarga con predicciones idénticas y hashes verificados. '+
        'Las cuatro ejecuciones nuevas conservan además el último estado completo, cargado en CPU para verificar época, historia, scheduler, optimizador, scaler y RNG. '+
        'No se ejecutó un entrenamiento adicional para probar reanudación ni una simulación de corte eléctrico.', '']
    lines += [f"- {row['recipe']}/{row['seed']}: `{row['checkpoint']}`." for row in results]
    lines += ['', '## Presupuesto y límites','',
        f"D: {new_seconds:.2f} s. C–D acumulado: {ledger['CD_training_gpu_seconds']:.2f}/14.400 s; quedan {14400-ledger['CD_training_gpu_seconds']:.2f} s. "+
        f"V3 entrenamiento: {ledger['new_training_gpu_seconds']:.2f}/28.800 s; 8/18 trayectorias. "+
        f"ASR: {ledger['ASR_gpu_seconds']:.2f} s, sin gasto nuevo. Servicios pagados: US$0.", '',
        'Anotación: 999/1.200 entradas únicas; queda una entrada de desarrollo y 200 de S. '+
        'La inspección diagnóstica de discrepancias existentes no emite nuevas propuestas ni cambia referencias; tokens del proveedor no observables. '+
        'T600 no cabe en el margen actual y no se ejecuta.', '',
        f"Espacio libre tras D: {summary['free_bytes_after']/1024**3:.2f} GiB. Retención limitada a nuevas ejecuciones; resultados de C intactos. "+
        'Snapshots esenciales locales en `artifacts/beto-v3/phase-d/before/`, pesos en `outputs/beto-v3/phase-c/`. No se verificó respaldo externo.', '',
        'Ledger: [budget-ledger-after-D.json](../../artifacts/beto-v3/budget-ledger-after-D.json), derivado del snapshot tras C más sólo recibos D, sin doble conteo. '+
        'El tiempo heredado V2 permanece separado; los fallos antiguos de duración desconocida no se presentan como cero.', '',
        'V cubre 444/489 unidades anotadas resolubles (90,80 %), no videos completos. Las referencias son asistidas por IA, no gold experto; '+
        'persisten las limitaciones admitidas de once huecos internos de subtítulos. La enmienda 23+23 sólo abarca C–D. '+
        'No se acredita éxito final ni se abre S.', '',
        f"Freeze SHA-256: `{r.filehash(r.FREEZE)}`.", '',
        '## Diagnóstico e intervención siguiente','',
        'El análisis cualitativo y la recomendación se registran en [phase-d-analysis.md](phase-d-analysis.md).']
    write(r.ROOT/'docs/beto-v3/phase-d-results.md','\n'.join(lines)+'\n')
    print(json.dumps(dict(aggregate=aggregate,paired=paired,new_seconds=new_seconds,persistent_errors=len(persistent)),indent=2))


if __name__ == '__main__':
    main()
