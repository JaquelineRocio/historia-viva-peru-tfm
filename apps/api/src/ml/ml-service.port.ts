/**
 * MlServicePort — puerto de salida (hexagonal) hacia la capa de cómputo ML.
 *
 * El dominio de NestJS NO conoce Python/HTTP: habla contra esta interfaz.
 * La implementación concreta es `HttpMlAdapter` (secondary adapter).
 */

export const ML_SERVICE_PORT = Symbol('ML_SERVICE_PORT');

/** Un fragmento crudo de subtítulo con timestamp (segundos). */
export interface MlCue {
  start: number;
  duration: number;
  text: string;
}

/** Resultado de transcripción (subtítulos o Whisper). */
export interface MlTranscriptResult {
  video_id: string;
  language: string;
  source: 'api' | 'whisper';
  is_generated: boolean;
  cue_count: number;
  full_text: string;
  cues: MlCue[];
}

/** Un segmento por ventana temporal. */
export interface MlSegment {
  idx: number;
  start_sec: number;
  end_sec: number;
  text: string;
}

export interface MlSegmentResult {
  count: number;
  segments: MlSegment[];
}

export interface MlPdfResult {
  page_count: number;
  full_text: string;
  segments: Array<{ idx: number; page_start: number; page_end: number; text: string }>;
}

export interface MlEntityMention {
  type: 'person' | 'place' | 'organization' | 'date' | 'period' | 'other';
  text: string;
  normalized_value: string;
  start: number;
  end: number;
  confidence: number;
  year_start?: number | null;
  year_end?: number | null;
  method: string;
  out_of_scope?: boolean;
}

export interface MlEntityResult {
  model: string;
  model_available: boolean;
  error?: string | null;
  results: MlEntityMention[][];
}

export interface SegmentParams {
  window_sec?: number;
  overlap_sec?: number;
}

// ----------------------------- Entrenamiento e inferencia --------------------
export interface MlDatasetItem {
  text: string;
  label: string;
  split: 'train' | 'val' | 'test';
}

export interface MlHyperparams {
  epochs?: number;
  lr?: number;
  batch_size?: number;
  max_len?: number;
  seed?: number;
}

export interface MlTrainRequest {
  version_tag: string;
  labels: string[];
  items: MlDatasetItem[];
  base_model: string; // BETO o ruta de artefacto padre (fine-tuning incremental)
  hyperparams?: MlHyperparams;
  output_dir?: string;
}

export interface MlPerClassMetric {
  label: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface MlMetrics {
  accuracy: number;
  precision_macro: number;
  recall_macro: number;
  f1_macro: number;
  /** F1 ponderado por soporte; se conserva para el informe académico. */
  f1_weighted?: number;
  per_class: MlPerClassMetric[];
  confusion_matrix: number[][];
  labels: string[];
  /** Split real sobre el que se calcularon (test, o val/train si hubo fallback). */
  split?: string;
  /** Intervalo de confianza percentil del F1 macro, calculado sobre test. */
  f1_macro_ci95?: {
    method: string;
    iterations: number;
    seed: number;
    low: number;
    high: number;
  };
  /** Resultados desagregados, por ejemplo PDF frente a YouTube. */
  results_by_source_type?: Record<string, unknown>;
  /** Baseline reproducible que este modelo debe superar para ser recomendado. */
  baseline?: {
    name: string;
    f1_macro: number;
    dataset_sha256?: string;
  };
}

export interface MlJobStatus {
  job_id: string;
  status: 'queued' | 'running' | 'done' | 'failed' | 'cancelled';
  progress: number;
  current_epoch?: number | null;
  error?: string | null;
  artifact_path?: string | null;
  metrics?: MlMetrics | null;
}

export interface MlPrediction {
  label: string;
  confidence: number;
}

export interface MlServicePort {
  /** Salud del servicio ML. */
  health(): Promise<{ status: string }>;

  /** Lanza un entrenamiento (job async). Devuelve el id del job en el servicio ML. */
  train(req: MlTrainRequest): Promise<{ job_id: string }>;

  /** Estado (y métricas al terminar) de un job de entrenamiento. */
  getJob(jobId: string): Promise<MlJobStatus>;

  /** Carga un modelo (por ruta de artefacto) como modelo activo en memoria. */
  loadModel(artifactPath: string): Promise<{ loaded: boolean; labels: string[] }>;

  /** Clasifica textos con el modelo activo. */
  infer(texts: string[]): Promise<MlPrediction[]>;

  /** Transcripción vía subtítulos de YouTube. Lanza `MlTranscriptUnavailable` si no hay. */
  transcribeSubtitles(youtubeUrl: string, languages?: string[]): Promise<MlTranscriptResult>;

  /** Fallback: descarga audio y transcribe con Whisper (lento). */
  transcribeAudio(youtubeUrl: string, languages?: string[]): Promise<MlTranscriptResult>;

  /** Segmenta cues en ventanas temporales con solape. */
  segment(cues: MlCue[], params?: SegmentParams): Promise<MlSegmentResult>;

  /** Extrae texto de un PDF nativo conservando el número de página. */
  extractPdf(content: Buffer, filename: string): Promise<MlPdfResult>;

  /** Genera embeddings semánticos multilingües normalizados. */
  embed(texts: string[]): Promise<{ model: string; dimensions: number; embeddings: number[][] }>;

  /** Extrae entidades históricas y expresiones temporales. */
  extractEntities(texts: string[]): Promise<MlEntityResult>;
}

/** El servicio ML respondió 422: no hay subtítulos → conviene el fallback Whisper. */
export class MlTranscriptUnavailable extends Error {}
