"""Verify aligned predictions and build the Spanish evidence report after all six runs."""
from collections import Counter
from datetime import datetime,timezone
from statistics import mean
from run_beto_first_training_v2 import *

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(v).replace('|','/') for v in r)+' |' for r in rows])

def main():
    p,byid=inputs();data=read(OUT/'canonical-dataset.json');rows=data['items']
    results={};baseline={};checks=[];paired=[];predictions=[]
    for f in p['folds']:
        val=[byid[i] for i in f['validation']]
        for condition in ['A','B']:
            key=f['id']+'-'+condition;folder=OUT/'runs'/key
            result=read(folder/'result.json');base=read(folder/'baselines.json')
            assert result['status']=='complete' and result['protocol_hash']==fingerprint(p)
            assert len(result['history'])==4 and result['reload_predictions_identical']
            assert [r['segment_id'] for r in result['predictions']]==f['validation']
            assert [r['segment_id'] for r in base['predictions']]==f['validation']
            train=[byid[i] for i in f['train_'+condition]];validate(train,val)
            pred=[r['predicted'] for r in result['predictions']]
            for truth,record in zip(val,result['predictions']):
                assert record['truth']==truth['label'] and record['text_sha256']==truth['text_sha256'] and record['family_id']==truth['family_id']
            assert result['metrics']==subsets(val,pred)
            for method in ['tfidf','majority']:
                assert base[method]==subsets(val,[r[method] for r in base['predictions']])
            assert result['best_epoch']==max(range(1,5),key=lambda i:result['history'][i-1]['f1_macro'])
            checkpoint=folder/f"checkpoint-{result['best_epoch']}"
            for name,h in result['checkpoint_hashes'].items():assert filehash(checkpoint/name)==h
            assert all(len(result['metrics'][s]['per_class'])==7 for s in ['combined','historical','new_AI'])
            results[key]=result;baseline[key]=base
            predictions += [{'fold':f['id'],'condition':condition,**r,'tfidf':b['tfidf'],'majority':b['majority']} for r,b in zip(result['predictions'],base['predictions'])]
        a=results[f['id']+'-A']['predictions'];b=results[f['id']+'-B']['predictions']
        for ar,br in zip(a,b):
            if ar['predicted']!=br['predicted']:
                status='corrected' if br['predicted']==br['truth'] else 'regression' if ar['predicted']==ar['truth'] else 'different_error'
                paired.append({'fold':f['id'],'segment_id':ar['segment_id'],'family_id':ar['family_id'],'role':ar['role'],'truth':ar['truth'],'A':ar['predicted'],'B':br['predicted'],'status':status,'text_sha256':ar['text_sha256']})
    assert len({i for f in p['folds'] for i in f['validation']})==len(rows)
    assert sum(len(f['validation']) for f in p['folds'])==len(rows)
    checks=['Six complete BETO fits, four epochs each; seed42; no extra hyperparameter trials','All canonical rows validated once across three disjoint held family sets','Each A/B train includes seven classes; all held families excluded','Prediction IDs/truth/hashes align across A/B/TF-IDF/majority','Seven-class metrics recalculated from segment predictions, for each subset','Selected epoch obeys frozen max combined F1, earliest tie rule','Saved model/tokenizer files match recorded hashes; fresh reload predictions identical','Frozen dataset, guides, source code, package versions and public base hashes unchanged']
    averages={subset:{condition:mean(results[f['id']+'-'+condition]['metrics'][subset]['f1_macro'] for f in p['folds']) for condition in ['A','B']} for subset in ['combined','historical','new_AI']}
    delta=averages['combined']['B']-averages['combined']['A']
    report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'status':'complete','full_beto_fits':6,'protocol_sha256':filehash(ART/'protocol.json'),'mean_f1_macro':averages,'combined_mean_delta_B_minus_A':delta,'seconds_beto':sum(r['seconds'] for r in results.values()),'seconds_baselines':sum(r['seconds'] for r in baseline.values()),'checks':checks,'folds':[{**f,'results':{c:results[f['id']+'-'+c] for c in ['A','B']},'baselines':{c:baseline[f['id']+'-'+c] for c in ['A','B']}} for f in p['folds']],'paired_change_counts':dict(Counter(r['status'] for r in paired)),'decision':'positive_exploratory_signal_confirm_other_seeds' if delta>0 else 'no_improvement_investigate_specific_validation_errors'}
    save(ART/'report.json',report);save(ART/'verification.json',{'status':'passed','checks':checks})
    save(OUT/'paired-errors.json',{'items':paired})
    import csv
    with (OUT/'predictions-by-segment.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(predictions[0]));writer.writeheader();writer.writerows(predictions)
    families=read(ART/'families.json')['works'];ann=read(ART/'annotation-summary.json')
    candidates=[json.loads(s) for s in (ROOT/'outputs/beto-v2/pilot/annotation-candidates-final.jsonl').read_text(encoding='utf-8').splitlines()]
    active={r['segment_id'] for r in rows};pending_ids={r['segment_id'] for r in data['pending']}
    inactive_ids=set()
    for relation in data['relations']:
        if relation.get('candidate_active'):inactive_ids.add(relation['other_id'])
        if relation.get('other_active'):inactive_ids.add(relation['candidate_id'])
    role_index=[]
    for r in candidates:
        sid=r['segment_id']
        role='new_AI_active' if sid in active else 'pending_ambiguity' if sid in pending_ids else 'inactive_alternative' if sid in inactive_ids else 'pending_extraction' if r['quality_flags'] else 'pending_annotation'
        role_index.append({'segment_id':sid,'source_id':r['source_id'],'family_id':families.get(r['source_id'],{}).get('family_id',r['family_id']),'role':role,'active':sid in active,'original_reference':'outputs/beto-v2/pilot/annotation-candidates-final.jsonl','quality_flags':r['quality_flags']})
    assert sum(r['active'] for r in role_index)==49
    save(ART/'canonical-role-index.json',{'items':role_index,'counts':dict(Counter(r['role'] for r in role_index)),'historical_pending_reference':'outputs/beto-v2/first-training/canonical-dataset.json#pending','historical_evaluations':data['historical_evaluations'],'reserved_final':data['reserved_final'],'prior_version_relationships':data['relations']})
    prior_manifest=read(ROOT/'artifacts/beto-v2/pilot/delivery-manifest.json')['outputs_sha256']
    prior_files={path:h for path,h in prior_manifest.items() if '/cache/' in path or path.endswith(('pilot-annotated.json','annotation-input.json','pass-a.json','pass-b.json','adjudication.json'))}
    assert len(prior_files)==65 and all(filehash(ROOT/path)==h for path,h in prior_files.items())
    save(ART/'prior-pilot-integrity.json',{'status':'unchanged','files_checked':65,'original_cache_entries':60,'input_manifest':'artifacts/beto-v2/pilot/delivery-manifest.json','sha256':filehash(ROOT/'artifacts/beto-v2/pilot/delivery-manifest.json')})
    lines=['# BETO v2: primera comparación controlada por familias','',f"Fecha UTC: {report['created_at_utc']}. **Se completaron seis entrenamientos BETO: A/B × tres folds, semilla42, cuatro épocas por ejecución.** F1 macro medio conjunto: A **{averages['combined']['A']:.6f}**, B **{averages['combined']['B']:.6f}**, diferencia B−A **{delta:+.6f}**. Son resultados exploratorios de desarrollo; una semilla y pocos folds no demuestran un modelo óptimo.",'','## Datos y anotaciones','',
    'Se reutilizaron las adquisiciones, los29 aceptados del piloto y sus60 cachés originales. Se seleccionaron23 pasajes adicionales de cinco obras legibles ya adquiridas: S01/S03/S06/S10/S15. No se adquirieron fuentes nuevas. Dos contextos aislados del mismo GPT-6 en Codex produjeron23 propuestas cada uno; no se expusieron otras etiquetas ni predicciones. No hay independencia entre modelos ni validación de expertos. Se guardaron46 cachés nuevos con hash de texto/contexto/guía/configuración/pasada; ninguna clave coincidía con cachés anteriores.',
    '',f"Acuerdo de clase: {ann['class_agreement']}/23; acuerdo sobre ambigüedad: {ann['ambiguity_agreement']}/23. La adjudicación semántica revisó también los acuerdos: **20 aceptados adicionales y3 pendientes**, que se suman a29 aceptados y1 pendiente del piloto. Los dos nuevos ejemplos R2 desarrollan cambio ideológico gaditano y traslado de soberanía del rey a la nación, ambos en S01. No se forzó el pasaje mixto de desembarco/Cádiz para llenar cuotas.",
    '', 'Pendientes adicionales: `S01-seg0007-s01472` (ritual colonial/innovación constitucional), `S06-seg0008-s00000` (desembarco/crisis liberal), `S10-seg0015-s00645` (datación de planteamientos frente a reediciones). Se resolvió `S01-seg0007-s05495` como R5 por la reutilización efectiva del ritual en1825, conservando R1 como alternativa. Evidencia literal, offsets, pasadas y fundamentos individuales: `outputs/beto-v2/first-training/adjudication.json`.',
    '', '## Vista canónica y compatibilidad','',
    '**542 históricos elegibles +49 nuevos aceptados por IA =591 filas activas.** Se usa exclusivamente el train del snapshot revisado v4 como población histórica; sus correcciones previas y seis cuarentenas permanecen archivadas. De613 filas train, se excluyeron69 de una transcripción cuya obra no está identificada y dos duplicados (uno normalizado, otro casi idéntico). No se concatenaron18 snapshots, controles inválidos ni muestras de mantenimiento.',
    '', 'Las dos guías mantienen taxonomía, periodo y dominancia. La guía v2 hace explícitos metahistoriografía, instituciones/proyectos y extracción pendiente. Se conserva la resolución v4 de estas fronteras; ninguna etiqueta se cambió para favorecer resultados de esta comparación. La pauta histórica de120–250 palabras y las unidades completas breves v2 difieren: se registra este cambio de longitud como límite. La calidad y anotación histórica se heredan del snapshot revisado, sin afirmar una nueva revisión experta exhaustiva. Detalle: `artifacts/beto-v2/first-training/guide-compatibility.json`.',
    '', 'Cada fila activa tiene procedencia, texto/hash, familia, etiqueta y motivo de elegibilidad. Las alternativas completas, correcciones visuales y duplicados conservan relaciones e IDs; sólo una versión entra en entrenamiento. Las filas pendientes conservan etiqueta null o razón de exclusión. `canonical-role-index.json` distingue el estado de los594 registros/versiones candidatos; los textos y colas OCR siguen en sus archivos originales. No se recuperó toda la cola OCR.',
    '', 'Val/test históricos (81/137), `external-development-v1` y `evaluation-pilot-v2` quedan como evaluaciones históricas fuera de esta comparación. No son un test externo nuevo. La reserva S04/S09/S16/V03/V04 se referencia por manifiesto; no se abrieron sus textos ni se utilizó para guía, folds o métricas.',
    '', table(['Clase','Histórico activo','Nuevo IA','Total'],[[l,sum(r['label']==l and r['role']=='historical_train' for r in rows),sum(r['label']==l and r['role']=='new_AI' for r in rows),sum(r['label']==l for r in rows)] for l in LABELS]),
    '', '## Obras, familias y particiones','',
    'Se agrupan conservadoramente Basadre/Hampe/S15, O’Phelan/Huamanga, Fonseca/Hünefeldt/S17 y los artículos navales S03/S06. Son bloques de dependencia documental, no afirmaciones de que todos sus textos sean versiones idénticas. Los demás conservan su obra completa. La independencia absoluta de documentos primarios, paráfrasis o autores no queda certificada.',
    '', table(['ID de fuente','Obra','Familia','Hist.','IA'],[[s,m['title'],m['family_id'],sum(r['source_id']==s and r['role']=='historical_train' for r in rows),sum(r['source_id']==s and r['role']=='new_AI' for r in rows)] for s,m in families.items()]),
    '', 'Regla congelada: GroupKFold3 por tamaño de familias históricas; los nuevos ejemplos ligados heredan fold. Familias exclusivamente nuevas se asignan por tamaño decreciente al fold con menos filas IA, con desempate por ID. Se verificó cobertura de siete clases en cada train. Una preparación inicial con GroupKFold sobre toda la población se rechazó porque dejaba una validación sin IA; ocurrió antes de ajustar clasificadores. Se conservó el borrador inicial y la corrección de descripción del protocolo. No se eligieron folds por desempeño.',
    '',table(['Fold','Train A','Train B','Val histórica','Val IA','Familias retenidas'],[[f['id'],len(f['train_A']),len(f['train_B']),sum(f['counts']['validation_historical'].values()),sum(f['counts']['validation_new_AI'].values()),', '.join(f['validation_families'])] for f in p['folds']]),
    '', 'Todas las familias retenidas se excluyen completamente de ambos entrenamientos, incluidos sus nuevos ejemplos. A/B, mayoría y TF-IDF predicen las mismas filas y orden. “Validación histórica” en las tablas siguientes significa filas de origen histórico retenidas del antiguo train; no se reutiliza el antiguo split val.',
    '', '## Correcciones y verificaciones del pipeline experimental','',
    'El módulo nuevo `scripts/run_beto_first_training_v2.py` rechaza train/val vacíos, clases train ausentes, etiquetas desconocidas, filas inelegibles, familias o textos cruzados; calcula métricas con siete etiquetas explícitas; valida label2id/id2label y metadatos de recarga; fija semilla antes del modelo; usa padding/truncamiento explícitos y normaliza la pérdida por el peso total de los targets del grupo efectivo. Reutiliza únicamente el helper de acumulación existente. No se modificaron los trainers de producción ni el notebook histórico.',
    '', 'El control numérico compara pérdida y gradientes contra batches físicos completos en float64, con microbatches homogéneos y grupo final incompleto. Tolerancia1e-12. Una fixture BERT pequeña verifica inicialización reproducible, guardado safetensors, recarga y mapping; logits coinciden con tolerancia1e-8 absoluta/1e-5 relativa. La primera exigencia de igualdad bit a bit detectó redondeo de1.86e-9 entre kernels, no una diferencia de etiquetas. No se contabiliza la fixture como entrenamiento BETO. En los seis modelos reales, las predicciones tras recarga son idénticas.',
    '', table(['Caso','Pérdida acumulada','Pérdida batch completo','Máx. error gradiente'],[[c['n'],f"{c['accumulated_loss']:.12f}",f"{c['full_batch_loss']:.12f}",c['max_gradient_absolute_error']] for c in read(ART/'preflight.json')['weighted_accumulation']]),
    '', '## Receta exacta y reproducibilidad','',
    f"Base pública cased `{BASE}`, revisión `{REV}`. Cada ejecución inicia desde esa base, nunca desde BETO v1 ajustado. Modelo/tokenizer se cargan offline y sus hashes se verifican. Semilla42; cuatro épocas, learning rate2e-5; microbatch2 × acumulación8 = batch efectivo16 (último grupo real más pequeño); AdamW, weight decay0.01, clipping1.0, pesos inversos por frecuencia del train de cada condición; warmup10% mínimo1 paso y descenso lineal; CUDA fp16 con GradScaler y gradient checkpointing. El scheduler avanza sólo cuando AMP aplica el paso. La misma fórmula puede producir pesos de clase y números de pasos diferentes por el tamaño A/B.",
    '', f"Longitud común384, padding fijo, truncamiento explícito con tokens especiales. En591 filas: mediana{p['token_summary']['quantiles']['p50']:.0f}, p95={p['token_summary']['quantiles']['p95']:.1f}, máximo{p['token_summary']['max']}; sólo{p['token_summary']['above_384']} exceden384, con{p['token_summary']['lost_tokens_384']} tokens totales truncados. No se hizo búsqueda de longitud o learning rate. GPU: {p['hardware']['gpu']},4GB.",
    '', 'Selección de checkpoint: mayor F1 macro conjunto de siete clases en validación, empate a favor de época más temprana; sin early stopping. Estas mismas filas seleccionan época y producen el resultado de desarrollo: no es estimación imparcial de test. El train se baraja con semilla42+época; la cabeza se inicializa con42. Reanudación por frontera de época con modelo, optimizador, scheduler, scaler y RNG Python/NumPy/CPU/CUDA; los resultados completos se reutilizan. No se hizo un entrenamiento adicional para probar una trayectoria BETO interrumpida.',
    '', 'Referencias: mayoría del train con desempate alfabético; TF-IDF de palabras1–2, min_df2, máximo50.000 características, sublinear_tf y normalización de acentos; regresión logística C4, pesos balanceados, lbfgs, máximo2.000 iteraciones, semilla42. Se ajustan referencias para A y B con sus mismos train, usando textos completos. No hay tuning en estos folds.',
    '', table(['Paquete','Versión'],p['versions'].items()),
    '', 'Los hashes completos de guías, dataset, scripts, revisión base y configuración están en `protocol.json`; los de cada checkpoint en su `result.json`. Los originales y cambios previos se conservaron.',
    '', '## Resultados: F1 macro con siete clases','']
    for subset,title in [('combined','Conjunto'),('historical','Sólo validación de origen histórico'),('new_AI','Sólo validación con nuevas etiquetas IA')]:
        metric_rows=[]
        for f in p['folds']:
            av,bv=[results[f['id']+'-'+c]['metrics'][subset]['f1_macro'] for c in ['A','B']]
            reference=[baseline[f['id']+'-'+c][method][subset]['f1_macro'] for method in ['tfidf','majority'] for c in ['A','B']]
            metric_rows.append([f['id'],f'{av:.6f}',f'{bv:.6f}',f'{bv-av:+.6f}']+[f'{v:.6f}' for v in reference])
        av,bv=[averages[subset][c] for c in ['A','B']]
        reference=[mean(baseline[f['id']+'-'+c][method][subset]['f1_macro'] for f in p['folds']) for method in ['tfidf','majority'] for c in ['A','B']]
        metric_rows.append(['Promedio',f'{av:.6f}',f'{bv:.6f}',f'{bv-av:+.6f}']+[f'{v:.6f}' for v in reference])
        lines += [f'### {title}','',table(['Fold','BETO A','BETO B','B−A','TF-IDF A','TF-IDF B','Mayoría A','Mayoría B'],metric_rows),'']
    lines += ['El promedio da igual peso a cada fold, aunque sus soportes son distintos. F1 de clases ausentes en una validación se mantiene en0; el denominador siempre es7. No se infiere exactitud histórica de la validación IA.','', '## F1 y soporte por clase','']
    for f in p['folds']:
        lines += [f"### {f['id']}",'',table(['Clase','Train A','Train B','Soporte hist.','Soporte IA','F1 A conjunto','F1 B conjunto','TF-IDF A','TF-IDF B'],[[l,f['counts']['train_A'][l],f['counts']['train_B'][l],f['counts']['validation_historical'][l],f['counts']['validation_new_AI'][l],*[f"{results[f['id']+'-'+c]['metrics']['combined']['per_class'][l]['f1-score']:.6f}" for c in ['A','B']],*[f"{baseline[f['id']+'-'+c]['tfidf']['combined']['per_class'][l]['f1-score']:.6f}" for c in ['A','B']]] for l in LABELS]),'']
    lines += ['F1, precision, recall y soporte por clase también se guardan por separado para origen histórico/IA en `artifacts/beto-v2/first-training/report.json`, junto con matrices de confusión de7×7.','', '## Diferencias por segmento y siguiente hipótesis','',f"Cambios de predicción A→B: {dict(Counter(r['status'] for r in paired))}. Archivo completo `outputs/beto-v2/first-training/paired-errors.json`; todas las predicciones, incluidos TF-IDF y mayoría: `predictions-by-segment.csv`.",'']
    chosen=[]
    for status in ['corrected','regression','different_error']:
        chosen += [r for r in paired if r['status']==status][:3]
    lines += [table(['Fold / segmento','Cambio','Verdad','A','B','Evidencia del objetivo (inicio)'],[[r['fold']+' / '+r['segment_id'],r['status'],r['truth'],r['A'],r['B'],byid[r['segment_id']]['text'][:200].replace('\n',' ')] for r in chosen]),'']
    tfidf_deltas=[baseline[f['id']+'-B']['tfidf']['combined']['f1_macro']-baseline[f['id']+'-A']['tfidf']['combined']['f1_macro'] for f in p['folds']]
    lines += [f"TF-IDF cambia su F1 macro conjunto en {', '.join(f'{v:+.6f}' for v in tfidf_deltas)} por fold (promedio {mean(tfidf_deltas):+.6f}). Este contraste usa los mismos train/val; su representación ve el texto completo y su optimización difiere de BETO.",'']
    all_pred={c:[r for f in p['folds'] for r in results[f['id']+'-'+c]['predictions']] for c in ['A','B']}
    confusion={c:Counter((r['truth'],r['predicted']) for r in all_pred[c] if r['truth']!=r['predicted']) for c in ['A','B']}
    worst=confusion['B'].most_common(4)
    lines += ['Confusiones más frecuentes de B respecto a las etiquetas conservadas (recuento conjunto de predicciones de desarrollo; no implica que esas etiquetas sean gold experto):','',table(['Etiqueta conservada → predicha','Errores A','Errores B','Ejemplos B'],[[truth+' → '+pred,confusion['A'][(truth,pred)],count,', '.join(r['segment_id'] for r in all_pred['B'] if r['truth']==truth and r['predicted']==pred)[:180]] for (truth,pred),count in worst]),'']
    if delta>0:
        lines += ['B mejora el promedio exploratorio. El siguiente paso propuesto es confirmar la diferencia con otras semillas sobre estos folds congelados y ampliar anotación diversa, especialmente ideas/antecedentes en otras obras; no se ejecutaron esas semillas. Revisar también regresiones y heterogeneidad entre familias antes de atribuir una mejora general a los datos nuevos.']
    else:
        lines += ['B no mejora el promedio exploratorio. La siguiente hipótesis es que BETO no aprovecha de forma estable este lote pequeño bajo una sola trayectoria de optimización y ponderación: conviene contrastar las regresiones y confusiones listadas por familia antes de ampliar datos. Los dos ejemplos nuevos de ideas pertenecen a S01 y quedan completamente fuera del entrenamiento del fold que retiene S01, por lo que esta carencia sigue casi intacta. No cambiar etiquetas para acomodarlas al modelo.']
        if all(v>0 for v in tfidf_deltas):
            lines += ['Como TF-IDF sí mejora en los tres folds, estos resultados no justifican declarar inútil el lote nuevo. El contraste sugiere comprobar estabilidad de BETO entre semillas y localizar errores de frontera persistentes, manteniendo congelados datos y folds; esas nuevas ejecuciones requieren una fase posterior y no se realizaron aquí.']
    lines += ['', 'La señal no separa aumento de datos de cambios en pesos de clase, número de actualizaciones y mezcla de longitudes. No se evaluó un test reservado, ejecutó Optuna, DAPT ni despliegue.','', '## Tiempos, comandos y entregables','',table(['Ejecución','Época seleccionada','Tiempo BETO (s)','F1 conjunto seleccionado'],[[k,r['best_epoch'],f"{r['seconds']:.2f}",f"{r['metrics']['combined']['f1_macro']:.6f}"] for k,r in results.items()]),'',f"Tiempo acumulado BETO: {report['seconds_beto']:.2f}s ({report['seconds_beto']/60:.1f}min); referencias: {report['seconds_baselines']:.2f}s. El tiempo BETO incluye entrenamiento, validación y guardados por época; excluye preparación/anotación y la última recarga de verificación.",'','Para reanudar una interrupción o comprobar/reutilizar ejecuciones completas (mismas versiones y caché base):','','```powershell','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_first_training_v2.py run','```','','La preparación ya ejecutada y el informe rechazan sobrescribir evidencia. En un workspace limpio con las entradas conservadas, el orden de reproducción es:','','```powershell','outputs/venv-ml/Scripts/python.exe scripts/prepare_beto_first_training_v2.py','# Reutilizar pass-a.json/pass-b.json y sus cachés; no repetir anotaciones idénticas.','outputs/venv-ml/Scripts/python.exe scripts/check_beto_first_training_v2.py','outputs/venv-ml/Scripts/python.exe scripts/freeze_beto_first_training_v2.py','outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_first_training_v2.py run','outputs/venv-ml/Scripts/python.exe scripts/report_beto_first_training_v2.py','```','','No lanzar ahora una segunda campaña de seis fits: el presupuesto inicial ya quedó consumido. El runner omite resultados completos. Para trasladar a otro entorno GPU se necesitan los archivos originales/de procedencia, los scripts y versiones del protocolo, y la caché base fijada por revisión; no se iniciaron servicios de pago.','','- `outputs/beto-v2/first-training/`: entrada, pasadas, adjudicación, cachés, vista canónica, predicciones y checkpoints/reanudación.','- `artifacts/beto-v2/first-training/`: protocolo, familias, compatibilidad de guías, preflight, tokens, métricas y verificación.','- Los archivos de las fases01–03 y las bitácoras de decisiones anteriores se mantienen intactos; `journal.jsonl` añade los hechos de esta fase.','']
    text='\n'.join(lines)
    import re
    # Add prose spacing without touching filenames, labels, IDs or code.
    for word in ['los','sus','produjeron','guardaron','seleccionaron','aceptados','y','de','con','en','versión','snapshot','paso','semilla','épocas','rate','microbatch','acumulación','batch','decay','clipping','warmup','máximo','mínimo','longitud','común','filas','mediana','p95=','microbatches','Tolerancia','tolerancia','GPU','lr','min_df','C','regresión','palabras']:
        text=re.sub(r'\b'+re.escape(word)+r'(?=\d)',word+' ',text)
    for a,b in [('GroupKFold3','GroupKFold 3'),('denominador siempre es7','denominador siempre es 7'),('con7×7','con 7×7'),('de7×7','de 7×7'),('de1.86','de 1.86'),('absoluta/1e-5','absoluta / 1e-5'),('desde1860','desde 1860'),('máximo50.000','máximo 50.000'),('sólo3','sólo 3'),('con94','con 94'),('4GB','4 GB')]:text=text.replace(a,b)
    (ROOT/'docs/beto-v2/04-primer-entrenamiento.md').write_text(text,encoding='utf-8')
    journal=[{'at':p['created_at_utc'],'event':'protocol_frozen','evidence':'protocol.json','no_reserved_text_read':True},{'at':report['created_at_utc'],'event':'six_fits_completed_verified','mean_delta':delta,'evidence':'report.json','production_modified':False}]
    with (ART/'journal.jsonl').open('x',encoding='utf-8') as f:
        for r in journal:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    save(ART/'delivery-manifest.json',{'created_at_utc':report['created_at_utc'],'files':{path.relative_to(ROOT).as_posix():filehash(path) for path in list(ART.glob('*'))+[ROOT/'docs/beto-v2/04-primer-entrenamiento.md',ROOT/'scripts/report_beto_first_training_v2.py',OUT/'predictions-by-segment.csv',OUT/'paired-errors.json'] if path.is_file()}})
    print(json.dumps({'mean_f1':averages,'delta':delta,'seconds':report['seconds_beto'],'verification':'passed'},ensure_ascii=False))

if __name__=='__main__':main()
