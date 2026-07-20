const YT_ID_PATTERNS = [
  /(?:v=|\/videos\/|embed\/|youtu\.be\/|\/v\/|watch\?v=|&v=)([A-Za-z0-9_-]{11})/,
  /^([A-Za-z0-9_-]{11})$/,
];

/** Extrae el ID de 11 caracteres de una URL de YouTube (o lo devuelve si ya es ID). */
export function extractYoutubeId(urlOrId: string): string | null {
  const s = urlOrId.trim();
  for (const p of YT_ID_PATTERNS) {
    const m = s.match(p);
    if (m) return m[1];
  }
  return null;
}
