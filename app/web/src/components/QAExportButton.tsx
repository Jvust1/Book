import { useLayoutEffect, useRef, useState } from 'react'
import type { QAResponse } from '../api/types'
import { buildQAEvidenceZip, QA_EXPORT_ERROR, QA_EXPORT_FILENAME } from '../export/qaEvidenceZip'

interface Props {
  courseId: string
  bookId: string | null
  question: string | null
  content: string
  response: QAResponse
  route: string
  disabled: boolean
}

export function QAExportButton({ courseId, bookId, question, content, response, route, disabled }: Props) {
  const [status, setStatus] = useState<'idle' | 'working' | 'requested' | 'error'>('idle')
  const generation = useRef(0)
  const busy = useRef(false)
  const downloadUrl = useRef<string | null>(null)
  const revokeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const releaseUrl = () => {
    if (revokeTimer.current !== null) clearTimeout(revokeTimer.current)
    revokeTimer.current = null
    if (downloadUrl.current !== null) URL.revokeObjectURL(downloadUrl.current)
    downloadUrl.current = null
  }

  useLayoutEffect(() => {
    generation.current++
    busy.current = false
    setStatus('idle')
    return () => {
      generation.current++
      busy.current = false
      releaseUrl()
    }
  }, [courseId, bookId, question, content, response, route, disabled])

  const exportAnswer = async () => {
    if (disabled || busy.current || !bookId || question === null) return
    const owner = generation.current
    busy.current = true
    setStatus('working')
    try {
      const bytes = await buildQAEvidenceZip({ courseId, bookId, question, content, response })
      if (owner !== generation.current) return
      releaseUrl()
      // Own a distinct ArrayBuffer; never hand a shared buffer to the download API.
      downloadUrl.current = URL.createObjectURL(new Blob([new Uint8Array(bytes).buffer], { type: 'application/zip' }))
      const anchor = document.createElement('a')
      anchor.href = downloadUrl.current
      anchor.download = QA_EXPORT_FILENAME
      document.body.append(anchor)
      try { anchor.click() } finally { anchor.remove() }
      // Allow the browser to consume the URL, then release it; cleanup also revokes on route/unmount.
      revokeTimer.current = setTimeout(releaseUrl, 1000)
      setStatus('requested')
    } catch {
      if (owner === generation.current) {
        releaseUrl()
        setStatus('error')
      }
    } finally {
      if (owner === generation.current) busy.current = false
    }
  }

  return (
    <div>
      <button className="secondary-button" type="button"
        disabled={disabled || status === 'working' || !bookId || question === null} onClick={exportAnswer}>
        {status === 'working' ? '正在生成问答证据…' : '导出本次问答 ZIP'}
      </button>
      <p className="secondary-text">仅下载本次问题、AI 回答与引用定位，不额外读取教材或 PDF。</p>
      {status === 'requested' ? <p role="status">已交给浏览器下载；文件不会自动上传。</p> : null}
      {status === 'error' ? <p role="alert">{QA_EXPORT_ERROR}</p> : null}
    </div>
  )
}
