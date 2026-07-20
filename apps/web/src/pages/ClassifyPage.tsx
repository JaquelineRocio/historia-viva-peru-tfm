import { useMemo, useRef, useState } from 'react'
import YouTube, { type YouTubePlayer } from 'react-youtube'
import { useSetLabel, useTaxonomy } from '../api/labels'
import { useActiveModel, useClassifyVideo } from '../api/training'
import { useVideo } from '../api/videos'
import { VideoSelect } from '../components/VideoSelect'
import { apiError } from '../lib/apiClient'
import { buildLabelMap, labelColor, labelName } from '../lib/labels'
import { formatTime } from '../lib/format'
import type { SegmentPrediction } from '../types'

export function ClassifyPage() {
  const activeModel = useActiveModel()
  const [videoId, setVideoId] = useState<string | null>(null)

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold">Clasificar</h2>
        <VideoSelect value={videoId} onChange={setVideoId} onlyDone placeholder="Elige un video transcrito…" />
        {activeModel.data ? (
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
            modelo activo: {activeModel.data.versionTag}
          </span>
        ) : (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">
            sin modelo activo — entrena y activa una versión
          </span>
        )}
      </div>
      {videoId ? <Classifier videoId={videoId} /> : <p className="text-slate-500">Selecciona un video.</p>}
    </div>
  )
}

