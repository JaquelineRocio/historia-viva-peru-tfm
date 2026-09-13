import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import YouTube, { type YouTubePlayer } from 'react-youtube'
import { Link } from 'react-router-dom'
import { publicExploreResource, publicExploreResources, publicProcessingStatus, publicProcessYoutube } from '../api/resources'
import { apiError } from '../lib/apiClient'
import { formatTime } from '../lib/format'
import type { PublicExploreResponse, PublicProcessingResponse, PublicProcessingStage, PublicVideoResource, PublicVideoSegment } from '../types'

const STAGES: Array<{ key: PublicProcessingStage; label: string }> = [
  { key: 'validating_video', label: 'Validando el video' },
  { key: 'preparing_source', label: 'Preparando la fuente' },
  { key: 'generating_transcription', label: 'Generando la transcripción' },
  { key: 'analyzing_subtopics', label: 'Analizando los subtemas' },
  { key: 'ready', label: 'Resultado listo' },
]

const PROCESS = [
  'Se obtiene el contenido del video.',
  'Se genera la transcripción.',
  'La transcripción se divide en fragmentos.',
  'El modelo BETO identifica el subtema histórico de cada fragmento.',
  'Los resultados se organizan por minuto.',
]

function youtubeId(url?: string) {
  if (!url) return ''
  try {
    const parsed = new URL(url)
    return parsed.hostname === 'youtu.be' ? parsed.pathname.split('/')[1] : parsed.searchParams.get('v') || ''
  } catch {
    return ''
  }
}

function youtubeAt(url: string, seconds: number) {
  const id = youtubeId(url)
  return id ? `https://www.youtube.com/watch?v=${id}&t=${Math.floor(seconds)}s` : url
}

