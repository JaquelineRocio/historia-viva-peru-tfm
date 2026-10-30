import type { LabelTaxonomy, ReviewStatus, Suggestion } from '../types'

/**
 * Reglas de la indexación temática asistida (tesis, cap. IV, «Implicaciones
 * para la práctica docente»): se ocultan los fragmentos no relevantes, cada
 * fragmento muestra sus dos subtemas más probables, los muy seguros se
 * etiquetan solos y el resto queda para que el docente confirme con un clic.
 */

/** Desde esta confianza el fragmento se etiqueta solo (informe de cierre v5, §9). */
export const AUTO_CONFIDENCE = 0.6
/** Probabilidad mínima para mostrar una segunda sugerencia (umbral conforme α = 0,2). */
export const MIN_SUGGESTION = 0.1
export const NOT_RELEVANT = 'no_relevante'

export interface Subtopic {
  key: string
  name: string
  color: string
  description: string
}

/** Las siete categorías de la guía v3.1 (Tabla 8); la API puede actualizar nombre y color. */
export const SUBTOPICS: Subtopic[] = [
  { key: 'contexto_colonial_antecedentes', name: 'Contexto colonial y antecedentes', color: '#4f46e5', description: 'Estructuras, administración y condiciones coloniales que explican el proceso.' },
  { key: 'crisis_ideas_emancipadoras', name: 'Crisis e ideas emancipadoras', color: '#0891b2', description: 'Crisis de la monarquía y difusión de las ideas de independencia.' },
  { key: 'campanias_conflictos_militares', name: 'Campañas y conflictos militares', color: '#dc2626', description: 'Expediciones, batallas, ejércitos y desarrollo de la guerra.' },
  { key: 'liderazgos_diplomacia_proyectos', name: 'Liderazgos, diplomacia y proyectos', color: '#7c3aed', description: 'Decisiones de los líderes, negociaciones y proyectos de gobierno en disputa.' },
  { key: 'organizacion_consecuencias_republicanas', name: 'Organización y consecuencias republicanas', color: '#059669', description: 'Instituciones, ciudadanía, economía y constituciones de la república.' },
  { key: 'participacion_social_regional', name: 'Participación social y regional', color: '#d97706', description: 'Participación indígena, afroperuana, popular, femenina y de las regiones.' },
  { key: NOT_RELEVANT, name: 'No relevante', color: '#64748b', description: 'Presentaciones, método, otros periodos o contenido sin desarrollo histórico.' },
]

export type SubtopicMap = Record<string, Subtopic>

export function buildSubtopicMap(taxonomy?: LabelTaxonomy[]): SubtopicMap {
  const map: SubtopicMap = Object.fromEntries(SUBTOPICS.map((item) => [item.key, item]))
  for (const item of taxonomy ?? []) {
    const known = map[item.key]
    map[item.key] = {
      key: item.key,
      name: item.name,
      color: item.color || known?.color || '#94a3b8',
      description: known?.description || item.description || '',
    }
  }
  return map
}

export function subtopicName(map: SubtopicMap, key?: string | null) {
  return key ? map[key]?.name ?? key : 'Sin subtema'
}

export function subtopicColor(map: SubtopicMap, key?: string | null) {
  return key ? map[key]?.color ?? '#94a3b8' : '#94a3b8'
}

/** Campos comunes a los fragmentos privados y a los de la demostración pública. */
export interface IndexedSegment {
  id: string
  startSec?: number | null
  endSec?: number | null
  text: string
  suggestedLabelKey?: string | null
  suggestedConfidence?: number | null
  suggestedAlternatives?: Suggestion[] | null
  reviewedLabelKey?: string | null
  reviewStatus?: ReviewStatus
}

export type SegmentState = 'confirmed' | 'auto' | 'pending' | 'unclassified'

export function segmentState(segment: IndexedSegment): SegmentState {
  if (segment.reviewStatus ? segment.reviewStatus === 'reviewed' : !!segment.reviewedLabelKey) return 'confirmed'
  if (!segment.suggestedLabelKey) return 'unclassified'
  return (segment.suggestedConfidence ?? 0) >= AUTO_CONFIDENCE ? 'auto' : 'pending'
}

/** Subtema vigente: el confirmado por el docente o, si no hay, la primera sugerencia. */
export function currentLabel(segment: IndexedSegment) {
  return segment.reviewedLabelKey || segment.suggestedLabelKey || null
}

export function isHidden(segment: IndexedSegment) {
  return segment.reviewStatus === 'excluded' || currentLabel(segment) === NOT_RELEVANT
}

/** Hasta dos sugerencias: la principal y, si alcanza el mínimo, la siguiente. */
export function suggestions(segment: IndexedSegment): Suggestion[] {
  if (!segment.suggestedLabelKey) return []
  const first = { label: segment.suggestedLabelKey, confidence: segment.suggestedConfidence ?? 0 }
  const second = segment.suggestedAlternatives?.find((item) => item.label !== first.label && item.confidence >= MIN_SUGGESTION)
  return second ? [first, second] : [first]
}

export function percent(value: number) {
  return `${Math.round(value * 100)} %`
}
