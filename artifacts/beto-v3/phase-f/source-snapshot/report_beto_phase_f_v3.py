"""Verify all F results and report the preregistered paired comparison."""
import statistics as st
import run_beto_phase_f_v3 as f
import os
os.environ['MPLCONFIGDIR']=str(f.CACHE/'matplotlib')
r=f.r

def desc(xs): return dict(mean=st.mean(xs),sample_sd=st.stdev(xs),values=xs)
def fmt(d): return f"{d['mean']:.6f} ± {d['sample_sd']:.6f}"

def main():
    _,rows=r.frozen_inputs(); val=rows['V']
    contract=r.read(f.A/'preregistration.json')
    assert contract['freeze_sha256']==r.filehash(r.FREEZE)
    for entry in contract['controls']: f.pinned(entry)
    records=[]
    for seed in (42,43,44):
        for name,root,sub in [('H+T',r.OUT,'R2'),('T',f.OUT,'T-only')]:
            dest=root/f'seed-{seed}'/sub
            config=r.read(dest/'config.json');result=r.verify_result(dest,config,val)
            train=rows['T300'] if name=='T' else rows['H']+rows['T300']
            assert config['execution']['train_rows_hash']==r.fingerprint(train)
            assert config['execution']['validation_rows_hash']==r.fingerprint(val)
            assert config['execution']['epochs']==20 and config['execution']['lr']==2e-5
            assert config['execution']['seed']==seed
            assert result['reload_predictions_identical'] and len(result['history'])==20
            assert result['best_epoch']==max(result['history'],key=lambda h:h['f1_macro'])['epoch']
            if name=='T':
                assert r.read(dest/'resume-verification.json')['status']=='passed'
                assert r.read(dest/'history.json')==result['history']
                assert (dest/'resume-epoch-20.pt').stat().st_size>1_000_000_000
                assert config['execution']['preregistration_sha256']==r.filehash(f.A/'preregistration.json')
            attempts=[r.read(p) for p in (root/'attempts').glob('*.json')]
            cost=sum(a['wall_seconds'] for a in attempts if a.get('seed',42)==seed and a['recipe']==('R2' if name=='H+T' else 'F-T-only-R2'))
            work=r.by_work(val,[p['predicted'] for p in result['predictions']])
            records.append(dict(condition=name,seed=seed,metrics=result['metrics']['combined'],by_work=work,
                best_epoch=result['best_epoch'],history=result['history'],wall_seconds=cost,
                result_path=str((dest/'result.json').relative_to(f.ROOT)),result_sha256=r.filehash(dest/'result.json'),
                checkpoint=str((dest/f"checkpoint-{result['best_epoch']}").relative_to(f.ROOT)),
                class_weights=result['class_weights'],steps_per_epoch=result['steps_per_epoch'],warmup_steps=result['warmup_steps']))
    lookup={(x['condition'],x['seed']):x for x in records}
    aggregate={c:desc([lookup[c,s]['metrics']['f1_macro'] for s in (42,43,44)]) for c in ('H+T','T')}
    paired=[dict(seed=s,delta=lookup['T',s]['metrics']['f1_macro']-lookup['H+T',s]['metrics']['f1_macro']) for s in (42,43,44)]
    delta=desc([v['delta'] for v in paired])
    classes={}
    for label in r.LABELS:
        classes[label]={c:{m:desc([lookup[c,s]['metrics']['per_class'][label][m] for s in (42,43,44)]) for m in ('precision','recall','f1-score')} for c in ('H+T','T')}
        classes[label]['support']=lookup['T',42]['metrics']['per_class'][label]['support']
        classes[label]['paired_delta']=desc([lookup['T',s]['metrics']['per_class'][label]['f1-score']-lookup['H+T',s]['metrics']['per_class'][label]['f1-score'] for s in (42,43,44)])
    works={}
    for work in records[0]['by_work']:
        works[work]={c:desc([lookup[c,s]['by_work'][work]['f1_macro'] for s in (42,43,44)]) for c in ('H+T','T')}
        works[work]['n']=lookup['T',42]['by_work'][work]['n']
        works[work]['paired_delta']=desc([lookup['T',s]['by_work'][work]['f1_macro']-lookup['H+T',s]['by_work'][work]['f1_macro'] for s in (42,43,44)])
    base=r.baseline(rows['T300'],val,f.OUT/'baselines/T',dict(train=r.fingerprint(rows['T300']),V=r.fingerprint(val),protocol=r.filehash(r.ART/'protocol.json')))
    control_base=r.read(r.OUT/'baselines/H-T300/baselines.json')
    costs={c:sum(lookup[c,s]['wall_seconds'] for s in (42,43,44)) for c in ('H+T','T')}
    if abs(delta['mean'])<.005:
        selected='T' if costs['T']<costs['H+T'] else 'H+T';reason='difference <0.005; lower measured cost'
    else:
        selected='T' if delta['mean']>0 else 'H+T';reason='higher mean V macro F1'
    positive_seeds=sum(v['delta']>0 for v in paired)
    positive_classes=sum(v['paired_delta']['mean']>0 for v in classes.values())
    positive_works=sum(v['paired_delta']['mean']>0 for v in works.values())
    weak_T=[l for l,v in classes.items() if v['T']['f1-score']['mean']<.5]
    attempts=[r.read(p) for p in (f.OUT/'attempts').glob('*.json')]
    assert all('wall_seconds' in a for a in attempts)
    assert {a['seed'] for a in attempts}=={42,43,44}
    assert len(list(f.OUT.glob('seed-*/T-only/attempt-started.json')))==3
    budget=f.ledger('F_complete')
    budget['prior_ledger']=dict(path=str((f.A/'before/budget-ledger-after-D.json').relative_to(f.ROOT)),sha256=r.filehash(f.A/'before/budget-ledger-after-D.json'))
    f.write(r.ART/'budget-ledger-after-F.json',budget)
    f.write(r.ART/'budget-ledger-current.json',budget)
    assert budget['new_training_trajectories']==11 and budget['new_training_gpu_seconds']<=28800
    summary=dict(registered_comparison=r.filehash(f.A/'preregistration.json'),freeze_sha256=r.filehash(r.FREEZE),
        S_content_opened=False,records=records,aggregate=aggregate,paired=paired,paired_summary=delta,
        per_class=classes,per_work=works,selected=selected,selection_reason=reason,costs=costs,
        baselines={'T':base['tfidf'],'H+T':control_base['tfidf']},budget=budget,
        final_success_evaluated=False,production_model_changed=False)
    f.write(f.A/'comparison.json',summary)
    f.write(f.A/'verification.json',dict(status='passed',checked_utc=f.now(),new_trajectories=3,
        epochs_each=20,controls_hashes_unchanged=True,freeze_unchanged=True,checkpoint_reload_identical=True,
        last_resume_loaded_cpu=True,complete_migration_verified=False,outputs_respaldo_touched=False,
        S_content_opened=False,free_space=f.storage(),no_new_experiment_started=True))
    lines=['# BETO V3: F completada, sólo T frente al control R2 H+T','',
        f"Resultado de desarrollo: se conserva **{selected}** según el criterio registrado: {'menor coste dentro de la tolerancia 0,005' if abs(delta['mean'])<.005 else 'mayor F1 macro medio en V'}. Diferencia media T−H+T: **{delta['mean']:+.6f}**, DE muestral {delta['sample_sd']:.6f}. No se selecciona una semilla favorable.",'',
        f"Sólo T {'mejora' if delta['mean']>0 else 'retrocede'} en la media principal. Hay diferencias positivas en {positive_seeds}/3 semillas, {positive_classes}/7 clases y {positive_works}/8 obras. Se informan tanto ganancias como pérdidas. Las clases T con F1 medio inferior a 0,50 son: {', '.join(weak_T) or 'ninguna'}.",'',
        '| Condición | F1 macro medio ± DE muestral |','|---|---:|',
        *[f'| {c} | {fmt(aggregate[c])} |' for c in ('H+T','T')],'',
        '| Semilla | H+T F1 | T F1 | T−H+T | Mejor época H+T / T |','|---|---:|---:|---:|---:|',
        *[f"| {s} | {lookup['H+T',s]['metrics']['f1_macro']:.6f} | {lookup['T',s]['metrics']['f1_macro']:.6f} | {paired[i]['delta']:+.6f} | {lookup['H+T',s]['best_epoch']} / {lookup['T',s]['best_epoch']} |" for i,s in enumerate((42,43,44))],'',
        '## Resultados por clase','',
        '| Clase | Soporte | H+T F1 medio ± DE | T F1 medio ± DE | Δ medio |','|---|---:|---:|---:|---:|',
        *[f"| {l} | {v['support']} | {fmt(v['H+T']['f1-score'])} | {fmt(v['T']['f1-score'])} | {v['paired_delta']['mean']:+.6f} |" for l,v in classes.items()],'',
        'Precisión, recall, F1, soportes y matrices de confusión de cada ejecución y obra, junto con las medias y DE por clase, están en [comparison.json](../../artifacts/beto-v3/phase-f/comparison.json).','',
        '## Resultados por obra','',
        '| Obra | n | H+T F1 medio ± DE | T F1 medio ± DE | Δ medio |','|---|---:|---:|---:|---:|',
        *[f"| {w} | {v['n']} | {fmt(v['H+T'])} | {fmt(v['T'])} | {v['paired_delta']['mean']:+.6f} |" for w,v in works.items()],'',
        'F1 por obra usa siete clases explícitas, zero_division=0; una obra sin todas las clases tiene un techo inferior a uno. El criterio principal es V agrupada, no la media de obras.','',
        '## Curvas y conservación','',
        '![Curvas F y control reutilizado](../../artifacts/beto-v3/phase-f/curves-F.png)','',
        '| Condición/semilla | Train F1 final | V F1 final | Pérdida final | Actualizaciones / omisiones AMP |','|---|---:|---:|---:|---:|',
        *[f"| {x['condition']}/{x['seed']} | {x['history'][-1]['train_metrics_eval']['f1_macro']:.6f} | {x['history'][-1]['f1_macro']:.6f} | {x['history'][-1]['weighted_train_loss']:.6f} | {sum(h['optimizer_updates'] for h in x['history'])} / {sum(h['amp_skips'] for h in x['history'])} |" for x in records],'',
        'Las tres trayectorias T completan 20 épocas con horizonte de 20. T usa 27 pasos/época y warmup 54; H+T usa 64 y 128. Pesos calculados con N/(7 n_clase) sólo en el train de cada condición. Esto compara recetas prácticas; no aísla causalmente retirar H.','',
        'Las tres T llegan a train F1=1,0 y mantienen una brecha amplia frente a V. El resultado no apoya retirar H para mejorar esta evaluación, ni demuestra que añadir más épocas lo resolvería. No identifica por sí solo causas del error o calidad de las referencias.','',
        'Cada ejecución nueva conserva history.json/result.json con todas las épocas, los checkpoints mejorados y todos los estados completos por época. El mejor checkpoint se recargó y produjo exactamente las mismas predicciones en V. El estado de época 20 se cargó en CPU y se verificaron protocolo, historia, optimizador, scheduler, scaler y RNG; no se simuló un corte ni se reentrenó para verificarlo.','',
        *[f"- T/{s}: `{lookup['T',s]['checkpoint']}`; último estado `outputs/beto-v3/phase-f/seed-{s}/T-only/resume-epoch-20.pt`." for s in (42,43,44)],'',
        '## Baselines, presupuesto y límites','',
        f"TF-IDF comparable T: {base['tfidf']['f1_macro']:.6f}; H+T reutilizado: {control_base['tfidf']['f1_macro']:.6f}. T se ajustó una vez con fórmula congelada, sin búsqueda, en CPU ({base['seconds']:.2f} s).",'',
        f"F consume {budget['phase_F_wall_seconds']:.2f} s; V3 acumulado {budget['new_training_gpu_seconds']:.2f}/28800 s, quedan {28800-budget['new_training_gpu_seconds']:.2f} s. Trayectorias 11/18. C–D permanece en 7205,39/14400 s. Anotación 999/1200, una entrada de desarrollo y 200 reservadas; ASR sin cambios; servicios pagados US$0. El tiempo heredado V2 y fallos antiguos desconocidos siguen separados.",'',
        'La DE utiliza divisor n−1 y sólo tres semillas. No estima incertidumbre por obras nuevas: V tiene ocho familias, tamaños desiguales y resultados por obra heterogéneos. Checkpoints y condiciones se seleccionan sobre V reutilizada; la evaluación es de desarrollo. No hay evidencia independiente en S ni una garantía de transferencia. No tratar épocas, unidades o semillas como nuevas obras independientes.','',
        'Se conserva la excepción 23+23 sólo para desarrollo F: la meta original de 25 sigue incumplida. V tiene 444/489 referencias resolubles, anotación asistida por IA, tramos muestreados y limitaciones ASR/huecos admitidos. No se alteraron etiquetas, particiones ni objetivos originales. No se acredita éxito final.','',
        'Almacenamiento: Junction comprobada a E, cachés/temporales específicos del proceso en E y ningún archivo existente borrado o movido. outputs_respaldo intacto. Verificación acotada a los prerrequisitos de F; no certifica migración completa ni respaldo. No se cambió el servicio de producción.','',
        '## Continuidad Codex/Claude','',
        'Leer `artifacts/beto-v3/development-current.json`, el ledger señalado y este informe. `budget-ledger-current.json` ahora refleja el ledger posterior a F; el snapshot anterior se conserva. Scripts: `run_beto_phase_f_v3.py` y `report_beto_phase_f_v3.py` con outputs/venv-ml/Scripts/python.exe -B -X utf8. Figuras: `python -B -X utf8 scripts/plot_beto_phase_f_v3.py`, usando el Matplotlib ya instalado en el Python del sistema. Reutilizar resultados existentes. F queda cerrada; no abrir S ni ejecutar E, TAPT, G u otro experimento automáticamente. La decisión final requiere una instrucción posterior.','']
    (f.ROOT/'docs/beto-v3/phase-f-results.md').write_text('\n'.join(lines),encoding='utf-8')
    state=r.read(r.ART/'development-current.json')
    state.update(candidate='F-T-only-R2' if selected=='T' else 'R2',results='artifacts/beto-v3/phase-f/comparison.json',
        next_action='Stop: no S opening or further experiment authorized',phase_F_selected_condition=selected)
    f.write(r.ART/'development-current.json',state)
    (f.ROOT/'docs/beto-v3/progress.md').write_text('\n'.join(['# BETO V3: F completada; S cerrada','',
        f"F T: {fmt(aggregate['T'])}; control R2 H+T: {fmt(aggregate['H+T'])}. Δ emparejada T−H+T: {fmt(delta)}. Se conserva {selected} según el registro prospectivo.",'',
        '[Informe completo, limitaciones y continuidad Codex/Claude](phase-f-results.md) · [Registro prospectivo y enmienda F](phase-f-preregistration.md)','',
        f"11/18 trayectorias; {budget['new_training_gpu_seconds']:.2f}/28800 s V3. Ledger vigente: artifacts/beto-v3/budget-ledger-after-F.json (también reflejado en budget-ledger-current.json). Estado: artifacts/beto-v3/development-current.json.",'',
        'T426 y V444 congeladas; tres controles reutilizados y sólo tres nuevos ajustes T con semillas 42/43/44, 20 épocas. Recargas de mejores checkpoints y últimos estados verificadas. Producción sin cambios. outputs es Junction a E:/BETO/outputs; cachés y temporales F en E. outputs_respaldo intacto. Comprobación de archivos necesarios para F, no migración completa.','',
        'Detenerse aquí. No abrir S, añadir anotaciones, TAPT ni iniciar otro experimento sin una instrucción posterior.']),encoding='utf-8')
    print(r.json.dumps(dict(aggregate=aggregate,paired=paired,selected=selected,budget_seconds=budget['new_training_gpu_seconds']),indent=2))

if __name__=='__main__':main()
