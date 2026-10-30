import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCreateYoutubeResource, useProcessResource, useResources } from '../api/resources'
import { useActiveProject } from '../projects/ProjectContext'
import { apiError } from '../lib/apiClient'
import { youtubeId } from '../lib/format'
import type { ProcessingStatus } from '../types'

const STATUS: Record<ProcessingStatus, { label: string; cls: string }> = {
  pending: { label: 'En espera', cls: 'bg-slate-100 text-slate-600' },
  processing: { label: 'Indexando…', cls: 'bg-amber-100 text-amber-800' },
  ready: { label: 'Listo', cls: 'bg-emerald-100 text-emerald-800' },
  needs_attention: { label: 'Revisar', cls: 'bg-orange-100 text-orange-800' },
  failed: { label: 'No se pudo indexar', cls: 'bg-red-100 text-red-700' },
}

export function VideosPage() {
  const { project } = useActiveProject()
  const resources = useResources(project?.id)
  const videos = (resources.data ?? []).filter((item) => item.type === 'youtube')

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Encuentra el minuto exacto de cada subtema</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          Pega un video de YouTube sobre la Independencia del Perú. La aplicación lo divide en fragmentos, descarta lo que no trata el tema
          y te propone los subtemas de cada fragmento para que los confirmes con un clic.
        </p>
        <AddVideo projectId={project?.id} />
      </section>

      <section>
        <h2 className="text-lg font-bold">Mis videos</h2>
        <ul className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {videos.map((video) => {
            const id = video.sourceUrl ? youtubeId(video.sourceUrl) : ''
            return (
              <li key={video.id}>
                <Link to={`/videos/${video.id}`} className="block overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-300 hover:shadow-md">
                  {id ? <img src={`https://i.ytimg.com/vi/${id}/mqdefault.jpg`} alt="" loading="lazy" className="aspect-video w-full bg-slate-200 object-cover" /> : <div className="aspect-video bg-slate-200" />}
                  <div className="p-4">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS[video.processingStatus].cls}`}>{STATUS[video.processingStatus].label}</span>
                    <p className="mt-2 line-clamp-2 font-semibold leading-snug text-slate-900">{video.title}</p>
                    {video.author && <p className="mt-1 truncate text-xs text-slate-500">{video.author}</p>}
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
        {resources.isLoading && <p className="mt-3 text-sm text-slate-500">Cargando tus videos…</p>}
        {resources.isSuccess && !videos.length && <p className="mt-3 rounded-2xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">Todavía no has añadido videos. Pega el enlace de uno arriba para empezar.</p>}
      </section>
    </div>
  )
}

function AddVideo({ projectId }: { projectId?: string }) {
  const navigate = useNavigate()
  const create = useCreateYoutubeResource(projectId)
  const processVideo = useProcessResource(projectId)
  const [url, setUrl] = useState('')
  const [rights, setRights] = useState(false)
  const [error, setError] = useState('')
  const busy = create.isPending || processVideo.isPending

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      const created = await create.mutateAsync({ url: url.trim(), rightsConfirmed: rights })
      await processVideo.mutateAsync(created.id)
      navigate(`/videos/${created.id}`)
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <form onSubmit={submit} className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <label className="block text-sm font-semibold text-slate-800" htmlFor="video-url">Enlace del video</label>
      <div className="mt-2 flex flex-col gap-3 sm:flex-row">
        <input id="video-url" required type="url" inputMode="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://www.youtube.com/watch?v=…" className="min-h-11 min-w-0 flex-1 rounded-xl border border-slate-300 px-3 text-sm" />
        <button disabled={!projectId || busy} className="min-h-11 rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
          {busy ? 'Enviando…' : 'Indexar video'}
        </button>
      </div>
      <label className="mt-3 flex items-start gap-2 text-xs leading-5 text-slate-600">
        <input required type="checkbox" checked={rights} onChange={(event) => setRights(event.target.checked)} className="mt-0.5 h-4 w-4 shrink-0 accent-indigo-600" />
        Usaré este video con fines educativos.
      </label>
      {error && <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
    </form>
  )
}
