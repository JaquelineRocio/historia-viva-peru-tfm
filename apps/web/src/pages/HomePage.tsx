import { Link } from 'react-router-dom'
import { useProjectDashboard } from '../api/resources'
import { useActiveProject } from '../projects/ProjectContext'

export function HomePage() {
  const { project } = useActiveProject()
  const dashboard = useProjectDashboard(project?.id)
  const stats = dashboard.data
  const progress = stats?.segments ? Math.round((stats.reviewed / stats.segments) * 100) : 0

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-700 via-indigo-600 to-violet-600 px-7 py-8 text-white shadow-lg">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-indigo-100">Historia Viva Perú</p>
        <h1 className="max-w-2xl text-3xl font-bold leading-tight">Encuentra y cita evidencia histórica sin recorrer fuentes completas.</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-indigo-100">Añade un video o PDF, revisa sus subtemas y localiza cada evidencia en el minuto o página exactos.</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/fuentes" className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-700 shadow-sm">Añadir una fuente</Link>
          <Link to="/buscar" className="rounded-xl border border-white/40 px-4 py-2.5 text-sm font-semibold hover:bg-white/10">Buscar evidencia</Link>
        </div>
      </section>
      <section>
        <div className="mb-3 flex items-end justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Proyecto activo</p>
            <h2 className="text-xl font-bold">{project?.name ?? 'Preparando proyecto inicial…'}</h2>
            {project && <p className="text-sm text-slate-500">{project.periodStart}–{project.periodEnd}</p>}
          </div>
          <Link to="/proyectos" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">Ver proyectos</Link>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Fuentes" value={stats?.resources ?? 0} hint="YouTube y PDF" />
          <Stat label="Fragmentos" value={stats?.segments ?? 0} hint="Con página o minuto" />
          <Stat label="Revisados" value={stats?.reviewed ?? 0} hint={`${progress}% de avance`} accent />
          <Stat label="Pendientes" value={stats?.pending ?? 0} hint="Por confirmar" />
        </div>
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="font-semibold">Tu flujo de trabajo</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-5">
          {[
            ['1', 'Añadir', 'Video o PDF'],
            ['2', 'Procesar', 'Texto y segmentos'],
            ['3', 'Revisar', 'Confirmar subtemas'],
            ['4', 'Entrenar', 'Mejorar BETO'],
            ['5', 'Encontrar', 'Evidencia citable'],
          ].map(([step, title, caption]) => (
            <div key={step} className="rounded-xl bg-slate-50 p-3">
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-indigo-100 text-xs font-bold text-indigo-700">{step}</span>
              <p className="mt-2 text-sm font-semibold">{title}</p>
              <p className="text-xs text-slate-500">{caption}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

function Stat({ label, value, hint, accent }: { label: string; value: number; hint: string; accent?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${accent ? 'border-indigo-200 bg-indigo-50' : 'border-slate-200 bg-white'}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-slate-900">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{hint}</p>
    </div>
  )
}
