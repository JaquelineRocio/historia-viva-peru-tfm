import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
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
    publicExploreResource(selectedId)
      .then((item) => {
        setVideo(item)
        setSelectedSegmentId(item.segments?.[0]?.id || '')
      })
      .catch((error) => setCatalogError(apiError(error)))
      .finally(() => setLoadingExample(false))
  }, [selectedId])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/explorar" className="flex shrink-0 items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-600 font-serif text-lg font-bold text-white">H</span>
            <span className="font-bold text-slate-900">Historia Viva <span className="text-indigo-600">Perú</span></span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="hidden rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 sm:inline-flex">Acceso público</span>
            <Link to="/login" className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100">Espacio docente</Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <section className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Demostración pública</p>
          <h1 className="mt-1 max-w-4xl text-2xl font-bold">Explora videos sobre la Independencia del Perú por subtemas</h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">Comprueba cómo el sistema conecta cada fragmento con su minuto, transcripción y subtema histórico identificado.</p>
        </section>

        <PublicProcessSection config={catalog?.processing} />

        <section className="mt-8" aria-labelledby="explore-title">
          <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Ejemplo procesado</p>
              <h2 id="explore-title" className="mt-1 text-xl font-bold">Explorar un video por segmentos</h2>
              <p className="mt-1 max-w-3xl text-sm text-slate-500">Selecciona un segmento para reproducir el video desde el minuto exacto.</p>
            </div>
            {(catalog?.items.length || 0) > 1 && (
              <label className="text-sm font-semibold text-slate-700">Video de ejemplo
                <select value={selectedId} onChange={(event) => setSelectedId(event.target.value)} className="mt-2 block w-full max-w-md rounded-xl border border-slate-300 px-3 py-2.5 font-normal md:w-96">
                  {catalog?.items.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
                </select>
              </label>
            )}
          </div>

          {loadingExample && <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">Cargando el ejemplo procesado…</div>}
          {catalogError && <div role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{catalogError}</div>}
          {!loadingExample && !catalogError && !video && <div className="mt-6 rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">No hay videos aprobados y procesados para mostrar.</div>}
          {video && !loadingExample && <VideoExplorer video={video} selectedSegmentId={selectedSegmentId} onSelect={setSelectedSegmentId} />}
        </section>
      </main>

      <footer className="mt-8 border-t border-slate-200 bg-white px-4 py-6 text-center text-xs text-slate-500">Historia Viva Perú · Proyecto académico sobre trazabilidad de fuentes históricas</footer>
    </div>
  )
}

