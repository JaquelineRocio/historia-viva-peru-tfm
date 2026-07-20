import { useMemo, useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTaxonomy } from '../api/labels'
import { useActivateModel, useModelMetrics, useModels } from '../api/training'
import { apiError } from '../lib/apiClient'
import { buildLabelMap, labelName } from '../lib/labels'
import type { ModelVersion } from '../types'

const pct = (n?: number | null) => (n == null ? '—' : `${(n * 100).toFixed(1)}%`)

export function VersionsPage() {
  const models = useModels()
  const activate = useActivateModel()
  const [detailId, setDetailId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const ready = (models.data ?? []).filter((m) => m.status !== 'failed')

  async function onActivate(m: ModelVersion) {
    setError(null)
    try {
      await activate.mutateAsync(m.id)
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <div>
      <h2 className="mb-1 text-lg font-semibold">Versiones del modelo</h2>
      <p className="mb-4 text-sm text-slate-500">
        Compara métricas entre versiones (la clave del TFM: demostrar la mejora v1→v2) y activa la mejor. La versión
        activa es la que usa la clasificación.
      </p>
      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <div className="mb-6 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Versión</th>
              <th className="px-4 py-2">Estado</th>
              <th className="px-4 py-2">Base</th>
              <th className="px-4 py-2">Creada</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {ready.map((m) => (
              <tr key={m.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-medium">
                  {m.versionTag}
                  {m.isActive && (
                    <span className="ml-2 rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">activa</span>
                  )}
                  <span
                    className={`ml-2 rounded-full px-2 py-0.5 text-xs ${
                      m.recommendationStatus === 'recommended'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}
                  >
                    {m.recommendationStatus === 'recommended' ? 'recomendado' : 'experimental'}
                  </span>
                </td>
                <td className="px-4 py-2">{m.status}</td>
                <td className="px-4 py-2 text-xs text-slate-500">
                  {m.parentVersionId ? 'incremental' : 'BETO'}
                </td>
                <td className="px-4 py-2 text-xs text-slate-400">{new Date(m.createdAt).toLocaleDateString()}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => setDetailId(detailId === m.id ? null : m.id)}
                    className="mr-2 rounded-md border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
                  >
                    {detailId === m.id ? 'Ocultar' : 'Métricas'}
                  </button>
                  {m.status === 'ready' && !m.isActive && (
                    <button
                      onClick={() => onActivate(m)}
                      disabled={activate.isPending}
                      className="rounded-md bg-indigo-600 px-2 py-1 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                      Activar
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {ready.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  Aún no hay versiones. Entrena un modelo primero.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {detailId && <VersionDetail versionId={detailId} />}
    </div>
  )
}

function VersionDetail({ versionId }: { versionId: string }) {
  const metrics = useModelMetrics(versionId)
  const taxonomy = useTaxonomy()
  const labelMap = useMemo(() => buildLabelMap(taxonomy.data), [taxonomy.data])
  // Prioriza la métrica de test; si el entrenamiento reportó otro split (fallback), usa la primera.
  const m = metrics.data?.find((x) => x.split === 'test') ?? metrics.data?.[0]

  if (metrics.isLoading) return <p className="text-slate-500">Cargando métricas…</p>
  if (!m) return <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-700">Esta versión aún no tiene métricas.</p>

  const perClass = (m.perClassMetrics ?? []).map((c) => ({
    name: labelName(labelMap, c.label),
    f1: c.f1,
    color: labelMap[c.label]?.color ?? '#94a3b8',
  }))
  const cm = m.confusionMatrix
  const baselineDelta =
    m.f1Macro != null && m.baselineF1Macro != null ? m.f1Macro - m.baselineF1Macro : null

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold">Métricas globales ({m.split})</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Metric label="Accuracy" value={pct(m.accuracy)} />
          <Metric label="F1 macro" value={pct(m.f1Macro)} highlight />
          <Metric label="F1 ponderado" value={pct(m.f1Weighted)} />
          <Metric label="Precisión macro" value={pct(m.precisionMacro)} />
          <Metric label="Recall macro" value={pct(m.recallMacro)} />
          <Metric label="Baseline TF-IDF" value={pct(m.baselineF1Macro)} />
        </div>
        <div
          className={`mt-3 rounded-lg px-3 py-2 text-sm ${
            m.exceedsBaseline === true
              ? 'bg-emerald-50 text-emerald-800'
              : m.exceedsBaseline === false
                ? 'bg-red-50 text-red-800'
                : 'bg-amber-50 text-amber-800'
          }`}
        >
          {m.exceedsBaseline === true && `BETO supera TF-IDF por ${pct(baselineDelta)}.`}
          {m.exceedsBaseline === false && `BETO no supera TF-IDF (${pct(baselineDelta)} de diferencia).`}
          {m.exceedsBaseline == null && 'Esta version no tiene una comparacion de baseline auditable.'}
          {m.f1MacroCi95 && (
            <span className="ml-1">
              IC95 del F1 macro: {pct(m.f1MacroCi95.low)} - {pct(m.f1MacroCi95.high)}.
            </span>
          )}
        </div>
        <h3 className="mb-2 mt-4 text-sm font-semibold">F1 por clase</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={perClass} margin={{ top: 4, right: 8, bottom: 4, left: -20 }}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-12} textAnchor="end" height={46} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => (v * 100).toFixed(1) + '%'} />
              <Bar dataKey="f1" radius={[4, 4, 0, 0]}>
                {perClass.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {cm && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold">Matriz de confusión</h3>
          <ConfusionMatrix labels={cm.labels.map((l) => labelName(labelMap, l))} matrix={cm.matrix} />
        </div>
      )}
    </div>
  )
}

function Metric({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`rounded-lg p-3 ${highlight ? 'bg-indigo-50' : 'bg-slate-50'}`}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-xl font-bold ${highlight ? 'text-indigo-700' : 'text-slate-800'}`}>{value}</p>
    </div>
  )
}

function ConfusionMatrix({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const max = Math.max(1, ...matrix.flat())
  return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead>
          <tr>
            <th className="p-1"></th>
            {labels.map((l) => (
              <th key={l} className="p-1 font-normal text-slate-400" title={l}>
                {l.slice(0, 6)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <td className="p-1 font-medium text-slate-500" title={labels[i]}>
                {labels[i]?.slice(0, 10)}
              </td>
              {row.map((v, j) => (
                <td
                  key={j}
                  className="h-8 w-8 text-center"
                  style={{
                    background: `rgba(79,70,229,${v / max})`,
                    color: v / max > 0.5 ? 'white' : '#334155',
                  }}
                >
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-slate-400">Filas = verdad · columnas = predicción</p>
    </div>
  )
}
