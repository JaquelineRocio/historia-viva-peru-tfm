import { useState, type FormEvent } from 'react'
import { useCreateProject, useProjects } from '../api/resources'
import { apiError } from '../lib/apiClient'

export function ProjectsPage() {
  const projects = useProjects()
  const create = useCreateProject()
  const [name, setName] = useState('')
  const [start, setStart] = useState(1780)
  const [end, setEnd] = useState(1842)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      await create.mutateAsync({ name, periodStart: start, periodEnd: end })
      setName('')
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
      <section>
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Organización</p>
        <h1 className="text-2xl font-bold">Mis proyectos históricos</h1>
        <p className="mt-1 text-sm text-slate-500">Cada proyecto reúne fuentes, revisiones y modelos de un periodo.</p>
        <div className="mt-5 space-y-3">
          {projects.data?.map((project, index) => (
            <article key={project.id} className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-semibold">{project.name}</h2>
                  <p className="mt-1 text-sm text-slate-500">{project.periodStart}–{project.periodEnd}</p>
                  {project.description && <p className="mt-2 text-sm text-slate-600">{project.description}</p>}
                </div>
                {index === 0 && <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">Activo</span>}
              </div>
            </article>
          ))}
        </div>
      </section>
      <form onSubmit={submit} className="h-fit rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="font-semibold">Nuevo proyecto</h2>
        <label className="mt-4 block text-sm font-medium">Nombre</label>
        <input value={name} onChange={(e) => setName(e.target.value)} required className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm" placeholder="Ej. Guerra del Pacífico" />
        <div className="mt-3 grid grid-cols-2 gap-3">
          <label className="text-sm font-medium">Desde<input type="number" value={start} onChange={(e) => setStart(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5" /></label>
          <label className="text-sm font-medium">Hasta<input type="number" value={end} onChange={(e) => setEnd(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5" /></label>
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        <button disabled={create.isPending} className="mt-4 w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
          {create.isPending ? 'Creando…' : 'Crear proyecto'}
        </button>
      </form>
    </div>
  )
}
