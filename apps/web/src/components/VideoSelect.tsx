import { useVideos } from '../api/videos'
import type { Video } from '../types'

interface Props {
  value: string | null
  onChange: (id: string) => void
  onlyDone?: boolean
  placeholder?: string
}

/** Selector de video reutilizable (opcionalmente solo los ya transcritos). */
export function VideoSelect({ value, onChange, onlyDone, placeholder }: Props) {
  const videos = useVideos()
  const list: Video[] = (videos.data ?? []).filter((v) => (onlyDone ? v.transcriptionStatus === 'done' : true))

  return (
    <select
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      className="w-full max-w-md rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
    >
      <option value="" disabled>
        {placeholder ?? 'Selecciona un video…'}
      </option>
      {list.map((v) => (
        <option key={v.id} value={v.id}>
          {v.title || v.youtubeId} {v.transcriptionStatus !== 'done' ? '(sin transcribir)' : ''}
        </option>
      ))}
    </select>
  )
}
