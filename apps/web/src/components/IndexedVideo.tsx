import { useEffect, useRef, useState } from 'react'
import { VideoPlayer, type VideoPlayerHandle } from './VideoPlayer'
import { SegmentCard } from './SegmentCard'
import { SUBTOPICS, currentLabel, isHidden, segmentState, type IndexedSegment, type SubtopicMap } from '../lib/indexing'

interface Props {
  sourceUrl: string
  segments: IndexedSegment[]
  subtopics: SubtopicMap
  /** Sin esta función la vista es de solo lectura (demostración pública). */
  onDecide?: (segmentId: string, labelKey: string) => void
  decidingId?: string
  initialSegmentId?: string
}

/** Video con su índice temático: reproductor, filtros por subtema y lista de fragmentos. */
export function IndexedVideo({ sourceUrl, segments, subtopics, onDecide, decidingId, initialSegmentId }: Props) {
  const player = useRef<VideoPlayerHandle | null>(null)
  const playerBox = useRef<HTMLDivElement | null>(null)
  const initial = segments.find((segment) => segment.id === initialSegmentId)
  const [activeId, setActiveId] = useState(initial?.id ?? '')
  const [topic, setTopic] = useState('')
  const [showHidden, setShowHidden] = useState(!!initial && isHidden(initial))
  const [onlyPending, setOnlyPending] = useState(false)

  useEffect(() => {
    if (initial?.id) document.getElementById(`segmento-${initial.id}`)?.scrollIntoView({ block: 'center' })
  }, [initial?.id])

  const visible = segments.filter((segment) => !isHidden(segment))
  const hiddenCount = segments.length - visible.length
  const pendingCount = visible.filter((segment) => segmentState(segment) === 'pending').length
  const base = showHidden ? segments : visible
  const counts = new Map<string, number>()
  for (const segment of base) {
    const key = currentLabel(segment)
    if (key) counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  const shown = base
    .filter((segment) => !topic || currentLabel(segment) === topic)
    .filter((segment) => !onlyPending || segmentState(segment) === 'pending')

  function play(segment: IndexedSegment) {
    setActiveId(segment.id)
    player.current?.seekTo(segment.startSec ?? 0)
    if (window.innerWidth < 1024) playerBox.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const chip = (selected: boolean) => `min-h-9 rounded-full border px-3 text-xs font-semibold transition ${selected ? 'border-indigo-600 bg-indigo-600 text-white' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-100'}`

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:items-start">
      <div ref={playerBox} className="scroll-mt-20 lg:sticky lg:top-20">
        <VideoPlayer key={sourceUrl} ref={player} sourceUrl={sourceUrl} startSec={initial?.startSec ?? 0} />
        <p className="mt-2 text-xs text-slate-500">Pulsa el minuto de un fragmento para ver ese momento del video.</p>
      </div>

      <section aria-label="Fragmentos del video" className="min-w-0">
        <p className="text-sm text-slate-600">
          <strong className="text-slate-900">{visible.length}</strong> {visible.length === 1 ? 'fragmento' : 'fragmentos'} sobre la Independencia
          {onDecide && pendingCount > 0 && <> · <strong className="text-amber-700">{pendingCount}</strong> por confirmar</>}
          {hiddenCount > 0 && <> · {hiddenCount === 1 ? '1 oculto por no ser relevante' : `${hiddenCount} ocultos por no ser relevantes`}</>}
        </p>

        <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Filtrar por subtema">
          <button type="button" onClick={() => setTopic('')} className={chip(!topic)}>Todos · {base.length}</button>
          {SUBTOPICS.filter((item) => counts.has(item.key)).map((item) => (
            <button key={item.key} type="button" onClick={() => setTopic(topic === item.key ? '' : item.key)} title={subtopics[item.key]?.description} className={chip(topic === item.key)}>
              <span className="mr-1.5 inline-block h-2 w-2 rounded-full align-middle" style={{ backgroundColor: subtopics[item.key]?.color ?? item.color }} aria-hidden="true" />
              {subtopics[item.key]?.name ?? item.name} · {counts.get(item.key)}
            </button>
          ))}
        </div>

        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-600">
          {onDecide && pendingCount > 0 && (
            <label className="inline-flex items-center gap-2"><input type="checkbox" checked={onlyPending} onChange={(event) => setOnlyPending(event.target.checked)} className="h-4 w-4 accent-indigo-600" />Solo los que faltan confirmar</label>
          )}
          {hiddenCount > 0 && (
            <label className="inline-flex items-center gap-2"><input type="checkbox" checked={showHidden} onChange={(event) => setShowHidden(event.target.checked)} className="h-4 w-4 accent-indigo-600" />Mostrar los no relevantes</label>
          )}
        </div>

        <ol className="mt-4 space-y-3">
          {shown.map((segment) => (
            <SegmentCard
              key={segment.id}
              segment={segment}
              subtopics={subtopics}
              active={segment.id === activeId}
              onPlay={() => play(segment)}
              onDecide={onDecide ? (labelKey) => onDecide(segment.id, labelKey) : undefined}
              busy={decidingId === segment.id}
            />
          ))}
        </ol>
        {!shown.length && <p className="mt-4 rounded-2xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">No hay fragmentos con este filtro.</p>}
      </section>
    </div>
  )
}
