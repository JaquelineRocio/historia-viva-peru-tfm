"""Paired descriptive stability analysis of the frozen development folds; no fitting."""
import csv
import statistics as stats
from collections import Counter, defaultdict
from run_beto_first_training_v2 import *

SOUT=ROOT/'outputs/beto-v2/stability'
SART=ROOT/'artifacts/beto-v2/stability'
SEEDS=(42,43,44)

def dispersion(values):
    return {'values':values,'mean':stats.mean(values),'sample_sd':stats.stdev(values),
            'min':min(values),'max':max(values),'range':max(values)-min(values)}

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(x) for x in row)+' |' for row in rows])

def result_path(seed,fold,condition):
    return (OUT/'runs' if seed==42 else SOUT/f'seed-{seed}')/(fold+'-'+condition)

def main():
    p,byid=inputs();manifest=read(SART/'protocol.json')
    assert filehash(ROOT/'artifacts/beto-v2/stability/runner-stability-original.py')==manifest['runner_sha256']
    runs={}; flat=[]; paired=[]; verification={}
    for seed in SEEDS:
        for fold in p['folds']:
            val=[byid[i] for i in fold['validation']]
            for c in ('A','B'):
                dest=result_path(seed,fold['id'],c)
                config=p if seed==42 else read(dest/'config.json')
                if seed!=42:
                    assert config=={**p,'execution':{'seed':seed,'fold':fold['id'],'condition':c,
                        'train_rows_hash':fingerprint([byid[i] for i in fold['train_'+c]]),
                        'validation_rows_hash':fingerprint(val),'stability_manifest_hash':fingerprint(manifest)}}
                r=verify_result(dest,config,val);runs[seed,fold['id'],c]=r
                reference=runs[42,fold['id'],c]
                for field in ('class_weights','steps_per_epoch','warmup_steps'):
                    assert r[field]==reference[field],(seed,fold['id'],c,field)
                assert len(r['history'])==4 and [h['epoch'] for h in r['history']]==[1,2,3,4]
                assert all(h['optimizer_updates']+h['amp_skips']==r['steps_per_epoch'] for h in r['history'])
                assert r['best_epoch']==max(r['history'],key=lambda h:h['f1_macro'])['epoch']
                assert r['metrics']['combined']==r['history'][r['best_epoch']-1]['metrics']['combined']
                verification[f'{seed}-{fold["id"]}-{c}']={'result_sha256':filehash(dest/'result.json'),
                    'config_hash':fingerprint(config),'best_epoch':r['best_epoch'],
                    'amp_skips':sum(h['amp_skips'] for h in r['history']),
                    'optimizer_updates':sum(h['optimizer_updates'] for h in r['history']),
                    'seconds':r['seconds'],'checkpoint_hashes':r['checkpoint_hashes']}
                for pred in r['predictions']:flat.append({'seed':seed,'fold':fold['id'],'condition':c,**pred})
            old=OUT/'runs'/(fold['id']+'-A')/'baselines.json'
            for c in ('A','B'):
                bpath=OUT/'runs'/(fold['id']+'-'+c)/'baselines.json'
                assert filehash(bpath)==manifest['baseline_hashes'][fold['id']+'-'+c]
                b=read(bpath)
                assert [v['segment_id'] for v in b['predictions']]==fold['validation']
                assert b['tfidf']==subsets(val,[v['tfidf'] for v in b['predictions']])
            a=runs[seed,fold['id'],'A'];b=runs[seed,fold['id'],'B']
            paired.append({'seed':seed,'fold':fold['id'],'subsets':{s:{'A':a['metrics'][s],
                'B':b['metrics'][s],'difference':b['metrics'][s]['f1_macro']-a['metrics'][s]['f1_macro']} for s in ('combined','historical','new_AI')}})
    summaries={}
    for subset in ('combined','historical','new_AI'):
        per_seed=[]
        for seed in SEEDS:
            selected=[r['subsets'][subset] for r in paired if r['seed']==seed]
            a=stats.mean(r['A']['f1_macro'] for r in selected);b=stats.mean(r['B']['f1_macro'] for r in selected)
            per_seed.append({'seed':seed,'A':a,'B':b,'difference':b-a})
        summaries[subset]={'per_seed':per_seed,**{k:dispersion([r[k] for r in per_seed]) for k in ('A','B','difference')},
                           'seeds_favoring_B':sum(r['difference']>0 for r in per_seed)}
    classes=[];folds=[]
    for fold in p['folds']:
        items=[x for x in paired if x['fold']==fold['id']]
        ds=[x['subsets']['combined']['difference'] for x in items]
        folds.append({'fold':fold['id'],'families':fold['held_out_families'] if 'held_out_families' in fold else sorted({byid[i]['family_id'] for i in fold['validation']}),
                      'difference_across_seeds':dispersion(ds),'seeds_favoring_B':sum(d>0 for d in ds)})
        for label in LABELS:
            ds=[x['subsets']['combined']['B']['per_class'][label]['f1-score']-x['subsets']['combined']['A']['per_class'][label]['f1-score'] for x in items]
            classes.append({'fold':fold['id'],'label':label,'differences':dispersion(ds),
                'B_wins':sum(d>0 for d in ds),'B_losses':sum(d<0 for d in ds),
                'support':{s:items[0]['subsets'][s]['A']['per_class'][label]['support'] for s in ('combined','historical','new_AI')}})
    class_summary=[]
    for label in LABELS:
        ds=[stats.mean(r['differences']['values'][i] for r in classes if r['label']==label) for i in range(3)]
        class_summary.append({'label':label,'paired_fold_mean_difference':dispersion(ds),'B_wins':sum(d>0 for d in ds),'B_losses':sum(d<0 for d in ds)})
    # Family metrics remain descriptive strata, never additional independent replicates.
    families=[]
    for family in sorted({r['family_id'] for r in byid.values()}):
        for seed in SEEDS:
            result={}
            for c in ('A','B'):
                vals=[r for r in flat if r['seed']==seed and r['condition']==c and r['family_id']==family]
                result[c]=subsets([byid[r['segment_id']] for r in vals],[r['predicted'] for r in vals])
            families.append({'family':family,'seed':seed,**result,'difference':result['B']['combined']['f1_macro']-result['A']['combined']['f1_macro']})
    lookup={(r['segment_id'],r['seed'],r['condition']):r['predicted'] for r in flat}
    errors=[];transitions=[]
    for seed in SEEDS:
        counts=Counter()
        for sid,row in byid.items():
            a=lookup[sid,seed,'A'];b=lookup[sid,seed,'B'];truth=row['label']
            counts['corrected' if a!=truth and b==truth else 'regression' if a==truth and b!=truth else 'both_correct' if a==truth else 'same_error' if a==b else 'different_error']+=1
        transitions.append({'seed':seed,**counts})
    for sid,row in byid.items():
        preds={c:{str(s):lookup[sid,s,c] for s in SEEDS} for c in ('A','B')}
        wrong={c:sum(v!=row['label'] for v in preds[c].values()) for c in ('A','B')}
        if max(wrong.values())<2:continue
        errors.append({'segment_id':sid,'truth':row['label'],'family_id':row['family_id'],'source_id':row['source_id'],
                       'role':row['role'],'text':row['text'],'provenance':row.get('provenance'),
                       'context':row.get('context'),'pages':row.get('pages_exact',row.get('pages')),
                       'predictions':preds,'wrong_seed_count':wrong})
    errors.sort(key=lambda r:(-r['wrong_seed_count']['B'],-r['wrong_seed_count']['A'],r['segment_id']))
    persistent_confusions=[]
    for truth in LABELS:
        for predicted in LABELS:
            if truth==predicted:continue
            item={'truth':truth,'predicted':predicted}
            for c in ('A','B'):
                item[c]={'counts_by_seed':{str(s):sum(r['truth']==truth and r['predicted']==predicted and r['seed']==s and r['condition']==c for r in flat) for s in SEEDS},
                    'same_confusion_at_least_two_seeds':sum(r['label']==truth and sum(lookup[sid,s,c]==predicted for s in SEEDS)>=2 for sid,r in byid.items()),
                    'same_confusion_all_three_seeds':sum(r['label']==truth and all(lookup[sid,s,c]==predicted for s in SEEDS) for sid,r in byid.items())}
            persistent_confusions.append(item)
    # Up to four cases in each requested boundary; deterministic diversity by reference/prediction/family.
    groups={'crisis_ideas':lambda t,ps:t==LABELS[2] or LABELS[2] in ps,
        'antecedentes_organizacion':lambda t,ps:(t==LABELS[1] and LABELS[5] in ps) or (t==LABELS[5] and LABELS[1] in ps),
        'organizacion_liderazgos':lambda t,ps:(t==LABELS[3] and LABELS[5] in ps) or (t==LABELS[5] and LABELS[3] in ps),
        'participacion_social':lambda t,ps:t==LABELS[6] or LABELS[6] in ps}
    cases=[];seen=set()
    annotation=read(OUT/'annotation-input.json')['items']
    contexts={r['segment_id']:r for r in annotation}
    for group,match in groups.items():
        candidates=[r for r in errors if r['segment_id'] not in seen and match(r['truth'],set(r['predictions']['B'].values()))]
        selected=[];strata=set()
        for r in candidates:
            stratum=(r['truth'],Counter(r['predictions']['B'].values()).most_common(1)[0][0],r['family_id'])
            if stratum not in strata:selected.append(r);strata.add(stratum)
            if len(selected)==4:break
        for r in candidates:
            if len(selected)==4:break
            if r not in selected:selected.append(r)
        for r in selected:
            seen.add(r['segment_id']);context=contexts.get(r['segment_id']) or r.get('context')
            cases.append({**r,'boundary':group,'available_annotation_context':context,
                          'context_status':'Original annotation input attached' if context else 'Canonical target and source provenance only; no adjacent passage supplied in canonical row',
                          'review_status':'Pending qualitative review; disagreement alone does not invalidate reference'})
    report={'seeds':list(SEEDS),'new_runs':12,'reused_runs':6,'sd_convention':'sample standard deviation, ddof=1; descriptive n=3 seeds',
        'paired_fold_metrics':paired,'seed_summaries':summaries,'fold_differences':folds,'class_fold_differences':classes,
        'class_summary':class_summary,'family_metrics':families,'paired_prediction_transitions':transitions,
        'persistent_error_count':len(errors),'persistent_confusions':persistent_confusions,'verification':verification,'baseline_reuse':manifest['baseline_hashes'],
        'limits':['Development rows also select epoch','Three seeds on the same three folds; not nine independent studies',
                  'A/B differ in data, class weights and update counts','AI annotations are not independent expert gold']}
    save(SART/'report.json',report);save(SOUT/'persistent-errors.json',errors);save(SOUT/'representative-cases.json',cases)
    with (SOUT/'predictions-by-seed.csv').open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    lines=['# BETO v2: estabilidad entre semillas','',
        'Se completaron 12 entrenamientos nuevos (43 y 44) y se reutilizaron los seis de la semilla 42. Las 591 filas, roles, etiquetas, guías, familias y validaciones permanecieron congelados. Cada ejecución nueva partió de BETO base en la revisión original; longitud 384, cuatro épocas y toda la receta se conservaron.','',
        'La semilla se aplica antes de inicializar el modelo y el barajado usa semilla + época. El protocolo original y su runner se conservan; la extensión registra la identidad de filas ordenadas, semilla, fold, condición, código, configuración, entradas, base y versiones. Se verificaron hashes de checkpoints, alineación de predicciones, métricas y selección de época.','',
        '## Comparaciones emparejadas','']
    for subset,title in [('combined','Conjunto'),('historical','Origen histórico'),('new_AI','Origen IA')]:
        lines += ['### '+title,'',table(['Semilla','Fold','F1 A','F1 B','B−A'],[[r['seed'],r['fold'],f"{r['subsets'][subset]['A']['f1_macro']:.6f}",f"{r['subsets'][subset]['B']['f1_macro']:.6f}",f"{r['subsets'][subset]['difference']:+.6f}"] for r in paired]),'',
            table(['Semilla','Media A (3 folds)','Media B (3 folds)','B−A'],[[r['seed'],f"{r['A']:.6f}",f"{r['B']:.6f}",f"{r['difference']:+.6f}"] for r in summaries[subset]['per_seed']]),'',
            table(['Magnitud entre semillas','Media','DE muestral','Mínimo','Máximo'],[[k,*[f"{summaries[subset][k][v]:.6f}" for v in ('mean','sample_sd','min','max')]] for k in ('A','B','difference')]),'']
    lines += ['La unidad del resumen es el promedio de los mismos tres folds por semilla, con igual peso por fold. DE muestral usa n−1, con n=3; es descriptiva. Las nueve combinaciones fold/semilla no son nueve estudios independientes. No se calculan pruebas de significación ni intervalos que supongan tal independencia.','',
        '## Heterogeneidad entre folds y familias','',table(['Fold','B−A medio entre semillas','DE entre semillas dentro del fold','Semillas B>A'],[[r['fold'],f"{r['difference_across_seeds']['mean']:+.6f}",f"{r['difference_across_seeds']['sample_sd']:.6f}",r['seeds_favoring_B']] for r in folds]),'',
        'Cada fold retiene familias distintas, con soportes y composiciones diferentes. Su heterogeneidad documental se describe por separado; no se mezcla con la DE de los promedios entre semillas. Los desgloses completos por familia y origen están en `artifacts/beto-v2/stability/report.json`, campo `family_metrics`.','',
        table(['Familia','Soporte','B−A s42','B−A s43','B−A s44'],[[family,next(r['A']['combined']['n'] for r in families if r['family']==family),*[f"{next(r['difference'] for r in families if r['family']==family and r['seed']==s):+.6f}" for s in SEEDS]] for family in sorted({r['family'] for r in families})]),'',
        '## Clases que explican la diferencia','',table(['Clase','B−A medio de F1 (folds y semillas)','DE de diferencias medias entre semillas','Semillas + / −'],[[r['label'],f"{r['paired_fold_mean_difference']['mean']:+.6f}",f"{r['paired_fold_mean_difference']['sample_sd']:.6f}",f"{r['B_wins']} / {r['B_losses']}"] for r in class_summary]),'',
        'La diferencia macro es el promedio de las siete diferencias por clase de esta tabla. Los cambios de F1 no equivalen a un balance simple de aciertos.','',
        table(['Fold','Clase','B−A medio','Semillas + / −','Soporte histórico','Soporte IA'],[[r['fold'],r['label'],f"{r['differences']['mean']:+.6f}",f"{r['B_wins']} / {r['B_losses']}",r['support']['historical'],r['support']['new_AI']] for r in classes]),'',
        'Todos los F1 macro mantienen siete clases explícitas y zero_division=0, incluidas clases sin soporte. Precisión, recall, F1, soporte y confusión 7×7 para cada semilla/fold/condición y origen están en el informe JSON.','']
    for fold in p['folds']:
        for subset in ('historical','new_AI'):
            absent=[r['label'] for r in classes if r['fold']==fold['id'] and r['support'][subset]==0]
            lines.append(f"- {fold['id']} / {subset}: clases ausentes: {', '.join(absent) or 'ninguna'}.")
    lines += ['','## Errores persistentes','',table(['Semilla','Corrige B','Introduce B','Error igual','Error distinto'],[[r['seed'],r.get('corrected',0),r.get('regression',0),r.get('same_error',0),r.get('different_error',0)] for r in transitions]),'',
        f'Se identificaron {len(errors)} filas erróneas en al menos dos semillas de A o B. El inventario conserva todas ellas en `persistent-errors.json`; `representative-cases.json` contiene {len(cases)} casos, hasta cuatro por frontera solicitada, priorizando persistencia y diversidad de familia/referencia/predicción. La selección es descriptiva y no estima prevalencia. Se conserva el texto completo, procedencia, contexto de anotación disponible y las seis predicciones. Ninguna etiqueta se modifica.','',
        '## Ejecuciones y reanudación','',table(['Semilla/fold/condición','Época','Actualizaciones','Omisiones AMP','Segundos'],[[k,v['best_epoch'],v['optimizer_updates'],v['amp_skips'],f"{v['seconds']:.2f}"] for k,v in verification.items()]),'',
        'Se conservaron resultados desfavorables, curvas, checkpoints y estados de modelo/optimizador/scheduler/scaler/RNG por frontera de época. Las referencias TF-IDF y mayoría se reutilizaron con hashes y métricas comprobados; sus datos y configuración no cambiaron.','',
        '```powershell','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_first_training_v2.py run --seed 43','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_first_training_v2.py run --seed 44','```','',
        'Estos comandos verifican y omiten ejecuciones completas; reanudan las incompletas desde la última frontera de época. El generador del informe (`scripts/report_beto_stability_v2.py`) no entrena y rechaza sobrescribir sus resultados.','',
        'Son métricas de desarrollo que también seleccionan época, no una evaluación final independiente. A/B cambian contenido, pesos por clase y número de actualizaciones: no se atribuye la diferencia exclusivamente al contenido añadido. No se abrió la reserva ni se ejecutaron Optuna, DAPT o despliegue; producción permanece fuera de esta fase.','']
    (ROOT/'docs/beto-v2/05-estabilidad.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'summaries':summaries,'class_summary':class_summary,'cases':[r['segment_id'] for r in cases]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
