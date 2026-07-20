import { useEffect, useState } from 'react'
import { useDatasets, useCreateTrainingJob, useTrainingJobs, useModels } from '../api/training'
import { apiError } from '../lib/apiClient'
import type { JobStatus } from '../types'
import { useActiveProject } from '../projects/ProjectContext'

const JOB_CLS: Record<JobStatus, string> = {
  queued: 'bg-slate-100 text-slate-600',
  running: 'bg-amber-100 text-amber-700',
  done: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-700',
  cancelled: 'bg-slate-100 text-slate-500',
}

export function TrainingPage() {
  const { projectId } = useActiveProject()
  const datasets = useDatasets(projectId)
  const models = useModels()
  const jobs = useTrainingJobs()
  const createJob = useCreateTrainingJob()

  const [datasetId, setDatasetId] = useState('')
  const [parentVersionId, setParentVersionId] = useState('')
  const [epochs, setEpochs] = useState(4)
  const [batchSize, setBatchSize] = useState(8)
  const [maxLen, setMaxLen] = useState(192)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!datasetId && datasets.data?.length) setDatasetId(datasets.data[0].id)
  }, [datasets.data, datasetId])

  async function onTrain() {
    setError(null)
    try {
      await createJob.mutateAsync({
        datasetId,
        parentVersionId: parentVersionId || undefined,
        hyperparams: { epochs, batch_size: batchSize, max_len: maxLen },
      })
    } catch (err) {
      setError(apiError(err))
    }
  }

  const versionTag = (id?: string | null) => models.data?.find((m) => m.id === id)?.versionTag ?? '—'

  return (
    <div>
      <h2 className="mb-1 text-lg font-semibold">Entrenamiento</h2>
      <p className="mb-4 text-sm text-slate-500">
        Fine-tunea BETO sobre un dataset. El cómputo lo hace el servicio Python; para datasets grandes usa el
        notebook de Colab (GPU gratis) e importa los pesos. El primer modelo entrenado se activa automáticamente.
      </p>

      <div className="mb-6 grid grid-cols-1 gap-4 rounded-xl border border-slate-200 bg-white p-4 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Dataset</label>
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="" disabled>
              Selecciona…
            </option>
            {datasets.data?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.nSamples})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Versión padre <span className="text-slate-400">(incremental, opcional)</span>
          </label>
          <select
            value={parentVersionId}
            onChange={(e) => setParentVersionId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">BETO base</option>
            {models.data?.filter((m) => m.status === 'ready').map((m) => (
              <option key={m.id} value={m.id}>
                {m.versionTag}
              </option>
            ))}
          </select>
        </div>
        <Num label="Épocas" value={epochs} setValue={setEpochs} min={1} max={10} />
        <Num label="Batch size" value={batchSize} setValue={setBatchSize} min={2} max={64} />
        <Num label="Max length (tokens)" value={maxLen} setValue={setMaxLen} min={64} max={512} step={32} />
        <div className="flex items-end">
          <button
            onClick={onTrain}
            disabled={!datasetId || createJob.isPending}
            className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {createJob.isPending ? 'Lanzando…' : 'Entrenar'}
          </button>
        </div>
      </div>
      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <h3 className="mb-2 text-sm font-semibold text-slate-500">Jobs</h3>
      <div className="space-y-2">
        {jobs.data?.map((j) => (
          <div key={j.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-medium">{versionTag(j.modelVersionId)}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${JOB_CLS[j.status]}`}>
                {j.status}
                {j.currentEpoch != null ? ` · época ${j.currentEpoch}` : ''}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full bg-indigo-500 transition-all" style={{ width: `${j.progress}%` }} />
            </div>
            {j.error && <p className="mt-1 text-xs text-red-600">{j.error}</p>}
          </div>
        ))}
        {jobs.data?.length === 0 && <p className="text-sm text-slate-400">Sin jobs todavía.</p>}
      </div>
    </div>
  )
}

function Num({
  label,
  value,
  setValue,
  min,
  max,
  step,
}: {
  label: string
  value: number
  setValue: (n: number) => void
  min: number
  max: number
  step?: number
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-slate-700">{label}</label>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step ?? 1}
        onChange={(e) => setValue(Number(e.target.value))}
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
      />
    </div>
  )
}