function PublicProcessSection({ config }: { config?: PublicExploreResponse['processing'] }) {
  const [url, setUrl] = useState('')
  const [rights, setRights] = useState(false)
  const [status, setStatus] = useState<PublicProcessingResponse>()
  const [stage, setStage] = useState<PublicProcessingStage>()
  const [error, setError] = useState('')
  const sessionId = useMemo(() => crypto.randomUUID(), [])

  useEffect(() => {
    if (!status?.requestId || stage === 'ready' || stage === 'failed') return
    const timer = window.setInterval(() => {
      publicProcessingStatus(status.requestId, sessionId)
        .then((next) => {
          setStatus(next)
          setStage(next.stage)
          if (next.stage === 'failed') setError(next.error || 'No se pudo procesar el video.')
        })
        .catch((pollError) => setError(apiError(pollError)))
    }, 2500)
    return () => window.clearInterval(timer)
  }, [sessionId, stage, status?.requestId])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setStatus(undefined)
    setStage('validating_video')
    try {
      const response = await publicProcessYoutube({ url: url.trim(), rightsConfirmed: true }, sessionId)
      setStatus(response)
      setStage(response.stage)
    } catch (submitError) {
      setStage('failed')
      setError(apiError(submitError))
    }
  }

  const busy = !!stage && stage !== 'ready' && stage !== 'failed'
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5" aria-labelledby="process-title">
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Prueba controlada</p>
            <h2 id="process-title" className="mt-1 text-lg font-bold">Agregar y procesar un video</h2>
            <p className="mt-1 max-w-xl text-sm text-slate-500">Usa un video educativo de YouTube de hasta {Math.floor((config?.maxDurationSec || 7200) / 60)} minutos. El título y el canal se obtienen automáticamente.</p>
            <ol className="mt-5 space-y-2.5">
              {PROCESS.map((item, index) => <li key={item} className="flex gap-3 text-sm leading-5 text-slate-600"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-indigo-50 text-xs font-bold text-indigo-700">{index + 1}</span><span>{item}</span></li>)}
            </ol>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
            {config && !config.enabled && <div className="mb-5 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">Procesamiento en modo supervisado. El formulario permanece visible, pero el alta pública está desactivada temporalmente.</div>}
            <form onSubmit={submit} className="space-y-4">
              <label className="block text-sm font-semibold">URL del video de YouTube
                <input required type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://www.youtube.com/watch?v=…" className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm" />
              </label>
              <label className="flex items-start gap-2 text-xs text-slate-600"><input required type="checkbox" checked={rights} onChange={(event) => setRights(event.target.checked)} className="mt-0.5" />Confirmo que la fuente se utilizará con fines educativos.</label>
              <button disabled={busy || config?.enabled === false} className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">{busy ? 'Procesando…' : 'Agregar y procesar'}</button>
            </form>

            {stage && <ProcessingProgress stage={stage} error={error} />}
            {stage === 'ready' && status?.resource.segments?.length ? <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5"><p className="font-bold text-emerald-900">Resultado real listo</p><p className="mt-1 text-sm text-emerald-800">{status.resource.title} · {status.resource.segments.length} segmentos obtenidos.</p></div> : null}
            <p className="mt-4 text-xs leading-5 text-slate-500">Protección activa: URL exclusiva de YouTube, máximo {Math.floor((config?.maxDurationSec || 7200) / 60)} min, duplicados bloqueados y {config?.maxPerSession || 1} solicitud por sesión cada {config?.windowHours || 24} h. La fuente nueva permanece privada.</p>
          </div>
        </div>
    </section>
  )
}

function ProcessingProgress({ stage, error }: { stage: PublicProcessingStage; error: string }) {
  const current = STAGES.findIndex((item) => item.key === stage)
  return <div className="mt-6" aria-live="polite">
    <ol className="grid gap-2 sm:grid-cols-5">
      {STAGES.map((item, index) => {
        const complete = stage !== 'failed' && index <= current
        const active = item.key === stage
        return <li key={item.key} className={`rounded-lg border px-2 py-2.5 text-[11px] font-semibold ${complete ? 'border-indigo-200 bg-indigo-50 text-indigo-700' : active ? 'border-red-200 bg-red-50 text-red-700' : 'border-slate-200 bg-white text-slate-400'}`}><span className="mb-1 block text-sm">{complete ? '✓' : active ? '!' : '○'}</span>{item.label}</li>
      })}
    </ol>
    {stage === 'failed' && <p role="alert" className="mt-3 rounded-xl bg-red-50 p-3 text-sm text-red-800"><strong>Error de procesamiento.</strong> {error}</p>}
    {stage !== 'failed' && stage !== 'ready' && <p className="mt-3 text-xs text-slate-500">Puedes seguir explorando el ejemplo terminado mientras esperas.</p>}
  </div>
}

function VideoExplorer({ video, selectedSegmentId, onSelect }: { video: PublicVideoResource; selectedSegmentId: string; onSelect: (id: string) => void }) {
  const player = useRef<YouTubePlayer | null>(null)
  const [embedError, setEmbedError] = useState(false)
  const segments = video.segments || []
  const selected = segments.find((segment) => segment.id === selectedSegmentId) || segments[0]

  useEffect(() => setEmbedError(false), [video.id])

  function select(segment: PublicVideoSegment) {
    onSelect(segment.id)
    player.current?.seekTo(segment.startSec, true)
    player.current?.playVideo?.()
  }

  return <div className="mt-6">
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div><h3 className="text-lg font-bold">{video.title}</h3><p className="mt-1 text-sm text-slate-500"><strong className="font-semibold text-slate-600">Canal o autor:</strong> {video.author || 'No indicado'}</p><p className="mt-1 text-sm text-slate-500"><strong className="font-semibold text-slate-600">Procedencia:</strong> {video.provenance}</p></div>
        <a href={video.sourceUrl} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center justify-center rounded-xl border border-indigo-300 px-4 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-50">Abrir contenido original ↗</a>
      </div>
    </div>

    <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)] lg:items-start">
      <div className="min-w-0 space-y-4 lg:sticky lg:top-5">
        <div className="overflow-hidden rounded-2xl bg-slate-950 shadow-sm">
          {!embedError && youtubeId(video.sourceUrl) ? <div className="aspect-video"><YouTube videoId={youtubeId(video.sourceUrl)} className="h-full w-full" iframeClassName="h-full w-full" opts={{ width: '100%', height: '100%', playerVars: { rel: 0, modestbranding: 1 } }} onReady={(event) => { player.current = event.target }} onError={() => setEmbedError(true)} /></div> : <div className="grid aspect-video place-items-center p-8 text-center text-white"><div><p className="font-bold">YouTube no permite reproducir este video aquí.</p><a href={youtubeAt(video.sourceUrl, selected?.startSec || 0)} target="_blank" rel="noreferrer" className="mt-4 inline-flex rounded-xl bg-white px-4 py-3 text-sm font-bold text-slate-900">Abrir en YouTube desde {formatTime(selected?.startSec || 0)} ↗</a></div></div>}
        </div>
        {selected && <article className="rounded-2xl border border-indigo-200 bg-indigo-50 p-5" aria-live="polite"><div className="flex flex-wrap items-center gap-2"><span className="rounded-lg bg-indigo-600 px-2.5 py-1 text-xs font-bold text-white">{formatTime(selected.startSec)}–{formatTime(selected.endSec)}</span><span className="rounded-full bg-violet-100 px-2.5 py-1 text-xs font-semibold text-violet-700">Subtema: {selected.labelName}</span></div><h4 className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">Fragmento de la transcripción</h4><p className="mt-2 text-sm leading-6 text-slate-700">{selected.text}</p></article>}
      </div>

      <section className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5" aria-label="Segmentos temáticos">
        <div className="border-b border-slate-100 pb-4"><h3 className="font-semibold">Segmentos temáticos</h3><p className="mt-1 text-xs text-slate-500">{segments.length} fragmentos · selecciona uno para ir a ese minuto</p></div>
        <div className="mt-4 space-y-3 lg:max-h-[720px] lg:overflow-y-auto lg:pr-1">
          {segments.map((segment) => {
            const active = segment.id === selected?.id
            return <button key={segment.id} type="button" aria-pressed={active} onClick={() => select(segment)} className={`w-full rounded-xl border p-4 text-left transition ${active ? 'border-indigo-400 bg-indigo-50 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300'}`}><div className="flex flex-wrap items-center gap-2"><span className={`rounded-lg px-2.5 py-1 text-xs font-bold ${active ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'}`}>{formatTime(segment.startSec)}–{formatTime(segment.endSec)}</span>{active && <span className="text-xs font-semibold text-indigo-700">Reproduciendo desde aquí</span>}</div><p className="mt-3 text-sm font-semibold text-slate-900">{segment.labelName}</p><p className="mt-1 line-clamp-3 text-sm leading-5 text-slate-500">{segment.text}</p></button>
          })}
        </div>
      </section>
    </div>
  </div>
}
