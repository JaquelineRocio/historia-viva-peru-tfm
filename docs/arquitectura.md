# Arquitectura — TFM: Segmentación temática de videos con BETO

## Visión

App web para docentes de historia: transcribe videos educativos largos de YouTube
sobre la Independencia del Perú, los segmenta por ventanas temporales y clasifica
cada segmento en subtemas usando **BETO** (BERT en español). El docente localiza
fragmentos temáticos con **timestamps navegables**.

Ciclo central (human-in-the-loop / active learning):
`transcribir → segmentar → etiquetar → entrenar → clasificar → corregir → reentrenar`.

## Arquitectura híbrida

Elegimos **NestJS** (TypeScript) para el backend, pero el núcleo ML es Python
(BETO/Whisper/scikit-learn). Por eso separamos responsabilidades:

```
React 19 (Vite) ──REST/JSON + polling──▶ NestJS API (orquestador, dueño de la BD)
                                              │
                       (Postgres via TypeORM) ◀┤
                                              │  HTTP interno
                                              │  (MlServicePort → HttpMlAdapter)
                                              ▼
                                   Servicio ML (Python + FastAPI)
                                   - transcripción (youtube-transcript-api → Whisper)
                                   - segmentación por ventanas
                                   - fine-tuning BETO (jobs async)
                                   - inferencia (modelo activo en memoria)
                                   - métricas (scikit-learn)
                                              │
                                              ▼
                                   Volumen: storage/models/vN/
```

- **NestJS** = fuente de verdad (auth JWT, CRUD, estado de jobs). No computa ML;
  delega vía `MlServicePort` (puerto de salida) implementado por `HttpMlAdapter`.
- **Servicio ML** = cómputo puro invocado por HTTP. Jobs largos async.
- **Entrenamiento pesado** = GPU gratis en Colab/Kaggle (mismo `trainer.py`),
  pesos importados vía `POST /models/import`. Producción solo hace inferencia (CPU).

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | React 19 · Vite · TypeScript · TanStack Query · Tailwind · react-youtube · Recharts |
| Backend  | NestJS 10 · TypeScript · TypeORM · PostgreSQL 16 · JWT (bcrypt) · Swagger |
| ML       | Python 3.11 · FastAPI · HuggingFace Transformers (BETO) · scikit-learn · faster-whisper · youtube-transcript-api |
| Infra    | Docker Compose (dev) · Vercel (web) · Render/Railway (api + ml + postgres) |

## Modelo de datos

Ver [apps/api/claude_workspace/architecture/ddl.sql](../apps/api/claude_workspace/architecture/ddl.sql)
(fuente de verdad). Tablas clave: `videos, transcripts, segments, labels_taxonomy,
segment_labels, datasets, dataset_items, model_versions, training_jobs,
training_metrics, users`. Convenciones: soft delete + auditoría por `JWT.sub`.

Decisiones de diseño:
- **Snapshot inmutable de dataset** (`dataset_items` congela texto+label+split) →
  reproducibilidad y comparación justa entre versiones.
- **`segment_labels.source`** distingue etiqueta humana (gold) de predicción del
  modelo → habilita active learning.
- **`model_versions.parent_version_id`** → fine-tuning incremental (linaje).

## Estado (Día 1)

- ✅ Servicio ML: transcripción (youtube-transcript-api v1.2.4) + segmentación por
  ventanas, verificados en videos reales de la Independencia del Perú.
- ✅ `ddl.sql` + docker-compose (postgres con seed del DDL + servicio ML).
- ⏳ Scaffold NestJS + React, fallback Whisper, pipeline de entrenamiento (Días 2–4).
