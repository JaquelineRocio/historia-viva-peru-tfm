-- =============================================================================
-- ddl.sql — Fuente de verdad del esquema (PostgreSQL 16)
-- TFM: Segmentación temática de videos educativos con BETO
-- =============================================================================
-- Convenciones :
--   * Soft delete: is_deleted + deleted_at + deleted_user_id (nunca DELETE físico)
--   * Auditoría:   created_user_id / updated_user_id / deleted_user_id = JWT.sub
--   * Toda query de lectura filtra WHERE is_deleted = false
--   * PKs UUID (pgcrypto: gen_random_uuid())
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS tfm_schema;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

SET search_path TO tfm_schema;

-- ─────────────────────────────────────────────────────────────────────────────
-- users — autenticación JWT usuario/contraseña (incluye usuario de prueba del TFM)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username          VARCHAR(80)  NOT NULL UNIQUE,
    hashed_password   VARCHAR(255) NOT NULL,          -- bcrypt
    display_name      VARCHAR(120),
    role              VARCHAR(20)  NOT NULL DEFAULT 'docente',  -- docente | admin
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    is_deleted        BOOLEAN      NOT NULL DEFAULT false,
    deleted_at        TIMESTAMPTZ,
    created_user_id   UUID,
    updated_user_id   UUID,
    deleted_user_id   UUID
);

-- ─────────────────────────────────────────────────────────────────────────────
-- videos — video de YouTube ingerido
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.videos (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    youtube_id            VARCHAR(20)  NOT NULL,
    url                   VARCHAR(500) NOT NULL,
    title                 VARCHAR(300),
    channel               VARCHAR(200),
    duration_sec          INTEGER,
    transcription_status  VARCHAR(20)  NOT NULL DEFAULT 'pending',  -- pending|processing|done|failed
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    is_deleted            BOOLEAN      NOT NULL DEFAULT false,
    deleted_at            TIMESTAMPTZ,
    created_user_id       UUID,
    updated_user_id       UUID,
    deleted_user_id       UUID
);
CREATE UNIQUE INDEX ux_videos_youtube_id ON tfm_schema.videos (youtube_id) WHERE is_deleted = false;

-- ─────────────────────────────────────────────────────────────────────────────
-- transcripts — transcripción de un video (api | whisper)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.transcripts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id          UUID NOT NULL REFERENCES tfm_schema.videos(id),
    language          VARCHAR(10),
    source            VARCHAR(10) NOT NULL,           -- api | whisper
    is_generated      BOOLEAN NOT NULL DEFAULT true,
    full_text         TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted        BOOLEAN NOT NULL DEFAULT false,
    deleted_at        TIMESTAMPTZ,
    created_user_id   UUID,
    updated_user_id   UUID,
    deleted_user_id   UUID
);
CREATE INDEX ix_transcripts_video ON tfm_schema.transcripts (video_id) WHERE is_deleted = false;

-- ─────────────────────────────────────────────────────────────────────────────
-- segments — fragmento de transcripción (ventana temporal); start/end → seek navegable
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.segments (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id          UUID NOT NULL REFERENCES tfm_schema.videos(id),
    transcript_id     UUID NOT NULL REFERENCES tfm_schema.transcripts(id),
    idx               INTEGER NOT NULL,
    start_sec         NUMERIC(10,3) NOT NULL,
    end_sec           NUMERIC(10,3) NOT NULL,
    text              TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted        BOOLEAN NOT NULL DEFAULT false,
    deleted_at        TIMESTAMPTZ,
    created_user_id   UUID,
    updated_user_id   UUID,
    deleted_user_id   UUID
);
CREATE INDEX ix_segments_video ON tfm_schema.segments (video_id) WHERE is_deleted = false;

