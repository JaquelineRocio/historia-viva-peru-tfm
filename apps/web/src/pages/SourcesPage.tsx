import { useEffect, useMemo, useState, type FormEvent } from 'react'
import {
  useClassifyResource,
  useCreatePdfResource,
  useCreateYoutubeResource,
  useProcessResource,
  useRequestPublication,
  useUnpublishResource,
  usePagedResourceSegments,
  useResources,
  useSetCorpusStatus,
  useUpdateResourceMetadata,
} from '../api/resources'
import { useTaxonomy } from '../api/labels'
import { useActiveProject } from '../projects/ProjectContext'
import { apiError } from '../lib/apiClient'
import { formatTime } from '../lib/format'
import { buildLabelMap } from '../lib/labels'
import type { HistoryResource, ProcessingStatus } from '../types'

const STATUS: Record<ProcessingStatus, { label: string; cls: string }> = {
  pending: { label: 'Pendiente', cls: 'bg-slate-100 text-slate-600' },
  processing: { label: 'Procesando…', cls: 'bg-amber-100 text-amber-700' },
  ready: { label: 'Lista', cls: 'bg-emerald-100 text-emerald-700' },
  needs_attention: { label: 'Requiere atención', cls: 'bg-orange-100 text-orange-700' },
  failed: { label: 'Falló', cls: 'bg-red-100 text-red-700' },
}

