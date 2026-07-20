import { useEffect, useRef, useState } from 'react'
import { getDocument, GlobalWorkerOptions, type PDFDocumentProxy } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import { getPdfFile, getPublicPdfFile } from '../api/resources'
import type { SearchEvidence } from '../types'

GlobalWorkerOptions.workerSrc = workerUrl

export function PdfEvidenceViewer({ evidence, onClose, publicMode = false }: { evidence: SearchEvidence; onClose: () => void; publicMode?: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [document, setDocument] = useState<PDFDocumentProxy>()
  const [page, setPage] = useState(evidence.pageStart || 1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    const fileRequest = publicMode ? getPublicPdfFile(evidence.resourceId) : getPdfFile(evidence.resourceId)
    fileRequest
      .then((buffer) => getDocument({ data: new Uint8Array(buffer) }).promise)
      .then((pdf) => {
        if (!cancelled) {
          setDocument(pdf)
          setPage(Math.min(Math.max(evidence.pageStart || 1, 1), pdf.numPages))
        }
      })
      .catch(() => !cancelled && setError('No fue posible abrir el documento.'))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [evidence, publicMode])

  useEffect(() => {
    if (!document || !canvasRef.current) return
    let cancelled = false
    let renderTask: ReturnType<Awaited<ReturnType<PDFDocumentProxy['getPage']>>['render']> | undefined
    document.getPage(page).then((pdfPage) => {
      if (cancelled || !canvasRef.current) return
      const viewport = pdfPage.getViewport({ scale: 1.35 })
      const ratio = window.devicePixelRatio || 1
      const canvas = canvasRef.current
      const context = canvas.getContext('2d')
      if (!context) return
      canvas.width = Math.floor(viewport.width * ratio)
      canvas.height = Math.floor(viewport.height * ratio)
      canvas.style.width = `${Math.floor(viewport.width)}px`
      canvas.style.height = `${Math.floor(viewport.height)}px`
      renderTask = pdfPage.render({
        canvas,
        canvasContext: context,
        viewport,
        transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
      })
      return renderTask.promise
    }).catch((reason) => {
      if (reason?.name !== 'RenderingCancelledException') setError('No fue posible renderizar esta página.')
    })
    return () => {
      cancelled = true
      renderTask?.cancel()
    }
  }, [document, page])

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/70 p-3 backdrop-blur-sm sm:p-6" role="dialog" aria-modal="true">
      <div className="mx-auto flex h-full max-w-7xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-3">
          <div className="min-w-0">
            <p className="truncate font-semibold">{evidence.title}</p>
            <p className="text-xs text-slate-500">Fuente verificable · página {page} de {document?.numPages || '…'}</p>
          </div>
          <button onClick={onClose} className="rounded-xl bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-600">Cerrar</button>
        </header>
        <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-h-0 overflow-auto bg-slate-200 p-4">
            {loading && <div className="grid h-full place-items-center text-sm text-slate-500">Cargando documento…</div>}
            {error && <div className="m-auto max-w-md rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</div>}
            <canvas ref={canvasRef} className="mx-auto bg-white shadow-lg" />
          </div>
          <aside className="min-h-0 overflow-y-auto border-l border-slate-200 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Fragmento citado</p>
            <mark className="mt-3 block rounded-xl bg-amber-100 p-4 text-sm leading-7 text-slate-800">{evidence.text}</mark>
            <p className="mt-3 text-xs leading-5 text-slate-500">El resaltado corresponde al fragmento extraído de esta página. Compáralo siempre con el documento original antes de citarlo.</p>
            <div className="mt-6 flex items-center justify-between gap-2">
              <button disabled={page <= 1} onClick={() => setPage((current) => current - 1)} className="rounded-xl border border-slate-300 px-3 py-2 text-sm disabled:opacity-40">← Anterior</button>
              <span className="text-sm font-semibold">{page}/{document?.numPages || '…'}</span>
              <button disabled={!document || page >= document.numPages} onClick={() => setPage((current) => current + 1)} className="rounded-xl border border-slate-300 px-3 py-2 text-sm disabled:opacity-40">Siguiente →</button>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
