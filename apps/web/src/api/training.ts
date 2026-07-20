import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/apiClient'
import type { Dataset, ModelVersion, SegmentPrediction, TrainingJob, TrainingMetric } from '../types'

export interface ValidationCampaign {
  id: string
  projectId: string
  name: string
  sampleRate: number
  seed: number
  status: 'open' | 'closed'
  sampleCount: number
  completedCount: number
  createdAt: string
}

export interface ValidationSample {
  id: string
  segmentId: string
  secondaryLabelKey?: string | null
  reviewedAt?: string | null
  text: string
  locatorType: 'page' | 'timestamp'
  pageStart?: number | null
  startSec?: number | null
  resourceTitle: string
  resourceType: 'pdf' | 'youtube'
}

export interface ValidationAgreement {
  total: number
  completed: number
  observedAgreement: number
  expectedAgreement: number
  kappa: number | null
  targetMet: boolean
}

export interface AnnotationCampaign {
  id: string
  projectId: string
  name: string
  targetCount: number
  seed: number
  maxPerSource: number
  status: 'open' | 'closed'
  sampleCount: number
  completedCount: number
  sourceCount: number
  createdAt: string
}

export interface AnnotationCampaignProgress {
  campaign: Pick<AnnotationCampaign, 'id' | 'projectId' | 'name' | 'targetCount' | 'seed' | 'maxPerSource' | 'status'>
  totals: { total: number; pending: number; reviewed: number; ambiguous: number; excluded: number }
  sources: Array<{
    resourceId: string
    title: string
    type: 'pdf' | 'youtube'
    total: number
    pending: number
    reviewed: number
    ambiguous: number
    excluded: number
  }>
  classes: Array<{ key: string; name: string; color: string; count: number; target: number; missing: number }>
}

export function useAnnotationCampaigns(projectId?: string) {
  return useQuery({
    queryKey: ['annotation-campaigns', projectId],
    enabled: !!projectId,
    queryFn: async () => (await api.get<AnnotationCampaign[]>(`/projects/${projectId}/annotation-campaigns`)).data,
  })
}

export function useCreateAnnotationCampaign(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => (await api.post<AnnotationCampaign>(`/projects/${projectId}/annotation-campaigns`, {
      name: 'Corpus gold v1',
      targetCount: 700,
      seed: 42,
      maxPerSource: 150,
    })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['annotation-campaigns', projectId] }),
  })
}

export function useAnnotationCampaignProgress(campaignId?: string) {
  return useQuery({
    queryKey: ['annotation-campaign-progress', campaignId],
    enabled: !!campaignId,
    queryFn: async () => (await api.get<AnnotationCampaignProgress>(`/annotation-campaigns/${campaignId}/progress`)).data,
  })
}

// ---- datasets ----
export function useDatasets(projectId?: string) {
  return useQuery({ queryKey: ['datasets', projectId], queryFn: async () => (await api.get<Dataset[]>(projectId ? `/projects/${projectId}/datasets` : '/datasets')).data })
}

export function useDatasetReadiness(projectId?: string) {
  return useQuery({
    queryKey: ['dataset-readiness', projectId],
    queryFn: async () => (await api.get<{
      targetPerClass: number
      targetTotalMin?: number
      targetTotalMax?: number
      total: number
      ready: boolean
      sources?: { total: number; pdf: number; youtube: number; processed: number; gold: number; targetMin: number; targetMax: number }
      distribution: Array<{ key: string; name: string; count: number }>
    }>(projectId ? `/projects/${projectId}/datasets/readiness` : '/datasets/readiness')).data,
  })
}

export function useCreateDataset(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { name: string; description?: string; trainRatio?: number; valRatio?: number }) =>
      (await api.post<Dataset>(projectId ? `/projects/${projectId}/datasets` : '/datasets', payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['datasets'] }),
  })
}

export function useValidationCampaigns(projectId?: string) {
  return useQuery({
    queryKey: ['validation-campaigns', projectId],
    enabled: !!projectId,
    queryFn: async () => (await api.get<ValidationCampaign[]>(`/projects/${projectId}/validation-campaigns`)).data,
  })
}

export function useCreateValidationCampaign(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => (await api.post<ValidationCampaign>(`/projects/${projectId}/validation-campaigns`, { sampleRate: 0.2, seed: 42 })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['validation-campaigns', projectId] }),
  })
}

export function useValidationSamples(campaignId?: string, page = 1) {
  return useQuery({
    queryKey: ['validation-samples', campaignId, page],
    enabled: !!campaignId,
    queryFn: async () => (await api.get<{ items: ValidationSample[]; page: number; total: number; totalPages: number }>(`/validation-campaigns/${campaignId}/samples`, { params: { page, limit: 10 } })).data,
  })
}

export function useSaveSecondaryAnnotation(campaignId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ sampleId, labelKey }: { sampleId: string; labelKey: string }) =>
      (await api.patch(`/validation-samples/${sampleId}`, { labelKey })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['validation-samples', campaignId] })
      qc.invalidateQueries({ queryKey: ['validation-agreement', campaignId] })
      qc.invalidateQueries({ queryKey: ['validation-campaigns'] })
    },
  })
}

export function useValidationAgreement(campaignId?: string) {
  return useQuery({
    queryKey: ['validation-agreement', campaignId],
    enabled: !!campaignId,
    queryFn: async () => (await api.get<ValidationAgreement>(`/validation-campaigns/${campaignId}/agreement`)).data,
  })
}

// ---- training jobs ----
export function useTrainingJobs() {
  return useQuery({
    queryKey: ['training-jobs'],
    queryFn: async () => (await api.get<TrainingJob[]>('/training/jobs')).data,
    refetchInterval: (q) =>
      (q.state.data ?? []).some((j) => j.status === 'running' || j.status === 'queued') ? 2500 : false,
  })
}

export function useCreateTrainingJob() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: {
      datasetId: string
      parentVersionId?: string
      hyperparams?: Record<string, number>
    }) => (await api.post<TrainingJob>('/training/jobs', payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['training-jobs'] })
      qc.invalidateQueries({ queryKey: ['models'] })
    },
  })
}

// ---- models / versions ----
export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => (await api.get<ModelVersion[]>('/models')).data,
    refetchInterval: (q) => ((q.state.data ?? []).some((m) => m.status === 'training') ? 3000 : false),
  })
}

export function useActiveModel() {
  return useQuery({ queryKey: ['active-model'], queryFn: async () => (await api.get<ModelVersion | null>('/models/active')).data })
}

export function useActivateModel() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => (await api.post<ModelVersion>(`/models/${id}/activate`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['models'] })
      qc.invalidateQueries({ queryKey: ['active-model'] })
    },
  })
}

export function useModelMetrics(id: string | null) {
  return useQuery({
    queryKey: ['metrics', id],
    enabled: !!id,
    queryFn: async () => (await api.get<TrainingMetric[]>(`/metrics/models/${id}`)).data,
  })
}

// ---- inference (active learning) ----
export function useClassifyVideo() {
  return useMutation({
    mutationFn: async (videoId: string) =>
      (await api.post<SegmentPrediction[]>(`/inference/video/${videoId}`)).data,
  })
}
