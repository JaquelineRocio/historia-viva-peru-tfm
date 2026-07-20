import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import YouTube, { type YouTubePlayer } from 'react-youtube'
import { useSetLabel, useTaxonomy, useVideoLabels } from '../api/labels'
import { useTranscript, useVideo, useVideos } from '../api/videos'
import { VideoSelect } from '../components/VideoSelect'
import { buildLabelMap, labelColor } from '../lib/labels'
import { formatTime } from '../lib/format'

export function LabelingPage() {
  const videos = useVideos()
  const [videoId, setVideoId] = useState<string | null>(null)

  // Autoselecciona el primer video transcrito.
  useEffect(() => {
    if (!videoId && videos.data?.length) {
      const done = videos.data.find((v) => v.transcriptionStatus === 'done')
      if (done) setVideoId(done.id)
    }
  }, [videos.data, videoId])

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h2 className="text-lg font-semibold">Etiquetado</h2>
        <VideoSelect value={videoId} onChange={setVideoId} onlyDone placeholder="Elige un video transcrito…" />
      </div>
      {videoId ? (
        <LabelingEditor videoId={videoId} />
      ) : (
        <p className="text-slate-500">Selecciona un video ya transcrito para empezar a etiquetar.</p>
      )}
    </div>
  )
}

function LabelingEditor({ videoId }: { videoId: string }) {
  const video = useVideo(videoId)
  const transcript = useTranscript(videoId, true)
  const taxonomy = useTaxonomy()
  const labels = useVideoLabels(videoId)
  const setLabel = useSetLabel(videoId)
  const playerRef = useRef<YouTubePlayer | null>(null)
  const [active, setActive] = useState(0)

  const labelMap = useMemo(() => buildLabelMap(taxonomy.data), [taxonomy.data])
  const segments = useMemo(() => transcript.data?.segments ?? [], [transcript.data?.segments])
  const labelBySegment = labels.data ?? {}
  const labeledCount = Object.values(labelBySegment).filter((l) => l.isGold).length

  const seekTo = useCallback((sec: number) => {
    playerRef.current?.seekTo(sec, true)
    playerRef.current?.playVideo()
  }, [])

  const apply = useCallback(
    (segmentId: string, labelKey: string, advance: boolean) => {
      setLabel.mutate({ segmentId, labelKey })
      if (advance) setActive((a) => Math.min(a + 1, segments.length - 1))
    },
    [setLabel, segments.length],
  )

  // Atajos: teclas 1..N etiquetan el segmento activo; flechas mueven el foco.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      const tax = taxonomy.data ?? []
      const seg = segments[active]
      if (!seg) return
      if (e.key >= '1' && e.key <= '9') {
        const i = Number(e.key) - 1
        if (i < tax.length) {
          e.preventDefault()
          apply(seg.id, tax[i].key, true)
        }
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        setActive((a) => Math.min(a + 1, segments.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setActive((a) => Math.max(a - 1, 0))
      } else if (e.key === ' ') {
        e.preventDefault()
        seekTo(seg.startSec)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [active, segments, taxonomy.data, apply, seekTo])

  if (!video.data) return <div className="text-slate-500">Cargando…</div>

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.2fr]">
      {/* Player + leyenda */}
      <div className="lg:sticky lg:top-4 lg:self-start">
        <div className="overflow-hidden rounded-xl">
          <YouTube
            videoId={video.data.youtubeId}
            onReady={(e) => (playerRef.current = e.target)}
            opts={{ width: '100%', height: '260', playerVars: { rel: 0 } }}
            iframeClassName="h-full w-full"
          />
        </div>

        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium">Progreso</span>
            <span className="text-slate-500">
              {labeledCount}/{segments.length} etiquetados
            </span>
          </div>
          <div className="mb-4 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full bg-emerald-500 transition-all"
              style={{ width: `${segments.length ? (labeledCount / segments.length) * 100 : 0}%` }}
            />
          </div>
          <p className="mb-2 text-xs font-medium text-slate-500">Subtemas (atajo = número)</p>
          <div className="flex flex-wrap gap-1.5">
            {(taxonomy.data ?? []).map((t, i) => (
              <button
                key={t.key}
                onClick={() => segments[active] && apply(segments[active].id, t.key, true)}
                className="flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs hover:bg-slate-50"
                style={{ borderColor: t.color ?? '#cbd5e1' }}
              >
                <span className="grid h-4 w-4 place-items-center rounded text-[10px] font-bold text-white" style={{ background: t.color ?? '#94a3b8' }}>
                  {i + 1}
                </span>
                {t.name}
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-400">
            ↑/↓ mover foco · número = etiquetar y avanzar · espacio = ir al momento
          </p>
        </div>
      </div>

      {/* Lista de segmentos */}
      <ol className="max-h-[70vh] space-y-1 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2">
        {segments.map((s, i) => {
          const lab = labelBySegment[s.id]
          const color = labelColor(labelMap, lab?.labelKey)
          const isActive = i === active
          return (
            <li key={s.id}>
              <div
                onClick={() => {
                  setActive(i)
                  seekTo(s.startSec)
                }}
                className={`cursor-pointer rounded-md border-l-4 px-3 py-2 ${
                  isActive ? 'bg-indigo-50 ring-1 ring-indigo-300' : 'hover:bg-slate-50'
                }`}
                style={{ borderLeftColor: lab?.isGold ? color : 'transparent' }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-indigo-600">{formatTime(s.startSec)}</span>
                  {lab?.isGold && (
                    <span className="rounded px-1.5 py-0.5 text-[10px] font-medium text-white" style={{ background: color }}>
                      {labelMap[lab.labelKey]?.name ?? lab.labelKey}
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-sm text-slate-700">{s.text}</p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
