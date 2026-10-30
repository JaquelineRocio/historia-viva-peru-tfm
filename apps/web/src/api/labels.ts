import { useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/apiClient'
import { buildSubtopicMap } from '../lib/indexing'
import type { LabelMap, LabelTaxonomy } from '../types'

export function useTaxonomy() {
  return useQuery({
    queryKey: ['taxonomy'],
    staleTime: 5 * 60 * 1000,
    queryFn: async () => (await api.get<LabelTaxonomy[]>('/labels/taxonomy')).data,
  })
}

/** Subtemas de la tesis, con nombre y color actualizados desde la API cuando responde. */
export function useSubtopics() {
  const taxonomy = useTaxonomy()
  return useMemo(() => buildSubtopicMap(taxonomy.data), [taxonomy.data])
}

export function useVideoLabels(videoId: string | null) {
  return useQuery({
    queryKey: ['labels', videoId],
    enabled: !!videoId,
    queryFn: async () => (await api.get<LabelMap>(`/labels/by-video/${videoId}`)).data,
  })
}

export function useSetLabel(videoId: string | null) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ segmentId, labelKey }: { segmentId: string; labelKey: string }) =>
      (await api.post(`/segments/${segmentId}/label`, { labelKey })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['labels', videoId] }),
  })
}
