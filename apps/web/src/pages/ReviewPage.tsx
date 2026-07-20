import { useEffect, useMemo, useState } from 'react'
import { useTaxonomy } from '../api/labels'
import { useBulkReviewSegments, usePagedResourceSegments, useReplaceSegmentEntities, useResources, useReviewResourceSegment, useSegmentEntities } from '../api/resources'
import { useActiveProject } from '../projects/ProjectContext'
import { buildLabelMap } from '../lib/labels'
import { formatTime } from '../lib/format'
import { apiError } from '../lib/apiClient'
import type { HistoricalEntity, LabelTaxonomy, ResourceSegment } from '../types'
import { useAnnotationCampaignProgress, useAnnotationCampaigns, useCreateAnnotationCampaign } from '../api/training'

export function ReviewPage() {
  const { project } = useActiveProject()
  const resources = useResources(project?.id)
  const ready = useMemo(
    () => resources.data?.filter((item) => item.processingStatus === 'ready' && item.corpusStatus === 'included') ?? [],
    [resources.data],
  )
  const [resourceId, setResourceId] = useState<string>()
  const [filter, setFilter] = useState<'pending' | 'all'>('pending')
  const [page, setPage] = useState(1)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [bulkLabel, setBulkLabel] = useState('')
  const [showGuide, setShowGuide] = useState(false)
  const [showProgress, setShowProgress] = useState(true)
  const campaigns = useAnnotationCampaigns(project?.id)
  const createCampaign = useCreateAnnotationCampaign(project?.id)
  const [campaignId, setCampaignId] = useState<string>()
  const progress = useAnnotationCampaignProgress(campaignId)

  useEffect(() => {
    if (!campaignId && campaigns.data?.length) setCampaignId(campaigns.data[0].id)
  }, [campaignId, campaigns.data])

  useEffect(() => {
    if (!resourceId) {
      const nextSource = progress.data?.sources.find((item) => item.pending > 0)?.resourceId
      if (nextSource) setResourceId(nextSource)
      else if (ready.length) setResourceId(ready[0].id)
    }
  }, [progress.data, ready, resourceId])

  const segments = usePagedResourceSegments(project?.id, resourceId, {
    page, limit: 25, status: filter === 'pending' ? 'pending' : undefined, sort: 'low_confidence', campaignId,
  })
  const bulk = useBulkReviewSegments()
  const taxonomy = useTaxonomy()
  const labelMap = useMemo(() => buildLabelMap(taxonomy.data), [taxonomy.data])
  const visible = segments.data?.items ?? []
  const total = segments.data?.total ?? 0
  const campaign = campaigns.data?.find((item) => item.id === campaignId)
  const sourceProgress = useMemo(
    () => new Map(progress.data?.sources.map((item) => [item.resourceId, item]) ?? []),
    [progress.data?.sources],
  )

  function runBulk(status: 'reviewed' | 'ambiguous' | 'excluded') {
    bulk.mutate({ segmentIds: selectedIds, status, labelKey: status === 'reviewed' ? bulkLabel : undefined }, {
      onSuccess: () => setSelectedIds([]),
    })
  }

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Calidad del dato</p>
      <h1 className="text-2xl font-bold">Revisión de subtemas</h1>
      <p className="mt-1 text-sm text-slate-500">BETO sugiere; tú decides qué etiquetas se convierten en evidencia de entrenamiento.</p>

      <div className="mt-4 flex flex-wrap items-end gap-3 rounded-2xl border border-indigo-200 bg-indigo-50 p-4">
        <label className="min-w-64 flex-1 text-sm font-semibold text-indigo-950">Campaña primaria
          <select value={campaignId ?? ''} onChange={(event) => { setCampaignId(event.target.value || undefined); setResourceId(undefined); setPage(1) }} className="mt-1 w-full rounded-xl border border-indigo-200 bg-white px-3 py-2.5 text-sm font-normal">
            <option value="">Sin campaña</option>
            {campaigns.data?.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.completedCount}/{item.sampleCount}</option>)}
          </select>
        </label>
        {campaign ? (
          <div className="min-w-64 flex-1">
            <div className="flex justify-between text-xs text-indigo-700"><span>{campaign.sourceCount} fuentes · seed {campaign.seed}</span><strong>{Math.round((campaign.completedCount / campaign.sampleCount) * 100)}%</strong></div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-indigo-100"><div className="h-full bg-indigo-600" style={{ width: `${(campaign.completedCount / campaign.sampleCount) * 100}%` }} /></div>
          </div>
        ) : (
          <button disabled={createCampaign.isPending || !project?.id} onClick={() => createCampaign.mutate()} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40">Crear selección de 700</button>
        )}
      </div>

      {campaign && progress.data && (
        <section className="mt-3 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-900">Avance de la campaña</p>
              <p className="text-xs text-slate-500">{progress.data.totals.reviewed} revisados · {progress.data.totals.pending} pendientes · {progress.data.totals.ambiguous} ambiguos · {progress.data.totals.excluded} excluidos</p>
            </div>
            <button onClick={() => setShowProgress((value) => !value)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600">{showProgress ? 'Ocultar detalle' : 'Ver detalle'}</button>
          </div>
          {showProgress && (
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Objetivo por clase</p>
                <div className="space-y-2">
                  {progress.data.classes.map((item) => (
                    <div key={item.key}>
                      <div className="flex justify-between text-xs"><span>{item.name}</span><strong className={item.count >= item.target ? 'text-emerald-600' : 'text-slate-600'}>{item.count}/{item.target}</strong></div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full" style={{ width: String(Math.min(100, item.count)) + '%', backgroundColor: item.color }} /></div>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Progreso por fuente</p>
                <div className="max-h-56 space-y-1.5 overflow-y-auto pr-1">
                  {progress.data.sources.map((item) => (
                    <button key={item.resourceId} onClick={() => { setResourceId(item.resourceId); setPage(1); setSelectedIds([]) }} className="w-full rounded-lg border border-slate-100 px-3 py-2 text-left text-xs hover:bg-slate-50">
                      <span className="block truncate font-semibold text-slate-700">{item.title}</span>
                      <span className="text-slate-500">{item.reviewed}/{item.total} revisados · {item.pending} pendientes</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      <div className="mt-4 rounded-2xl border border-violet-200 bg-violet-50 p-4">
        <div className="flex items-center justify-between gap-3">
          <div><p className="text-sm font-semibold text-violet-950">Guía de etiquetado 1780–1842</p><p className="text-xs text-violet-700">Elige la idea histórica dominante; años, personajes y lugares son entidades, no temas.</p></div>
          <button onClick={() => setShowGuide((value) => !value)} className="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-violet-700 shadow-sm">{showGuide ? 'Ocultar guía' : 'Consultar guía'}</button>
        </div>
        {showGuide && (
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {taxonomy.data?.map((item) => <div key={item.key} className="rounded-xl bg-white p-3"><p className="text-xs font-semibold" style={{ color: item.color }}>{item.name}</p><p className="mt-1 text-xs leading-5 text-slate-600">{item.description}</p></div>)}
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3"><p className="text-xs font-semibold text-amber-800">¿Dos temas con el mismo peso?</p><p className="mt-1 text-xs leading-5 text-amber-700">Marca el segmento como ambiguo. Portadas, índices, bibliografías y ruido corresponden a No relevante.</p></div>
          </div>
        )}
      </div>

      <div className="mt-5 flex flex-wrap items-end gap-3 rounded-2xl border border-slate-200 bg-white p-4">
        <label className="min-w-64 flex-1 text-sm font-medium">Fuente
          <select value={resourceId ?? ''} onChange={(e) => { setResourceId(e.target.value); setPage(1); setSelectedIds([]) }} className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2.5">
            <option value="">Selecciona una fuente procesada</option>
            {ready.map((item) => {
              const itemProgress = sourceProgress.get(item.id)
              return <option key={item.id} value={item.id}>{item.title}{itemProgress ? ' · ' + itemProgress.reviewed + '/' + itemProgress.total : ''}</option>
            })}
          </select>
        </label>
        <div className="min-w-48 flex-1">
          <div className="mb-1 flex justify-between text-xs text-slate-500"><span>Fragmentos en la vista</span><span>{total}</span></div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full bg-indigo-500" style={{ width: `${segments.isLoading ? 20 : 100}%` }} /></div>
        </div>
        <div className="flex rounded-xl bg-slate-100 p-1 text-xs font-semibold">
          <button onClick={() => { setFilter('pending'); setPage(1); setSelectedIds([]) }} className={`rounded-lg px-3 py-1.5 ${filter === 'pending' ? 'bg-white shadow-sm' : 'text-slate-500'}`}>Pendientes</button>
          <button onClick={() => { setFilter('all'); setPage(1); setSelectedIds([]) }} className={`rounded-lg px-3 py-1.5 ${filter === 'all' ? 'bg-white shadow-sm' : 'text-slate-500'}`}>Todos</button>
        </div>
      </div>

      {selectedIds.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 rounded-2xl border border-indigo-200 bg-indigo-50 p-3">
          <span className="text-sm font-semibold text-indigo-900">{selectedIds.length} seleccionados</span>
          <select value={bulkLabel} onChange={(event) => setBulkLabel(event.target.value)} className="min-w-64 rounded-xl border border-indigo-200 px-3 py-2 text-sm">
            <option value="">Selecciona un subtema…</option>
            {taxonomy.data?.map((item) => <option key={item.key} value={item.key}>{item.name}</option>)}
          </select>
          <button disabled={!bulkLabel || bulk.isPending} onClick={() => runBulk('reviewed')} className="rounded-xl bg-emerald-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-40">Confirmar lote</button>
          <button disabled={bulk.isPending} onClick={() => runBulk('ambiguous')} className="rounded-xl border border-amber-300 px-3 py-2 text-xs font-semibold text-amber-700">Ambiguos</button>
          <button disabled={bulk.isPending} onClick={() => runBulk('excluded')} className="rounded-xl border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700">Excluir</button>
          {bulk.isError && <span className="text-xs font-semibold text-red-700">{apiError(bulk.error)}</span>}
          {bulk.isSuccess && <span className="text-xs font-semibold text-emerald-700">Lote guardado</span>}
        </div>
      )}

      <div className="mt-4 space-y-3">
        {visible.map((segment) => <ReviewCard key={segment.id} segment={segment} taxonomy={taxonomy.data ?? []} labelMap={labelMap} selected={selectedIds.includes(segment.id)} onToggle={() => setSelectedIds((current) => current.includes(segment.id) ? current.filter((id) => id !== segment.id) : [...current, segment.id])} />)}
        {resourceId && !visible.length && <div className="rounded-2xl border border-dashed border-emerald-300 bg-emerald-50 p-8 text-center text-sm text-emerald-700">No quedan fragmentos pendientes en esta vista.</div>}
        {!resourceId && <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400">Procesa una fuente y selecciónala para empezar.</div>}
      </div>
      {resourceId && (segments.data?.totalPages ?? 1) > 1 && (
        <div className="mt-5 flex items-center justify-center gap-3">
          <button disabled={page <= 1} onClick={() => { setPage((value) => value - 1); setSelectedIds([]) }} className="rounded-xl border border-slate-300 px-4 py-2 text-sm disabled:opacity-40">← Anterior</button>
          <span className="text-sm font-semibold">Página {page} de {segments.data?.totalPages}</span>
          <button disabled={page >= (segments.data?.totalPages ?? 1)} onClick={() => { setPage((value) => value + 1); setSelectedIds([]) }} className="rounded-xl border border-slate-300 px-4 py-2 text-sm disabled:opacity-40">Siguiente →</button>
        </div>
      )}
    </div>
  )
}

function ReviewCard({ segment, taxonomy, labelMap, selected, onToggle }: { segment: ResourceSegment; taxonomy: LabelTaxonomy[]; labelMap: ReturnType<typeof buildLabelMap>; selected: boolean; onToggle: () => void }) {
  const review = useReviewResourceSegment(segment.resourceId)
  const [label, setLabel] = useState(segment.reviewedLabelKey || segment.suggestedLabelKey || taxonomy[0]?.key || '')
  const [showEntities, setShowEntities] = useState(false)
  const locator = segment.locatorType === 'timestamp' ? formatTime(segment.startSec ?? 0) : `Página ${segment.pageStart}`
  return (
    <article className={`rounded-2xl border bg-white p-4 ${segment.reviewStatus === 'reviewed' ? 'border-emerald-200' : 'border-slate-200'}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <label className="flex items-center gap-2 text-xs font-semibold text-slate-500"><input type="checkbox" checked={selected} onChange={onToggle} /> Seleccionar</label>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded-lg bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700">{locator}</span>
            {segment.suggestedLabelKey && (
              <span className="text-xs text-slate-400">Sugerencia: {labelMap[segment.suggestedLabelKey]?.name ?? segment.suggestedLabelKey} · {Math.round((segment.suggestedConfidence ?? 0) * 100)}%</span>
            )}
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-700">{segment.text}</p>
          {(segment.suggestedConfidence == null || segment.suggestedConfidence < 0.6) && (
            <p className="mt-2 inline-flex rounded-lg bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">Revisión prioritaria · confianza baja o sin modelo</p>
          )}
          {!!segment.entities?.length && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {segment.entities.filter((entity) => ['person', 'place', 'date', 'period'].includes(entity.type)).slice(0, 10).map((entity, index) => (
                <span key={`${entity.type}-${entity.normalizedValue}-${index}`} className={`rounded-full px-2 py-1 text-[11px] font-medium ${entity.outOfScope ? 'bg-slate-100 text-slate-500 line-through' : 'bg-violet-50 text-violet-700'}`}>
                  {entity.type === 'person' ? 'Personaje' : entity.type === 'place' ? 'Lugar' : 'Año'} · {entity.text}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="w-full shrink-0 sm:w-64">
          <select value={label} onChange={(e) => setLabel(e.target.value)} className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm">
            {taxonomy.map((item) => <option key={item.key} value={item.key}>{item.name}</option>)}
          </select>
          <button disabled={review.isPending} onClick={() => review.mutate({ id: segment.id, status: 'reviewed', labelKey: label })} className="mt-2 w-full rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">{review.isPending ? 'Guardando…' : 'Confirmar subtema'}</button>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <button onClick={() => review.mutate({ id: segment.id, status: 'ambiguous' })} className="rounded-lg border border-amber-300 px-2 py-1.5 text-xs font-medium text-amber-700">Ambiguo</button>
            <button onClick={() => review.mutate({ id: segment.id, status: 'excluded' })} className="rounded-lg border border-slate-300 px-2 py-1.5 text-xs font-medium text-slate-600">Excluir</button>
          </div>
          {review.isError && <p className="mt-2 text-xs font-semibold text-red-700">{apiError(review.error)}</p>}
          {review.isSuccess && <p className="mt-2 text-xs font-semibold text-emerald-700">Revisión guardada</p>}
        </div>
      </div>
      <div className="mt-3 border-t border-slate-100 pt-3">
        <button onClick={() => setShowEntities((value) => !value)} className="text-xs font-semibold text-violet-700">
          {showEntities ? 'Ocultar entidades' : 'Revisar personajes, lugares y fechas'}
        </button>
        {showEntities && <EntityEditor segmentId={segment.id} />}
      </div>
    </article>
  )
}

type EditableEntity = Pick<HistoricalEntity, 'type' | 'text' | 'yearStart' | 'yearEnd'>

function EntityEditor({ segmentId }: { segmentId: string }) {
  const entities = useSegmentEntities(segmentId)
  const replace = useReplaceSegmentEntities(segmentId)
  const [draft, setDraft] = useState<EditableEntity[]>([])

  useEffect(() => {
    if (entities.data) {
      setDraft(entities.data.map((item) => ({
        type: item.type,
        text: item.text,
        yearStart: item.yearStart,
        yearEnd: item.yearEnd,
      })))
    }
  }, [entities.data])

  function update(index: number, changes: Partial<EditableEntity>) {
    setDraft((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, ...changes } : item))
  }

  return (
    <div className="mt-3 rounded-xl bg-violet-50 p-3">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold text-violet-900">Entidades detectadas</p>
          <p className="text-[11px] text-violet-600">Al guardar, esta revisión humana reemplaza las sugerencias visibles y queda auditada.</p>
        </div>
        <button onClick={() => setDraft((current) => [...current, { type: 'person', text: '' }])} className="rounded-lg bg-white px-2 py-1.5 text-xs font-semibold text-violet-700 shadow-sm">+ Añadir</button>
      </div>
      {entities.isLoading && <p className="py-3 text-xs text-slate-500">Cargando entidades…</p>}
      <div className="space-y-2">
        {draft.map((entity, index) => (
          <div key={index} className="grid gap-2 rounded-xl border border-violet-100 bg-white p-2 sm:grid-cols-[140px_minmax(0,1fr)_100px_100px_auto]">
            <select value={entity.type} onChange={(e) => update(index, { type: e.target.value as HistoricalEntity['type'] })} className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs">
              <option value="person">Personaje</option>
              <option value="place">Lugar</option>
              <option value="organization">Organización</option>
              <option value="date">Fecha</option>
              <option value="period">Periodo</option>
              <option value="other">Otro</option>
            </select>
            <input value={entity.text} onChange={(e) => update(index, { text: e.target.value })} placeholder="Texto de la entidad" className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
            {['date', 'period'].includes(entity.type) ? (
              <>
                <input type="number" min={1000} max={2100} value={entity.yearStart ?? ''} onChange={(e) => update(index, { yearStart: e.target.value ? Number(e.target.value) : undefined })} placeholder="Desde" className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
                <input type="number" min={1000} max={2100} value={entity.yearEnd ?? ''} onChange={(e) => update(index, { yearEnd: e.target.value ? Number(e.target.value) : undefined })} placeholder="Hasta" className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
              </>
            ) : <div className="hidden sm:col-span-2 sm:block" />}
            <button onClick={() => setDraft((current) => current.filter((_, itemIndex) => itemIndex !== index))} className="rounded-lg px-2 text-xs font-semibold text-red-600">Quitar</button>
          </div>
        ))}
        {!entities.isLoading && !draft.length && <p className="rounded-xl border border-dashed border-violet-200 p-3 text-center text-xs text-violet-600">No se detectaron entidades. Puedes añadirlas manualmente.</p>}
      </div>
      <button
        disabled={replace.isPending || draft.some((item) => !item.text.trim())}
        onClick={() => replace.mutate(draft.map((item) => ({
          type: item.type,
          text: item.text.trim(),
          yearStart: item.yearStart ?? undefined,
          yearEnd: item.yearEnd ?? undefined,
        })))}
        className="mt-3 rounded-xl bg-violet-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-40"
      >
        {replace.isPending ? 'Guardando…' : replace.isSuccess ? 'Revisión guardada ✓' : 'Guardar revisión de entidades'}
      </button>
    </div>
  )
}
