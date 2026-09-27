import { forwardRef, useImperativeHandle, useRef, useState } from 'react'
import YouTube, { type YouTubePlayer } from 'react-youtube'
import { formatTime } from '../lib/format'

export interface VideoPlayerHandle {
  seekTo: (seconds: number) => void
}

function youtubeId(url: string) {
  try {
    const parsed = new URL(url)
    const host = parsed.hostname.toLowerCase()
    const id = host === 'youtu.be' ? parsed.pathname.split('/')[1]
      : ['youtube.com', 'www.youtube.com', 'm.youtube.com'].includes(host)
        ? parsed.searchParams.get('v') || (/^\/(embed|shorts|live)\//.test(parsed.pathname) ? parsed.pathname.split('/')[2] : '')
        : ''
    return id && /^[a-zA-Z0-9_-]{11}$/.test(id) ? id : ''
  } catch {
    return ''
  }
}

// Mount with key={sourceUrl} so a different source gets a fresh player.
export const VideoPlayer = forwardRef<VideoPlayerHandle, { sourceUrl: string; startSec?: number }>(function VideoPlayer({ sourceUrl, startSec = 0 }, ref) {
  const player = useRef<YouTubePlayer | null>(null)
  const pendingSeek = useRef<number | null>(null)
  const [embedError, setEmbedError] = useState(false)
  const id = youtubeId(sourceUrl)
  const seconds = Math.max(0, Math.floor(startSec))
  const externalUrl = id ? `https://www.youtube.com/watch?v=${id}&t=${seconds}s` : undefined

  useImperativeHandle(ref, () => ({
    seekTo(value) {
      pendingSeek.current = Math.max(0, value)
      if (player.current) {
        player.current.seekTo(pendingSeek.current, true)
        player.current.playVideo()
        pendingSeek.current = null
      }
    },
  }), [])

  return <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-lg shadow-slate-900/10">
    {!embedError && id ? <div className="aspect-video"><YouTube videoId={id} title="Video de la fuente" className="h-full w-full" iframeClassName="h-full w-full" opts={{ width: '100%', height: '100%', playerVars: { rel: 0 } }} onReady={(event) => {
      player.current = event.target
      if (pendingSeek.current !== null) {
        event.target.seekTo(pendingSeek.current, true)
        event.target.playVideo()
        pendingSeek.current = null
      }
    }} onError={() => { player.current = null; setEmbedError(true) }} /></div> : <div className="grid aspect-video place-items-center p-8 text-center text-white"><div><p className="font-bold">No se puede reproducir este video aquí.</p>{externalUrl && <a href={externalUrl} target="_blank" rel="noreferrer" className="mt-4 inline-flex rounded-xl bg-white px-4 py-3 text-sm font-bold text-slate-900">Abrir en YouTube desde {formatTime(seconds)} ↗</a>}</div></div>}
  </div>
})
