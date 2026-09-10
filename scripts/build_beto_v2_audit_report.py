"""Assemble the forensic report from measured evidence, without overwrites."""
import collections,csv,json,subprocess
from pathlib import Path
from audit_beto_v2 import ROOT,read,sha,save,canonical
out=ROOT/'artifacts/beto-v2/audit'; docs=ROOT/'docs/beto-v2';docs.mkdir(parents=True,exist_ok=True)
a=read(out/'dataset-audit.json');checks=read(out/'forensic-checks.json');gold=next(d for d in a['datasets'] if d['path']=='artifacts/datasets/gold-v1-source-aware.json')
orig='apps/ml/storage/models/beto-v1-gold-source-aware';local='outputs/experiments/beto-u1/beto-lr2e5'
old=read(ROOT/'artifacts/experiments/course-u1/beto/report.json')
rows=read(ROOT/gold['path'])['items']; dist=list(csv.DictReader((out/'source-class-distribution.csv').open(encoding='utf-8-sig')))
dg=[r for r in dist if r['dataset']==gold['path']]
tk=list(csv.DictReader((out/'token-lengths.csv').open(encoding='utf-8-sig')))
flags=list(csv.DictReader((out/'suspicious-labels.csv').open(encoding='utf-8-sig')))
noise=collections.Counter(x for r in flags if r['dataset']==gold['path'] for x in r['reason'].split(';'))
def table(headers,lines):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in lines])
metrics=table(['Checkpoint','Split','n','Aciertos','F1 macro (7)'],[(p,sp,m['n'],m['correct'],f"{m['f1_macro_seven']:.9f}") for p,sm in a['reproduced_metrics'].items() for sp,m in sm.items()])
lengthtable=table(['Límite BETO','Segmentos truncados','Porcentaje','Tokens perdidos'],[(m,v['segments'],f"{100*v['fraction']:.2f}%",v['lost_tokens']) for m,v in gold['tokens']['truncation'].items()])
source_table=table(['Fuente (resourceId)','Split/formato','n','Clases ausentes','Clases con 1–4 filas'],[(s,','.join(sorted({r['split']+'/'+r['format'] for r in dg if r['source']==s})),sum(int(r['count']) for r in dg if r['source']==s),sum(int(r['count'])==0 for r in dg if r['source']==s),sum(0<int(r['count'])<5 for r in dg if r['source']==s)) for s in sorted({r['source'] for r in dg})])
classtable=table(['Clase','Train','Val','Test'],[(lab,*[sum(r['label']==lab and r['split']==sp for r in rows) for sp in ['train','val','test']]) for lab in gold['labels']])
datasettable=table(['Snapshot / evidencia (no sumar versiones)','Filas','Splits','SHA256 canónico'],[(d['path'],d['n'],str(d['split_counts']),d['canonical_sha256']) for d in a['datasets']])
same_maps=all(a['checkpoint_metadata'][p]['labels.json']['id2label']==a['checkpoint_metadata'][p]['config.json']['id2label'] for p in [orig,local])
z=a['zip_evidence']['modelo_vN.zip']['entries']; zip_match=z['modelo_vN/model.safetensors']==a['checkpoints'][orig]['model.safetensors']
archive_gold=a['zip_evidence']['artifacts/training/historia-viva-beto-v1-colab.zip']['entries']['gold-v1-source-aware.json']==gold['file_sha256']
text=f'''# Auditoría forense BETO y plan de mejora

Fecha: {a['created_at']}. Commit observado: `{a['commit']}`. El árbol tenía modificaciones y experimentos sin seguimiento antes de la auditoría; un commit por sí solo no reconstruye el estado. Los hashes de `input_manifest` fijan el código y los datos realmente leídos.

## Dictamen y alcance

Los resultados proceden de dos checkpoints y dos poblaciones de evaluación diferentes. **0.425 es el redondeo de 0.4246107966; 0.31066 pertenece al experimento local posterior; el dato cercano a 3/34 es 3/31 en desarrollo externo.** La usuaria aclaró que 3/34 era aproximado: no se certifica una evaluación manual de 34 casos. Se reprodujeron las 31 predicciones externas originales.

Se inspeccionaron {len(a['input_manifest'])} archivos de código/evidencia y {len(a['datasets'])} JSON con `items` etiquetados; son versiones, muestras y controles, **no {len(a['datasets'])} corpus independientes**. La métrica principal corresponde al snapshot gold original. Las muestras, maintenance y `invalid-base-control.json` se inventarían como evidencia, nunca como candidatos válidos de entrenamiento. Los JSON sin etiquetas completas no entran en los estadísticos de clasificación.

No se entrenó, descargó corpus, cambió etiqueta, modificó código de entrenamiento, publicó ni activó un modelo. La investigación bibliográfica utilizó web pública. Se ejecutó inferencia offline de solo lectura; no se llamó al servicio desplegado. **La identidad binaria del proceso remoto actualmente activo queda sin verificar**: el repositorio no prueba su memoria en ejecución.

## Reproducción y cadena de custodia

Comandos desde la raíz:

```powershell
outputs/venv-ml/Scripts/python.exe scripts/audit_beto_v2.py
outputs/venv-ml/Scripts/python.exe scripts/audit_beto_v2_checks.py
outputs/venv-ml/Scripts/python.exe scripts/build_beto_v2_audit_report.py
```

Los scripts rechazan sobrescribir salidas. Para repetir el primer análisis usar `--output artifacts/beto-v2/audit-REPETICION`; los otros dos tienen destinos fijos y requieren adaptar su destino en una copia. Python: {a['python']}; versiones medidas: `{json.dumps(a['versions'])}`. El `.venv` de `apps/ml` apunta a un Python 3.9 inexistente; se usó `outputs/venv-ml`. No se instalaron paquetes.

Dataset gold SHA256 de bytes: `{gold['file_sha256']}`. SHA256 canónico (JSON ordenado, UTF-8, sin espacios): `{gold['canonical_sha256']}`. No confundir ambas funciones de hash. El dataset del ZIP de preparación coincide por bytes: **{archive_gold}**.

| Resultado | Checkpoint y datos | Código/configuración y límite de trazabilidad |
|---|---|---|
| 0.4246107966 ≈ 0.425 | `apps/ml/storage/models/beto-v1-gold-source-aware`; gold 596/81/137 | `notebooks/train_beto_colab.ipynb` y notebook del ZIP; receta declarada: cased, 4 épocas máximas, lr 2e-5, batch 16, 192 tokens, seed 42, pesos inversos, early stopping 2. Notebook sin outputs ni ejecución archivada: no certifica época ganadora, entorno completo ni commit ejecutado en Colab. |
| 0.31066 | `outputs/experiments/beto-u1/beto-lr2e5`; mismo gold | `apps/ml/app/ml/beto_experiment.py`, `experiments.py`, `configs/experiments/beto.json`; informe del 2026-09-07, commit `{old['git_commit']}`, dirty=true. Revisión base `c4d86612f51b4f46759c8390d1798c2febe71b93`; 3 épocas, mejor época 2, microbatch 2 × acumulación 8, lr 2e-5, 192 tokens. |
| 3/31 | mismo checkpoint local; `artifacts/datasets/external-development-v1.json` | `scripts/compare_beto_length.py`, protocolo y reporte en `artifacts/experiments/beto-length-v1/`. Conjunto de dos obras, cinco clases presentes; aciertos, no F1. F1 cinco=0.10; F1 siete=0.07142857. Predicciones conservadas y ahora reproducidas. |

SHA256 pesos v1: `{a['checkpoints'][orig]['model.safetensors']}`. SHA256 pesos local: `{a['checkpoints'][local]['model.safetensors']}`. Coincidencia ZIP `modelo_vN.zip` con pesos v1: **{zip_match}**. Esto vincula el artefacto importable con el archivo local, no con una instancia remota actual.

`metrics.json` v1 incluye hash canónico del gold en `baseline.dataset_sha256`. La versión de transformers declarada en ambos `config.json` es 4.57.6; no equivale a un lock completo de la sesión Colab. El primer commit localizado del notebook es `994c824` (2026-07-20); es procedencia del archivo, no prueba del commit ejecutado al entrenar.

## Métricas recalculadas, sin selección de candidatos

Inferencia CPU float32, batch 16, padding dinámico y `max_len` del artefacto: misma transformación y decodificación que `beto.infer`; proceso aislado sin tocar el singleton del servidor. F1 con las siete etiquetas explícitas y `zero_division=0`. Train es diagnóstico de ajuste, nunca rendimiento de generalización.

{metrics}

Para el conjunto externo se ejecutó además `predict_beto`, CUDA/float16 del código experimental, batch 2: **31/31 predicciones coincidentes**, 3 aciertos. SHA256 externo `{checks['external']['dataset_sha256']}`. Evidencia: `forensic-checks.json` y `predictions-external.csv`. No se comparan sus cinco clases con el macro de siete sin declarar el denominador.

## Paridad entrenamiento / evaluación / despliegue

| Elemento | Resultado verificable |
|---|---|
| Checkpoint | v1 y local tienen pesos distintos. Modal configura `Jaqueline98/historia-viva-beto-v1`; ni build ni bootstrap fijan `revision`. Identidad remota actual desconocida. |
| id2label / label2id | Los dos artefactos locales usan el mismo orden alfabético de siete etiquetas. `labels.json` y `config.json` coinciden: {same_maps}. |
| Tokenizer | IDs idénticos en los 814 textos gold: {a['tokenizer_ids_equal_on_gold']}. Settings y hashes completos en JSON; igualdad funcional observada no requiere igualdad de serialización. |
| max_length | 192 en los dos artefactos, notebook y default servicio. Ensayos 384 son candidatos separados. `predict_beto` recibe longitud externa por params; no la coteja con labels.json. |
| Orden de etiquetas | Servicio decodifica labels.json; predictor experimental decodifica la lista recibida. No valida su igualdad con config: riesgo latente de permutación, no fallo observado aquí. El orden de presentación de la ficha del Hub es diferente al orden numérico. |
| Limpieza / segmentación | Entrenamiento y evaluación usan `row.text` ya almacenado. Ingesta PDF/ASR genera texto por rutas diferentes; no hay hash de la transformación asociado a cada ejemplo gold. Paridad de extremo a extremo no demostrable. |
| Precisión/padding | Experimento CUDA fp16 + padding fijo; servicio CPU fp32 + padding dinámico. Predicciones pueden variar cerca del empate. |
| Dependencias | `requirements-ml.txt` fija transformers 4.42.3 y torch <2.4; `requirements.txt` fija transformers 4.57.6; entorno experimental torch 2.7.1. Modal declara torch 2.12.0. No son entornos iguales. |

Hallazgos de despliegue: `main.py` descarga por repo sin revisión al arrancar; `modal_app.py` también. El endpoint `/infer` devuelve etiqueta/confianza sin fingerprint de pesos. `InferenceService.ensureActiveModel` consulta una versión activa en BD, pero no coteja el checkpoint del proceso ML. `resources.service.ts` conserva sugerencias sin SHA del modelo; `suggestLabels` absorbe excepciones. Por tanto, estado `ready` de un recurso no certifica inferencia BETO exitosa ni permite reconstruir una predicción antigua. No se atribuye una predicción remota concreta a esos fallos sin log.

## Distribución clase × fuente × formato × split

{classtable}

{source_table}

El CSV entrega todas las celdas por fuente/formato/split, incluidas clases con cero filas dentro de cada combinación observada. Las combinaciones de splits no asignados a una fuente son ceros estructurales por separación, no ejemplos perdidos. Val tiene **una sola fuente** y test dos; 81 y 137 segmentos no equivalen a 81 y 137 observaciones documentales independientes. Basadre (`747ca90f…`) aporta 244/596 ejemplos train (40.94%). Hay 4 ejemplos de campañas y 4 de liderazgos en val; una variación pequeña cambia mucho sus F1.

Asociación fuente–etiqueta en gold: Cramér V **{gold['source_label_association']['cramers_v']:.6f}**, NMI **{gold['source_label_association']['normalized_mutual_information']:.6f}**, información mutua **{gold['source_label_association']['mutual_information_nats']:.6f} nats**. Es dependencia descriptiva, no prueba causal de que BETO memorice autores. El p-valor del JSON no debe interpretarse como inferencia IID dada la agrupación y celdas escasas. No existe campo autor en {gold['missing_author']}/{gold['n']} filas gold: **no puede calcularse una dependencia por autor completa y verificada con ese snapshot**. `resourceId` no garantiza obra/autores independientes. Las revisiones existentes documentan citas compartidas y colecciones comunes; hace falta una tabla editorial validada antes del próximo split.

## Tokens y pérdida por truncamiento

Conteo exacto con tokenizer local cased, sin truncar, incluidos `[CLS]` y `[SEP]`; cada fila en `token-lengths.csv` conserva índice base cero, hash del texto, dataset, clase/fuente/split y pérdida a cada límite. El presupuesto de contenido es L−2. Mínimo={gold['tokens']['min']}, mediana={gold['tokens']['median']}, máximo={gold['tokens']['max']}.

{lengthtable}

No se estimó con número de palabras. El tokenizer original y local producen los mismos IDs en gold. El análisis del resto de snapshots usa el tokenizer original, identificado por hashes. La pérdida de tokens no informa por sí sola si la evidencia de la etiqueta estaba en el prefijo o en la cola.

## Duplicados, contradicciones y ruido

Gold: {len(gold['exact_duplicate_groups'])} grupos de duplicados exactos por bytes y {len(gold['normalized_duplicate_groups'])} tras NFKC/casefold/espacios; {len(gold['contradictory_exact_groups'])} grupos normalizados con etiquetas contradictorias dentro del mismo snapshot. Fuentes en múltiples splits: `{gold['source_overlap']}`. Duplicados y cambios entre versiones no deben sumarse como fuga dentro de un único dataset.

Cribado aproximado sobre {a['similarity']['unique_texts']} textos únicos: TF-IDF de caracteres 3–5, `char_wb`, min_df=2, máximo 60000 características; umbral coseno ≥0.82. Detectó {a['similarity']['pairs_above_082']} pares y {a['similarity']['different_label_pairs']} pares con conjuntos de etiquetas distintos. Es un índice de similitud para auditoría, no entrenamiento del clasificador. El par gold **549/747** tiene similitud ≈0.99894, ambos train y campañas: redundancia intratrain, no fuga de test. El archivo `similarity-pairs.json` conserva todos los pares y sus referencias; el umbral puede omitir paráfrasis y no certifica ausencia de duplicados semánticos.

Hay cuatro textos idénticos con etiquetas diferentes **entre versiones**: gold índices 54, 360, 536 y 571. Corresponden a revisiones históricas previas: historiografía/participación; autonomía regional/ideas; negociación de paz/campañas; extranjeros y organización republicana/contexto colonial. No deben mezclarse snapshots para entrenar y después contar estas revisiones como errores de un gold único.

Señales heurísticas en gold (no tasas de error confirmadas): `{json.dumps(dict(noise),ensure_ascii=False)}`. El CSV `suspicious-labels.csv` marca `requires_context_review_not_confirmed_error`. La consola PowerShell puede representar acentos incorrectamente; las señales se calcularon sobre Unicode leído como UTF-8, no sobre el texto mostrado por la terminal.

PDF: `_clean_page` elimina cabeceras repetidas, líneas editoriales, números y reúne guiones; `_chunk_text` agrupa por página con objetivo 180/máximo orientativo 250 palabras. Una oración larga puede exceder el máximo y la frontera de página puede cortar una idea. El pipeline rechaza PDF sin texto seleccionable: no realiza OCR propio, aunque el PDF puede contener una capa OCR previa ruidosa. No hay transcripción de referencia suficiente para medir CER/OCR real.

ASR/subtítulos: ventanas de 60 s con solape de 10 s; cues compartidos crean pasajes repetidos y fronteras dependientes del tiempo, no del tema. Fuentes YouTube pueden venir de subtítulos nativos, Supadata o faster-whisper; `sourceType` no permite distinguir el motor para todos los ejemplos gold. Muletillas, repeticiones y nombres propios deformados son candidatos; no hay referencias alineadas para medir WER. No se volvió a transcribir audio.

## Ambigüedad y segmentos con varios temas

Revisión cualitativa dirigida, no anotación completa ni validación por historiador: gold 360 combina economía regional, élites y autonomía política; 536 incluye consecuencias militares y condiciones diplomáticas de paz; 571 mezcla disposiciones estatales y cambios sociales/económicos; 54 discute historiografía sobre actores subalternos en lugar de narrar directamente un episodio. Son fronteras reales entre clases; una única etiqueta exige una regla de tema dominante y de tratamiento de metahistoriografía. El desacuerdo no demuestra automáticamente una etiqueta incorrecta.

La cola conserva textos completos y referencia; no se adjudicó ninguna etiqueta en esta fase. La cantidad exacta de segmentos semánticamente ambiguos/multitemáticos del corpus queda **no determinada**: las heurísticas no la pueden certificar. Los informes previos `beto-historiography-boundary-v1.json` y `beto-training-cleanup-v1/adjudication.json` contienen decisiones asistidas que deben ser contrastadas por expertos. Acuerdo IA–IA no equivale a validez histórica independiente.

## Errores de evaluación y entrenamiento comprobados

1. `trainer.py`: val vacío → train; test vacío → val. Contrajemplos ejecutados por AST, sin entrenar. Reporta `metrics_split`, pero sigue usando el conjunto reutilizado.
2. Notebook: `split(name)` devuelve **todos los items** cuando no encuentra ese split. Sin test, puede evaluar train+val y rotularlo `val`. Es más grave que el fallback del servicio.
3. `experiment_data.validate_snapshot` sí rechaza fuente/texto normalizado entre splits y clases ausentes; no detecta todas las paráfrasis ni independencia por autor. Contrajemplo sin val correctamente rechazado.
4. Macro implícito del notebook/servicio usa la unión de clases observadas; sin clases presentes puede cambiar el denominador. El test gold tiene siete clases, por lo que este mecanismo no explica la diferencia entre 0.425 y 0.31066.
5. El experimento pondera y promedia cada microbatch antes de acumular. El contrajemplo da pérdida {checks['checks'][4]['micro_loss']:.6f} frente a {checks['checks'][4]['full_loss']:.6f} para el batch completo: batch efectivo 16 no reproduce exactamente la pérdida ponderada de batch físico 16.
6. Semilla: el experimento llama `set_seed` antes de crear la cabeza; notebook/servicio establecen seed en TrainingArguments después de inicializar el modelo. La inicialización original no queda controlada por ese argumento por sí solo.
7. El servicio/notebook no pasan tokenizer/data_collator explícito al Trainer pese a secuencias de longitudes variables. Su ejecutabilidad depende de defaults/versiones; es un riesgo a verificar en una fase de ingeniería, no una prueba de que el entrenamiento histórico fallara.
8. API deriva clases presentes en el dataset y solo exige dos; puede entrenar fuera de la taxonomía de siete. Importar métricas sin `split` usa `test` por defecto (`training.service.ts`). No se cambia ninguno de estos comportamientos en esta fase.

## Contaminación histórica y límites de test

El test gold ya se publicó y evaluó en varias comparaciones; no es un test ciego para una campaña nueva que decide usando esos resultados. Esta auditoría también lo inspecciona. La coincidencia de fuentes disjuntas no revierte exposición previa a resultados/etiquetas. No se encontró evidencia suficiente para afirmar que sus filas entraran directamente en el entrenamiento local seleccionado; se distingue fuga de datos de adaptación a un benchmark ya conocido.

Val original ha guiado selección de learning rate y época y revisiones sucesivas; sus 81 filas de una obra son una base muy estrecha. El conjunto externo de 31 filas ya guio análisis de longitud y no debe convertirse en test final. `evaluation-pilot-v2.json` declara 22 aceptados, cuatro fuentes y dos grupos de colección; su informe dice explícitamente que no es test final independiente. La auditoría no predijo ese piloto. Familia documental y autores citados deben agruparse antes de reservar una evaluación nueva en una fase posterior autorizada.

## Qué ya se ha probado y qué no atribuir causalmente

Los reportes previos muestran que 192→384 pasó de 3/31 a 4/31 externos (F1 cinco 0.10→0.13333); variar tasa, normalizar pérdida y limpiar train no resolvió de forma consistente ideas en obras retenidas. Evidencia: `beto-length-v1`, `beto-learning-rate-v1`, `beto-loss-normalization-v1`, `beto-training-cleanup-v1`, `tfidf-beto-work-control-v1`. No se ejecutaron otra vez sus entrenamientos. La reducción de contexto existe, pero no es explicación suficiente del fallo de transferencia. El 0.425 no demuestra superioridad reproducible frente al entrenamiento local sin controlar todas las diferencias de receta, inicialización y selección.

## Investigación primaria y documentación

Consultada el 2026-09-08; documentación viva no sustituye a fijar versiones. No se importaron modelos nuevos ni bibliotecas.

- [BETO, repositorio de los autores](https://github.com/dccuchile/beto) y [artículo original de Cañete et al.](https://pml4dc.github.io/iclr2020/program/pml4dc_10.html): variantes cased/uncased y evaluación española. Compararlas es una hipótesis razonable, no garantía de mejora histórica.
- [Hugging Face: padding/truncation](https://huggingface.co/docs/transformers/main/pad_truncation): padding dinámico/fijo y truncamiento son operaciones distintas. Propuesta: contrato explícito para todas las rutas.
- [PyTorch 2.7 CrossEntropyLoss](https://docs.pytorch.org/docs/2.7/generated/torch.nn.CrossEntropyLoss.html): la media ponderada normaliza por suma de pesos. Sustenta el contrajemplo de acumulación; no identifica por sí sola la causa del F1.
- [scikit-learn F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) y [StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html): declarar clases y mantener grupos disjuntos. Estratificación no crea soporte faltante ni independencia documental.
- [Mosbach et al., estabilidad de fine-tuning BERT](https://arxiv.org/abs/2006.04884): variabilidad entre semillas y optimización justifican repetir semillas y reportar dispersión en una fase futura, sin escoger la mejor semilla por test.
- [Northcutt et al., errores de etiquetas en test](https://arxiv.org/abs/2103.14749): motiva revisión humana independiente y trazabilidad; no autoriza corregir etiquetas por desacuerdo con BETO.
- [Yang et al., Hierarchical Attention Networks](https://aclanthology.org/N16-1174/): precedente de agregación de oraciones/documentos. Aplicar agregación de ventanas BETO sería una adaptación experimental que conserva BETO como encoder, no una mejora demostrada aquí.

## Hipótesis priorizadas y plan de la siguiente fase (no ejecutado)

| Prioridad / área | Hipótesis y prueba propuesta | Impacto esperado | Costo | Riesgo |
|---|---|---|---|---|
| P0 evaluación/despliegue | Unificar contrato: siete etiquetas, hash de pesos/tokenizer/dataset, revisión fija, max_length, segmentador y manifest por predicción; rechazar splits ausentes. | Alto para validez; puede no subir F1 | Bajo–medio | Bajo; revela métricas no comparables |
| P1 datos/fuentes | Diversidad insuficiente y dependencia obra–etiqueta limitan transferencia. Validación por obras/familias completas, concentración por clase y controles TF-IDF sobre mismas particiones. | Alto, sin promesa numérica | Medio–alto | Confundir autor con obra; pocas familias |
| P2 etiquetas | Regla inestable para tema dominante/metahistoriografía. Doble revisión ciega de expertos con contexto, adjudicación separada, sin mostrar predicciones. | Alto potencial | Alto humano | Cambiar el objetivo para favorecer el modelo |
| P3 segmentación | Cortes, notas y colas truncadas eliminan evidencia. Comparar 192/256/384/512 con mismo protocolo, y agregación de ventanas BETO conservando unidad de evaluación. | Medio | Medio; memoria crece | Propagar etiqueta del segmento a ventanas irrelevantes; duplicación entre splits |
| P4 entrenamiento | Inicialización, pérdida/normalización y scheduler explican parte de la variación. Fijar semillas antes del modelo, pérdida verificable y 3–5 semillas predeclaradas. | Medio | Medio GPU | Elegir retrospectivamente semilla/época |
| P5 representación | cased vs uncased puede cambiar sensibilidad a OCR/mayúsculas. Comparación pareada con idénticos folds y presupuesto de búsqueda. | Incierto/medio | Medio | Añadir búsqueda sin datos independientes |
| P6 arquitectura | Jerarquía relevante/no_relevante y seis temas, o agregación de ventanas BETO, puede tratar ruido y múltiples temas. | Incierto | Medio–alto | Errores en cascada, menos soporte, mayor complejidad |

Antes de entrenar: aprobar protocolo y objetivo de generalización (nuevas obras/autores o nuevas secciones de obras conocidas); adjudicar copias versionadas de datos; congelar grupos, roles y test final con custodia separada. Mantener originales y una bitácora de cambios con justificación histórica.

Diseño propuesto: con las siete fuentes train originales no asumir que cinco folds tendrán siete clases; construir particiones de grupos auditadas y rechazar las inviables. Selección de hiperparámetros exclusivamente dentro de desarrollo agrupado; comparar BETO con baseline mayoritario y TF-IDF bajo los mismos folds. Reportar macro siete, soporte, F1 por clase, matrices, resultados por obra/formato y semillas; intervalos por bootstrap de grupos, reconociendo que pocos grupos generan alta incertidumbre. Predeclarar presupuesto y criterio de parada. Evaluación final una vez tras congelar receta; si falla, reportar el resultado y abrir otra versión del protocolo, no seguir optimizando sobre ese test.

## Inventario y pendientes verificables

{datasettable}

No determinados con la evidencia existente: commit/época y lock completo del entrenamiento Colab; SHA del proceso remoto; evaluación manual exacta 3/34; tabla completa de autores; WER/CER reales; número exacto de segmentos ambiguos y duplicados semánticos. Estos límites quedan explícitos y no se sustituyen por estimaciones inventadas. El plan está listo para revisión; esta fase termina sin entrenamiento ni promoción.
'''
with (docs/'01-auditoria.md').open('x',encoding='utf-8') as f:f.write(text)
progress=f'''# Progreso BETO v2

Auditoría y plan finalizados: {a['created_at']}.
Commit base `{a['commit']}`; árbol previamente modificado conservado.

- Inventario, hashes de entradas y checkpoints, tokens por segmento y distribución cruzada generados.
- Reproducción local de ambos checkpoints en gold y del resultado externo 3/31 completada.
- Contrajemplos de fallbacks, macro y pérdida ponderada ejecutados sin entrenamiento.
- 14 puntos abordados en `01-auditoria.md`; límites no verificables señalados expresamente.
- Investigación primaria y plan por impacto/costo/riesgo incluidos.
- Ningún dato original, entrenamiento o artefacto desplegado modificado; sin publicación ni push.

Comandos y versiones: `artifacts/beto-v2/audit/dataset-audit.json` y `forensic-checks.json`.
No se usaron los resultados para seleccionar o promover un checkpoint.

Pendientes para una fase futura: identidad remota por hash, reconstrucción del entrenamiento Colab si existen logs, catálogo de autores/familias y adjudicación histórica independiente. No se inventa una medida exacta de ambigüedad ni WER/CER.
'''
with (docs/'progress.md').open('x',encoding='utf-8') as f:f.write(progress)
# Verify reproducibility of saved predictions and the canonical artifact relationship.
pred=list(csv.DictReader((out/'predictions-current.csv').open(encoding='utf-8-sig')))
assert len(pred)==2*gold['n']
from sklearn.metrics import f1_score
for ck in [orig,local]:
    for sp in ['train','val','test']:
        subset=[r for r in pred if r['checkpoint']==ck and r['split']==sp]
        score=f1_score([r['label'] for r in subset],[r['prediction'] for r in subset],labels=gold['labels'],average='macro',zero_division=0)
        assert abs(score-a['reproduced_metrics'][ck][sp]['f1_macro_seven'])<1e-12
assert gold['canonical_sha256']==old['dataset_sha256']
validation={'command':'outputs/venv-ml/Scripts/python.exe scripts/build_beto_v2_audit_report.py','commit':a['commit'],'prediction_rows':len(pred),'metrics_recomputed_from_csv':True,'input_hashes_preserved':a['input_preservation'],'outputs':{str(p.relative_to(ROOT)):sha(p) for p in [*out.glob('*'),docs/'01-auditoria.md',docs/'progress.md'] if p.is_file()},'scripts':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts').glob('*beto_v2*.py')}}
save(out/'verification.json',validation)
print(json.dumps({'documents_created':True,'prediction_rows':len(pred),'metrics_csv_verified':True}))
