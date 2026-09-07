# Informe de entrenamiento y puesta en producción — Unidad I

Autora: Jaqueline Ramos. Proyecto: Historia Viva Perú.

Estado: documento de trabajo con resultados medidos y pendientes explícitos.

## 1. Problema y comportamiento de la aplicación

Los docentes necesitan localizar evidencia histórica dentro de PDF y videos extensos. La aplicación extrae texto, lo segmenta y conserva página o tiempo de origen. Predice un subtema con BETO, permite revisión docente y recupera fragmentos con citas. El alcance temático es la Independencia y formación republicana del Perú, 1780–1842.

La predicción es una sugerencia corregible, no una validación histórica. El sistema también extrae años por reglas y personas/lugares mediante NER; utiliza embeddings para búsqueda semántica. Esos componentes no sustituyen la evaluación del clasificador temático.

## 2. Dataset y partición

Snapshot: `artifacts/datasets/gold-v1-source-aware.json`, identificador `9e99a778-7fab-4e29-bd8b-45466c3728dc`.

- 814 segmentos revisados de diez fuentes: 670 PDF y 144 YouTube.
- Train: 596; validación: 81; test: 137.
- Siete clases: contexto colonial; crisis e ideas emancipadoras; participación social y regional; campañas y conflictos militares; liderazgos, diplomacia y proyectos; organización y consecuencias republicanas; no relevante.
- Cada fuente pertenece a un único conjunto. Auditoría local: cero fuentes compartidas y cero textos normalizados idénticos entre conjuntos.
- Etiquetado y segunda revisión asistidos por IA; no hubo historiador independiente. Kappa documentado: 0.651, que no equivale a validación externa humana.

La distribución completa por clase y fuente se conserva en `dataset-audit.json` de cada ejecución. Solo cuatro ejemplos de validación pertenecen a campañas y cuatro a liderazgos; esta escasez aumenta la incertidumbre de la selección.

## 3. Características y modelos

**Baseline TF-IDF:** minúsculas, normalización de acentos, palabras y bigramas, frecuencia mínima de dos documentos, máximo 50 000 características y frecuencia de término sublineal. Regresión logística con pesos balanceados, solver lbfgs y hasta 2 000 iteraciones. El vocabulario se ajusta exclusivamente con train.

**BETO:** `dccuchile/bert-base-spanish-wwm-cased`, revisión fijada en la configuración del experimento. Tokenización en subpalabras con máximo 192 tokens, padding y máscara de atención. La cabeza de clasificación predice siete categorías y el ajuste fino modifica también las representaciones de BETO. La confianza proviene de softmax; no se ha demostrado que esté calibrada.

## 4. Optimización reproducible

El código `app.ml.experiments` recibe un snapshot y un JSON de configuración. Valida fuente, etiquetas, cobertura de clases y duplicados antes de entrenar. Selecciona por F1 macro de validación; los empates conservan el orden predefinido. Guarda la decisión antes de evaluar al ganador en test.

| Modelo/configuración | Parámetro comparado | F1 macro validación |
|---|---|---:|
| TF-IDF c025 | C=0.25 | 0.26736 |
| TF-IDF c1 | C=1 | 0.26751 |
| TF-IDF c4 | C=4 | **0.29004** |

TF-IDF seleccionado: C=4. F1 macro de test: **0.36300**. El baseline fijo C=1 obtiene **0.35343**, consistente con el resultado histórico. Los archivos medidos se conservan en `outputs/experiments/tfidf-u1` y su copia ligera versionable.

Para BETO se predefinieron tres tasas de aprendizaje: 1e-5, 2e-5 y 3e-5. Cada configuración ejecuta tres épocas; guarda la época con mejor F1 de validación. Parámetros comunes: semilla 42, microbatch 2, acumulación de gradientes 8 (batch efectivo 16), longitud 192, AdamW, weight decay 0.01, calentamiento del 10% de los pasos y descenso lineal posterior. La precisión mixta y gradient checkpointing permiten trabajar en una RTX 3050 Laptop de 4 GB.

| Configuración BETO | Tasa de aprendizaje | Mejor época | F1 macro validación |
|---|---:|---:|---:|
| beto-lr1e5 | 0.00001 | 2 | 0.34239 |
| beto-lr2e5 | 0.00002 | 2 | **0.43766** |
| beto-lr3e5 | 0.00003 | 3 | 0.36327 |

Ganador por validación: **beto-lr2e5, época 2**. F1 macro de test: **0.31066**. No supera el baseline fijo 0.35343 ni el BETO v1 documentado 0.42461; permanece experimental y no se activa en producción. Un resultado inferior también es evidencia válida de selección y control de calidad. No se evaluaron en test las otras dos configuraciones para intentar elegir otra a posteriori.

