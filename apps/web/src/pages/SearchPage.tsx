import { lazy, Suspense, useState, type FormEvent } from 'react'
import { askProject, useCollections, useEvidenceFeedback, useSaveEvidence, useSearchFacets } from '../api/resources'
import { useActiveProject } from '../projects/ProjectContext'
import { formatTime } from '../lib/format'
import type { HistoricalSearchFilters, SearchEvidence } from '../types'

const PdfEvidenceViewer = lazy(() => import('../components/PdfEvidenceViewer').then((module) => ({ default: module.PdfEvidenceViewer })))

export function SearchPage() {
  const { project } = useActiveProject()
  const collections = useCollections(project?.id)
  const saveEvidence = useSaveEvidence(project?.id)
  const facets = useSearchFacets(project?.id)
  const [collectionId, setCollectionId] = useState('')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [evidence, setEvidence] = useState<SearchEvidence[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [filters, setFilters] = useState<HistoricalSearchFilters>({})
  const [pdfEvidence, setPdfEvidence] = useState<SearchEvidence>()

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!project) return
    setLoading(true)
    setSearched(true)
    try {
      const result = await askProject(project.id, query, filters)
      setAnswer(result.answer)
      setEvidence(result.evidence)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Asistente con evidencia</p>
        <h1 className="mt-2 text-3xl font-bold">¿Qué quieres encontrar en tus fuentes?</h1>
        <p className="mx-auto mt-2 max-w-2xl text-sm text-slate-500">La respuesta solo utiliza fragmentos localizados. Siempre podrás volver al minuto o página original.</p>
      </div>
      <form onSubmit={submit} className="mt-7 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm focus-within:border-indigo-300">
        <div className="flex gap-2">
          <input value={query} onChange={(e) => setQuery(e.target.value)} minLength={3} required placeholder="Ej. ¿Qué consecuencias políticas tuvo la Independencia?" className="min-w-0 flex-1 border-0 px-3 py-2.5 text-base shadow-none ring-0 focus:border-0 focus:ring-0" />
          <button disabled={loading || !project} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">{loading ? 'Buscando…' : 'Buscar'}</button>
        </div>
        <div className="mt-2 grid gap-2 border-t border-slate-100 pt-3 sm:grid-cols-2 lg:grid-cols-5">
          <select value={filters.person ?? ''} onChange={(e) => setFilters((current) => ({ ...current, person: e.target.value || undefined }))} className="rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-600">
            <option value="">Todos los personajes</option>
            {facets.data?.persons.map((item) => <option key={String(item.value)} value={String(item.value)}>{item.label} ({item.count})</option>)}
          </select>
          <select value={filters.place ?? ''} onChange={(e) => setFilters((current) => ({ ...current, place: e.target.value || undefined }))} className="rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-600">
            <option value="">Todos los lugares</option>
            {facets.data?.places.map((item) => <option key={String(item.value)} value={String(item.value)}>{item.label} ({item.count})</option>)}
          </select>
          <input type="number" min={1000} max={2100} value={filters.yearStart ?? ''} onChange={(e) => setFilters((current) => ({ ...current, yearStart: e.target.value ? Number(e.target.value) : undefined }))} placeholder="Año desde" className="rounded-xl border border-slate-200 px-3 py-2 text-xs" />
          <input type="number" min={1000} max={2100} value={filters.yearEnd ?? ''} onChange={(e) => setFilters((current) => ({ ...current, yearEnd: e.target.value ? Number(e.target.value) : undefined }))} placeholder="Año hasta" className="rounded-xl border border-slate-200 px-3 py-2 text-xs" />
          <select value={filters.label ?? ''} onChange={(e) => setFilters((current) => ({ ...current, label: e.target.value || undefined }))} className="rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-600">
            <option value="">Todos los subtemas</option>
            {facets.data?.labels.map((item) => <option key={String(item.value)} value={String(item.value)}>{item.label} ({item.count})</option>)}
          </select>
        </div>
        {Object.values(filters).some((value) => value !== undefined && value !== '') && (
          <button type="button" onClick={() => setFilters({})} className="mt-2 px-2 text-xs font-semibold text-indigo-600">Limpiar filtros</button>
        )}
      </form>

      {searched && !loading && (
        <div className="mt-7 space-y-5">
          <section className={`rounded-2xl border p-5 ${evidence.length ? 'border-indigo-200 bg-indigo-50' : 'border-amber-200 bg-amber-50'}`}>
            <div className="flex items-start gap-3">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white text-indigo-700 shadow-sm">✦</span>
              <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Respuesta verificable</p><p className="mt-1 text-sm leading-6 text-slate-700">{answer}</p></div>
            </div>
          </section>
          {evidence.length > 0 && (
            <section>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <h2 className="font-semibold">Evidencias encontradas</h2>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">{evidence.length} citas</span>
                  <select value={collectionId} onChange={(e) => setCollectionId(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-1.5 text-xs">
                    <option value="">Guardar en colección…</option>
                    {collections.data?.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="space-y-3">
                {evidence.map((item, index) => (
                  <EvidenceCard
                    key={item.id}
                    item={item}
                    index={index + 1}
                    canSave={!!collectionId}
                    onSave={() => collectionId && saveEvidence.mutate({ collectionId, segmentId: item.id })}
                    onOpenPdf={() => setPdfEvidence(item)}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
      {pdfEvidence && <Suspense fallback={null}><PdfEvidenceViewer evidence={pdfEvidence} onClose={() => setPdfEvidence(undefined)} /></Suspense>}
    </div>
  )
}

function EvidenceCard({ item, index, canSave, onSave, onOpenPdf }: { item: SearchEvidence; index: number; canSave: boolean; onSave: () => void; onOpenPdf: () => void }) {
  const feedback = useEvidenceFeedback()
  const locator = item.locatorType === 'timestamp'
    ? `${formatTime(item.startSec ?? 0)}–${formatTime(item.endSec ?? 0)}`
    : `Página ${item.pageStart}`
  const href = item.type === 'youtube' && item.sourceUrl
    ? `${item.sourceUrl}${item.sourceUrl.includes('?') ? '&' : '?'}t=${Math.floor(item.startSec ?? 0)}s`
    : undefined
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 hover:border-indigo-300">
      <div className="flex items-start gap-3">
        <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-indigo-600 text-xs font-bold text-white">[{index}]</span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{item.title}</h3>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{item.type === 'youtube' ? 'Video' : 'PDF'} · {locator}</span>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-700">{item.text}</p>
          {!!item.entities?.length && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {item.entities
                .filter((entity) => ['person', 'place', 'date', 'period'].includes(entity.type))
                .filter((entity, entityIndex, all) => all.findIndex((other) => other.type === entity.type && other.normalizedValue === entity.normalizedValue) === entityIndex)
                .slice(0, 8)
                .map((entity) => (
                  <span key={`${entity.type}-${entity.normalizedValue}`} className="rounded-full bg-violet-50 px-2 py-1 text-[11px] font-medium text-violet-700">
                    {entity.type === 'person' ? '👤' : entity.type === 'place' ? '⌖' : '◷'} {entity.text}
                  </span>
                ))}
            </div>
          )}
          <div className="mt-3 flex flex-wrap gap-3">
            {href && <a href={href} target="_blank" rel="noreferrer" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">Abrir en el momento exacto ↗</a>}
            {item.type === 'pdf' && <button onClick={onOpenPdf} className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">Abrir página exacta ↗</button>}
            <button disabled={!canSave} onClick={onSave} className="text-xs font-semibold text-violet-600 disabled:text-slate-300">Guardar evidencia</button>
            <span className="text-xs text-slate-400">¿Esta evidencia ayuda?</span>
            <button onClick={() => feedback.mutate({ segmentId: item.id, value: 'useful' })} className="text-xs font-semibold text-emerald-700">Sí, útil</button>
            <button onClick={() => feedback.mutate({ segmentId: item.id, value: 'irrelevant' })} className="text-xs font-semibold text-amber-700">No es relevante</button>
            <button onClick={() => feedback.mutate({ segmentId: item.id, value: 'incorrect' })} className="text-xs font-semibold text-red-700">Es incorrecta</button>
            {feedback.isSuccess && <span className="text-xs font-semibold text-emerald-600">Feedback guardado ✓</span>}
          </div>
        </div>
      </div>
    </article>
  )
}
