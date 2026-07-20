import { useRef, useState, type FormEvent } from 'react'
import YouTube, { type YouTubePlayer } from 'react-youtube'
import {
  useCreateVideo,
  useDeleteVideo,
  useTranscribe,
  useTranscript,
  useVideo,
  useVideos,
} from '../api/videos'
import { StatusBadge } from '../components/StatusBadge'
import { apiError } from '../lib/apiClient'
import { formatTime } from '../lib/format'

export function IngestPage() {
  const videos = useVideos()
  const createVideo = useCreateVideo()
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  async function onAdd(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    try {
      const v = await createVideo.mutateAsync({ url, title: title || undefined })
      setUrl('')
      setTitle('')
      setSelectedId(v.id)
    } catch (err) {
      setFormError(apiError(err))
    }
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[340px_1fr]">
      {/* Columna izquierda: alta + lista */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">Ingesta de video</h2>
        <form onSubmit={onAdd} className="mb-6 space-y-3 rounded-xl border border-slate-200 bg-white p-4">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="URL o ID de YouTube"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
            required
          />
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Título (opcional)"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
          {formError && <p className="rounded bg-red-50 px-2 py-1 text-xs text-red-700">{formError}</p>}
          <button
            type="submit"
            disabled={createVideo.isPending}
            className="w-full rounded-md bg-indigo-600 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {createVideo.isPending ? 'Añadiendo…' : 'Añadir video'}
          </button>
        </form>

        <h3 className="mb-2 text-sm font-semibold text-slate-500">Videos</h3>
        <ul className="space-y-2">
          {videos.data?.map((v) => (
            <li key={v.id}>
              <button
                onClick={() => setSelectedId(v.id)}
                className={`w-full rounded-lg border p-3 text-left transition ${
                  selectedId === v.id
                    ? 'border-indigo-400 bg-indigo-50'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium">{v.title || v.youtubeId}</span>
                  <StatusBadge status={v.transcriptionStatus} />
                </div>
                <span className="text-xs text-slate-400">{v.youtubeId}</span>
              </button>
            </li>
          ))}
          {videos.data?.length === 0 && (
            <li className="rounded-lg border border-dashed border-slate-300 p-4 text-center text-sm text-slate-400">
              Aún no hay videos. Pega una URL de YouTube arriba.
            </li>
          )}
        </ul>
      </section>

      {/* Columna derecha: detalle del video seleccionado */}
      <section>
        {selectedId ? (
          <VideoDetail id={selectedId} onDeleted={() => setSelectedId(null)} />
        ) : (
          <div className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-dashed border-slate-300 text-slate-400">
            Selecciona un video para ver su transcripción
          </div>
        )}
      </section>
    </div>
  )
}

function VideoDetail({ id, onDeleted }: { id: string; onDeleted: () => void }) {
  const video = useVideo(id)
  const transcribe = useTranscribe()
  const deleteVideo = useDeleteVideo()
  const playerRef = useRef<YouTubePlayer | null>(null)
  const isDone = video.data?.transcriptionStatus === 'done'
  const transcript = useTranscript(id, isDone)

  function seekTo(seconds: number) {
    playerRef.current?.seekTo(seconds, true)
    playerRef.current?.playVideo()
  }

  if (video.isLoading || !video.data) return <div className="text-slate-500">Cargando…</div>
  const v = video.data

  return (
    <div>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">{v.title || v.youtubeId}</h2>
          <div className="mt-1 flex items-center gap-2">
            <StatusBadge status={v.transcriptionStatus} />
            {transcript.data && (
              <span className="text-xs text-slate-400">
                {transcript.data.segments.length} segmentos · fuente:{' '}
                {transcript.data.source === 'whisper' ? 'Whisper' : 'subtítulos'}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {(v.transcriptionStatus === 'pending' || v.transcriptionStatus === 'failed') && (
            <button
              onClick={() => transcribe.mutate(v.id)}
              disabled={transcribe.isPending}
              className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {v.transcriptionStatus === 'failed' ? 'Reintentar' : 'Transcribir'}
            </button>
          )}
          <button
            onClick={() => deleteVideo.mutate(v.id, { onSuccess: onDeleted })}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100"
          >
            Eliminar
          </button>
        </div>
      </div>

      <div className="mb-4 overflow-hidden rounded-xl">
        <YouTube
          videoId={v.youtubeId}
          onReady={(e) => (playerRef.current = e.target)}
          opts={{ width: '100%', height: '360', playerVars: { rel: 0 } }}
          className="aspect-video w-full"
          iframeClassName="h-full w-full"
        />
      </div>

      {v.transcriptionStatus === 'processing' && (
        <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-700">
          Transcribiendo… esto puede tardar unos segundos (o más si usa Whisper).
        </p>
      )}
      {v.transcriptionStatus === 'failed' && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          La transcripción falló. Puede que el video no tenga subtítulos y Whisper no esté disponible.
        </p>
      )}

      {isDone && transcript.data && (
        <ol className="mt-2 max-h-[420px] space-y-1 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2">
          {transcript.data.segments.map((s) => (
            <li key={s.id}>
              <button
                onClick={() => seekTo(s.startSec)}
                className="flex w-full gap-3 rounded-md px-2 py-1.5 text-left hover:bg-indigo-50"
              >
                <span className="mt-0.5 shrink-0 font-mono text-xs text-indigo-600">
                  {formatTime(s.startSec)}
                </span>
                <span className="text-sm text-slate-700">{s.text}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
