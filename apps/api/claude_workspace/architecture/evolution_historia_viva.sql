CREATE SCHEMA IF NOT EXISTS tfm_schema;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- Neon instala las extensiones compartidas habitualmente en `public`. TypeORM
-- configura `tfm_schema` como esquema por defecto, por lo que debemos conservar
-- ambos en el search_path para resolver operator classes como gin_trgm_ops.
SET search_path TO tfm_schema, public;

CREATE TABLE IF NOT EXISTS tfm_schema.projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(200) NOT NULL,
  description TEXT,
  period_start INTEGER,
  period_end INTEGER,
  is_public BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  created_user_id UUID,
  updated_user_id UUID
);

CREATE TABLE IF NOT EXISTS tfm_schema.resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES tfm_schema.projects(id),
  type VARCHAR(20) NOT NULL CHECK (type IN ('youtube', 'pdf')),
  title VARCHAR(300) NOT NULL,
  author VARCHAR(200),
  source_url VARCHAR(1000),
  storage_path VARCHAR(1000),
  original_filename VARCHAR(300),
  mime_type VARCHAR(120),
  size_bytes BIGINT,
  checksum VARCHAR(64),
  license VARCHAR(80),
  rights_confirmed BOOLEAN NOT NULL DEFAULT false,
  processing_status VARCHAR(30) NOT NULL DEFAULT 'pending',
  processing_error TEXT,
  language VARCHAR(10) DEFAULT 'es',
  publication_status VARCHAR(20) NOT NULL DEFAULT 'private',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  created_user_id UUID,
  updated_user_id UUID
);

CREATE TABLE IF NOT EXISTS tfm_schema.resource_segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL REFERENCES tfm_schema.resources(id),
  idx INTEGER NOT NULL,
  locator_type VARCHAR(20) NOT NULL,
  start_sec NUMERIC(10,3),
  end_sec NUMERIC(10,3),
  page_start INTEGER,
  page_end INTEGER,
  text TEXT NOT NULL,
  suggested_label_key VARCHAR(60),
  suggested_confidence NUMERIC(6,5),
  review_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  reviewed_label_key VARCHAR(60),
  reviewed_user_id UUID,
  reviewed_at TIMESTAMPTZ,
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(resource_id, idx)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_resources_url ON tfm_schema.resources(project_id, source_url)
  WHERE source_url IS NOT NULL AND is_deleted = false;
CREATE UNIQUE INDEX IF NOT EXISTS ux_resources_checksum ON tfm_schema.resources(project_id, checksum)
  WHERE checksum IS NOT NULL AND is_deleted = false;
CREATE INDEX IF NOT EXISTS ix_resource_segments_search
  ON tfm_schema.resource_segments USING gin(to_tsvector('spanish', text));
CREATE INDEX IF NOT EXISTS ix_resource_segments_trgm
  ON tfm_schema.resource_segments USING gin(text gin_trgm_ops);

INSERT INTO tfm_schema.projects(name, description, period_start, period_end, is_public)
SELECT 'Independencia y formación republicana', 'Proyecto inicial de Historia Viva Perú', 1780, 1842, false
WHERE NOT EXISTS (SELECT 1 FROM tfm_schema.projects WHERE is_deleted = false);

ALTER TABLE tfm_schema.dataset_items ALTER COLUMN segment_id DROP NOT NULL;
ALTER TABLE tfm_schema.dataset_items
  ADD COLUMN IF NOT EXISTS resource_segment_id UUID REFERENCES tfm_schema.resource_segments(id);

CREATE TABLE IF NOT EXISTS tfm_schema.collections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES tfm_schema.projects(id),
  name VARCHAR(200) NOT NULL,
  description TEXT,
  is_public BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  created_user_id UUID,
  updated_user_id UUID
);

CREATE TABLE IF NOT EXISTS tfm_schema.collection_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id UUID NOT NULL REFERENCES tfm_schema.collections(id),
  resource_segment_id UUID NOT NULL REFERENCES tfm_schema.resource_segments(id),
  note TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_user_id UUID,
  UNIQUE(collection_id, resource_segment_id)
);

