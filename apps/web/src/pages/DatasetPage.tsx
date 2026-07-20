import { useState, type FormEvent } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTaxonomy } from '../api/labels'
import { useCreateDataset, useCreateValidationCampaign, useDatasetReadiness, useDatasets, useSaveSecondaryAnnotation, useValidationAgreement, useValidationCampaigns, useValidationSamples, type ValidationCampaign } from '../api/training'
import { apiError } from '../lib/apiClient'
import { buildLabelMap } from '../lib/labels'
import type { Dataset } from '../types'
import { useActiveProject } from '../projects/ProjectContext'

export function DatasetPage() {
  const { projectId } = useActiveProject()
  const datasets = useDatasets(projectId)
  const createDataset = useCreateDataset(projectId)
  const readiness = useDatasetReadiness(projectId)
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const campaigns = useValidationCampaigns(projectId)
  const createCampaign = useCreateValidationCampaign(projectId)
  const [campaignId, setCampaignId] = useState<string>()

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await createDataset.mutateAsync({ name: name || `Dataset ${new Date().toISOString().slice(0, 10)}` })
      setName('')
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <div>
      <h2 className="mb-1 text-lg font-semibold">Datasets</h2>
      <p className="mb-4 text-sm text-slate-500">
        Un dataset es un <strong>snapshot inmutable</strong> de tus etiquetas gold (texto + subtema + split
        train/val/test). Congelarlo permite comparar versiones del modelo de forma justa.
      </p>

      {readiness.data && (
        <div className="mb-5 rounded-2xl border border-indigo-200 bg-indigo-50 p-4">
          <div className="flex items-center justify-between">
            <div><p className="font-semibold text-indigo-950">Preparación del corpus</p><p className="text-xs text-indigo-700">{readiness.data.total} fragmentos revisados · objetivo {readiness.data.targetPerClass} por clase</p></div>
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${readiness.data.ready ? 'bg-emerald-100 text-emerald-700' : 'bg-white text-indigo-700'}`}>{readiness.data.ready ? 'Listo' : 'Piloto'}</span>
          </div>
          {readiness.data.sources && <div className="mt-3 grid gap-2 sm:grid-cols-4">
            <div className="rounded-xl bg-white p-2.5 text-xs"><span className="block text-slate-500">Fuentes gold</span><strong>{readiness.data.sources.gold}/{readiness.data.sources.targetMin}–{readiness.data.sources.targetMax}</strong></div>
            <div className="rounded-xl bg-white p-2.5 text-xs"><span className="block text-slate-500">PDF</span><strong>{readiness.data.sources.pdf}</strong></div>
            <div className="rounded-xl bg-white p-2.5 text-xs"><span className="block text-slate-500">YouTube</span><strong>{readiness.data.sources.youtube}</strong></div>
            <div className="rounded-xl bg-white p-2.5 text-xs"><span className="block text-slate-500">Meta total</span><strong>{readiness.data.targetTotalMin}–{readiness.data.targetTotalMax}</strong></div>
          </div>}
          <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {readiness.data.distribution.map((item) => (
              <div key={item.key} className="rounded-xl bg-white p-2.5">
                <div className="flex justify-between text-xs"><span className="font-medium">{item.name}</span><span>{item.count}/{readiness.data.targetPerClass}</span></div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full bg-indigo-500" style={{ width: `${Math.min(100, item.count / readiness.data.targetPerClass * 100)}%` }} /></div>
              </div>
            ))}
          </div>
        </div>
      )}

      <section className="mb-6 rounded-2xl border border-violet-200 bg-white p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="font-semibold text-violet-950">Validación independiente del 20%</p><p className="text-xs text-slate-500">Crea una muestra estratificada cuando termine la primera revisión. La etiqueta principal queda oculta al segundo especialista.</p></div>
          <button
            disabled={createCampaign.isPending || !readiness.data?.total}
            onClick={() => createCampaign.mutate(undefined, { onSuccess: (campaign) => setCampaignId(campaign.id) })}
            className="rounded-xl bg-violet-700 px-4 py-2 text-xs font-semibold text-white disabled:opacity-40"
          >{createCampaign.isPending ? 'Creando muestra…' : 'Crear muestra 20%'}</button>
        </div>
        {createCampaign.isError && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{apiError(createCampaign.error)}</p>}
        <div className="mt-3 flex flex-wrap gap-2">
          {campaigns.data?.map((campaign) => (
            <button key={campaign.id} onClick={() => setCampaignId(campaign.id)} className={`rounded-xl border px-3 py-2 text-left text-xs ${campaignId === campaign.id ? 'border-violet-500 bg-violet-50' : 'border-slate-200'}`}>
              <span className="block font-semibold">{campaign.name}</span><span className="text-slate-500">{campaign.completedCount}/{campaign.sampleCount} revisados · seed {campaign.seed}</span>
            </button>
          ))}
          {!campaigns.data?.length && <p className="text-xs text-slate-400">Todavía no hay campañas. Se habilitará al existir segmentos revisados.</p>}
        </div>
        {campaignId && <ValidationPanel campaign={campaigns.data?.find((item) => item.id === campaignId)} campaignId={campaignId} />}
      </section>

      <form onSubmit={onCreate} className="mb-6 flex items-end gap-3 rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium text-slate-700">Nombre del snapshot</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Dataset v1"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={createDataset.isPending}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {createDataset.isPending ? 'Creando…' : 'Crear snapshot'}
        </button>
      </form>
      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <div className="space-y-4">
        {datasets.data?.map((d) => (
          <DatasetCard key={d.id} dataset={d} />
        ))}
        {datasets.data?.length === 0 && (
          <p className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-400">
            Aún no hay datasets. Etiqueta segmentos y crea tu primer snapshot.
          </p>
        )}
      </div>
    </div>
  )
}

function ValidationPanel({ campaign, campaignId }: { campaign?: ValidationCampaign; campaignId: string }) {
  const taxonomy = useTaxonomy()
  const [page, setPage] = useState(1)
  const samples = useValidationSamples(campaignId, page)
  const agreement = useValidationAgreement(campaignId)
  const save = useSaveSecondaryAnnotation(campaignId)

  return (
    <div className="mt-4 border-t border-slate-100 pt-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-600">Inicia sesión como <strong>especialista</strong> para realizar la segunda revisión independiente.</p>
        <div className="flex gap-2 text-xs">
          <span className="rounded-full bg-slate-100 px-2.5 py-1">Progreso {agreement.data?.completed ?? campaign?.completedCount ?? 0}/{agreement.data?.total ?? campaign?.sampleCount ?? 0}</span>
          <span className={`rounded-full px-2.5 py-1 font-semibold ${agreement.data?.targetMet ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>Kappa {agreement.data?.kappa == null ? 'pendiente' : agreement.data.kappa.toFixed(3)}</span>
        </div>
      </div>
      <div className="space-y-3">
        {samples.data?.items.map((sample) => (
          <div key={sample.id} className="rounded-xl border border-slate-200 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-violet-600">{sample.resourceTitle} · {sample.locatorType === 'page' ? `página ${sample.pageStart}` : `${Math.floor((sample.startSec ?? 0) / 60)}:${String((sample.startSec ?? 0) % 60).padStart(2, '0')}`}</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">{sample.text}</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <select defaultValue={sample.secondaryLabelKey ?? ''} id={`validation-${sample.id}`} className="min-w-72 flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm">
                <option value="">Selecciona el tema sin consultar la etiqueta primaria</option>
                {taxonomy.data?.map((label) => <option key={label.key} value={label.key}>{label.name}</option>)}
              </select>
              <button onClick={() => {
                const element = document.getElementById(`validation-${sample.id}`) as HTMLSelectElement
                if (element.value) save.mutate({ sampleId: sample.id, labelKey: element.value })
              }} className="rounded-xl bg-violet-700 px-3 py-2 text-xs font-semibold text-white">Guardar revisión</button>
              {sample.secondaryLabelKey && <span className="text-xs font-semibold text-emerald-600">Guardada</span>}
            </div>
          </div>
        ))}
      </div>
      {save.isError && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{apiError(save.error)}</p>}
      {(samples.data?.totalPages ?? 1) > 1 && <div className="mt-3 flex justify-center gap-2 text-xs"><button disabled={page === 1} onClick={() => setPage((value) => value - 1)} className="rounded-lg border px-3 py-1.5 disabled:opacity-40">Anterior</button><span className="px-2 py-1.5">{page}/{samples.data?.totalPages}</span><button disabled={page === samples.data?.totalPages} onClick={() => setPage((value) => value + 1)} className="rounded-lg border px-3 py-1.5 disabled:opacity-40">Siguiente</button></div>}
    </div>
  )
}

function DatasetCard({ dataset }: { dataset: Dataset }) {
  const taxonomy = useTaxonomy()
  const labelMap = buildLabelMap(taxonomy.data)
  const dist = dataset.classDistribution ?? {}
  const data = Object.entries(dist).map(([key, count]) => ({
    key,
    name: labelMap[key]?.name ?? key,
    count,
    color: labelMap[key]?.color ?? '#94a3b8',
  }))
  const split = dataset.splitConfig as { trainRatio?: number; valRatio?: number; testRatio?: number; seed?: number } | null

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="font-semibold">{dataset.name}</h3>
          <p className="text-xs text-slate-400">
            {dataset.nSamples} ejemplos · {new Date(dataset.createdAt).toLocaleString()}
          </p>
        </div>
        {split && (
          <div className="text-right text-xs text-slate-500">
            train {Math.round((split.trainRatio ?? 0) * 100)}% · val {Math.round((split.valRatio ?? 0) * 100)}% · test{' '}
            {Math.round((split.testRatio ?? 0) * 100)}% · seed {split.seed}
          </div>
        )}
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: -16 }}>
            <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-12} textAnchor="end" height={50} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {data.map((d) => (
                <Cell key={d.key} fill={d.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
