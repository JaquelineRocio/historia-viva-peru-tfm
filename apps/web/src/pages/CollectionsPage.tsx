import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useCollection, useCollections, useCreateCollection } from '../api/resources'
import { useActiveProject } from '../projects/ProjectContext'
import { formatTime } from '../lib/format'

export function CollectionsPage() {
  const { project } = useActiveProject()
  const collections = useCollections(project?.id)
  const create = useCreateCollection(project?.id)
  const [selectedId, setSelectedId] = useState<string>()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const selected = useCollection(selectedId)

  useEffect(() => {
    if (!selectedId && collections.data?.length) setSelectedId(collections.data[0].id)
  }, [collections.data, selectedId])

  async function submit(event: FormEvent) {
    event.preventDefault()
    const collection = await create.mutateAsync({ name, description: description || undefined })
    setSelectedId(collection.id)
    setName('')
    setDescription('')
  }

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Curación docente</p>
      <h1 className="text-2xl font-bold">Colecciones de evidencias</h1>
      <p className="mt-1 text-sm text-slate-500">Agrupa fragmentos citables para preparar clases y rutas de estudio.</p>
      <div className="mt-6 grid gap-5 lg:grid-cols-[320px_1fr]">
        <aside>
          <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-4">
            <h2 className="font-semibold">Nueva colección</h2>
            <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Ej. Campañas de San Martín" className="mt-3 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm" />
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Propósito de la colección" rows={2} className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm" />
            <button disabled={create.isPending || !project} className="mt-2 w-full rounded-xl bg-indigo-600 px-3 py-2.5 text-sm font-semibold text-white">Crear colección</button>
          </form>
          <div className="mt-4 space-y-2">
            {collections.data?.map((collection) => (
              <button key={collection.id} onClick={() => setSelectedId(collection.id)} className={`w-full rounded-xl border p-3 text-left ${selectedId === collection.id ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 bg-white'}`}>
                <p className="text-sm font-semibold">{collection.name}</p>
                <p className="mt-1 text-xs text-slate-400">{collection.itemCount ?? 0} evidencias</p>
              </button>
            ))}
          </div>
        </aside>
        <section className="rounded-2xl border border-slate-200 bg-white p-5">
          {selected.data ? (
            <>
              <div className="flex items-start justify-between gap-4">
                <div><h2 className="text-lg font-bold">{selected.data.name}</h2><p className="mt-1 text-sm text-slate-500">{selected.data.description || 'Colección docente'}</p></div>
                <Link to="/buscar" className="rounded-xl bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-700">Añadir evidencias</Link>
              </div>
              <div className="mt-5 space-y-3">
                {selected.data.items?.map((item, index) => (
                  <article key={item.id} className="rounded-xl bg-slate-50 p-4">
                    <div className="flex gap-3">
                      <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-indigo-600 text-xs font-bold text-white">{index + 1}</span>
                      <div><p className="text-xs font-semibold text-indigo-700">{item.title} · {item.locatorType === 'timestamp' ? formatTime(item.startSec ?? 0) : `Página ${item.pageStart}`}</p><p className="mt-2 text-sm leading-6 text-slate-700">{item.text}</p>{item.note && <p className="mt-2 text-xs italic text-slate-500">{item.note}</p>}</div>
                    </div>
                  </article>
                ))}
                {!selected.data.items?.length && <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400">Busca evidencia y guárdala en esta colección.</div>}
              </div>
            </>
          ) : (
            <div className="grid min-h-72 place-items-center text-sm text-slate-400">Crea o selecciona una colección.</div>
          )}
        </section>
      </div>
    </div>
  )
}
