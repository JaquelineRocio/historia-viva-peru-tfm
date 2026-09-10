"""Paired seven-class development evaluation; no model fitting or selection changes."""
import csv
import json
import statistics as stats
from pathlib import Path
import run_beto_first_training_v2 as b
from prepare_beto_context_v2 import ART,OUT
from run_beto_context_v2 import control,save_same

def report():
    p,byid=b.inputs();man=b.read(ART/'manifest.json');mi={m['segment_id']:m for m in man['items']}
    cp=b.read(ART/'protocol.json');gate=b.read(ART/'pilot-gate.json') if (ART/'pilot-gate.json').exists() else None
    reviewed={r['segment_id'] for r in b.read(b.ROOT/'outputs/beto-v2/stability/reviewed-cases.json')}
    results=[];predictions=[];errors=[];classes=[];hashes={}
    for seed in [42,43,44]:
        for f in p['folds']:
            dest=OUT/f'seed-{seed}'/(f['id']+'-B_context')
            if not (dest/'result.json').exists():continue
            val=[byid[i] for i in f['validation']]
            result=b.verify_result(dest,b.read(dest/'config.json'),val);base=control(seed,f,p,val)
            hashes[str((dest/'result.json').relative_to(b.ROOT))]=b.filehash(dest/'result.json')
            bp=[r['predicted'] for r in base['predictions']];xp=[r['predicted'] for r in result['predictions']]
            subsets={}
            for origin,role in [('combined',None),('historical','historical_train'),('new_AI','new_AI')]:
                for group,changed in [('all',None),('context_incorporated',True),('unchanged_input',False)]:
                    indices=[i for i,r in enumerate(val) if (role is None or r['role']==role) and (changed is None or mi[r['segment_id']]['changed']==changed)]
                    metrics={name:b.metrics([val[i] for i in indices],[pred[i] for i in indices]) for name,pred in [('B',bp),('B_context',xp)]}
                    delta=metrics['B_context']['f1_macro']-metrics['B']['f1_macro'] if indices else None
                    subsets[origin+'/'+group]={'n':len(indices),**metrics,'delta':delta}
                    for condition,value in metrics.items():
                        for label,v in value['per_class'].items():
                            classes.append({'seed':seed,'fold':f['id'],'origin':origin,'group':group,'condition':condition,'label':label,**v})
            results.append({'seed':seed,'fold':f['id'],'best_epoch':result['best_epoch'],'subsets':subsets,
                            'amp_skips':sum(h['amp_skips'] for h in result['history']),
                            'B_amp_skips':sum(h['amp_skips'] for h in base['history']),
                            'optimizer_updates':sum(h['optimizer_updates'] for h in result['history']),
                            'B_optimizer_updates':sum(h['optimizer_updates'] for h in base['history']),
                            'seconds':result['seconds']})
            for r,a,z in zip(val,bp,xp):
                item={k:r[k] for k in ['segment_id','family_id','role','label']}
                item.update(seed=seed,fold=f['id'],changed=mi[r['segment_id']]['changed'],B=a,B_context=z,previously_reviewed=r['segment_id'] in reviewed)
                predictions.append(item)
                if a!=r['label'] or z!=r['label'] or item['previously_reviewed']:
                    kind='corrected' if a!=r['label'] and z==r['label'] else 'introduced' if a==r['label'] and z!=r['label'] else 'both_correct' if z==r['label'] else 'both_wrong'
                    errors.append({**item,'kind':kind})
    summaries=[]
    for seed in sorted({r['seed'] for r in results}):
        runs=[r for r in results if r['seed']==seed]
        assert len(runs)==3,'Incomplete seed: do not report a partial fold average'
        means={key:{field:stats.mean(r['subsets'][key][field]['f1_macro'] for r in runs) for field in ['B','B_context']}
               for key in runs[0]['subsets'] if all(r['subsets'][key]['n'] for r in runs)}
        for v in means.values():v['delta']=v['B_context']-v['B']
        summaries.append({'seed':seed,'means':means})
    dispersion={}
    if len(summaries)==3:
        for key in set.intersection(*[set(s['means']) for s in summaries]):
            dispersion[key]={field:{'mean':stats.mean(s['means'][key][field] for s in summaries),'sample_std':stats.stdev(s['means'][key][field] for s in summaries)} for field in ['B','B_context','delta']}
    events=[json.loads(s) for s in (OUT/'execution-events.jsonl').read_text(encoding='utf-8').splitlines()] if (OUT/'execution-events.jsonl').exists() else []
    payload={'condition':'B_context','reference':'B','development_only':True,'coverage':man['coverage'],'changed_inputs':sum(m['changed'] for m in mi.values()),
             'completed_runs':len(results),'pilot_gate':gate,'runs':results,'seed_means':summaries,'between_seed_summary':dispersion,
             'errors':errors,'execution_events':events,'result_hashes':hashes,'protocol_sha256':b.filehash(ART/'protocol.json'),
             'manifest_sha256':b.filehash(ART/'manifest.json'),'interpretation':'Same validation selects epoch; no independent final evaluation. Nine runs, if present, summarized as three seeds, not nine independent studies.'}
    save_same(ART/'report.json',payload);save_same(OUT/'paired-predictions.json',predictions)
    save_same(OUT/'error-transitions.json',errors)
    for name,records in [('per-class.csv',classes),('paired-predictions.csv',predictions)]:
        if not records:continue
        import io
        buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
        path=OUT/name;data=buf.getvalue().encode('utf-8')
        if path.exists():assert path.read_bytes()==data
        else:path.write_bytes(data)
    write_markdown(payload,man,predictions)
    print(json.dumps({'completed_runs':len(results),'seed_means':summaries,'gate':gate},ensure_ascii=True),flush=True)

