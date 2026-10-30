import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useClassifyResource, useProcessResource, useResourceSegments, useResources, useReviewResourceSegment } from '../api/resources'
import { useSubtopics } from '../api/labels'
import { IndexedVideo } from '../components/IndexedVideo'
import { useActiveProject } from '../projects/ProjectContext'
import { apiError } from '../lib/apiClient'

export function VideoPage() {
  const { id = '' } = useParams()
  const [params] = useSearchParams()
  const { project } = useActiveProject()
  const resources = useResources(project?.id)
  const video = resources.data?.find((item) => item.id === id)
  const ready = video?.processingStatus === 'ready'
  const segments = useResourceSegments(ready ? id : undefined)
  const subtopics = useSubtopics()
  const review = useReviewResourceSegment(id)
  const classify = useClassifyResource(project?.id, id)
  const processVideo = useProcessResource(project?.id)

  const items = segments.data ?? []
  const unanalyzed = items.length > 0 && items.every((segment) => !segment.suggestedLabelKey)
  const withoutSecond = items.length > 0 && !unanalyzed && items.every((segment) => !segment.suggestedAlternatives)

  if (resources.isLoading) return <p className="text-sm text-slate-500">Cargando el video…</p>
  if (!video) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center">
        <p className="font-semibold">No encontramos este video.</p>
        <Link to="/" className="mt-3 inline-block text-sm font-semibold text-indigo-700">← Volver a mis videos</Link>
      </div>
    )
  }

  return (
    <div>
      <Link to="/" className="text-sm font-semibold text-indigo-700">← Mis videos</Link>
      <h1 className="mt-2 text-xl font-bold leading-snug sm:text-2xl">{video.title}</h1>
      {video.author && <p className="text-sm text-slate-500">{video.author}</p>}

      {(video.processingStatus === 'pending' || video.processingStatus === 'processing') && (
        <p className="mt-5 rounded-2xl bg-amber-50 p-5 text-sm leading-6 text-amber-900" aria-live="polite">
          Estamos obteniendo la transcripción, dividiéndola en fragmentos y analizando sus subtemas. Suele tardar uno o dos minutos; esta página se actualizará sola.
        </p>
      )}
      {(video.processingStatus === 'failed' || video.processingStatus === 'needs_attention') && (
        <div role="alert" className="mt-5 rounded-2xl bg-red-50 p-5 text-sm text-red-800">
          <p className="font-semibold">No se pudo indexar este video.</p>
          {video.processingError && <p className="mt-1">{video.processingError}</p>}
          <button onClick={() => processVideo.mutate(video.id)} disabled={processVideo.isPending} className="mt-3 min-h-10 rounded-xl bg-red-700 px-4 text-sm font-semibold text-white disabled:opacity-50">Volver a intentar</button>
        </div>
      )}

      {ready && (unanalyzed || withoutSecond) && (
        <div className="mt-5 flex flex-wrap items-center gap-3 rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-900">
          <p className="mr-auto">{unanalyzed ? 'Los fragmentos todavía no tienen subtemas.' : 'Este video se analizó antes de que la aplicación mostrara dos sugerencias.'}</p>
          <button onClick={() => classify.mutate(video.id)} disabled={classify.isPending} className="min-h-10 rounded-xl bg-indigo-600 px-4 font-semibold text-white disabled:opacity-50">
            {classify.isPending ? 'Analizando…' : unanalyzed ? 'Analizar subtemas' : 'Actualizar sugerencias'}
          </button>
          {classify.isError && <p className="w-full text-red-700">{apiError(classify.error)}</p>}
        </div>
      )}

      {ready && video.sourceUrl && (
        <div className="mt-5">
          {segments.isLoading && <p className="text-sm text-slate-500">Cargando los fragmentos…</p>}
          {review.isError && <p role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{apiError(review.error)}</p>}
          {segments.isSuccess && (
            <IndexedVideo
              sourceUrl={video.sourceUrl}
              segments={items}
              subtopics={subtopics}
              initialSegmentId={params.get('fragmento') ?? undefined}
              decidingId={review.isPending ? review.variables?.id : undefined}
              onDecide={(segmentId, labelKey) => review.mutate({ id: segmentId, status: 'reviewed', labelKey })}
            />
          )}
        </div>
      )}
    </div>
  )
}