export function PublicExplorePage() {
  const [catalog, setCatalog] = useState<PublicExploreResponse>()
  const [selectedId, setSelectedId] = useState('')
  const [video, setVideo] = useState<PublicVideoResource>()
  const [processedVideo, setProcessedVideo] = useState<PublicVideoResource>()
  const [selectedSegmentId, setSelectedSegmentId] = useState('')
  const [loadingExample, setLoadingExample] = useState(true)
  const [catalogError, setCatalogError] = useState('')

  useEffect(() => {
    publicExploreResources()
      .then((data) => {
        setCatalog(data)
        if (data.items.length) setSelectedId(data.items[0].id)
        else setLoadingExample(false)
      })
      .catch((error) => {
        setCatalogError(apiError(error))
        setLoadingExample(false)
      })
  }, [])

  useEffect(() => {
    if (!selectedId) return
    setLoadingExample(true)
    setCatalogError('')
    setVideo(undefined)
    publicExploreResource(selectedId)
      .then((item) => {
        setVideo(item)
        setSelectedSegmentId(item.segments?.[0]?.id || '')
      })
      .catch((error) => setCatalogError(apiError(error)))
      .finally(() => setLoadingExample(false))
  }, [selectedId])

  const displayedVideo = processedVideo ?? video

  const showProcessedVideo = useCallback((resource: PublicVideoResource) => {
    setProcessedVideo(resource)
    setSelectedSegmentId(resource.segments?.[0]?.id || '')
    window.requestAnimationFrame(() => document.getElementById('explore-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
  }, [])

  function selectExample(id: string) {
    if (id === '__processed__') return
    setProcessedVideo(undefined)
    setSelectedId(id)
  }

  return (
    <div className="min-h-screen overflow-x-hidden bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/explorar" className="flex min-w-0 items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-600 font-serif text-lg font-bold text-white">H</span>
            <span className="truncate text-sm font-bold text-slate-900 sm:text-base">Historia Viva <span className="text-indigo-600">Perú</span></span>
          </Link>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <span className="hidden rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 sm:inline-flex">Acceso público</span>
            <Link to="/login" className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100"><span className="sm:hidden">Docentes</span><span className="hidden sm:inline">Espacio docente</span></Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <section className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Demostración pública</p>
          <h1 className="mt-1 max-w-4xl text-2xl font-bold tracking-tight sm:text-3xl">De la fuente histórica al segmento temático</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">Agrega una fuente audiovisual y observa cómo cada fragmento conserva su minuto, su transcripción y el subtema histórico identificado.</p>
          <ol className="mt-5 grid max-w-3xl gap-2 sm:grid-cols-3" aria-label="Recorrido de la demostración">
            {['1. Fuente de YouTube', '2. Video y transcripción', '3. Segmentos temáticos'].map((item, index) => (
              <li key={item} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-xs font-semibold text-slate-600 shadow-sm">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-indigo-600 text-[11px] font-bold text-white">{index + 1}</span>
                <span>{item.replace(/^\d\. /, '')}</span>
              </li>
            ))}
          </ol>
        </section>

        <PublicProcessSection config={catalog?.processing} onReady={showProcessedVideo} />

        <section className="mt-8" aria-labelledby="explore-title">
          <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Resultado del procesamiento</p>
              <h2 id="explore-title" className="mt-1 text-xl font-bold">Video, transcripción y subtemas</h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">Selecciona un segmento: el video avanzará al minuto exacto y mostrará debajo el fragmento de transcripción relacionado.</p>
            </div>
            {(processedVideo || (catalog?.items.length || 0) > 1) && (
              <label className="min-w-0 text-sm font-semibold text-slate-700">Fuente que estás explorando
                <select value={processedVideo ? '__processed__' : selectedId} onChange={(event) => selectExample(event.target.value)} className="mt-2 block w-full max-w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal md:w-96">
                  {processedVideo && <option value="__processed__">Tu video recién procesado</option>}
                  {catalog?.items.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
                </select>
              </label>
            )}
          </div>

          {loadingExample && !processedVideo && <ExplorerLoading />}
          {catalogError && !processedVideo && <ExplorerError message={catalogError} />}
          {!loadingExample && !catalogError && !displayedVideo && <ExplorerEmpty />}
          {displayedVideo && (!loadingExample || processedVideo) && <VideoExplorer video={displayedVideo} selectedSegmentId={selectedSegmentId} onSelect={setSelectedSegmentId} isNewResult={!!processedVideo} />}
        </section>
      </main>

      <footer className="mt-8 border-t border-slate-200 bg-white px-4 py-6 text-center text-xs text-slate-500">Historia Viva Perú · Proyecto académico sobre trazabilidad de fuentes históricas</footer>
    </div>
  )
}

function PublicProcessSection({ config, onReady }: { config?: PublicExploreResponse['processing']; onReady: (resource: PublicVideoResource) => void }) {
  const [url, setUrl] = useState('')
  const [rights, setRights] = useState(false)
  const [status, setStatus] = useState<PublicProcessingResponse>()
  const [stage, setStage] = useState<PublicProcessingStage>()
  const [error, setError] = useState('')

  useEffect(() => {
    if (!status?.requestId || stage === 'ready' || stage === 'failed') return
    const timer = window.setInterval(() => {
      publicProcessingStatus(status.requestId)
        .then((next) => {
          setStatus(next)
          setStage(next.stage)
          setError(next.stage === 'failed' ? next.error || 'No se pudo procesar el video.' : '')
          if (next.stage === 'ready') onReady(next.resource)
        })
        .catch((pollError) => setError(apiError(pollError)))
    }, 2500)
    return () => window.clearInterval(timer)
  }, [onReady, stage, status?.requestId])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setStatus(undefined)
    setStage('validating_video')
    try {
      const response = await publicProcessYoutube({ url: url.trim(), rightsConfirmed: true })
      setStatus(response)
      setStage(response.stage)
      if (response.stage === 'ready') onReady(response.resource)
    } catch (submitError) {
      setStage('failed')
      setError(apiError(submitError))
    }
  }

  const busy = !!stage && stage !== 'ready' && stage !== 'failed'
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" aria-labelledby="process-title">
        <div className="grid min-w-0 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="min-w-0">
            <div className="p-5 sm:p-6 lg:p-7">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Paso 1 · Agrega una fuente</p>
            <h2 id="process-title" className="mt-1 text-xl font-bold">Procesa un video de YouTube</h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">Pega una URL educativa de hasta {Math.floor((config?.maxDurationSec || 3600) / 60)} minutos. El sistema obtiene el título y el canal directamente de YouTube.</p>
            <ol className="mt-5 space-y-2.5" aria-label="Etapas del procesamiento">
              {PROCESS.map((item, index) => <li key={item} className="flex gap-3 text-sm leading-5 text-slate-600"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-indigo-50 text-xs font-bold text-indigo-700">{index + 1}</span><span>{item}</span></li>)}
            </ol>
            </div>
          </div>

          <div className="min-w-0 border-t border-slate-200 bg-slate-50 p-5 sm:p-6 lg:border-l lg:border-t-0 lg:p-7">
            {config && !config.enabled && <div className="mb-5 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">Procesamiento en modo supervisado. El formulario permanece visible, pero el alta pública está desactivada temporalmente.</div>}
            <form onSubmit={submit} className="space-y-4">
              <label className="block text-sm font-semibold text-slate-800">Fuente del video
                <span className="mt-1 block text-xs font-normal text-slate-500">URL completa de YouTube</span>
                <input required type="url" inputMode="url" autoComplete="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://www.youtube.com/watch?v=…" className="mt-2 min-w-0 w-full max-w-full rounded-xl border border-slate-300 px-3 py-3 text-sm" />
              </label>
              <label className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-600"><input required type="checkbox" checked={rights} onChange={(event) => setRights(event.target.checked)} className="mt-0.5 h-4 w-4 shrink-0 accent-indigo-600" />Confirmo que esta fuente se utilizará con fines educativos.</label>
              <button disabled={busy || config?.enabled === false} className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto">{busy ? 'Procesando el video…' : 'Agregar y procesar'}</button>
            </form>

            {stage && <ProcessingProgress stage={stage} error={error} />}
            {stage === 'ready' && status ? <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5"><p className="font-bold text-emerald-900">Resultado listo para explorar</p><p className="mt-1 text-sm leading-6 text-emerald-800">{status.resource.title} · {status.resource.segments?.length || 0} segmentos obtenidos. El resultado ya aparece en la sección inferior.</p></div> : null}
            <p className="mt-4 text-xs leading-5 text-slate-500">La fuente se valida antes de iniciar. Máximo {Math.floor((config?.maxDurationSec || 3600) / 60)} min, duplicados bloqueados y hasta {config?.maxPerSession || 2} intentos por cuenta cada {config?.windowHours || 24} h. El video agregado permanece privado.</p>
          </div>
        </div>
    </section>
  )
}

function ProcessingProgress({ stage, error }: { stage: PublicProcessingStage; error: string }) {
  const current = STAGES.findIndex((item) => item.key === stage)
  return <div className="mt-6" aria-live="polite">
    <div className="mb-3 flex items-center justify-between gap-3 text-xs">
      <span className="font-semibold text-slate-700">Progreso del procesamiento</span>
      {stage !== 'failed' && <span className="text-slate-500">{Math.max(1, current + 1)} de {STAGES.length}</span>}
    </div>
    <ol className="grid gap-2 sm:grid-cols-5" aria-label="Progreso del procesamiento">
      {STAGES.map((item, index) => {
        const complete = stage !== 'failed' && index < current
        const active = index === current && stage !== 'failed'
        const ready = active && item.key === 'ready'
        return <li key={item.key} aria-current={active ? 'step' : undefined} className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 text-[11px] font-semibold sm:block ${ready ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : active ? 'border-indigo-400 bg-indigo-100 text-indigo-800 ring-2 ring-indigo-100' : complete ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : 'border-slate-200 bg-white text-slate-400'}`}><span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-current/10 text-xs sm:mb-1">{complete || ready ? '✓' : active ? '●' : '○'}</span>{item.label}</li>
      })}
    </ol>
    {stage === 'failed' && <p role="alert" className="mt-3 rounded-xl bg-red-50 p-3 text-sm text-red-800"><strong>Error de procesamiento.</strong> {error}</p>}
    {error && stage !== 'failed' && <p role="status" className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">No pudimos actualizar el estado por un momento. Seguiremos intentándolo automáticamente.</p>}
    {stage !== 'failed' && stage !== 'ready' && <p className="mt-3 text-xs text-slate-500">Puedes seguir explorando el ejemplo terminado mientras esperas.</p>}
  </div>
}

function ExplorerLoading() {
  return <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white" role="status" aria-label="Cargando video procesado">
    <div className="animate-pulse p-5 sm:p-6">
      <div className="h-3 w-28 rounded bg-slate-200" />
      <div className="mt-3 h-6 max-w-xl rounded bg-slate-200" />
      <div className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
        <div className="aspect-video rounded-2xl bg-slate-200" />
        <div className="space-y-3"><div className="h-28 rounded-xl bg-slate-100" /><div className="h-28 rounded-xl bg-slate-100" /></div>
      </div>
    </div>
    <p className="border-t border-slate-100 px-5 py-3 text-center text-xs text-slate-500">Cargando la fuente, la transcripción y sus segmentos…</p>
  </div>
}

function ExplorerError({ message }: { message: string }) {
  return <div role="alert" className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-5 sm:flex sm:items-center sm:justify-between sm:gap-4">
    <div><p className="font-semibold text-red-900">No pudimos cargar el video de demostración</p><p className="mt-1 text-sm leading-6 text-red-700">{message}</p></div>
    <button type="button" onClick={() => window.location.reload()} className="mt-4 min-h-10 rounded-xl border border-red-300 bg-white px-4 py-2 text-sm font-semibold text-red-700 transition hover:bg-red-100 sm:mt-0">Volver a intentar</button>
  </div>
}

function ExplorerEmpty() {
  return <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center sm:p-10">
    <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-indigo-50 text-xl text-indigo-600" aria-hidden="true">▶</span>
    <h3 className="mt-4 font-semibold text-slate-800">Aún no hay un ejemplo público disponible</h3>
    <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">Puedes agregar una fuente arriba. Cuando termine el procesamiento, el video, la transcripción y sus segmentos aparecerán aquí automáticamente.</p>
  </div>
}

function VideoExplorer({ video, selectedSegmentId, onSelect, isNewResult }: { video: PublicVideoResource; selectedSegmentId: string; onSelect: (id: string) => void; isNewResult: boolean }) {
  const player = useRef<YouTubePlayer | null>(null)
  const [embedError, setEmbedError] = useState(false)
  const segments = video.segments || []
  const selected = segments.find((segment) => segment.id === selectedSegmentId) || segments[0]
  const selectedIndex = selected ? segments.findIndex((segment) => segment.id === selected.id) : -1

  useEffect(() => setEmbedError(false), [video.id])

  function select(segment: PublicVideoSegment) {
    onSelect(segment.id)
    player.current?.seekTo(segment.startSec, true)
    player.current?.playVideo?.()
  }

  function selectByIndex(index: number) {
    const segment = segments[index]
    if (segment) select(segment)
  }

  return <div className="mt-6">
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-indigo-700">{isNewResult ? 'Resultado de tu prueba' : 'Fuente audiovisual'}</span><span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">Procesamiento completado</span></div>
          <h3 className="mt-3 text-xl font-bold tracking-tight text-slate-900">{video.title}</h3>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-500"><p><strong className="font-semibold text-slate-700">Canal:</strong> {video.author || 'No indicado'}</p><p><strong className="font-semibold text-slate-700">Fuente:</strong> {video.provenance}</p>{video.durationSec != null && <p><strong className="font-semibold text-slate-700">Duración:</strong> {formatTime(video.durationSec)}</p>}<p><strong className="font-semibold text-slate-700">Segmentos:</strong> {segments.length}</p></div>
          <p className="mt-2 truncate text-xs text-slate-400" title={video.sourceUrl}>{video.sourceUrl}</p>
        </div>
        <a href={video.sourceUrl} target="_blank" rel="noreferrer" className="inline-flex min-h-10 w-full items-center justify-center rounded-xl border border-indigo-300 px-4 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-50 sm:w-auto">Abrir contenido original ↗</a>
      </div>
    </div>

    <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)] lg:items-start">
      <div className="min-w-0 space-y-4 lg:sticky lg:top-20">
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-lg shadow-slate-900/10">
          {!embedError && youtubeId(video.sourceUrl) ? <div className="aspect-video"><YouTube videoId={youtubeId(video.sourceUrl)} className="h-full w-full" iframeClassName="h-full w-full" opts={{ width: '100%', height: '100%', playerVars: { rel: 0, modestbranding: 1 } }} onReady={(event) => { player.current = event.target }} onError={() => setEmbedError(true)} /></div> : <div className="grid aspect-video place-items-center p-8 text-center text-white"><div><p className="font-bold">YouTube no permite reproducir este video aquí.</p><a href={youtubeAt(video.sourceUrl, selected?.startSec || 0)} target="_blank" rel="noreferrer" className="mt-4 inline-flex rounded-xl bg-white px-4 py-3 text-sm font-bold text-slate-900">Abrir en YouTube desde {formatTime(selected?.startSec || 0)} ↗</a></div></div>}
        </div>
        {selected ? <article className="overflow-hidden rounded-2xl border border-indigo-300 bg-white shadow-sm" aria-live="polite">
          <div className="border-b border-indigo-100 bg-indigo-50 px-5 py-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2"><span className="rounded-lg bg-indigo-600 px-2.5 py-1 text-xs font-bold text-white">{formatTime(selected.startSec)}–{formatTime(selected.endSec)}</span><span className="rounded-full border border-violet-200 bg-violet-100 px-2.5 py-1 text-xs font-semibold text-violet-800">{selected.labelName}</span></div>
              <span className="text-xs font-semibold text-indigo-700">Segmento {selectedIndex + 1} de {segments.length}</span>
            </div>
            <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-indigo-700">Subtema seleccionado</p>
          </div>
          <div className="p-5">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Transcripción vinculada a este minuto</h4>
            <p className="mt-3 text-[15px] leading-7 text-slate-700">{selected.text}</p>
            <div className="mt-5 flex items-center justify-between gap-3 border-t border-slate-100 pt-4">
              <button type="button" disabled={selectedIndex <= 0} onClick={() => selectByIndex(selectedIndex - 1)} className="min-h-10 rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40">← Anterior</button>
              <button type="button" disabled={selectedIndex < 0 || selectedIndex >= segments.length - 1} onClick={() => selectByIndex(selectedIndex + 1)} className="min-h-10 rounded-xl border border-indigo-300 px-3 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-40">Siguiente →</button>
            </div>
          </div>
        </article> : <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-center text-sm text-slate-500">Este video todavía no tiene segmentos disponibles.</div>}
      </div>

      <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" aria-label="Segmentos temáticos">
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-4 sm:px-5"><div className="flex items-center justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Mapa del contenido</p><h3 className="mt-1 font-bold text-slate-900">Segmentos temáticos</h3></div><span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-slate-200">{segments.length}</span></div><p className="mt-2 text-xs leading-5 text-slate-500">Cada tarjeta enlaza un subtema con su minuto y transcripción.</p></div>
        <div className="max-h-[70vh] space-y-3 overflow-y-auto p-4 sm:p-5 lg:max-h-[760px]">
          {segments.map((segment) => {
            const active = segment.id === selected?.id
            return <button key={segment.id} type="button" aria-pressed={active} aria-current={active ? 'true' : undefined} onClick={() => select(segment)} className={`relative w-full overflow-hidden rounded-xl border p-4 text-left transition focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-100 ${active ? 'border-indigo-500 bg-indigo-50 shadow-md shadow-indigo-100' : 'border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50'}`}>{active && <span className="absolute inset-y-0 left-0 w-1 bg-indigo-600" aria-hidden="true" />}<div className="flex flex-wrap items-center justify-between gap-2"><span className={`rounded-lg px-2.5 py-1 text-xs font-bold ${active ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}>{formatTime(segment.startSec)}–{formatTime(segment.endSec)}</span>{active && <span className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-700"><span aria-hidden="true">●</span> Seleccionado</span>}</div><p className={`mt-3 text-sm font-bold ${active ? 'text-indigo-950' : 'text-slate-900'}`}>{segment.labelName}</p><p className="mt-1 line-clamp-3 text-sm leading-5 text-slate-500">{segment.text}</p></button>
          })}
          {!segments.length && <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center"><p className="text-sm font-semibold text-slate-700">Sin segmentos para mostrar</p><p className="mt-1 text-xs leading-5 text-slate-500">La fuente no devolvió fragmentos temáticos disponibles.</p></div>}
        </div>
      </section>
    </div>
  </div>
}