function Classifier({ videoId }: { videoId: string }) {
  const video = useVideo(videoId)
  const taxonomy = useTaxonomy()
  const activeModel = useActiveModel()
  const classify = useClassifyVideo()
  const setLabel = useSetLabel(videoId)
  const playerRef = useRef<YouTubePlayer | null>(null)
  const [preds, setPreds] = useState<SegmentPrediction[]>([])
  const [filter, setFilter] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const labelMap = useMemo(() => buildLabelMap(taxonomy.data), [taxonomy.data])

  function seekTo(sec: number) {
    playerRef.current?.seekTo(sec, true)
    playerRef.current?.playVideo()
  }

  async function onClassify() {
    setError(null)
    try {
      const result = await classify.mutateAsync(videoId)
      setPreds(result)
      setFilter(null)
    } catch (err) {
      setError(apiError(err))
    }
  }

  function correct(p: SegmentPrediction, labelKey: string) {
    const previous = { labelKey: p.labelKey, confidence: p.confidence }
    // Refleja la corrección en memoria (marca como gold visualmente)…
    setPreds((prev) => prev.map((x) => (x.segmentId === p.segmentId ? { ...x, labelKey, confidence: 1 } : x)))
    setLabel.mutate(
      { segmentId: p.segmentId, labelKey },
      {
        // …y revierte si el guardado falla.
        onError: (err) => {
          setPreds((prev) => prev.map((x) => (x.segmentId === p.segmentId ? { ...x, ...previous } : x)))
          setError(apiError(err))
        },
      },
    )
  }

  const total = video.data?.durationSec ?? Math.max(...preds.map((p) => p.endSec), 1)
  const shown = filter ? preds.filter((p) => p.labelKey === filter) : preds
  const counts = preds.reduce<Record<string, number>>((acc, p) => {
    acc[p.labelKey] = (acc[p.labelKey] ?? 0) + 1
    return acc
  }, {})

  if (!video.data) return <div className="text-slate-500">Cargando…</div>

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.2fr]">
      <div className="lg:sticky lg:top-4 lg:self-start">
        <div className="overflow-hidden rounded-xl">
          <YouTube
            videoId={video.data.youtubeId}
            onReady={(e) => (playerRef.current = e.target)}
            opts={{ width: '100%', height: '260', playerVars: { rel: 0 } }}
            iframeClassName="h-full w-full"
          />
        </div>

        <button
          onClick={onClassify}
          disabled={classify.isPending || !activeModel.data}
          className="mt-4 w-full rounded-md bg-indigo-600 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {classify.isPending ? 'Clasificando…' : preds.length ? 'Reclasificar' : 'Clasificar con modelo activo'}
        </button>
        {error && <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        {preds.length > 0 && (
          <>
            {/* Timeline coloreado por subtema */}
            <div className="mt-4">
              <p className="mb-1 text-xs font-medium text-slate-500">Mapa temporal por subtema</p>
              <div className="relative h-5 w-full overflow-hidden rounded bg-slate-100">
                {preds.map((p) => (
                  <button
                    key={p.segmentId}
                    title={`${labelName(labelMap, p.labelKey)} · ${formatTime(p.startSec)}`}
                    onClick={() => seekTo(p.startSec)}
                    className="absolute top-0 h-full hover:opacity-80"
                    style={{
                      left: `${(p.startSec / total) * 100}%`,
                      width: `${Math.max(0.4, ((p.endSec - p.startSec) / total) * 100)}%`,
                      background: labelColor(labelMap, p.labelKey),
                      opacity: filter && filter !== p.labelKey ? 0.15 : 1,
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Filtro por subtema */}
            <div className="mt-4 flex flex-wrap gap-1.5">
              <Chip active={filter === null} onClick={() => setFilter(null)} color="#64748b">
                Todos ({preds.length})
              </Chip>
              {(taxonomy.data ?? [])
                .filter((t) => counts[t.key])
                .map((t) => (
                  <Chip key={t.key} active={filter === t.key} onClick={() => setFilter(t.key)} color={t.color ?? '#94a3b8'}>
                    {t.name} ({counts[t.key]})
                  </Chip>
                ))}
            </div>
          </>
        )}
      </div>

      {/* Segmentos clasificados */}
      <ol className="max-h-[70vh] space-y-1 overflow-y-auto rounded-xl border border-slate-200 bg-white p-2">
        {shown.map((p) => {
          const color = labelColor(labelMap, p.labelKey)
          return (
            <li key={p.segmentId} className="rounded-md border-l-4 px-3 py-2 hover:bg-slate-50" style={{ borderLeftColor: color }}>
              <div className="flex items-center justify-between">
                <button onClick={() => seekTo(p.startSec)} className="font-mono text-xs text-indigo-600 hover:underline">
                  {formatTime(p.startSec)}
                </button>
                <span className="flex items-center gap-2">
                  <span className="rounded px-1.5 py-0.5 text-[10px] font-medium text-white" style={{ background: color }}>
                    {labelName(labelMap, p.labelKey)}
                  </span>
                  <span className="text-[10px] text-slate-400">{Math.round(p.confidence * 100)}%</span>
                </span>
              </div>
              <p className="mt-0.5 text-sm text-slate-700">{p.text}</p>
              {/* Corrección → alimenta el dataset (active learning) */}
              <details className="mt-1">
                <summary className="cursor-pointer text-[11px] text-slate-400 hover:text-slate-600">corregir</summary>
                <div className="mt-1 flex flex-wrap gap-1">
                  {(taxonomy.data ?? []).map((t) => (
                    <button
                      key={t.key}
                      onClick={() => correct(p, t.key)}
                      className="rounded border px-1.5 py-0.5 text-[10px] hover:bg-slate-100"
                      style={{ borderColor: t.color ?? '#cbd5e1' }}
                    >
                      {t.name}
                    </button>
                  ))}
                </div>
              </details>
            </li>
          )
        })}
        {preds.length === 0 && (
          <li className="p-6 text-center text-sm text-slate-400">
            Pulsa «Clasificar» para que el modelo activo prediga los subtemas de cada segmento.
          </li>
        )}
      </ol>
    </div>
  )
}

function Chip({
  active,
  onClick,
  color,
  children,
}: {
  active: boolean
  onClick: () => void
  color: string
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${active ? 'bg-slate-800 text-white' : 'bg-white hover:bg-slate-50'}`}
      style={{ borderColor: color }}
    >
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      {children}
    </button>
  )
}
