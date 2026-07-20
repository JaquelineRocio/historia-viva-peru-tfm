export interface EvidenceCandidate {
  text: string;
  score?: number;
}

const GENERIC_TERMS = new Set([
  'historia', 'peru', 'peruana', 'peruano', 'independencia', 'republica',
  'papel', 'relacion', 'tuvo', 'tenia', 'como', 'cual', 'para', 'entre',
  'sobre', 'formacion', 'explica', 'explicar', 'dime', 'segun', 'fuentes',
  'paso',
]);

export function normalizeEvidenceText(value: string): string {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

export function distinctiveTerms(query: string): string[] {
  const normalized = normalizeEvidenceText(query);
  return [...new Set((normalized.match(/[a-zñ]{4,}/g) || [])
    .filter((word) => !GENERIC_TERMS.has(word)))];
}

/**
 * La similitud semántica por sí sola no demuestra respaldo. Al menos un término
 * distintivo de la pregunta debe aparecer en el fragmento. Esto evita que una
 * pregunta fuera del corpus (p. ej. Apolo 11) reciba una cita histórica casual.
 */
export function supportedEvidence<T extends EvidenceCandidate>(query: string, evidence: T[]): T[] {
  const terms = distinctiveTerms(query);
  return evidence.filter((item) => {
    const text = normalizeEvidenceText(item.text);
    if (terms.length) {
      const matches = terms.filter((term) => text.includes(term)).length;
      const requiredMatches = terms.length === 1 ? 1 : 2;
      return matches >= requiredMatches && Number(item.score || 0) >= 0.20;
    }
    return Number(item.score || 0) >= 0.35;
  });
}
