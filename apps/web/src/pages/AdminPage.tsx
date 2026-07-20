import { useDecidePublication, usePublicationReviews } from '../api/resources'

export function AdminPage() {
  const reviews = usePublicationReviews()
  const decide = useDecidePublication()
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Curaduría</p>
      <h1 className="text-2xl font-bold">Solicitudes de publicación</h1>
      <p className="mt-1 text-sm text-slate-500">Comprueba procedencia, derechos y calidad antes de hacer visible una fuente.</p>
      <div className="mt-6 space-y-3">
        {reviews.data?.map((review) => (
          <article key={review.id} className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2"><h2 className="font-semibold">{review.title}</h2><span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">{review.type === 'youtube' ? 'YouTube' : 'PDF'}</span></div>
                <p className="mt-2 text-xs text-slate-500">Licencia: {review.license || 'No especificada'} · Derechos declarados: {review.rightsConfirmed ? 'Sí' : 'No'}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => decide.mutate({ id: review.id, status: 'rejected', note: 'Requiere corregir licencia o procedencia' })} className="rounded-xl border border-red-300 px-3 py-2 text-sm font-semibold text-red-700">Rechazar</button>
                <button onClick={() => decide.mutate({ id: review.id, status: 'approved' })} className="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white">Aprobar</button>
              </div>
            </div>
          </article>
        ))}
        {reviews.data?.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400">No hay solicitudes pendientes.</div>}
      </div>
    </div>
  )
}