CREATE TABLE IF NOT EXISTS tfm_schema.publication_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL REFERENCES tfm_schema.resources(id),
  status VARCHAR(20) NOT NULL DEFAULT 'proposed',
  note TEXT,
  requested_user_id UUID,
  reviewed_user_id UUID,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS tfm_schema.audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id UUID,
  action VARCHAR(80) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  entity_id UUID,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE tfm_schema.resource_segments
  ADD COLUMN IF NOT EXISTS embedding vector(384),
  ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(200),
  ADD COLUMN IF NOT EXISTS embedded_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS ix_resource_segments_embedding_hnsw
  ON tfm_schema.resource_segments USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS tfm_schema.entity_mentions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_segment_id UUID NOT NULL REFERENCES tfm_schema.resource_segments(id) ON DELETE CASCADE,
  entity_type VARCHAR(30) NOT NULL CHECK (entity_type IN ('person', 'place', 'organization', 'date', 'period', 'other')),
  mention_text VARCHAR(300) NOT NULL,
  normalized_value VARCHAR(300) NOT NULL,
  char_start INTEGER,
  char_end INTEGER,
  confidence NUMERIC(6,5),
  year_start INTEGER,
  year_end INTEGER,
  extraction_method VARCHAR(30) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_entity_mentions_segment
  ON tfm_schema.entity_mentions(resource_segment_id);
CREATE INDEX IF NOT EXISTS ix_entity_mentions_filter
  ON tfm_schema.entity_mentions(entity_type, normalized_value);
CREATE INDEX IF NOT EXISTS ix_entity_mentions_year
  ON tfm_schema.entity_mentions(year_start, year_end)
  WHERE entity_type IN ('date', 'period');

ALTER TABLE tfm_schema.entity_mentions
  ADD COLUMN IF NOT EXISTS is_human BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS created_user_id UUID,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE tfm_schema.resource_segments
  ADD COLUMN IF NOT EXISTS entities_reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS entities_reviewed_user_id UUID;

-- Historia Viva v2: taxonomía, membresías, procesamiento reproducible y feedback.
CREATE TABLE IF NOT EXISTS tfm_schema.taxonomy_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID REFERENCES tfm_schema.projects(id),
  version_tag VARCHAR(30) NOT NULL, name VARCHAR(160) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), created_user_id UUID, UNIQUE(project_id, version_tag)
);
CREATE TABLE IF NOT EXISTS tfm_schema.project_memberships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), project_id UUID NOT NULL REFERENCES tfm_schema.projects(id),
  user_id UUID NOT NULL REFERENCES tfm_schema.users(id), role VARCHAR(20) NOT NULL CHECK (role IN ('collaborator', 'curator', 'admin')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(project_id, user_id)
);
CREATE TABLE IF NOT EXISTS tfm_schema.resource_processing_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), resource_id UUID NOT NULL REFERENCES tfm_schema.resources(id),
  status VARCHAR(20) NOT NULL DEFAULT 'processing', pipeline_version VARCHAR(30) NOT NULL DEFAULT 'v2',
  segment_count INTEGER NOT NULL DEFAULT 0, error TEXT, started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ, created_user_id UUID
);
CREATE TABLE IF NOT EXISTS tfm_schema.evidence_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), resource_segment_id UUID NOT NULL REFERENCES tfm_schema.resource_segments(id),
  user_id UUID NOT NULL REFERENCES tfm_schema.users(id), value VARCHAR(20) NOT NULL CHECK (value IN ('useful', 'irrelevant', 'incorrect')),
  note TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(resource_segment_id, user_id)
);
ALTER TABLE tfm_schema.resource_segments DROP CONSTRAINT IF EXISTS resource_segments_resource_id_idx_key;
CREATE UNIQUE INDEX IF NOT EXISTS ux_resource_segments_active_idx
  ON tfm_schema.resource_segments(resource_id, idx) WHERE is_deleted = false;