def write_markdown(r,man,predictions):
    n=r['changed_inputs'];seeds=r['seed_means']
    delta=stats.mean(s['means']['combined/all']['delta'] for s in seeds) if seeds else None
    verdict=('mejoró' if delta>0 else 'empeoró' if delta<0 else 'empató') if delta is not None else 'no se pudo evaluar'
    lines=[f'**Cambiaron realmente {n}/591 entradas ({n/591:.1%}); el desempeño {verdict}'+(f': Δ F1 macro combinado B_context−B = {delta:+.6f}.' if delta is not None else '.' )+'**','',
           'B permanece como referencia. La hipótesis B_weights_A queda cerrada según la fase 06; no se reabrió ni se alteraron sus ejecuciones.','',
           '## Intervención y procedencia','',
           'Se conservaron las 591 unidades, textos objetivo, etiquetas, familias, folds y orden de filas. Se reutilizaron 20 originales locales, sin descargas de internet ni OCR adicional. Los contextos archivados tuvieron prioridad. Para los históricos se exigió una coincidencia completa y única del objetivo tras normalización NFKD, minúsculas y caracteres alfanuméricos; esa normalización solo localiza, no modifica el objetivo. Se tomó el prefijo anterior del bloque o el bloque textual inmediatamente anterior. Se rechazaron límites ambiguos de cabeceras, notas, cambio de página y coincidencias ausentes.','',
           'La primera comprobación mecánica se conserva con sufijo `preqa`. Antes de entrenar se descartaron cabeceras y límites dudosos; el manifiesto final se congeló después. La muestra reproducible usa SHA256 de `alignment-audit-v1:` + ID, una fila por fuente y las diez primeras por hash. Se cotejaron sus diez páginas: los diez antecedentes y sus límites son correctos. La fila historical-v4-0339 conserva una continuación auténtica de nota bibliográfica y sus defectos heredados. No se seleccionó la muestra por predicciones ni etiquetas.','',
           'La entrada tiene `[CLS] objetivo [SEP] contexto [SEP]`: los mismos tokens objetivo de B, más los últimos min(95, espacio disponible) tokens del pasaje anterior. Máximo 384 con especiales; segmento objetivo 0, contexto y separador final 1; padding con máscara 0 y tipo 0. Si no cabe un token adicional con su separador o falta contexto, los tres vectores reproducen B exactamente.','',
           'El manifiesto registra ID, fuente, hash del PDF, familia, fold, localización en extracción/archivo, tokens efectivamente incorporados, motivo de ausencia y hashes de ambos conjuntos de vectores. La etiqueta no entra en los vectores. Cada fuente conserva una única familia y fold de validación; los controles excluidos y las fuentes reservadas no se usaron como documentos de recuperación. El contenido reservado permaneció cerrado.','',
           '## Cobertura: encontrado frente a incorporado','']
    for field,groups in man['coverage'].items():
        lines += [f'### {field}','', '| Grupo | Total | Encontrado | Incorporado |','| --- | ---: | ---: | ---: |']
        lines += [f'| {key} | {v["total"]} | {v["found"]} | {v["incorporated"]} |' for key,v in groups.items()]
        lines+=['']
    lines+=['Motivos sin cambio: '+', '.join(f'{k}: {v}' for k,v in man['absence_reasons'].items())+'.','',
        '## Receta, incidencias y regla de ampliación','',
        'Se reutiliza directamente `train_run` de B mediante un cargador aislado de entradas congeladas. BETO base revisión c4d86612f51b4f46759c8390d1798c2febe71b93; pesos de train_B, cuatro épocas, AdamW 2e-5, weight decay 0,01, microbatch 2, acumulación 8, clipping 1, scheduler original, CUDA fp16 y gradient checkpointing. Semilla antes de inicializar; barajado semilla+época. Checkpoint con mayor F1 macro combinado, empate a primera época. Contexto tanto en entrenamiento como en validación.','',
        'La regla previa autoriza 43/44 solo con Δ combinado medio ≥0,01, mejora en ≥2 folds, Δ histórico medio ≥0 y contexto histórico en ≥2 familias. El 0,01 limita gasto; no es un umbral de calidad ni una prueba estadística.','']
    if r['pilot_gate']:
        g=r['pilot_gate'];o=g['observed']
        lines += [f'Piloto: Δ combinado {o["mean_combined_delta"]:+.6f}; folds mejores {o["improved_folds"]}/3; Δ histórico {o["mean_historical_delta"]:+.6f}; familias históricas con contexto {len(o["historical_families"])}. Regla: **'+('cumplida; ampliación a tres semillas.' if g['passed'] else 'no cumplida; se termina con tres entrenamientos. Un piloto de una semilla puede pasar por alto un beneficio real.')+'**','']
    lines += [f'Ejecuciones completas: {r["completed_runs"]}. Intentos fallidos registrados: {sum(e["status"]=="failed" for e in r["execution_events"])}. Todos los resultados desfavorables se conservan. Las incidencias completas y los estados disponibles para reanudar están en `execution-events.jsonl`; la reanudación conserva fronteras de época. No se promete identidad bit a bit en CUDA.','',
        '| Semilla | Fold | Época | AMP omitidos contexto / B | Actualizaciones contexto / B |','| --- | --- | ---: | ---: | ---: |']
    lines += [f'| {x["seed"]} | {x["fold"]} | {x["best_epoch"]} | {x["amp_skips"]} / {x["B_amp_skips"]} | {x["optimizer_updates"]} / {x["B_optimizer_updates"]} |' for x in r['runs']]
    lines += ['', '## Comparación emparejada','', '| Semilla | Fold | Origen / grupo | n | F1 B | F1 contexto | Δ |','| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for run in r['runs']:
        for key,v in run['subsets'].items():
            if v['n']:lines.append(f'| {run["seed"]} | {run["fold"]} | {key} | {v["n"]} | {v["B"]["f1_macro"]:.6f} | {v["B_context"]["f1_macro"]:.6f} | {v["delta"]:+.6f} |')
    lines += ['', 'F1 macro siempre sobre las siete clases, incluso cuando un subconjunto carece de alguna; división por cero = 0. Precisión, recall, F1 y soporte de cada clase para todos los folds, orígenes y grupos se entregan en `outputs/beto-v2/context/per-class.csv` y `artifacts/beto-v2/context/report.json`. Los grupos comparan exactamente las mismas filas. Las filas sin cambio de entrada también pueden cambiar de predicción por los parámetros aprendidos.','',
        '| Semilla | F1 medio B | F1 medio contexto | Δ de promedios de folds |','| --- | ---: | ---: | ---: |']
    for s in seeds:
        v=s['means']['combined/all'];lines.append(f'| {s["seed"]} | {v["B"]:.6f} | {v["B_context"]:.6f} | {v["delta"]:+.6f} |')
    if len(seeds)==3:
        lines+=['','Cada semilla es una unidad de resumen; los nueve folds no son estudios independientes. Media ± DE muestral entre tres semillas:','']
        for key,v in r['between_seed_summary'].items():lines.append(f'- {key}: Δ {v["delta"]["mean"]:+.6f} ± {v["delta"]["sample_std"]:.6f}.')
    lines+=['','## Errores corregidos e introducidos','', '| Semilla | Corregidos | Introducidos |','| --- | ---: | ---: |']
    for s in seeds:
        es=[e for e in r['errors'] if e['seed']==s['seed']]
        lines.append(f'| {s["seed"]} | {sum(e["kind"]=="corrected" for e in es)} | {sum(e["kind"]=="introduced" for e in es)} |')
    lines+=['','Inventario completo en `outputs/beto-v2/context/error-transitions.json`, enlazado por ID con objetivo y contexto de `inputs.json`. Casos previamente revisados:','',
        '| ID | Semilla | Contexto incorporado | B | B_context | Resultado |','| --- | ---: | --- | --- | --- | --- |']
    lines += [f'| {e["segment_id"]} | {e["seed"]} | {e["changed"]} | {e["B"]} | {e["B_context"]} | {e["kind"]} |' for e in r['errors'] if e['previously_reviewed']]
    lines+=['','## Límites y reproducción','',
        'Añadir contexto no corrige automáticamente OCR, etiquetas ambiguas ni unidades que mezclan temas. La recuperación exacta es conservadora y deja muchas filas sin antecedente demostrable; la cobertura no es aleatoria. El orden de bloques del PDF puede contener problemas fuera de la muestra verificada. Las etiquetas siguen siendo referencias de desarrollo asistidas por IA, no oro experto uniforme. La misma validación selecciona época: estos resultados no son una evaluación independiente. Producción, reserva, DAPT, nuevas anotaciones, variantes e hiperparámetros quedan fuera de esta fase.','',
        'Datos transformados y texto local: `outputs/beto-v2/context/inputs.json`. Manifiesto y protocolo: `artifacts/beto-v2/context/`. Localizaciones reconstruidas de los contextos archivados: `archived-context-locations.json`. Resultados y checkpoints separados: `outputs/beto-v2/context/seed-*/`. La extracción preserva los documentos y textos originales. Los textos completos permanecen en outputs, que ya está excluido de Git.','',
        'En una carpeta sin estos artefactos, ejecutar la preparación y cotejar la muestra reproducible antes de entrenar. En este espacio ya están congelados; el runner verifica hashes y omite resultados completos:','',
        '```powershell',
        '# Solo para reconstruir desde cero: outputs/venv-ml/Scripts/python.exe scripts/prepare_beto_context_v2.py',
        'outputs/venv-ml/Scripts/python.exe scripts/check_beto_context_provenance_v2.py',
        "$env:PYTORCH_CUDA_ALLOC_CONF='backend:native,max_split_size_mb:128'",
        'outputs/venv-ml/Scripts/python.exe -u scripts/run_beto_context_v2.py',
        'outputs/venv-ml/Scripts/python.exe scripts/report_beto_context_v2.py','```','']
    path=b.ROOT/'docs/beto-v2/07-contexto.md';text='\n'.join(lines)
    if path.exists():assert path.read_text(encoding='utf-8')==text
    else:path.write_text(text,encoding='utf-8')

if __name__=='__main__':report()
