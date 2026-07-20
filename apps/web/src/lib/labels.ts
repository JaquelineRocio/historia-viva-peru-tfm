import type { LabelTaxonomy } from '../types'

const FALLBACK = '#94a3b8'

export interface LabelMeta {
  name: string
  color: string
}

/** Construye un mapa key → {name, color} desde la taxonomía. */
export function buildLabelMap(taxonomy: LabelTaxonomy[] | undefined): Record<string, LabelMeta> {
  const map: Record<string, LabelMeta> = {}
  for (const t of taxonomy ?? []) map[t.key] = { name: t.name, color: t.color || FALLBACK }
  return map
}

export function labelColor(map: Record<string, LabelMeta>, key?: string | null): string {
  return key && map[key] ? map[key].color : FALLBACK
}

export function labelName(map: Record<string, LabelMeta>, key?: string | null): string {
  return key && map[key] ? map[key].name : (key ?? '—')
}
