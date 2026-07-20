import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/apiClient'
import type { Transcript, Video } from '../types'

export function useVideos() {
  return useQuery({
    queryKey: ['videos'],
    queryFn: async () => (await api.get<Video[]>('/videos')).data,
  })
}

export function useVideo(id: string | null) {
  return useQuery({
    queryKey: ['video', id],
    enabled: !!id,
    queryFn: async () => (await api.get<Video>(`/videos/${id}`)).data,
    // Polling mientras se está transcribiendo; para al terminar.
    refetchInterval: (query) =>
      query.state.data?.transcriptionStatus === 'processing' ? 2000 : false,
  })
}

export function useTranscript(id: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ['transcript', id],
    enabled: !!id && enabled,
    queryFn: async () => (await api.get<Transcript>(`/videos/${id}/transcript`)).data,
  })
}

export function useCreateVideo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { url: string; title?: string }) =>
      (await api.post<Video>('/videos', payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }),
  })
}

export function useTranscribe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => (await api.post(`/videos/${id}/transcribe`)).data,
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: ['video', id] })
      qc.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export function useDeleteVideo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => api.delete(`/videos/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }),
  })
}
