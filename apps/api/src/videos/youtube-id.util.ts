const YOUTUBE_ID = /^[A-Za-z0-9_-]{11}$/;
const YOUTUBE_HOSTS = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com']);

/** Extrae el ID de 11 caracteres de una URL de YouTube (o lo devuelve si ya es ID). */
export function extractYoutubeId(urlOrId: string): string | null {
  const s = urlOrId.trim();
  if (YOUTUBE_ID.test(s)) return s;
  try {
    const url = new URL(s);
    if (url.protocol !== 'https:') return null;
    const hostname = url.hostname.toLowerCase();
    if (hostname === 'youtu.be') {
      const id = url.pathname.split('/').filter(Boolean)[0];
      return id && YOUTUBE_ID.test(id) ? id : null;
    }
    if (!YOUTUBE_HOSTS.has(hostname)) return null;
    const pathParts = url.pathname.split('/').filter(Boolean);
    const candidate = url.pathname === '/watch'
      ? url.searchParams.get('v')
      : ['embed', 'shorts', 'live', 'v'].includes(pathParts[0]) ? pathParts[1] : null;
    return candidate && YOUTUBE_ID.test(candidate) ? candidate : null;
  } catch {
    return null;
  }
}

export function canonicalYoutubeUrl(urlOrId: string): string | null {
  const id = extractYoutubeId(urlOrId);
  return id ? `https://www.youtube.com/watch?v=${id}` : null;
}