ALTER TABLE tfm_schema.entity_mentions ADD COLUMN IF NOT EXISTS is_out_of_scope BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE tfm_schema.datasets ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES tfm_schema.projects(id), ADD COLUMN IF NOT EXISTS taxonomy_version_id UUID REFERENCES tfm_schema.taxonomy_versions(id);
ALTER TABLE tfm_schema.model_versions ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES tfm_schema.projects(id), ADD COLUMN IF NOT EXISTS taxonomy_version_id UUID REFERENCES tfm_schema.taxonomy_versions(id), ADD COLUMN IF NOT EXISTS recommendation_status VARCHAR(20) NOT NULL DEFAULT 'experimental';
INSERT INTO tfm_schema.taxonomy_versions(project_id, version_tag, name, is_active)
SELECT p.id, 'v1-1780-1842', 'Independencia y formación republicana 1780–1842', true FROM tfm_schema.projects p WHERE p.is_deleted = false
ON CONFLICT (project_id, version_tag) DO UPDATE SET is_active = EXCLUDED.is_active;
UPDATE tfm_schema.labels_taxonomy SET is_deleted = true WHERE key IN ('antecedentes', 'causas_internas', 'participacion_indigena', 'campanias_militares', 'personajes', 'consecuencias_politicas');
INSERT INTO tfm_schema.labels_taxonomy(key, name, description, color, sort_order, is_deleted) VALUES
  ('contexto_colonial_antecedentes', 'Contexto colonial y antecedentes', 'Estructura colonial, reformas, rebeliones previas y contexto internacional.', '#4f46e5', 1, false),
  ('crisis_ideas_emancipadoras', 'Crisis e ideas emancipadoras', 'Crisis monárquica, ideas políticas, conspiraciones y causas.', '#0891b2', 2, false),
  ('participacion_social_regional', 'Participación social y regional', 'Participación indígena, afroperuana, popular, femenina y regional.', '#d97706', 3, false),
  ('campanias_conflictos_militares', 'Campañas y conflictos militares', 'Expediciones, batallas, ejércitos y estrategia militar.', '#dc2626', 4, false),
  ('liderazgos_diplomacia_proyectos', 'Liderazgos, diplomacia y proyectos', 'Decisiones, negociaciones y proyectos de los actores históricos.', '#7c3aed', 5, false),
  ('organizacion_consecuencias_republicanas', 'Organización y consecuencias republicanas', 'Instituciones, constituciones y formación estatal entre 1821 y 1842.', '#059669', 6, false),
  ('no_relevante', 'No relevante', 'Portadas, índices, bibliografía, ruido o contenido fuera del alcance.', '#64748b', 7, false)
ON CONFLICT (key) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, color = EXCLUDED.color, sort_order = EXCLUDED.sort_order, is_deleted = false;
INSERT INTO tfm_schema.project_memberships(project_id, user_id, role)
SELECT p.id, u.id, CASE WHEN u.role = 'admin' THEN 'admin' ELSE 'curator' END FROM tfm_schema.projects p CROSS JOIN tfm_schema.users u
WHERE p.is_deleted = false AND u.is_deleted = false ON CONFLICT (project_id, user_id) DO NOTHING;

-- Historia Viva v2: taxonomía, membresías, procesamiento reproducible y feedback.
CREATE TABLE IF NOT EXISTS tfm_schema.taxonomy_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES tfm_schema.projects(id),
  version_tag VARCHAR(30) NOT NULL,
  name VARCHAR(160) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_user_id UUID,
  UNIQUE(project_id, version_tag)
);

CREATE TABLE IF NOT EXISTS tfm_schema.project_memberships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES tfm_schema.projects(id),
  user_id UUID NOT NULL REFERENCES tfm_schema.users(id),
  role VARCHAR(20) NOT NULL CHECK (role IN ('collaborator', 'curator', 'admin')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(project_id, user_id)
);

CREATE TABLE IF NOT EXISTS tfm_schema.resource_processing_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL REFERENCES tfm_schema.resources(id),
  status VARCHAR(20) NOT NULL DEFAULT 'processing',
  pipeline_version VARCHAR(30) NOT NULL DEFAULT 'v2',
  segment_count INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  created_user_id UUID
);

