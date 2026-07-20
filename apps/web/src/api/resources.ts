import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/apiClient'
import type { EvidenceCollection, HistoricalEntity, HistoricalSearchFilters, HistoryProject, HistoryResource, PagedResourceSegments, ProjectDashboard, ResourceSegment, SearchEvidence, SearchFacets } from '../types'

export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: async () => (await api.get<HistoryProject[]>('/projects')).data })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { name: string; description?: string; periodStart?: number; periodEnd?: number }) =>
      (await api.post<HistoryProject>('/projects', payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useProjectDashboard(projectId?: string) {
  return useQuery({
    queryKey: ['project-dashboard', projectId],
    enabled: !!projectId,
    queryFn: async () => (await api.get<ProjectDashboard>(`/projects/${projectId}/dashboard`)).data,
  })
}

export function useResources(projectId?: string) {
  return useQuery({
    queryKey: ['resources', projectId],
    enabled: !!projectId,
    queryFn: async () => (await api.get<HistoryResource[]>(`/projects/${projectId}/resources`)).data,
    refetchInterval: (query) => (query.state.data ?? []).some((item) => item.processingStatus === 'processing') ? 2000 : false,
  })
}

export function useCreateYoutubeResource(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { url: string; title: string; author?: string; rightsConfirmed: boolean }) =>
      (await api.post<HistoryResource>(`/projects/${projectId}/resources/youtube`, payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources', projectId] }),
  })
}

export function useCreatePdfResource(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (form: FormData) =>
      (await api.post<HistoryResource>(`/projects/${projectId}/resources/pdf`, form)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources', projectId] }),
  })
}

export function useProcessResource(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => (await api.post(`/resources/${id}/process`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources', projectId] }),
  })
}

export function useClassifyResource(projectId?: string, resourceId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) =>
      (await api.post<{ resourceId: string; classified: number }>(`/resources/${id}/classify`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['paged-resource-segments', projectId, resourceId] })
      qc.invalidateQueries({ queryKey: ['resource-segments', resourceId] })
    },
  })
}

export function useUpdateResourceMetadata(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...payload }: { id: string; title: string; author?: string; sourceUrl?: string }) =>
      (await api.patch<HistoryResource>(`/resources/${id}`, payload)).data,
    onSuccess: (resource) => {
      qc.invalidateQueries({ queryKey: ['resources', projectId] })
      qc.setQueryData(['resource', resource.id], resource)
    },
  })
}

export function useSetCorpusStatus(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, status, sourceStyle }: { id: string; status: 'candidate' | 'included' | 'excluded'; sourceStyle?: string }) =>
      (await api.patch<HistoryResource>(`/resources/${id}/corpus`, { status, sourceStyle })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['resources', projectId] })
      qc.invalidateQueries({ queryKey: ['dataset-readiness', projectId] })
    },
  })
}

export function useResourceSegments(resourceId?: string) {
  return useQuery({
    queryKey: ['resource-segments', resourceId],
    enabled: !!resourceId,
    queryFn: async () => (await api.get<ResourceSegment[]>(`/resources/${resourceId}/segments`)).data,
  })
}

export function usePagedResourceSegments(
  projectId?: string,
  resourceId?: string,
  params: { page: number; limit?: number; status?: string; label?: string; sort?: string; campaignId?: string } = { page: 1 },
) {
  return useQuery({
    queryKey: ['paged-resource-segments', projectId, resourceId, params],
    enabled: !!projectId && !!resourceId,
    queryFn: async () => (await api.get<PagedResourceSegments>(
      `/projects/${projectId}/resources/${resourceId}/segments`, { params },
    )).data,
  })
}

export async function getPdfFile(resourceId: string) {
  return (await api.get<ArrayBuffer>(`/resources/${resourceId}/file`, { responseType: 'arraybuffer' })).data
}

export async function getPublicPdfFile(resourceId: string) {
  return (await api.get<ArrayBuffer>(`/public/resources/${resourceId}/file`, { responseType: 'arraybuffer' })).data
}

export function useSegmentEntities(segmentId?: string, enabled = true) {
  return useQuery({
    queryKey: ['segment-entities', segmentId],
    enabled: !!segmentId && enabled,
    queryFn: async () => (await api.get<HistoricalEntity[]>(`/resource-segments/${segmentId}/entities`)).data,
  })
}

export function useReplaceSegmentEntities(segmentId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (entities: Array<{ type: HistoricalEntity['type']; text: string; yearStart?: number; yearEnd?: number }>) =>
      (await api.put<HistoricalEntity[]>(`/resource-segments/${segmentId}/entities`, { entities })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['segment-entities', segmentId] })
      qc.invalidateQueries({ queryKey: ['search-facets'] })
    },
  })
}

