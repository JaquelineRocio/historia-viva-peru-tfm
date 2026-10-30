import { useState } from 'react'
import { formatTime } from '../lib/format'
import {
  NOT_RELEVANT,
  SUBTOPICS,
  currentLabel,
  percent,
  segmentState,
  subtopicColor,
  subtopicName,
  suggestions,
  type IndexedSegment,
  type SegmentState,
  type SubtopicMap,
} from '../lib/indexing'

const STATE: Record<SegmentState, { label: string; cls: string }> = {
  confirmed: { label: 'Confirmado', cls: 'bg-emerald-100 text-emerald-800' },
  auto: { label: 'Etiquetado automático', cls: 'bg-indigo-100 text-indigo-800' },
  pending: { label: 'Por confirmar', cls: 'bg-amber-100 text-amber-800' },
  unclassified: { label: 'Sin analizar', cls: 'bg-slate-100 text-slate-600' },
}

interface Props {
  segment: IndexedSegment
  subtopics: SubtopicMap
  active?: boolean
  onPlay: () => void
  /** Sin esta función la tarjeta es de solo lectura. */
  onDecide?: (labelKey: string) => void
  busy?: boolean
}

export function SegmentCard({ segment, subtopics, active, onPlay, onDecide, busy }: Props) {
  const [editing, setEditing] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const state = segmentState(segment)
  const label = currentLabel(segment)
  const options = suggestions(segment)
  const start = segment.startSec ?? 0
  const end = segment.endSec ?? start
  const asking = !!onDecide && (state === 'pending' || editing)

  function decide(labelKey: string) {
    onDecide?.(labelKey)
    setEditing(false)
  }

  return (
    <li id={`segmento-${segment.id}`} className={`scroll-mt-24 rounded-2xl border bg-white p-4 shadow-sm transition ${active ? 'border-indigo-500 ring-2 ring-indigo-100' : 'border-slate-200'}`}>
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={onPlay} aria-pressed={active} className="inline-flex min-h-9 items-center gap-1.5 rounded-lg bg-indigo-600 px-3 text-sm font-bold text-white hover:bg-indigo-700">
          <span aria-hidden="true">▶</span> {formatTime(start)}
          <span className="font-normal text-indigo-200">– {formatTime(end)}</span>
        </button>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATE[state].cls}`}>{STATE[state].label}</span>
      </div>

      <div className="mt-3 flex items-start gap-2">
        <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: subtopicColor(subtopics, label) }} aria-hidden="true" />
        <div className="min-w-0">
          <p className="font-bold leading-snug text-slate-900">{label ? subtopicName(subtopics, label) : 'Subtema pendiente de análisis'}</p>
          {state !== 'confirmed' && options.length > 0 && (
            <p className="mt-0.5 text-xs text-slate-500">
              {percent(options[0].confidence)} de confianza
              {options[1] && ` · también podría ser ${subtopicName(subtopics, options[1].label)} (${percent(options[1].confidence)})`}
            </p>
          )}
        </div>
      </div>

      <p className={`mt-3 text-sm leading-6 text-slate-700 ${expanded ? '' : 'line-clamp-3'}`}>{segment.text}</p>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs font-semibold">
        {segment.text.length > 240 && (
          <button type="button" onClick={() => setExpanded((value) => !value)} className="text-slate-500 hover:text-slate-700">
            {expanded ? 'Ver menos' : 'Leer la transcripción completa'}
          </button>
        )}
        {onDecide && !asking && state !== 'unclassified' && (
          <button type="button" onClick={() => setEditing(true)} className="text-indigo-700 underline-offset-2 hover:underline">Corregir subtema</button>
        )}
      </div>

      {asking && (
        <div className="mt-3 rounded-xl bg-slate-50 p-3">
          <p className="text-xs font-semibold text-slate-600">¿Qué subtema trata este fragmento?</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {options.filter((item) => item.label !== NOT_RELEVANT).map((item) => (
              <button key={item.label} type="button" disabled={busy} onClick={() => decide(item.label)} className="min-h-9 rounded-lg border border-indigo-300 bg-white px-3 text-left text-sm font-semibold text-indigo-800 hover:bg-indigo-50 disabled:opacity-50">
                ✓ {subtopicName(subtopics, item.label)}
              </button>
            ))}
            <select disabled={busy} value="" onChange={(event) => event.target.value && decide(event.target.value)} aria-label="Elegir otro subtema" className="min-h-9 max-w-full rounded-lg border border-slate-300 bg-white px-2 text-sm text-slate-700">
              <option value="">Otro subtema…</option>
              {SUBTOPICS.filter((item) => item.key !== NOT_RELEVANT).map((item) => <option key={item.key} value={item.key}>{subtopics[item.key]?.name ?? item.name}</option>)}
            </select>
            <button type="button" disabled={busy} onClick={() => decide(NOT_RELEVANT)} className="min-h-9 rounded-lg border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-600 hover:bg-slate-100 disabled:opacity-50">No es relevante</button>
            {editing && <button type="button" onClick={() => setEditing(false)} className="min-h-9 px-2 text-sm text-slate-500 underline">Cancelar</button>}
          </div>
        </div>
      )}
    </li>
  )
}