CREATE TABLE IF NOT EXISTS tfm_schema.evidence_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_segment_id UUID NOT NULL REFERENCES tfm_schema.resource_segments(id),
  user_id UUID NOT NULL REFERENCES tfm_schema.users(id),
  value VARCHAR(20) NOT NULL CHECK (value IN ('useful', 'irrelevant', 'incorrect')),
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(resource_segment_id, user_id)
);

ALTER TABLE tfm_schema.entity_mentions
  ADD COLUMN IF NOT EXISTS is_out_of_scope BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE tfm_schema.datasets
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES tfm_schema.projects(id),
  ADD COLUMN IF NOT EXISTS taxonomy_version_id UUID REFERENCES tfm_schema.taxonomy_versions(id);

ALTER TABLE tfm_schema.model_versions
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES tfm_schema.projects(id),
  ADD COLUMN IF NOT EXISTS taxonomy_version_id UUID REFERENCES tfm_schema.taxonomy_versions(id),
  ADD COLUMN IF NOT EXISTS recommendation_status VARCHAR(20) NOT NULL DEFAULT 'experimental';

INSERT INTO tfm_schema.taxonomy_versions(project_id, version_tag, name, is_active)
SELECT p.id, 'v1-1780-1842', 'Independencia y formación republicana 1780–1842', true
FROM tfm_schema.projects p WHERE p.is_deleted = false
ON CONFLICT (project_id, version_tag) DO UPDATE SET is_active = EXCLUDED.is_active;

-- La taxonomía anterior se conserva para snapshots legacy, pero deja de mostrarse.
UPDATE tfm_schema.labels_taxonomy SET is_deleted = true
WHERE key IN ('antecedentes', 'causas_internas', 'participacion_indigena',
              'campanias_militares', 'personajes', 'consecuencias_politicas');

INSERT INTO tfm_schema.labels_taxonomy(key, name, description, color, sort_order, is_deleted) VALUES
  ('contexto_colonial_antecedentes', 'Contexto colonial y antecedentes', 'Estructura colonial, reformas, rebeliones previas y contexto internacional.', '#4f46e5', 1, false),
  ('crisis_ideas_emancipadoras', 'Crisis e ideas emancipadoras', 'Crisis monárquica, ideas políticas, conspiraciones y causas.', '#0891b2', 2, false),
  ('participacion_social_regional', 'Participación social y regional', 'Participación indígena, afroperuana, popular, femenina y regional.', '#d97706', 3, false),
  ('campanias_conflictos_militares', 'Campañas y conflictos militares', 'Expediciones, batallas, ejércitos y estrategia militar.', '#dc2626', 4, false),
  ('liderazgos_diplomacia_proyectos', 'Liderazgos, diplomacia y proyectos', 'Decisiones, negociaciones y proyectos de los actores históricos.', '#7c3aed', 5, false),
  ('organizacion_consecuencias_republicanas', 'Organización y consecuencias republicanas', 'Instituciones, constituciones y formación estatal entre 1821 y 1842.', '#059669', 6, false),
  ('no_relevante', 'No relevante', 'Portadas, índices, bibliografía, ruido o contenido fuera del alcance.', '#64748b', 7, false)
ON CONFLICT (key) DO UPDATE SET
  name = EXCLUDED.name, description = EXCLUDED.description, color = EXCLUDED.color,
  sort_order = EXCLUDED.sort_order, is_deleted = false;

INSERT INTO tfm_schema.project_memberships(project_id, user_id, role)
SELECT p.id, u.id,
       CASE WHEN u.role = 'admin' THEN 'admin'
            WHEN u.role IN ('curador', 'curator') THEN 'curator'
            ELSE 'collaborator' END
FROM tfm_schema.projects p CROSS JOIN tfm_schema.users u
WHERE p.is_deleted = false AND u.is_deleted = false
ON CONFLICT (project_id, user_id) DO NOTHING;

