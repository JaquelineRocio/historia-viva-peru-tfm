import type { TranscriptionStatus } from '../types'

const MAP: Record<TranscriptionStatus, { label: string; cls: string }> = {
  pending: { label: 'Pendiente', cls: 'bg-slate-100 text-slate-600' },
  processing: { label: 'Transcribiendo…', cls: 'bg-amber-100 text-amber-700 animate-pulse' },
  done: { label: 'Listo', cls: 'bg-emerald-100 text-emerald-700' },
  failed: { label: 'Error', cls: 'bg-red-100 text-red-700' },
}

export function StatusBadge({ status }: { status: TranscriptionStatus }) {
  const { label, cls } = MAP[status]
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>{label}</span>
}
