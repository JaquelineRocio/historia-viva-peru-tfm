"""Paired descriptive analysis; no fits and no selection of favorable seeds."""
import csv
import statistics as stats
from collections import Counter
from run_beto_class_weights_v2 import *

C='B_weights_A'
SUBSETS=('combined','historical','new_AI')

def dispersion(xs):
    return {'values':xs,'mean':stats.mean(xs),'sample_sd':stats.stdev(xs),'min':min(xs),'max':max(xs)}

def table(head,rows):
    return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])

def f(x):return f'{x:.6f}'
def d(x):return f'{x:+.6f}'

def main():
    p,byid,m=preflight();runs={};flat=[];paired=[];execution=[]
    for seed in SEEDS:
        for fold,fm in zip(p['folds'],m['folds']):
            fid=fold['id'];val=[byid[i] for i in fold['validation']]
            for c in ('A','B',C):
                dest=old_path(seed,fid,c) if c!=C else WOUT/f'seed-{seed}'/(fid+'-'+C)
                if c==C and fm['equivalent_under_weighted_mean']:
                    dest=old_path(seed,fid,'B')
                config=p if seed==42 and dest==old_path(seed,fid,c) else read(dest/'config.json')
                r=verify_result(dest,config,val);runs[seed,fid,c]=r
                if c==C:
                    assert not fm['equivalent_under_weighted_mean'], 'This report expects effective contrasts in all three folds'
                    assert config=={**p,'execution':{'seed':seed,'fold':fid,'condition':C,'train_rows_hash':fingerprint([byid[i] for i in fold['train_B']]),'validation_rows_hash':fingerprint(val),'weight_source':'train_A','weight_rows_hash':fingerprint([byid[i] for i in fold['train_A']]),'weights':fm['weights_float32']['A'],'planned_updates':fm['planned_updates'],'class_weights_manifest_hash':fingerprint(m)}}
                    assert r['class_weights']==fm['weights_float32']['A']
                    assert r['steps_per_epoch']==runs[seed,fid,'B']['steps_per_epoch']
                assert len(r['history'])==4
                assert all(h['optimizer_updates']+h['amp_skips']==r['steps_per_epoch'] for h in r['history'])
                assert r['best_epoch']==max(r['history'],key=lambda h:h['f1_macro'])['epoch']
                assert r['metrics']==r['history'][r['best_epoch']-1]['metrics']
                execution.append({'seed':seed,'fold':fid,'condition':c,'best_epoch':r['best_epoch'],'planned_updates':4*r['steps_per_epoch'],'applied_updates':sum(h['optimizer_updates'] for h in r['history']),'amp_skips':sum(h['amp_skips'] for h in r['history']),'seconds':r['seconds'],'result_sha256':filehash(dest/'result.json'),'config_hash':fingerprint(config),'checkpoint_hashes':r['checkpoint_hashes']})
                flat.extend({'seed':seed,'fold':fid,'condition':c,**v} for v in r['predictions'])
            paired.append({'seed':seed,'fold':fid,'subsets':{s:{**{c:runs[seed,fid,c]['metrics'][s] for c in ('A','B',C)},'difference':runs[seed,fid,C]['metrics'][s]['f1_macro']-runs[seed,fid,'B']['metrics'][s]['f1_macro'],'difference_vs_A':runs[seed,fid,C]['metrics'][s]['f1_macro']-runs[seed,fid,'A']['metrics'][s]['f1_macro']} for s in SUBSETS}})
    summaries={}
    for s in SUBSETS:
        per_seed=[]
        for seed in SEEDS:
            items=[r['subsets'][s] for r in paired if r['seed']==seed]
            item={'seed':seed,**{c:stats.mean(r[c]['f1_macro'] for r in items) for c in ('A','B',C)}}
            item['difference']=item[C]-item['B'];item['difference_vs_A']=item[C]-item['A'];per_seed.append(item)
        summaries[s]={'per_seed':per_seed,**{k:dispersion([r[k] for r in per_seed]) for k in ('A','B',C,'difference','difference_vs_A')},'seeds_favoring_weights_A':sum(r['difference']>0 for r in per_seed),'seeds_favoring_B':sum(r['difference']<0 for r in per_seed),'ties':sum(r['difference']==0 for r in per_seed)}
    classes=[]
    for s in SUBSETS:
        for label in LABELS:
            ps=[]
            for seed in SEEDS:
                items=[r['subsets'][s] for r in paired if r['seed']==seed]
                values={c:stats.mean(r[c]['per_class'][label]['f1-score'] for r in items) for c in ('A','B',C)}
                ps.append({'seed':seed,**values,'difference':values[C]-values['B']})
            classes.append({'subset':s,'label':label,'per_seed':ps,'difference':dispersion([r['difference'] for r in ps]),'positive_seeds':sum(r['difference']>0 for r in ps),'negative_seeds':sum(r['difference']<0 for r in ps)})
    supports=[]
    for fold in p['folds']:
        for s in SUBSETS:
            metric=runs[42,fold['id'],'B']['metrics'][s]
            supports.append({'fold':fold['id'],'subset':s,'n':metric['n'],'class_support':{l:metric['per_class'][l]['support'] for l in LABELS},'absent_classes':[l for l in LABELS if metric['per_class'][l]['support']==0]})
    lookup={(r['segment_id'],r['seed'],r['condition']):r['predicted'] for r in flat}
    transitions=[];errors=[]
    old_errors=read(ROOT/'outputs/beto-v2/stability/persistent-errors.json')
    old_ids={r['segment_id'] for r in old_errors}
    for sid,row in byid.items():
        preds={c:{str(seed):lookup[sid,seed,c] for seed in SEEDS} for c in ('A','B',C)}
        wrong={c:sum(v!=row['label'] for v in preds[c].values()) for c in preds}
        errors.append({'segment_id':sid,'truth':row['label'],'role':row['role'],'family_id':row['family_id'],'predictions':preds,'wrong_seed_count':wrong,'phase05_persistent':sid in old_ids,'corrected_seeds':[s for s in SEEDS if lookup[sid,s,'B']!=row['label'] and lookup[sid,s,C]==row['label']],'regressed_seeds':[s for s in SEEDS if lookup[sid,s,'B']==row['label'] and lookup[sid,s,C]!=row['label']]})
    for seed in SEEDS:
        counts=Counter()
        for row in errors:
            a=row['predictions']['B'][str(seed)];b=row['predictions'][C][str(seed)];truth=row['truth']
            counts['corrected' if a!=truth and b==truth else 'regression' if a==truth and b!=truth else 'both_correct' if a==truth else 'same_error' if a==b else 'different_error']+=1
        transitions.append({'seed':seed,**counts})
    index={r['segment_id']:r for r in errors};reviewed=[]
    for old in read(ROOT/'outputs/beto-v2/stability/reviewed-cases.json'):
        change=index[old['segment_id']]
        assert old['truth']==byid[old['segment_id']]['label'] and old['text']==byid[old['segment_id']]['text']
        assert old['predictions']=={c:change['predictions'][c] for c in ('A','B')}
        reviewed.append({**old,'predictions':change['predictions'],'wrong_seed_count':change['wrong_seed_count'],'corrected_seeds':change['corrected_seeds'],'regressed_seeds':change['regressed_seeds']})
    persistent={'phase05_total':len(old_ids),'B_persistent_at_least_two':sum(r['wrong_seed_count']['B']>=2 for r in errors),'weights_A_persistent_at_least_two':sum(r['wrong_seed_count'][C]>=2 for r in errors),'resolved_persistence_ids':[r['segment_id'] for r in errors if r['wrong_seed_count']['B']>=2 and r['wrong_seed_count'][C]<2],'new_persistence_ids':[r['segment_id'] for r in errors if r['wrong_seed_count']['B']<2 and r['wrong_seed_count'][C]>=2],'B_wrong_all_three_corrected_all_three':[r['segment_id'] for r in errors if r['wrong_seed_count']['B']==3 and r['wrong_seed_count'][C]==0]}
    primary=summaries['combined'];mean=primary['difference']['mean'];sd=primary['difference']['sample_sd'];wins=primary['seeds_favoring_weights_A']
    status='mejora consistente descriptiva' if wins==3 else 'empeoramiento en las tres semillas' if primary['seeds_favoring_B']==3 else 'resultado mixto/inconcluyente'
    keep=C if wins==3 else 'B'
    conclusions={'status':status,'retain_for_next_experiment':keep,'mean_difference':mean,'sample_sd':sd,'positive_seeds':wins,'negative_seeds':primary['seeds_favoring_B'],'mean_difference_vs_A':primary['difference_vs_A']['mean'],'next_intervention_not_executed':'Añadir exclusivamente contexto previo archivado en el espacio libre de la entrada de 384 tokens. Conservar los tokens del objetivo usados por la referencia; añadir como segundo segmento hasta 95 tokens finales del pasaje previo que quepan, contando los separadores. Si no hay contexto o no cabe al menos un token de contexto con sus separadores, conservar la entrada original. Misma regla para todas las filas, sin recortar más el objetivo para dar cabida al contexto. Congelar el manifiesto antes de entrenar, mantener etiquetas y filas de validación, no seleccionar casos por resultado. Comparar en los mismos folds y semillas con la referencia conservada; informar cobertura y cantidad efectiva de contexto por fila.'}
    report={'condition':C,'seeds':list(SEEDS),'new_runs':9,'reused_runs':18,'unit':'equal-weight three-fold mean per seed; sample SD ddof=1 across three seeds; nine cells are not independent studies','paired_fold_metrics':paired,'summaries':summaries,'class_summary':classes,'supports':supports,'transitions':transitions,'persistent_summary':persistent,'execution':execution,'conclusions':conclusions,'input_hashes':{'protocol':filehash(WART/'protocol.json'),'reviewed_cases_phase05':filehash(ROOT/'outputs/beto-v2/stability/reviewed-cases.json'),'persistent_errors_phase05':filehash(ROOT/'outputs/beto-v2/stability/persistent-errors.json'),'report_script':filehash(__file__)}}
    report['input_hashes']['runtime']=filehash(WART/'runtime.json')
    report['resume_diagnostic']={'parameters':read(WART/'resume-check.json'),'predictions':read(WART/'resume-predictions-check.json')}
    report['input_hashes']['resume_check']=filehash(WART/'resume-check.json')
    report['input_hashes']['resume_predictions_check']=filehash(WART/'resume-predictions-check.json')
    report['execution_attempts']={'completed_trajectories':9,'failed_before_first_epoch':1,'epoch_boundary_resumes':1,'distinct_seed_fold_conditions':9}
    csvpath=WOUT/'predictions-by-seed.csv'
    import io
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    if csvpath.exists():assert csvpath.read_bytes()==buf.getvalue().encode('utf-8')
    else:csvpath.write_bytes(buf.getvalue().encode('utf-8'))
    lines=[f'**¿Cambiar los pesos mejora B de manera consistente y cuánto?** {status.capitalize()}: B_weights_A−B = **{d(mean)} F1 macro** ({mean*100:+.3f} puntos porcentuales), con **DE muestral {f(sd)}**. Favorece B_weights_A en {wins}/3 semillas y B en {primary["seeds_favoring_B"]}/3; empates: {primary["ties"]}.',
        '',f'Se conserva **{keep}** como referencia para el siguiente experimento. B_weights_A promedia {f(primary[C]["mean"])} ± {f(primary[C]["sample_sd"])}; B, {f(primary["B"]["mean"])} ± {f(primary["B"]["sample_sd"])}; A, {f(primary["A"]["mean"])} ± {f(primary["A"]["sample_sd"])}. La diferencia B_weights_A−A es {d(primary["difference_vs_A"]["mean"])} (DE {f(primary["difference_vs_A"]["sample_sd"])}). '+('Las tres diferencias positivas son apoyo descriptivo en estas divisiones, no una prueba de generalización.' if wins==3 else 'El cambio no justifica sustituir B por una regla de pesos con ventaja inestable. Se cierra esta hipótesis sin variantes adicionales ni nuevas semillas.'),
        '', '## Identidad y contraste efectivo', '',
        'Se verificaron las 591 filas canónicas, los hashes congelados, las versiones, BETO base y revisión c4d86612f51b4f46759c8390d1798c2febe71b93, los 18 resultados A/B, sus checkpoints, métricas y predicciones ordenadas. No se repitió la auditoría del corpus. El mapa siguiente fija el orden de todos los vectores.', '',
        table(['ID','Etiqueta'],list(enumerate(LABELS))), '',
        'Pesos = n_train/(7 × recuento de clase). A y B no son proporcionales en ninguno de los folds: el factor n_train/7 se cancela, pero las frecuencias relativas difieren. La pérdida divide la suma ponderada por la suma de pesos de los objetivos del batch efectivo real. Se comprobó el gradiente contra batches completos, incluido un grupo final parcial, para ambos vectores.', '']
    for fold in m['folds']:
        lines += [f'### {fold["fold"]}', '',table(['Clase','n A','n B','Peso A','Peso B','A/B'],[[l,fold['counts']['A'][i],fold['counts']['B'][i],f(fold['weights_float64']['A'][i]),f(fold['weights_float64']['B'][i]),f(fold['A_over_B'][i])] for i,l in enumerate(LABELS)]),'']
    lines += ['Se entrenó únicamente B_weights_A: exactamente train_B y validación original; vector de train_A del mismo fold. Cada ejecución parte de BETO base, nunca de parámetros entrenados de A. El análisis AST verifica que solo cambia el origen del vector: semilla antes de inicializar, mismas filas ordenadas y barajado semilla+época. Se conservan longitud 384, cuatro épocas, AdamW lr 2e-5 y weight decay 0,01, microbatch 2, acumulación 8, clipping 1, scheduler original y precisión CUDA fp16. Selección: mayor F1 macro combinado, empate a la primera época.', '', '## Comparación emparejada', '']
    for s,title in [('combined','Conjunto'),('historical','Origen histórico'),('new_AI','Origen IA')]:
        sm=summaries[s]
        lines += [f'### {title}', '',table(['Semilla','Fold','A','B',C,'Δ vs B'],[[r['seed'],r['fold'],f(r['subsets'][s]['A']['f1_macro']),f(r['subsets'][s]['B']['f1_macro']),f(r['subsets'][s][C]['f1_macro']),d(r['subsets'][s]['difference'])] for r in paired]),'',table(['Semilla','Media A','Media B','Media '+C,'Δ vs B','Δ vs A'],[[r['seed'],f(r['A']),f(r['B']),f(r[C]),d(r['difference']),d(r['difference_vs_A'])] for r in sm['per_seed']]),'',f'Δ vs B medio: {d(sm["difference"]["mean"])}; DE muestral: {f(sm["difference"]["sample_sd"])}; semillas a favor de B_weights_A/B: {sm["seeds_favoring_weights_A"]}/{sm["seeds_favoring_B"]}.','']
    lines += ['Cada promedio asigna el mismo peso a los tres folds. La unidad del resumen es la semilla (n=3), con DE muestral n−1. Las nueve combinaciones no son nueve estudios independientes. Son resultados de desarrollo y la misma validación selecciona época; no son una evaluación final independiente.', '', '## Soportes y clases', '', table(['Fold','Origen','n','Clases ausentes'],[[r['fold'],r['subset'],r['n'],', '.join(r['absent_classes']) or 'ninguna'] for r in supports]),'', 'Todos los F1 macro incluyen las siete clases y zero_division=0, también donde faltan clases. El desglose IA tiene soporte pequeño y anotación asistida; no demuestra mejora histórica general. Los soportes por clase, precisión, recall, F1 y matrices 7×7 por ejecución/origen están en report.json.','']
    for s in SUBSETS:
        lines += [f'### Diferencias por clase: {s}', '',table(['Clase','Δ s42','Δ s43','Δ s44','Media Δ','DE','Semillas +/−'],[[r['label'],*[d(v['difference']) for v in r['per_seed']],d(r['difference']['mean']),f(r['difference']['sample_sd']),f'{r["positive_seeds"]}/{r["negative_seeds"]}'] for r in classes if r['subset']==s]),'']
    lines += ['## Errores persistentes y casos de fase 05','',table(['Semilla','Corrige','Introduce','Error igual','Error distinto'],[[r['seed'],r.get('corrected',0),r.get('regression',0),r.get('same_error',0),r.get('different_error',0)] for r in transitions]),'',f'Errores en al menos dos semillas: B {persistent["B_persistent_at_least_two"]}, B_weights_A {persistent["weights_A_persistent_at_least_two"]}. Dejan de ser persistentes {len(persistent["resolved_persistence_ids"])} filas y aparecen {len(persistent["new_persistence_ids"])} nuevas. Los IDs, transiciones por semilla y todas las predicciones se conservan en errors.json. Esto describe aciertos, no sustituye F1.', '', 'Se reutilizan los 20 casos revisados, con sus textos, contextos, comentarios y referencias intactos. La selección es deliberada y no estima prevalencia. Las ternas siguen 42/43/44; los números de la tabla son IDs del mapa explícito anterior.', '',table(['Caso','Referencia','B','B_weights_A','Corrige semillas','Introduce semillas'],[[r['segment_id'],LABELS.index(r['truth']),'/'.join(str(LABELS.index(r['predictions']['B'][str(s)])) for s in SEEDS),'/'.join(str(LABELS.index(r['predictions'][C][str(s)])) for s in SEEDS),','.join(map(str,r['corrected_seeds'])) or '—',','.join(map(str,r['regressed_seeds'])) or '—'] for r in reviewed]),'', '## Ejecución y reproducción','',table(['Semilla','Fold','Condición','Época','Planificadas','Aplicadas','AMP omitidas'],[[r['seed'],r['fold'],r['condition'],r['best_epoch'],r['planned_updates'],r['applied_updates'],r['amp_skips']] for r in execution]),'', 'Nueve entrenamientos nuevos de una sola condición; nueve B y nueve A reutilizados. No se descartan resultados desfavorables. Configuraciones, curvas, predicciones, checkpoints y estados de reanudación por época están en outputs/beto-v2/class-weights/seed-*/. El protocolo, pesos float32 efectivos, hashes y verificaciones están en artifacts/beto-v2/class-weights/protocol.json.', '', '```powershell','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_class_weights_v2.py preflight','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_first_training_v2.py run --seed 42 --weight-source train_A','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_first_training_v2.py run --seed 43 --weight-source train_A','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_first_training_v2.py run --seed 44 --weight-source train_A','outputs/venv-ml/Scripts/python.exe -u scripts/report_beto_class_weights_v2.py','```','', 'Los comandos omiten resultados completos tras verificar su identidad y reanudan los incompletos desde la última frontera de época. El informe reutiliza archivos idénticos y rechaza discrepancias. El runner anterior se archiva en artifacts/beto-v2/stability/runner-stability-original.py, conservando la verificabilidad de la fase 05.', '', '## Cierre y siguiente intervención propuesta, no ejecutada','',conclusions['next_intervention_not_executed'],'','La justificación es contextual: S01-seg0008-s00000 comienza con una referencia al pasaje anterior; S01-seg0014-whole distingue proyecto de implantación mediante el contexto previo. historical-v4-0265 carece de anclaje temporal local y historical-v4-0430 comienza con «esta asamblea». Solo se usa contexto ya archivado del mismo documento/familia; no se inventa contexto para los históricos que carezcan de él. El manifiesto debe documentar cobertura por origen/fold y verificar que ninguna entrada atraviesa familias o incorpora etiquetas. Se puntúan las mismas 591 unidades objetivo con sus etiquetas intactas, además del subconjunto con contexto como desglose secundario. La regla se aplica a todas las filas elegibles, no solo a errores revisados. No se cambia la referencia después de observar predicciones.','', 'Este contraste estudia pesos dentro de B. No demuestra que añadir datos sea beneficioso ni separa la diferencia de actualizaciones entre A y B. No hubo nuevas anotaciones, cambios de etiquetas, búsqueda de hiperparámetros, DAPT, acceso a ejemplos reservados ni despliegue.']
    focus=[]
    for label in (LABELS[1],LABELS[5],LABELS[6],LABELS[2]):
        r=next(r for r in classes if r['subset']=='combined' and r['label']==label)
        focus.append(f'{label}: Δ medio {d(r["difference"]["mean"])} con DE {f(r["difference"]["sample_sd"])}; mejora en {r["positive_seeds"]}/3 semillas y retrocede en {r["negative_seeds"]}/3.')
    focus += ['El promedio de las siete diferencias de F1 de clase reproduce la diferencia macro; un mayor número de aciertos no garantiza mayor F1 macro.']
    idx=lines.index('## Errores persistentes y casos de fase 05')
    lines[idx:idx]=[' '.join(focus),'']
    corrected=[r['segment_id'] for r in reviewed if r['corrected_seeds']]
    regressed=[r['segment_id'] for r in reviewed if r['regressed_seeds']]
    still=[r['segment_id'] for r in reviewed if r['wrong_seed_count'][C]==3]
    idx=lines.index('## Ejecución y reproducción')
    lines[idx:idx]=[f'Entre los casos revisados, se corrige en alguna semilla: {", ".join(corrected) or "ninguno"}. Aparecen errores en semillas antes correctas: {", ".join(regressed) or "ninguno"}. Permanecen erróneos en las tres semillas {len(still)}/20: {", ".join(still) or "ninguno"}. Estas transiciones no invalidan las referencias ni prueban que el problema sea únicamente de pesos.','']
    ratio=abs(mean)/sd if sd else None
    lines[0]=lines[0].replace('** '+status.capitalize(),'** '+('Sí, descriptivamente. ' if wins==3 else 'No. ')+status.capitalize())
    lines.insert(2,f'La magnitud de la diferencia media equivale a {ratio:.3f} veces su DE entre semillas.' if ratio is not None else 'La DE entre semillas es cero.')
    lines.insert(3,'La semilla 43 queda prácticamente empatada (Δ −0,000058 F1); su signo diminuto no debe interpretarse como un retroceso robusto. El balance desfavorable procede principalmente de la semilla 42. Las tres diferencias negativas describen estas ejecuciones, sin probar generalización.')
    lines.insert(lines.index('```powershell')+1,"$env:PYTORCH_CUDA_ALLOC_CONF='backend:cudaMallocAsync'")
    lines.insert(lines.index('outputs/venv-ml/Scripts/python.exe -u scripts/report_beto_class_weights_v2.py'),'outputs/venv-ml/Scripts/python.exe -u scripts/check_beto_class_weights_resume_v2.py')
    lines += ['', 'Incidencia de ejecución: la primera trayectoria s42/fold-1 se interrumpió por falta de memoria CUDA antes de completar una época y sin estado reanudable. Se reinició esa misma combinación, base y semilla usando el asignador cudaMallocAsync; no se modificó la receta matemática. El registro está en artifacts/beto-v2/class-weights/runtime.json. Se distinguen nueve trayectorias experimentales completas y un intento inicial fallido de la primera, sin añadir una décima combinación.']
    lines += ['', 'Además, s43/fold-1 se interrumpió durante la escritura del estado de época 2, sin traceback que permita establecer la causa. El checkpoint y temporal incompletos se preservaron en interrupted-after-epoch-1/ y se reanudó desde el estado completo de época 1, repitiendo únicamente el trabajo no confirmado. Las actualizaciones de la tabla son las de las trayectorias guardadas; el trabajo perdido por interrupciones no se presenta como una ejecución adicional independiente.']
    diagnostic=report['resume_diagnostic']
    lines += ['',f'La comprobación adicional de reanudación detectó {diagnostic["parameters"]["different_tensors"]} tensores con diferencias, con máximo absoluto {diagnostic["parameters"]["max_abs_difference"]:.9f}. La inferencia de la época 2 antes/después de repetirla cambió {diagnostic["predictions"]["changed_prediction_count"]} predicciones de {len(p["folds"][0]["validation"])}. No se garantiza reproducción bit a bit en CUDA; no se cambia la trayectoria elegida ni la regla de checkpoint después de este diagnóstico. Esta limitación es especialmente pertinente para diferencias próximas a cero, como la semilla 43. El diagnóstico es solo inferencia y no consume entrenamientos nuevos.']
    text='\n'.join(lines)+'\n';path=ROOT/'docs/beto-v2/06-pesos-clase.md'
    persist(WART/'report.json',report);persist(WART/'conclusions.json',conclusions);persist(WOUT/'errors.json',errors);persist(WOUT/'reviewed-cases.json',reviewed)
    if path.exists():assert path.read_text(encoding='utf-8')==text
    else:path.write_text(text,encoding='utf-8')
    print(json.dumps(conclusions,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