-- ─────────────────────────────────────────────────────────────────────────────
-- labels_taxonomy — catálogo de subtemas (editable)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.labels_taxonomy (
    key               VARCHAR(60) PRIMARY KEY,        -- ej. participacion_indigena
    name              VARCHAR(120) NOT NULL,
    description       TEXT,
    color             VARCHAR(9),                     -- #RRGGBB
    sort_order        INTEGER NOT NULL DEFAULT 0,
    is_deleted        BOOLEAN NOT NULL DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- segment_labels — etiqueta asignada a un segmento (human=gold | model=predicción)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.segment_labels (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id        UUID NOT NULL REFERENCES tfm_schema.segments(id),
    label_key         VARCHAR(60) NOT NULL REFERENCES tfm_schema.labels_taxonomy(key),
    source            VARCHAR(10) NOT NULL,           -- human | model
    confidence        NUMERIC(5,4),                   -- solo predicciones
    is_gold           BOOLEAN NOT NULL DEFAULT false, -- confirmada por humano
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted        BOOLEAN NOT NULL DEFAULT false,
    deleted_at        TIMESTAMPTZ,
    created_user_id   UUID,
    updated_user_id   UUID,
    deleted_user_id   UUID
);
-- una etiqueta "activa" por segmento
CREATE UNIQUE INDEX ux_segment_label_active ON tfm_schema.segment_labels (segment_id) WHERE is_deleted = false;

-- ─────────────────────────────────────────────────────────────────────────────
-- datasets — snapshot inmutable (reproducibilidad y comparación entre versiones)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.datasets (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  VARCHAR(150) NOT NULL,
    description           TEXT,
    n_samples             INTEGER NOT NULL DEFAULT 0,
    class_distribution    JSONB,
    split_config          JSONB,                      -- {train,val,test,stratify,seed}
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted            BOOLEAN NOT NULL DEFAULT false,
    deleted_at            TIMESTAMPTZ,
    created_user_id       UUID,
    updated_user_id       UUID,
    deleted_user_id       UUID
);

-- dataset_items — congela segmento + label + split
CREATE TABLE tfm_schema.dataset_items (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id        UUID NOT NULL REFERENCES tfm_schema.datasets(id),
    segment_id        UUID NOT NULL REFERENCES tfm_schema.segments(id),
    label_key         VARCHAR(60) NOT NULL REFERENCES tfm_schema.labels_taxonomy(key),
    text              TEXT NOT NULL,                  -- copia congelada del texto
    split             VARCHAR(10) NOT NULL            -- train | val | test
);
CREATE INDEX ix_dataset_items_dataset ON tfm_schema.dataset_items (dataset_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- model_versions — versión de modelo (linaje para fine-tuning incremental)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.model_versions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_tag       VARCHAR(30) NOT NULL,           -- v1, v2, ...
    dataset_id        UUID REFERENCES tfm_schema.datasets(id),
    base_model        VARCHAR(200) NOT NULL,          -- BETO o id de versión padre
    parent_version_id UUID REFERENCES tfm_schema.model_versions(id),
    hyperparams       JSONB,                          -- {epochs, lr, batch_size, max_len, seed}
    artifact_path     VARCHAR(400),                   -- storage/models/vN/
    status            VARCHAR(20) NOT NULL DEFAULT 'training',  -- training|ready|failed
    is_active         BOOLEAN NOT NULL DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted        BOOLEAN NOT NULL DEFAULT false,
    deleted_at        TIMESTAMPTZ,
    created_user_id   UUID,
    updated_user_id   UUID,
    deleted_user_id   UUID
);
CREATE UNIQUE INDEX ux_model_active ON tfm_schema.model_versions (is_active) WHERE is_active = true AND is_deleted = false;

-- ─────────────────────────────────────────────────────────────────────────────
-- training_jobs — NestJS espeja el estado del servicio ML por polling
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.training_jobs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id  UUID REFERENCES tfm_schema.model_versions(id),
    dataset_id        UUID REFERENCES tfm_schema.datasets(id),
    ml_job_id         VARCHAR(80),                    -- id del job en el servicio ML
    status            VARCHAR(20) NOT NULL DEFAULT 'queued',  -- queued|running|done|failed|cancelled
    progress          INTEGER NOT NULL DEFAULT 0,     -- 0-100
    current_epoch     INTEGER,
    logs              TEXT,
    error             TEXT,
    started_at        TIMESTAMPTZ,
    finished_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- training_metrics — métricas por versión (y por época opcional)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE tfm_schema.training_metrics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_version_id    UUID NOT NULL REFERENCES tfm_schema.model_versions(id),
    epoch               INTEGER,                      -- NULL = métrica final
    split               VARCHAR(10) NOT NULL,         -- val | test
    accuracy            NUMERIC(6,5),
    precision_macro     NUMERIC(6,5),
    recall_macro        NUMERIC(6,5),
    f1_macro            NUMERIC(6,5),
    f1_weighted         NUMERIC(6,5),
    f1_macro_ci95       JSONB,
    results_by_source_type JSONB,
    baseline_name       VARCHAR(80),
    baseline_f1_macro   NUMERIC(6,5),
    baseline_dataset_sha256 VARCHAR(64),
    exceeds_baseline    BOOLEAN,
    per_class_metrics   JSONB,
    confusion_matrix    JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_metrics_version ON tfm_schema.training_metrics (model_version_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Seed inicial de la taxonomía de subtemas (Independencia del Perú)
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO tfm_schema.labels_taxonomy (key, name, description, color, sort_order) VALUES
  ('antecedentes',            'Antecedentes',                'Contexto previo: reformas borbónicas, ideas ilustradas, rebeliones tempranas.', '#6366f1', 1),
  ('causas_internas',         'Causas internas',             'Descontento criollo/indígena, factores económicos y sociales locales.',        '#10b981', 2),
  ('participacion_indigena',  'Participación indígena',      'Rol de pueblos indígenas y líderes andinos en el proceso.',                     '#f59e0b', 3),
  ('campanias_militares',     'Campañas militares',          'Expediciones, batallas, corrientes libertadoras del sur y del norte.',          '#ef4444', 4),
  ('personajes',              'Personajes',                  'San Martín, Bolívar, Sucre, próceres y precursores.',                           '#8b5cf6', 5),
  ('consecuencias_politicas', 'Consecuencias políticas',     'Proclamación, primeros gobiernos, organización de la república.',               '#0ea5e9', 6)
ON CONFLICT (key) DO NOTHING;
