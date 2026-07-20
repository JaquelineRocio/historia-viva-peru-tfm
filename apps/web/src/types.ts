export type TranscriptionStatus = 'pending' | 'processing' | 'done' | 'failed'

export interface AuthUser {
  id: string
  username: string
  role: string
  displayName?: string | null
}

export interface Video {
  id: string
  youtubeId: string
  url: string
  title?: string | null
  channel?: string | null
  durationSec?: number | null
  transcriptionStatus: TranscriptionStatus
  createdAt: string
}

export interface Segment {
  id: string
  idx: number
  startSec: number
  endSec: number
  text: string
}

export interface Transcript {
  id: string
  videoId: string
  language?: string | null
  source: 'api' | 'whisper'
  isGenerated: boolean
  segments: Segment[]
}

export interface LabelTaxonomy {
  key: string
  name: string
  description?: string | null
  color?: string | null
  sortOrder: number
}

export type LabelSource = 'human' | 'model'

export interface SegmentLabelView {
  labelKey: string
  source: LabelSource
  confidence?: number | null
  isGold: boolean
}

export type LabelMap = Record<string, SegmentLabelView>

export interface Dataset {
  id: string
  name: string
  description?: string | null
  nSamples: number
  classDistribution?: Record<string, number> | null
  splitConfig?: Record<string, unknown> | null
  createdAt: string
}

export type ModelStatus = 'training' | 'ready' | 'failed'

export interface ModelVersion {
  id: string
  versionTag: string
  datasetId?: string | null
  baseModel: string
  parentVersionId?: string | null
  hyperparams?: Record<string, unknown> | null
  artifactPath?: string | null
  status: ModelStatus
  isActive: boolean
  recommendationStatus: 'experimental' | 'recommended'
  createdAt: string
}

export type JobStatus = 'queued' | 'running' | 'done' | 'failed' | 'cancelled'

export interface TrainingJob {
  id: string
  modelVersionId?: string | null
  datasetId?: string | null
  status: JobStatus
  progress: number
  currentEpoch?: number | null
  error?: string | null
}

export interface PerClassMetric {
  label: string
  precision: number
  recall: number
  f1: number
  support: number
}

export interface TrainingMetric {
  id: string
  modelVersionId: string
  split: string
  accuracy?: number | null
  precisionMacro?: number | null
  recallMacro?: number | null
  f1Macro?: number | null
  f1Weighted?: number | null
  f1MacroCi95?: { method: string; iterations: number; seed: number; low: number; high: number } | null
  resultsBySourceType?: Record<string, unknown> | null
  baselineName?: string | null
  baselineF1Macro?: number | null
  baselineDatasetSha256?: string | null
  exceedsBaseline?: boolean | null
  perClassMetrics?: PerClassMetric[]
  confusionMatrix?: { labels: string[]; matrix: number[][] } | null
}

export interface SegmentPrediction {
  segmentId: string
  idx: number
  startSec: number
  endSec: number
  text: string
  labelKey: string
  confidence: number
}

export interface HistoryProject {
  id: string
  name: string
  description?: string | null
  periodStart?: number | null
  periodEnd?: number | null
  isPublic: boolean
  createdAt: string
}

export type ResourceType = 'youtube' | 'pdf'
export type ProcessingStatus = 'pending' | 'processing' | 'ready' | 'needs_attention' | 'failed'
export type ReviewStatus = 'pending' | 'reviewed' | 'ambiguous' | 'excluded'

export interface HistoryResource {
  id: string
  projectId: string
  type: ResourceType
  title: string
  author?: string | null
  sourceUrl?: string | null
  originalFilename?: string | null
  processingStatus: ProcessingStatus
  processingError?: string | null
  publicationStatus: string
  corpusStatus: 'candidate' | 'included' | 'excluded'
  sourceStyle?: string | null
  corpusNotes?: string | null
  createdAt: string
}

export interface ResourceSegment {
  id: string
  resourceId: string
  idx: number
  locatorType: 'timestamp' | 'page'
  startSec?: number | null
  endSec?: number | null
  pageStart?: number | null
  pageEnd?: number | null
  text: string
  suggestedLabelKey?: string | null
  suggestedConfidence?: number | null
  reviewStatus: ReviewStatus
  reviewedLabelKey?: string | null
  entities?: HistoricalEntity[]
}

export interface PagedResourceSegments {
  items: ResourceSegment[]
  page: number
  limit: number
  total: number
  totalPages: number
}

export interface ProjectDashboard {
  resources: number
  segments: number
  reviewed: number
  pending: number
}

export interface SearchEvidence {
  id: string
  text: string
  locatorType: 'timestamp' | 'page'
  startSec?: number | null
  endSec?: number | null
  pageStart?: number | null
  pageEnd?: number | null
  resourceId: string
  title: string
  type: ResourceType
  sourceUrl?: string | null
  score: number
  semanticScore?: number | null
  entities?: HistoricalEntity[]
}

export type HistoricalEntityType = 'person' | 'place' | 'organization' | 'date' | 'period' | 'other'

export interface HistoricalEntity {
  id?: string
  type: HistoricalEntityType
  text: string
  normalizedValue: string
  yearStart?: number | null
  yearEnd?: number | null
  confidence?: number | null
  method?: string
  isHuman?: boolean
  outOfScope?: boolean
}

export interface HistoricalSearchFilters {
  person?: string
  place?: string
  yearStart?: number
  yearEnd?: number
  label?: string
}

export interface SearchFacet {
  value: string | number
  label?: string
  count: number
}

export interface SearchFacets {
  persons: SearchFacet[]
  places: SearchFacet[]
  years: SearchFacet[]
  labels: SearchFacet[]
}

export interface EvidenceCollection {
  id: string
  name: string
  description?: string | null
  isPublic: boolean
  itemCount?: number
  items?: Array<SearchEvidence & { note?: string | null }>
}
