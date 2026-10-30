import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useResources, useSegmentsOfResources } from '../api/resources'
import { useSubtopics } from '../api/labels'
import { useActiveProject } from '../projects/ProjectContext'
import { formatTime } from '../lib/format'
import { MIN_SUGGESTION, NOT_RELEVANT, SUBTOPICS, currentLabel, segmentState } from '../lib/indexing'
import type { HistoryResource, ResourceSegment } from '../types'

interface Hit {
  video: HistoryResource
  segment: ResourceSegment
}

/** Reúne, de todos los videos, los fragmentos de un mismo subtema. */
export function TopicsPage() {
  const { project } = useActiveProject()
  const resources = useResources(project?.id)
  const videos = (resources.data ?? []).filter((item) => item.type === 'youtube' && item.processingStatus === 'ready')
  const queries = useSegmentsOfResources(videos.map((video) => video.id))
  const subtopics = useSubtopics()
  const [topic, setTopic] = useState(SUBTOPICS[0].key)
  const loading = resources.isLoading || queries.some((query) => query.isLoading)

  const all: Hit[] = videos.flatMap((video, index) => (queries[index]?.data ?? []).map((segment) => ({ video, segment })))
  const main = all.filter((hit) => currentLabel(hit.segment) === topic)
  const possible = all.filter((hit) =>
    currentLabel(hit.segment) !== topic &&
    segmentState(hit.segment) !== 'confirmed' &&
    hit.segment.suggestedAlternatives?.[0]?.label === topic &&
    hit.segment.suggestedAlternatives[0].confidence >= MIN_SUGGESTION,
  )
  const count = (key: string) => all.filter((hit) => currentLabel(hit.segment) === key).length

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight">Fragmentos por subtema</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Elige un subtema y verás, de todos tus videos, los fragmentos que lo tratan con su minuto exacto.</p>

      <div className="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-3" role="group" aria-label="Subtemas">
        {SUBTOPICS.filter((item) => item.key !== NOT_RELEVANT).map((item) => {
          const selected = item.key === topic
          return (
            <button key={item.key} type="button" aria-pressed={selected} onClick={() => setTopic(item.key)} className={`rounded-2xl border p-3 text-left transition ${selected ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-100' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
              <span className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 font-semibold text-slate-900">
                  <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: subtopics[item.key]?.color ?? item.color }} aria-hidden="true" />
                  {subtopics[item.key]?.name ?? item.name}
                </span>
                <span className="text-xs font-semibold text-slate-500">{loading ? '…' : count(item.key)}</span>
              </span>
              <span className="mt-1 block text-xs leading-5 text-slate-500">{item.description}</span>
            </button>
          )
        })}
      </div>

      {loading && <p className="mt-6 text-sm text-slate-500">Reuniendo los fragmentos de tus videos…</p>}
      {!loading && !videos.length && <p className="mt-6 rounded-2xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">Todavía no tienes videos indexados. <Link to="/" className="font-semibold text-indigo-700">Añade uno</Link>.</p>}
      {!loading && videos.length > 0 && (
        <>
          <HitList title={main.length === 1 ? '1 fragmento' : `${main.length} fragmentos`} hits={main} empty="Ningún fragmento de tus videos trata este subtema como tema principal." />
          {possible.length > 0 && <HitList title={`También podrían tratarlo (${possible.length})`} hint="Es su segunda sugerencia; confírmalo en el video si te sirve." hits={possible} />}
        </>
      )}
    </div>
  )
}

function HitList({ title, hint, hits, empty }: { title: string; hint?: string; hits: Hit[]; empty?: string }) {
  return (
    <section className="mt-7">
      <h2 className="font-bold">{title}</h2>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      <ul className="mt-3 space-y-3">
        {hits.map(({ video, segment }) => (
          <li key={segment.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center gap-2">
              <Link to={`/videos/${video.id}?fragmento=${segment.id}`} className="inline-flex min-h-9 items-center gap-1.5 rounded-lg bg-indigo-600 px-3 text-sm font-bold text-white hover:bg-indigo-700">
                <span aria-hidden="true">▶</span> {formatTime(segment.startSec ?? 0)}
              </Link>
              <span className="min-w-0 truncate text-sm font-semibold text-slate-700">{video.title}</span>
              {segmentState(segment) === 'confirmed' && <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">Confirmado</span>}
            </div>
            <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-700">{segment.text}</p>
          </li>
        ))}
      </ul>
      {!hits.length && empty && <p className="mt-3 rounded-2xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">{empty}</p>}
    </section>
  )
}
