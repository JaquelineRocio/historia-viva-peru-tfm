# Plan de trabajo: Unidad I y Unidad II

Este documento separa implementación, ejecución local y evidencia en producción.
Una configuración escrita no equivale a un pipeline ejecutado en GitHub.

## Orden de trabajo

| Bloque | Resultado | Estado |
|---|---|---|
| Diagnóstico | Compilar web/API, ejecutar suites y revisar dataset | API 37 pruebas, ML 42 pruebas y web verificados localmente |
| Experimentos | Comparar hiperparámetros usando validación; test solo del ganador | Tres configuraciones TF-IDF y tres BETO ejecutadas en este equipo |
| Informe Unidad I | Dataset, características, parámetros, resultados, despliegue y límites | Borrador en informe-unidad-1.md |
| Demo Unidad I | Dos pruebas funcionales completas y explicación en inglés | PDF cargado, predicho tras reintento y revisión persistida vía API. Primera clasificación fallida y recorrido visual pendientes |
| Mantenimiento | Validar snapshot, entrenar, evaluar y archivar candidato | TF-IDF ejecutado en GitHub; métricas y candidato archivados. Correcciones automáticas pendientes |
| Integración continua | Tests, builds y comprobación agregada Quality gate | Ejecución en GitHub correcta para `3974f4a` |
| Despliegue | Esperar CI, verificar versión y recuperar ante fallos | Nueva ruta de salud accesible en Render; falta verificar SHA y controles de despliegue |
| Entrega Unidad II | Tres casos ejecutados, con logs y resultados | Controles locales; demostración remota pendiente |

## Organización de los cambios en Git

Las consultas de Git pueden realizarlas el asistente o la autora. Las ramas, el staging, los commits, los merges y el push los gestiona exclusivamente la autora. Cada bloque se revisa y verifica antes de registrarlo; se espera su confirmación para pasar al siguiente. Publicar o desplegar requiere su autorización.

| Bloque | Commit local verificado | Estado |
|---|---|---|
| Salud de la API y pruebas | `ca2da38` | Publicado; ruta accesible en Render |
| Experimentos y preparación del reentrenamiento | `3548851` | Registrado; pruebas locales correctas |
| Scripts de verificación | `2483a4f` | Registrado; pruebas locales correctas |
| Automatización y configuración de Render | `62073ac` | Publicado; CI y mantenimiento TF-IDF ejecutados correctamente |
| Evidencias e informes | `847b141` | Publicado |
| Exclusiones del material local | `3974f4a` | Publicado; presentación conservada localmente |
| Arranque de BETO antes de aceptar peticiones | `24f03be` | Registrado; pruebas locales correctas, despliegue ML pendiente |
| Errores de almacenamiento PDF | `0bc365a` | Registrado; pruebas y compilación correctas, despliegue API pendiente |

Las modificaciones personales de `.gitignore` se revisan por separado.

## Qué debes poder explicar

1. El modelo recibe **texto de un fragmento**, tokenizado en subpalabras, truncado a 192 tokens, con máscara de atención. Predice una de siete clases.
2. BETO usa representaciones aprendidas del texto. Años, personas y lugares son salidas adicionales: no son automáticamente las variables de entrada del clasificador.
3. TF-IDF representa palabras y bigramas; la regresión logística sirve como comparación económica.
4. Train ajusta pesos; validación selecciona hiperparámetros y época; test mide el resultado de la selección terminada.
5. La separación por fuente evita que páginas o fragmentos del mismo material aparezcan a ambos lados de la evaluación. También se rechazan duplicados de texto entre conjuntos.
6. F1 macro promedia el F1 de todas las clases con igual peso. No es porcentaje de respuestas correctas; ese porcentaje se mide con accuracy.
7. CI verifica cambios de software. Mantenimiento ML produce y evalúa candidatos a partir de datos versionados. Son flujos relacionados pero distintos.
8. Un candidato entrenado no se convierte por sí solo en el modelo activo de producción.

## Ejecutar los experimentos en este equipo

Se creó `outputs/venv-ml` porque el entorno anterior referencia un Python inexistente.
Los resultados grandes permanecen en `outputs/`, excluido de Git. No se modificó `.gitignore`.

Desde PowerShell, en la raíz:

```powershell
$env:PYTHONPATH = 'apps/ml'
outputs/venv-ml/Scripts/python.exe -m app.ml.experiments --dataset artifacts/datasets/gold-v1-source-aware.json --config configs/experiments/tfidf.json --output outputs/experiments/tfidf-nueva-ejecucion
outputs/venv-ml/Scripts/python.exe -m app.ml.experiments --dataset artifacts/datasets/gold-v1-source-aware.json --config configs/experiments/beto.json --output outputs/experiments/beto-nueva-ejecucion
```

La carpeta de salida debe ser nueva para conservar la evidencia previa. Cada ejecución guarda auditoría, parámetros, selección, métricas finales, dependencias y candidato. Los experimentos BETO requieren CUDA por defecto; el perfil usa microbatches de 2 y acumulación de 8 (batch efectivo 16), precisión mixta y gradient checkpointing.

Para reproducir el entorno en otro equipo con GPU compatible:

```powershell
python -m venv outputs/venv-ml
outputs/venv-ml/Scripts/python.exe -m pip install -r apps/ml/requirements-test.txt
outputs/venv-ml/Scripts/python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
outputs/venv-ml/Scripts/python.exe -m pip install -r apps/ml/requirements-experiments.txt
```

El índice CUDA depende del hardware/controlador; la receta se basa en los [binarios oficiales de PyTorch](https://pytorch.org/get-started/previous-versions/). Las versiones efectivamente utilizadas quedan registradas en `report.json`.

## Workflows preparados

- **CI**: API tests/build, web lint/build y ML tests. `Quality gate` falla si cualquiera falla o no termina correctamente. Los resultados ML quedan como artefacto JUnit.
- **ML maintenance**: ejecuta el experimento por cambios de datos/configuración, manualmente o cada semana. Por defecto utiliza TF-IDF en CPU. BETO requiere un runner configurado con etiquetas `self-hosted`, `ml-gpu`; puede seleccionarse manualmente o mediante la variable `ML_BACKEND=beto`. No se ha registrado un runner en este trabajo.
- **Production smoke**: comprueba API+ML, autenticación, acceso a proyectos, abstención y HTML web. Se ejecuta manualmente o diariamente; archiva un JSON incluso cuando detecta fallos. Esto es monitorización, todavía no verificación del commit recién desplegado.

El workflow de mantenimiento comienza desde el snapshot académico versionado. Si se configura `ML_REVIEWED_SNAPSHOT` con la ruta de un export completo y revisado, prepara un snapshot nuevo conservando intactas las fuentes de validación/test y entrena solo si hay al menos 20 altas, retiros o cambios de etiqueta en train. `ML_REFERENCE_SNAPSHOT` permite fijar la referencia anterior. Sin export revisado, el workflow repite el experimento académico para verificar reproducibilidad.

**Todavía falta extraer automáticamente las correcciones desde producción** y comparar el candidato con el activo antes de promoverlo. El umbral de cambios se calcula respecto a la referencia configurada: tras aceptar una nueva versión debe actualizarse esa referencia para no repetir su entrenamiento.

Prueba ejecutable sin cambios:

```powershell
$env:PYTHONPATH = 'apps/ml'
outputs/venv-ml/Scripts/python.exe -m app.ml.maintenance --reference artifacts/datasets/gold-v1-source-aware.json --reviewed artifacts/datasets/gold-v1-source-aware.json --config configs/experiments/tfidf.json --output outputs/maintenance-nueva-comprobacion
```

Debe producir `status: skipped` y no entrenar. El export revisado debe contener todo el conjunto aprobado, porque omitir un ejemplo de train significa retirarlo. Las etiquetas revisadas de fuentes reservadas para evaluación no se incorporan al entrenamiento.

`render.yaml` incorpora `autoDeployTrigger: checksPass`, opción documentada por [Render](https://render.com/docs/blueprint-spec#autodeploytrigger). Debe sincronizarse o configurarse en Render y verificarse allí. No se ha cambiado la configuración del servicio remoto. Vercel requiere su propio control para impedir que despliegue antes de CI.

## Tres casos para Unidad II

| Caso | Acción | Evidencia necesaria |
|---|---|---|
| Cambio válido | Ejecutar CI con una modificación válida y desplegar ese commit | URL de la ejecución verde, SHA desplegado y smoke posterior |
| Fallo detectado | Introducir un fallo controlado en una rama de demostración | Ejecución roja y evidencia de que producción conserva el commit anterior |
| Mantenimiento ML | Procesar un snapshot nuevo y evaluar candidato | Huella del dataset, parámetros, métricas, candidato registrado y decisión justificada |

Los tests locales ya comprueban que un dataset con fuga de fuentes se rechaza, que test no decide el ganador y que no se promueve un candidato que incumple los criterios. Estos controles no sustituyen los tres casos remotos.

## Pendientes para completar el ciclo

- [x] Ejecutar y archivar la comparación BETO: candidato seleccionado F1 test 0.31066, permanece experimental.
- [x] Verificar carga e inferencia con pesos reales y conservación del modelo ante una carga fallida (FastAPI local).
- [ ] Repetir recorrido real PDF/YouTube → predicción → corrección persistida.
- [ ] Confirmar si la exigencia de inglés alcanza también a la interfaz.
- [x] Publicar los cambios y conservar URLs de GitHub Actions.
- [ ] Conectar snapshots de correcciones, identidad estable de evaluación y detección de cambios.
- [ ] Guardar pesos BETO en almacenamiento accesible al servicio ML: un artefacto de Actions por sí solo no es una ruta de Modal.
- [ ] Comparar candidato y activo, verificar carga y hacer activación recuperable.
- [ ] Resolver consistencia entre modelo activo de la BD y modelo incorporado en la imagen Modal al reiniciar.
- [ ] Verificar despliegue del SHA correcto y recuperación para API, web y modelo.
- [ ] Ejecutar los tres casos y terminar informe final.

No es necesario incorporar MLflow, Airflow o un feature store independiente para cumplir la rúbrica. El repositorio ya posee registro de modelos y almacenamiento de vectores; primero conviene completar y demostrar su ciclo.

## Evidencia de esta sesión

- Resultados: [TF-IDF](../artifacts/experiments/course-u1/tfidf/report.md) y [BETO](../artifacts/experiments/course-u1/beto/report.md).
- [Pruebas funcionales con pesos reales](../artifacts/experiments/course-u1/evidence/model-functional.json): autenticación interna, carga/inferencia y fallo de reemplazo sin pérdida del modelo cargado.
- [Comprobación de producción](../artifacts/experiments/course-u1/evidence/production-smoke.json): frontend correcto; API/login agotaron el tiempo de espera.
- [Recuperación de producción](recuperacion-produccion.md): posteriormente pasaron las seis comprobaciones; BETO v1 y embeddings cargados. Corrección preventiva de liveness preparada y pendiente de despliegue.
- [Mantenimiento sin cambios](../artifacts/experiments/course-u1/evidence/maintenance-no-changes.json): se omitió entrenamiento.
- Los tres workflows pasaron validación estática con actionlint 1.7.12. Los checks locales no demuestran que GitHub haya ejecutado los workflows nuevos.

## Verificación tras publicar `3974f4a`

El 7 de septiembre de 2026 a las 04:08 UTC se verificaron las ejecuciones disparadas por el push:

- [CI correcto](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34081879616): API, web, ML y Quality gate terminaron con éxito.
- [Mantenimiento correcto](https://github.com/JaquelineRocio/historia-viva-peru-tfm/actions/runs/34081879646): se repitió el experimento TF-IDF sobre el snapshot académico. Se seleccionó C=4, con F1 macro de test 0.363; se archivaron informes y candidato. Producción no fue modificada por este workflow. Esto aún no demuestra reentrenamiento automático desde correcciones.
- [Comprobación de producción posterior](../artifacts/experiments/course-u1/evidence/production-smoke-post-push.json): las seis comprobaciones pasaron desde este equipo. No equivale a una ejecución del workflow Production smoke en GitHub, que continúa pendiente.
- `/api/health/live` respondió HTTP 200 con `status: ok` y `service: api`. Esto confirma que la ruta está disponible, pero no identifica el SHA exacto ni confirma la configuración del health check en el panel de Render.
- Vercel reportó éxito mientras CI seguía en curso. Falta configurar y demostrar que el despliegue espere a CI.

Los estados y SHA de las ejecuciones se conservan en [github-actions-post-push.json](../artifacts/experiments/course-u1/evidence/github-actions-post-push.json). Siguiente bloque: verificar el recorrido fuente → predicción → corrección persistida en producción.

### Incidencia al verificar el recorrido PDF

El 7 de septiembre de 2026 a las 04:11 UTC se creó el proyecto privado de prueba `9676bb4a-1e6d-44a5-9154-17814af4427e`. La carga de un PDF sintético de 2 511 bytes devolvió HTTP 500 y el proyecto quedó sin recursos. El extractor local pudo leer las tres páginas y generar tres segmentos. No se llegó a ejecutar procesamiento remoto ni revisión; no se modificaron fuentes existentes.

Además, la descarga del PDF existente `9154f7f7-86c9-4bad-bcba-47eaf54b93e1`, registrado con proveedor S3, devolvió HTTP 404. Los logs aportados de Render muestran `DatabaseTimeout` tanto al cargar como al descargar: el servicio S3 devolvió un timeout de su base de datos. La descarga repetida a las 04:14 UTC volvió a fallar. No se ha demostrado que el archivo esté eliminado ni que las credenciales sean incorrectas. Evidencia: [source-flow-failed.json](../artifacts/experiments/course-u1/evidence/source-flow-failed.json).

Se preparó una corrección local: los fallos de almacenamiento devuelven HTTP 503 con un mensaje claro; una descarga solo devuelve 404 por archivo ausente (`NoSuchKey` o `ENOENT`) o por referencia inexistente. Seis pruebas nuevas y la compilación pasaron. Esto no restaura el servicio de Supabase y aún no está desplegado.

[Supabase documenta DatabaseTimeout](https://supabase.com/docs/guides/storage/debugging/error-codes) como timeout al acceder a la base de datos de Storage. La causa operativa exacta sigue pendiente. El navegador integrado no estuvo disponible, por lo que la verificación visual sigue pendiente.

Actualización a las 04:17 UTC: la autora mostró el bucket con archivos en el panel de Supabase. La descarga repetida del PDF existente respondió 200. El PDF sintético se cargó en el proyecto de prueba y produjo tres segmentos con referencias de página, pero sin etiquetas sugeridas. El recurso privado es `f81c491d-766a-4a2d-8cb5-ae86ea5b7b25`; no debe incluirse en el corpus histórico.

La reclasificación devolvió «No hay modelo activo cargado». La consulta autenticada a Modal mostró BETO con `ready: false`, `status: error` y un fallo al importar `AutoModelForSequenceClassification` desde `transformers`. Embeddings y NER figuraban cargados. No se cambió el modelo ni se desplegó código durante estas comprobaciones. Evidencia: [source-flow-storage-recovered.json](../artifacts/experiments/course-u1/evidence/source-flow-storage-recovered.json).

El diagnóstico continuó con el arranque de BETO y la revisión del PDF de prueba, como se describe a continuación.

### Arranque de BETO y revisión persistida

En un nuevo arranque de Modal, BETO cargó sin cambiar sus pesos ni desplegar código. Se verificaron en el contenedor `transformers 4.57.6`, `torch 2.12.0+cpu` y `sentence-transformers 5.1.2`; la importación del clasificador funcionó en una comprobación separada. El error anterior fue intermitente. La carga en segundo plano permitía que peticiones concurrentes importaran las mismas dependencias; este es un riesgo identificado, no una causa reproducida de forma concluyente.

Se preparó una corrección local para terminar la carga de BETO durante el arranque ASGI antes de aceptar solicitudes. Si falla el modelo configurado, el arranque falla explícitamente y registra la excepción. También se fijó `transformers==4.57.6`, la versión observada en el contenedor. Las cinco pruebas nuevas y la suite ML completa (42 pruebas) pasaron. Se verificó además arranque e inferencia con pesos reales del candidato local, simulando solamente la descarga: [beto-startup-local.json](../artifacts/experiments/course-u1/evidence/beto-startup-local.json). Falta desplegar y probar esta corrección en Modal.

En producción, la reclasificación del PDF privado existente obtuvo tres predicciones. Se confirmó `no_relevante` en la página 3 y se comprobó su persistencia desde una sesión autenticada nueva. El archivo descargado coincidió byte por byte con el PDF cargado. [Evidencia del recorrido con reintento](../artifacts/experiments/course-u1/evidence/source-flow-reviewed.json). La revisión confirmó una etiqueta ya correcta; no demuestra la corrección de una predicción equivocada. El primer intento de clasificación falló, por lo que no se declara aprobada la ejecución automática completa.

Las correcciones quedaron registradas en `24f03be` (ML) y `0bc365a` (API). Siguiente paso: registrar estas evidencias, publicar los commits y, con autorización de la autora, desplegar ML y verificar un arranque nuevo con predicción automática. Permanecen pendientes la corrección de una etiqueta distinta y la comprobación visual de la interfaz.