-- Campañas reproducibles para la segunda revisión independiente del 20 %.
CREATE TABLE IF NOT EXISTS tfm_schema.annotation_validation_campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES tfm_schema.projects(id),
  name VARCHAR(160) NOT NULL,
  sample_rate NUMERIC(5,4) NOT NULL DEFAULT 0.20,
  seed INTEGER NOT NULL DEFAULT 42,
  status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ,
  created_user_id UUID REFERENCES tfm_schema.users(id)
);

CREATE TABLE IF NOT EXISTS tfm_schema.annotation_validation_samples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES tfm_schema.annotation_validation_campaigns(id) ON DELETE CASCADE,
  resource_segment_id UUID NOT NULL REFERENCES tfm_schema.resource_segments(id),
  primary_label_key VARCHAR(80) NOT NULL REFERENCES tfm_schema.labels_taxonomy(key),
  primary_user_id UUID REFERENCES tfm_schema.users(id),
  secondary_label_key VARCHAR(80) REFERENCES tfm_schema.labels_taxonomy(key),
  secondary_user_id UUID REFERENCES tfm_schema.users(id),
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(campaign_id, resource_segment_id)
);

CREATE INDEX IF NOT EXISTS annotation_validation_samples_campaign_idx
  ON tfm_schema.annotation_validation_samples(campaign_id, secondary_label_key);

-- Selección reproducible de candidatos para la primera anotación gold.
CREATE TABLE IF NOT EXISTS tfm_schema.primary_annotation_campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES tfm_schema.projects(id),
  name VARCHAR(160) NOT NULL,
  target_count INTEGER NOT NULL CHECK (target_count BETWEEN 1 AND 2000),
  seed INTEGER NOT NULL DEFAULT 42,
  max_per_source INTEGER NOT NULL DEFAULT 150 CHECK (max_per_source BETWEEN 1 AND 500),
  status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ,
  created_user_id UUID REFERENCES tfm_schema.users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS primary_annotation_campaigns_one_open_idx
  ON tfm_schema.primary_annotation_campaigns(project_id) WHERE status = 'open';

CREATE TABLE IF NOT EXISTS tfm_schema.primary_annotation_samples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES tfm_schema.primary_annotation_campaigns(id) ON DELETE CASCADE,
  resource_segment_id UUID NOT NULL REFERENCES tfm_schema.resource_segments(id),
  position INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(campaign_id, resource_segment_id),
  UNIQUE(campaign_id, position)
);

CREATE INDEX IF NOT EXISTS primary_annotation_samples_campaign_idx
  ON tfm_schema.primary_annotation_samples(campaign_id, position);

ALTER TABLE tfm_schema.resources
  ADD COLUMN IF NOT EXISTS corpus_status VARCHAR(20) NOT NULL DEFAULT 'candidate',
  ADD COLUMN IF NOT EXISTS source_style VARCHAR(30),
  ADD COLUMN IF NOT EXISTS corpus_notes TEXT;

-- Almacenamiento portable: las instalaciones existentes conservan storage_path
-- y las nuevas pueden utilizar una clave de objeto S3.
ALTER TABLE tfm_schema.resources
  ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(20),
  ADD COLUMN IF NOT EXISTS storage_key VARCHAR(1000),
  ADD COLUMN IF NOT EXISTS file_publication_status VARCHAR(20) NOT NULL DEFAULT 'private';

UPDATE tfm_schema.resources
SET storage_provider = 'local'
WHERE storage_path IS NOT NULL AND storage_provider IS NULL;

-- Evidencia académica para comparar BETO con el baseline del mismo snapshot.
ALTER TABLE tfm_schema.training_metrics
  ADD COLUMN IF NOT EXISTS f1_weighted NUMERIC(6,5),
  ADD COLUMN IF NOT EXISTS f1_macro_ci95 JSONB,
  ADD COLUMN IF NOT EXISTS results_by_source_type JSONB,
  ADD COLUMN IF NOT EXISTS baseline_name VARCHAR(80),
  ADD COLUMN IF NOT EXISTS baseline_f1_macro NUMERIC(6,5),
  ADD COLUMN IF NOT EXISTS baseline_dataset_sha256 VARCHAR(64),
  ADD COLUMN IF NOT EXISTS exceeds_baseline BOOLEAN;
