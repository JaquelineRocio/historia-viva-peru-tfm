import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { publicProjects, publicSearch } from '../api/resources'
import { formatTime } from '../lib/format'
import type { HistoryProject, SearchEvidence } from '../types'

const PdfEvidenceViewer = lazy(() => import('../components/PdfEvidenceViewer').then((module) => ({ default: module.PdfEvidenceViewer })))

export function PublicExplorePage() {
  const [projects, setProjects] = useState<HistoryProject[]>([])
  const [projectId, setProjectId] = useState('')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [evidence, setEvidence] = useState<SearchEvidence[]>([])
  const [loading, setLoading] = useState(false)
  const [pdfEvidence, setPdfEvidence] = useState<SearchEvidence>()

  useEffect(() => {
    publicProjects().then((items) => {
      setProjects(items)
      if (items.length) setProjectId(items[0].id)
    })
  }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    try {
      const result = await publicSearch(projectId, query)
      setAnswer(result.answer)
      setEvidence(result.evidence)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/explorar" className="flex items-center gap-2 font-bold"><span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-600 font-serif text-white">H</span>Historia Viva <span className="text-indigo-600">Perú</span></Link>
          <Link to="/login" className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold">Espacio docente</Link>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-12">
        <section className="text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600">Repositorio histórico verificable</p>
          <h1 className="mx-auto mt-3 max-w-3xl text-4xl font-bold leading-tight">Busca evidencia en fuentes revisadas por docentes.</h1>
          <p className="mx-auto mt-3 max-w-2xl text-slate-500">Cada resultado conserva su página o minuto original. Si no existe respaldo, te lo diremos claramente.</p>
        </section>
        {projects.length ? (
          <>
            <form onSubmit={submit} className="mx-auto mt-8 flex max-w-3xl gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
              <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="max-w-52 rounded-xl border-0 bg-slate-100 px-3 text-sm font-medium shadow-none">
                {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
              </select>
              <input required minLength={3} value={query} onChange={(e) => setQuery(e.target.value)} placeholder="¿Qué deseas investigar?" className="min-w-0 flex-1 border-0 px-3 shadow-none focus:ring-0" />
              <button disabled={loading} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white">{loading ? 'Buscando…' : 'Buscar'}</button>
            </form>
            {answer && <div className="mx-auto mt-8 max-w-3xl rounded-2xl border border-indigo-200 bg-indigo-50 p-5 text-sm text-indigo-950"><span className="font-semibold">Resultado: </span>{answer}</div>}
            <div className="mx-auto mt-5 max-w-3xl space-y-3">
              {evidence.map((item, index) => (
                <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5">
                  <div className="flex gap-3">
                    <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-indigo-600 text-xs font-bold text-white">[{index + 1}]</span>
                    <div>
                      <p className="text-xs font-semibold text-indigo-700">{item.title} · {item.locatorType === 'timestamp' ? formatTime(item.startSec ?? 0) : `Página ${item.pageStart}`}</p>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{item.text}</p>
                      {item.type === 'pdf' && <button onClick={() => setPdfEvidence(item)} className="mt-3 text-xs font-semibold text-indigo-600">Abrir página exacta ↗</button>}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </>
        ) : (
          <div className="mx-auto mt-10 max-w-xl rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">Todavía no hay proyectos públicos. Un curador debe aprobar la primera fuente.</div>
        )}
      </main>
      {pdfEvidence && <Suspense fallback={null}><PdfEvidenceViewer evidence={pdfEvidence} publicMode onClose={() => setPdfEvidence(undefined)} /></Suspense>}
    </div>
  )
}