export function useReviewResourceSegment(resourceId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (input: { id: string; status: 'reviewed' | 'ambiguous' | 'excluded'; labelKey?: string }) =>
      (await api.patch<ResourceSegment>(`/resource-segments/${input.id}/review`, input)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['resource-segments', resourceId] })
      qc.invalidateQueries({ queryKey: ['paged-resource-segments'] })
      qc.invalidateQueries({ queryKey: ['project-dashboard'] })
      qc.invalidateQueries({ queryKey: ['annotation-campaigns'] })
      qc.invalidateQueries({ queryKey: ['annotation-campaign-progress'] })
      qc.invalidateQueries({ queryKey: ['dataset-readiness'] })
    },
  })
}

export function useBulkReviewSegments() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { segmentIds: string[]; status: 'reviewed' | 'ambiguous' | 'excluded'; labelKey?: string }) =>
      (await api.post<{ updated: number }>('/segments/review/bulk', payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['paged-resource-segments'] })
      qc.invalidateQueries({ queryKey: ['project-dashboard'] })
      qc.invalidateQueries({ queryKey: ['annotation-campaigns'] })
      qc.invalidateQueries({ queryKey: ['annotation-campaign-progress'] })
      qc.invalidateQueries({ queryKey: ['dataset-readiness'] })
    },
  })
}

export function useEvidenceFeedback() {
  return useMutation({
    mutationFn: async (payload: { segmentId: string; value: 'useful' | 'irrelevant' | 'incorrect'; note?: string }) =>
      (await api.post(`/segments/${payload.segmentId}/evidence-feedback`, { value: payload.value, note: payload.note })).data,
  })
}

export function useUnpublishResource(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (resourceId: string) => (await api.post(`/resources/${resourceId}/unpublish`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources', projectId] }),
  })
}

export async function searchProject(projectId: string, query: string, filters: HistoricalSearchFilters = {}) {
  return (await api.get<{ query: string; answer: string; evidence: SearchEvidence[] }>(
    `/projects/${projectId}/search`,
    { params: { q: query, ...filters } },
  )).data
}

export async function askProject(projectId: string, query: string, filters: HistoricalSearchFilters = {}) {
  return (await api.post<{ query: string; answer: string; evidence: SearchEvidence[]; mode: 'extractive' | 'generated' | 'abstained' }>(
    `/projects/${projectId}/assistant/query`,
    { query, ...filters },
  )).data
}

export function useSearchFacets(projectId?: string) {
  return useQuery({
    queryKey: ['search-facets', projectId],
    enabled: !!projectId,
    queryFn: async () => (await api.get<SearchFacets>(`/projects/${projectId}/search-facets`)).data,
  })
}

export function useCollections(projectId?: string) {
  return useQuery({
    queryKey: ['collections', projectId],
    enabled: !!projectId,
    queryFn: async () => (await api.get<EvidenceCollection[]>(`/projects/${projectId}/collections`)).data,
  })
}

export function useCollection(id?: string) {
  return useQuery({
    queryKey: ['collection', id],
    enabled: !!id,
    queryFn: async () => (await api.get<EvidenceCollection>(`/collections/${id}`)).data,
  })
}

export function useCreateCollection(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { name: string; description?: string }) =>
      (await api.post<EvidenceCollection>(`/projects/${projectId}/collections`, payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['collections', projectId] }),
  })
}

export function useSaveEvidence(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { collectionId: string; segmentId: string; note?: string }) =>
      (await api.post(`/collections/${payload.collectionId}/items`, { segmentId: payload.segmentId, note: payload.note })).data,
    onSuccess: (_data, payload) => {
      qc.invalidateQueries({ queryKey: ['collections', projectId] })
      qc.invalidateQueries({ queryKey: ['collection', payload.collectionId] })
    },
  })
}

export function useRequestPublication(projectId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (resourceId: string) => (await api.post(`/resources/${resourceId}/request-publication`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['resources', projectId] }),
  })
}

export async function publicProjects() {
  return (await api.get<HistoryProject[]>('/public/projects')).data
}

export async function publicSearch(projectId: string, query: string, filters: HistoricalSearchFilters = {}) {
  return (await api.get<{ query: string; answer: string; evidence: SearchEvidence[] }>(
    `/public/projects/${projectId}/search`,
    { params: { q: query, ...filters } },
  )).data
}

export function usePublicationReviews() {
  return useQuery({
    queryKey: ['publication-reviews'],
    queryFn: async () => (await api.get<Array<{
      id: string
      resourceId: string
      title: string
      type: 'youtube' | 'pdf'
      license?: string | null
      rightsConfirmed: boolean
      requestedAt: string
    }>>('/publication-reviews')).data,
  })
}

export function useDecidePublication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { id: string; status: 'approved' | 'rejected'; note?: string }) =>
      (await api.patch(`/publication-reviews/${payload.id}`, { status: payload.status, note: payload.note })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['publication-reviews'] }),
  })
}