La comparación nueva cambia además el régimen de entrenamiento respecto de v1; no permite atribuir toda diferencia exclusivamente a la tasa de aprendizaje. La caída entre validación y test indica generalización limitada en este experimento. No justifica seguir ajustando parámetros mirando test.

## 5. Resultados históricos y límites

BETO v1 documentado: F1 macro **0.42461**, accuracy **0.50365**. Supera el baseline histórico, pero no cumple el criterio interno de F1 macro ≥0.70 y F1 por clase ≥0.50. Se conserva como experimental. El umbral no está impuesto por las indicaciones del curso, sino por el protocolo del proyecto.

El test académico ya fue consultado para v1; esta nueva comparación sobre el mismo test sirve como evaluación reproducible, pero no como prueba externa completamente nueva. Para futuras mejoras debe evitarse ajustar reiteradamente el modelo mirando ese resultado. Se necesita ampliar y revisar manualmente el corpus, especialmente clases confundidas.

## 6. Puesta en producción

Arquitectura declarada: React/Vercel → NestJS/Render → PostgreSQL+pgvector/Neon; PDF en Supabase Storage y servicio ML en Modal; pesos de referencia en Hugging Face.

Comprobación inicial: el frontend público respondió HTTP 200. Las solicitudes a `/api/health` y al login de Render agotaron los tiempos de espera. En ese momento no se pudo verificar el recorrido completo en producción; la recuperación posterior se describe a continuación.

El informe inicial HTTP está en `outputs/evidence/production-smoke.json`. No contiene credenciales ni tokens. La conexión al navegador integrado no estuvo disponible por un error del entorno, por lo que no se generaron capturas de UI.

Actualización de recuperación (7 de septiembre, 03:30 UTC): API y ML respondieron
correctamente y pasaron las seis comprobaciones de producción, incluido login,
acceso al proyecto y abstención. BETO v1 y embeddings figuran cargados en Modal.
Se conserva la evidencia en `artifacts/experiments/course-u1/evidence/production-smoke-recovered.json`.
No fue necesario modificar `ML_SERVICE_URL` ni el modelo de producción. La causa
exacta del 404 inicial continúa sin confirmar; la corrección preventiva del chequeo
de salud está probada localmente y pendiente de despliegue.

Para completar esta sección: registrar la versión desplegada, verificar la nueva ruta de salud tras su despliegue y completar el recorrido de fuente y corrección de la tabla siguiente. La comprobación de producción debe repetirse después del despliegue.

## 7. Pruebas de funcionamiento

| Caso | Pasos | Resultado esperado | Estado |
|---|---|---|---|
| U1-01: fuente y corrección | Añadir PDF/YouTube válido; procesar; abrir cita; corregir tema; recargar | Segmentos con referencia y predicción; corrección persistida | Pendiente del recorrido completo en producción |
| U1-02: ausencia de respaldo | Consultar relación de Apolo 11 con la Independencia peruana | Abstención y lista de evidencias vacía | Verificado en producción tras la recuperación |

Verificación de software local: API **31 pruebas** y compilación correctas; web lint y compilación correctos; ML **37 pruebas** correctas (24 existentes y 13 nuevas). Las nuevas pruebas verifican aislamiento del test, bloqueo de fugas, preservación del snapshot, rechazo de candidatos, mantenimiento con/sin cambios y comprobaciones de producción ante fallos simulados.

También se ejecutaron tres casos contra FastAPI local con los pesos reales del candidato: rechazo de acceso sin token (401), carga del modelo y predicción válida (200), y carga de un modelo inexistente (404) seguida de inferencia idéntica con el modelo previo. Se verificó ejecución y contrato de respuesta, no exactitud histórica de esas frases ni recuperación del despliegue remoto. Evidencia: `artifacts/experiments/course-u1/evidence/model-functional.json`.

Las pruebas locales no sustituyen los recorridos completos de producción de la tabla.

## 8. Evidencias y reproducción

- Plan y comandos: [README del curso](README.md).
- Guion en inglés: [demo-en.md](demo-en.md).
- Configuraciones: `configs/experiments/tfidf.json` y `beto.json`.
- Informes por ejecución: auditoría, configuración, selección, métricas por clase, matriz de confusión, dependencias, commit y estado del árbol de trabajo.
- Los pesos permanecen fuera de Git. Los workflows archivan el candidato ganador y los informes por separado.

Este documento deberá cerrarse con evidencias del recorrido completo en producción antes de declararse entrega terminada. Los experimentos nuevos y sus informes ligeros se archivan en `artifacts/experiments/course-u1/`.