export function SourcesPage() {
  const { project } = useActiveProject()
  const resources = useResources(project?.id)
  const processResource = useProcessResource(project?.id)
  const taxonomy = useTaxonomy()
  const labelMap = useMemo(() => buildLabelMap(taxonomy.data), [taxonomy.data])
  const [selectedId, setSelectedId] = useState<string>()

  useEffect(() => {
    if (!selectedId && resources.data?.length) setSelectedId(resources.data[0].id)
  }, [resources.data, selectedId])

  const selected = resources.data?.find((item) => item.id === selectedId)
  return (
    <div>
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Biblioteca</p>
        <h1 className="text-2xl font-bold">Fuentes verificables</h1>
        <p className="mt-1 text-sm text-slate-500">Añade un video o PDF. Conservaremos el minuto o página de cada fragmento.</p>
      </div>
      <SourceCreator projectId={project?.id} onCreated={setSelectedId} />
      <div className="mt-6 grid gap-5 lg:grid-cols-[320px_1fr]">
        <section className="space-y-2">
          <h2 className="mb-3 text-sm font-semibold text-slate-500">Fuentes del proyecto</h2>
          {resources.data?.map((resource) => (
            <button
              key={resource.id}
              onClick={() => setSelectedId(resource.id)}
              className={`w-full rounded-xl border p-3 text-left transition ${selectedId === resource.id ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 bg-white hover:border-slate-300'}`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="line-clamp-2 text-sm font-semibold">{resource.title}</span>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${STATUS[resource.processingStatus].cls}`}>{STATUS[resource.processingStatus].label}</span>
              </div>
              <p className="mt-1 text-xs text-slate-400">{resource.type === 'youtube' ? 'Video de YouTube' : 'Documento PDF'}</p>
              <span className={`mt-2 inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold ${resource.corpusStatus === 'included' ? 'bg-violet-100 text-violet-700' : resource.corpusStatus === 'excluded' ? 'bg-slate-100 text-slate-500' : 'bg-amber-50 text-amber-700'}`}>{resource.corpusStatus === 'included' ? 'Incluida en corpus' : resource.corpusStatus === 'excluded' ? 'Excluida del corpus' : 'Candidata'}</span>
            </button>
          ))}
          {!resources.data?.length && <p className="rounded-xl border border-dashed border-slate-300 p-5 text-center text-sm text-slate-400">Todavía no hay fuentes.</p>}
        </section>
        <SourceDetail resource={selected} labelMap={labelMap} onProcess={() => selected && processResource.mutate(selected.id)} />
      </div>
    </div>
  )
}

function SourceCreator({ projectId, onCreated }: { projectId?: string; onCreated: (id: string) => void }) {
  const [kind, setKind] = useState<'youtube' | 'pdf'>('youtube')
  const [title, setTitle] = useState('')
  const [url, setUrl] = useState('')
  const [author, setAuthor] = useState('')
  const [file, setFile] = useState<File>()
  const [rights, setRights] = useState(false)
  const [error, setError] = useState('')
  const youtube = useCreateYoutubeResource(projectId)
  const pdf = useCreatePdfResource(projectId)
  const processResource = useProcessResource(projectId)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      let created
      if (kind === 'youtube') {
        created = await youtube.mutateAsync({ url, title, author: author || undefined, rightsConfirmed: rights })
      } else {
        if (!file) throw new Error('Selecciona un PDF')
        if (file.size > 50 * 1024 * 1024) throw new Error('El PDF supera el límite máximo de 50 MB')
        const form = new FormData()
        form.append('file', file)
        form.append('title', title)
        form.append('author', author)
        if (url) form.append('sourceUrl', url)
        form.append('rightsConfirmed', String(rights))
        created = await pdf.mutateAsync(form)
      }
      onCreated(created.id)
      await processResource.mutateAsync(created.id)
      setTitle('')
      setUrl('')
      setAuthor('')
      setFile(undefined)
      setRights(false)
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="mb-4 flex gap-2">
        <button type="button" onClick={() => setKind('youtube')} className={`rounded-xl px-4 py-2 text-sm font-semibold ${kind === 'youtube' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}>Video de YouTube</button>
        <button type="button" onClick={() => setKind('pdf')} className={`rounded-xl px-4 py-2 text-sm font-semibold ${kind === 'pdf' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}>Documento PDF</button>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Título de la fuente" className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm" />
        <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Autor o canal (opcional)" className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm" />
        {kind === 'youtube' ? (
          <input required type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://youtube.com/watch?v=…" className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm md:col-span-2" />
        ) : (
          <><input type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="URL de procedencia del PDF (recomendada)" className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm md:col-span-2" /><label className="cursor-pointer rounded-xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500 md:col-span-2">
            {file?.name ?? 'Seleccionar PDF con texto · máximo 50 MB'}
            <input
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => {
                const selected = e.target.files?.[0]
                if (selected && selected.size > 50 * 1024 * 1024) {
                  setFile(undefined)
                  setError('El PDF supera el límite máximo de 50 MB')
                  e.target.value = ''
                  return
                }
                setError('')
                setFile(selected)
              }}
            />
          </label></>
        )}
      </div>
      <label className="mt-3 flex items-start gap-2 text-xs text-slate-600">
        <input type="checkbox" checked={rights} onChange={(e) => setRights(e.target.checked)} className="mt-0.5" required />
        Confirmo que puedo usar esta fuente con fines educativos y que revisaré su licencia antes de publicarla.
      </label>
      {error && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <button disabled={!projectId || youtube.isPending || pdf.isPending || processResource.isPending} className="mt-4 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
        Añadir y procesar
      </button>
    </form>
  )
}

function SourceDetail({ resource, labelMap, onProcess }: { resource?: HistoryResource; labelMap: ReturnType<typeof buildLabelMap>; onProcess: () => void }) {
  const [segmentPage, setSegmentPage] = useState(1)
  const segments = usePagedResourceSegments(
    resource?.projectId,
    resource?.processingStatus === 'ready' ? resource.id : undefined,
    { page: segmentPage, limit: 20, sort: 'document' },
  )
  const publication = useRequestPublication(resource?.projectId)
  const unpublish = useUnpublishResource(resource?.projectId)
  const corpus = useSetCorpusStatus(resource?.projectId)
  const updateMetadata = useUpdateResourceMetadata(resource?.projectId)
  const classify = useClassifyResource(resource?.projectId, resource?.id)
  const [editing, setEditing] = useState(false)
  const [metadataTitle, setMetadataTitle] = useState('')
  const [metadataAuthor, setMetadataAuthor] = useState('')
  const [metadataUrl, setMetadataUrl] = useState('')
  const [metadataError, setMetadataError] = useState('')
  useEffect(() => {
    setEditing(false)
    setMetadataError('')
    setSegmentPage(1)
  }, [resource?.id])
  if (!resource) return <div className="grid min-h-72 place-items-center rounded-2xl border border-dashed border-slate-300 text-sm text-slate-400">Selecciona una fuente</div>

  function startEditing() {
    setMetadataTitle(resource!.title)
    setMetadataAuthor(resource!.author ?? '')
    setMetadataUrl(resource!.sourceUrl ?? '')
    setMetadataError('')
    setEditing(true)
  }

  async function saveMetadata(event: FormEvent) {
    event.preventDefault()
    setMetadataError('')
    try {
      await updateMetadata.mutateAsync({
        id: resource!.id,
        title: metadataTitle.trim(),
        author: metadataAuthor.trim() || undefined,
        sourceUrl: metadataUrl.trim() || undefined,
      })
      setEditing(false)
    } catch (err) {
      setMetadataError(apiError(err))
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold">{resource.title}</h2>
          <p className="text-sm text-slate-500">{resource.author || (resource.type === 'youtube' ? 'YouTube' : resource.originalFilename)}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={startEditing} className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-600">Editar datos</button>
          {(resource.processingStatus === 'pending' || resource.processingStatus === 'failed') && <button onClick={onProcess} className="rounded-xl bg-indigo-600 px-3 py-2 text-sm font-semibold text-white">{resource.processingStatus === 'failed' ? 'Reintentar' : 'Procesar'}</button>}
          {resource.processingStatus === 'ready' && resource.publicationStatus === 'private' && <button onClick={() => publication.mutate(resource.id)} className="rounded-xl border border-indigo-300 px-3 py-2 text-sm font-semibold text-indigo-700">Solicitar publicación</button>}
          {resource.publicationStatus === 'proposed' && <span className="rounded-xl bg-amber-100 px-3 py-2 text-xs font-semibold text-amber-700">En revisión</span>}
          {resource.publicationStatus === 'approved' && <span className="rounded-xl bg-emerald-100 px-3 py-2 text-xs font-semibold text-emerald-700">Pública</span>}
          {resource.publicationStatus === 'approved' && <button onClick={() => unpublish.mutate(resource.id)} className="rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-700">Retirar</button>}
        </div>
      </div>
      {editing && (
        <form onSubmit={saveMetadata} className="mt-4 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-2">
          <label className="text-xs font-semibold text-slate-600">Título
            <input required value={metadataTitle} onChange={(event) => setMetadataTitle(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal" />
          </label>
          <label className="text-xs font-semibold text-slate-600">Autor o canal
            <input value={metadataAuthor} onChange={(event) => setMetadataAuthor(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal" />
          </label>
          <label className="text-xs font-semibold text-slate-600 md:col-span-2">Procedencia
            <input type="url" value={metadataUrl} onChange={(event) => setMetadataUrl(event.target.value)} placeholder="https://…" className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-normal" />
          </label>
          {metadataError && <p className="text-sm text-red-700 md:col-span-2">{metadataError}</p>}
          <div className="flex gap-2 md:col-span-2">
            <button disabled={updateMetadata.isPending} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Guardar cambios</button>
            <button type="button" onClick={() => setEditing(false)} className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-600">Cancelar</button>
          </div>
        </form>
      )}
      {resource.processingStatus === 'ready' && <div className="mt-4 flex flex-wrap items-center gap-2 rounded-xl border border-violet-100 bg-violet-50 p-3">
        <div className="mr-auto"><p className="text-xs font-semibold text-violet-900">Selección del corpus gold</p><p className="text-[11px] text-violet-600">Incluye solamente fuentes que aporten diversidad al conjunto de 8–12 recursos.</p></div>
        <select id={`style-${resource.id}`} defaultValue={resource.sourceStyle ?? 'book'} className="rounded-lg border border-violet-200 px-2 py-1.5 text-xs">
          <option value="book">Libro</option><option value="academic">Académica</option><option value="documentary">Documental</option><option value="lecture">Clase</option><option value="archive">Archivo</option><option value="other">Otra</option>
        </select>
        {resource.corpusStatus !== 'included' && <button onClick={() => corpus.mutate({ id: resource.id, status: 'included', sourceStyle: (document.getElementById(`style-${resource.id}`) as HTMLSelectElement).value })} className="rounded-lg bg-violet-700 px-3 py-1.5 text-xs font-semibold text-white">Incluir en corpus</button>}
        {resource.corpusStatus === 'included' && <button onClick={() => corpus.mutate({ id: resource.id, status: 'excluded' })} className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600">Excluir del corpus</button>}
      </div>}
      {resource.processingStatus === 'processing' && <p className="mt-5 rounded-xl bg-amber-50 p-4 text-sm text-amber-700">Estamos extrayendo, limpiando y segmentando la fuente…</p>}
      {resource.processingError && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{resource.processingError}</p>}
      {resource.processingStatus === 'ready' && (
        <div className="mt-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold">Segmentos temáticos</h3>
              <p className="mt-0.5 text-xs text-slate-500">Cada segmento conserva el minuto original y muestra el subtema propuesto por BETO.</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400">{segments.data?.total ?? 0} encontrados</span>
              <button onClick={() => classify.mutate(resource.id)} disabled={classify.isPending} className="rounded-xl bg-violet-600 px-3 py-2 text-xs font-semibold text-white hover:bg-violet-700 disabled:opacity-50">
                {classify.isPending ? 'Analizando…' : 'Analizar subtemas'}
              </button>
            </div>
          </div>
          {classify.isSuccess && <p className="mb-3 rounded-lg bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">{classify.data.classified} segmentos analizados con BETO.</p>}
          {classify.isError && <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">{apiError(classify.error)}</p>}
          <ol className="max-h-[520px] space-y-2 overflow-y-auto pr-1">
            {segments.data?.items.map((segment) => {
              const labelKey = segment.reviewedLabelKey || segment.suggestedLabelKey
              const label = labelKey ? labelMap[labelKey] : undefined
              const people = segment.entities?.filter((entity) => entity.type === 'person' && !entity.outOfScope).slice(0, 4) ?? []
              const places = segment.entities?.filter((entity) => entity.type === 'place' && !entity.outOfScope).slice(0, 4) ?? []
              const years = segment.entities?.filter((entity) => ['date', 'period'].includes(entity.type) && !entity.outOfScope).slice(0, 5) ?? []
              const start = segment.startSec ?? 0
              const end = segment.endSec ?? start
              const youtubeAt = resource.type === 'youtube' && resource.sourceUrl
                ? `${resource.sourceUrl}${resource.sourceUrl.includes('?') ? '&' : '?'}t=${Math.floor(start)}s`
                : undefined
              return (
                <li key={segment.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    {youtubeAt ? (
                      <a href={youtubeAt} target="_blank" rel="noreferrer" className="rounded-lg bg-indigo-50 px-2 py-1 text-xs font-bold text-indigo-700 hover:bg-indigo-100">▶ {formatTime(start)}–{formatTime(end)}</a>
                    ) : (
                      <span className="rounded-lg bg-indigo-50 px-2 py-1 text-xs font-bold text-indigo-700">Página {segment.pageStart}{segment.pageEnd && segment.pageEnd !== segment.pageStart ? `–${segment.pageEnd}` : ''}</span>
                    )}
                    <span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${segment.reviewStatus === 'reviewed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
                      {segment.reviewStatus === 'reviewed' ? 'Confirmado por docente' : 'Pendiente de revisión'}
                    </span>
                  </div>
                  <h4 className="mt-3 text-base font-bold text-slate-900">{label?.name ?? 'Sin subtema asignado'}</h4>
                  <p className="mt-1 text-xs font-medium" style={{ color: label?.color ?? '#64748b' }}>
                    {label
                      ? `${segment.reviewedLabelKey ? 'Subtema confirmado' : 'Subtema sugerido por BETO'}${segment.suggestedConfidence != null && !segment.reviewedLabelKey ? ` · ${Math.round(segment.suggestedConfidence * 100)}% de confianza` : ''}`
                      : 'Pulsa “Analizar subtemas” para obtener la clasificación de BETO.'}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-700">{segment.text}</p>
                  {(people.length > 0 || places.length > 0 || years.length > 0) && (
                    <div className="mt-3 flex flex-wrap gap-1.5 border-t border-slate-100 pt-3">
                      {people.map((entity, index) => <span key={`person-${index}`} className="rounded-full bg-violet-50 px-2 py-1 text-[11px] font-medium text-violet-700">Personaje · {entity.text}</span>)}
                      {places.map((entity, index) => <span key={`place-${index}`} className="rounded-full bg-sky-50 px-2 py-1 text-[11px] font-medium text-sky-700">Lugar · {entity.text}</span>)}
                      {years.map((entity, index) => <span key={`year-${index}`} className="rounded-full bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-700">Año · {entity.text}</span>)}
                    </div>
                  )}
                </li>
              )
            })}
          </ol>
          {(segments.data?.totalPages ?? 0) > 1 && (
            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3">
              <button disabled={segmentPage === 1} onClick={() => setSegmentPage((page) => Math.max(1, page - 1))} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 disabled:opacity-40">Anterior</button>
              <span className="text-xs text-slate-500">Página {segments.data?.page} de {segments.data?.totalPages}</span>
              <button disabled={segmentPage === segments.data?.totalPages} onClick={() => setSegmentPage((page) => page + 1)} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 disabled:opacity-40">Siguiente</button>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
