import { useRef, useState } from 'react'

import { ApiError, bookApi } from '../api/client'
import type { StudyExportResponse } from '../api/types'
import { isNativeRecorder, nativeCommand } from '../state/recorder'

const message = (error: unknown) => error instanceof ApiError ? error.message : '同步包处理失败，请重试'

export function SyncPage() {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const exportProgress = async () => {
    setBusy(true); setError(''); setNotice('')
    try {
      const payload = await bookApi.exportStudy()
      const content = JSON.stringify(payload, null, 2)
      const filename = `book-study-progress-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
      if (isNativeRecorder()) {
        await nativeCommand('export-data', { content, name: filename })
        setNotice(`已导出 ${payload.records.length} 条学习进度。请把文件传到另一台设备后导入。`)
        return
      }
      const blob = new Blob([content], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      URL.revokeObjectURL(url)
      setNotice(`已导出 ${payload.records.length} 条学习进度。请把文件传到另一台设备后导入。`)
    } catch (reason) { setError(message(reason)) }
    finally { setBusy(false) }
  }

  const importProgress = async (file: File) => {
    setBusy(true); setError(''); setNotice('')
    try {
      const payload = JSON.parse(await file.text()) as StudyExportResponse
      if (payload.schema_version !== 'book_study_sync_v1' || !Array.isArray(payload.records)) throw new Error('不是有效的 Book 学习进度包')
      const result = await bookApi.importStudy(payload)
      setNotice(`导入完成：${result.imported_count} 条已更新，${result.skipped_count} 条保持原值。`)
    } catch (reason) { setError(message(reason)) }
    finally { setBusy(false); if (input.current) input.current.value = '' }
  }

  return (
    <section className="page-stack">
      <header className="page-heading">
        <p className="eyebrow">TRANSFER · 手动同步</p>
        <h1>学习进度同步</h1>
        <p>导出一个小文件，用聊天工具、数据线或局域网传到另一台设备，再导入即可。</p>
      </header>
      <section className="content-card" style={{ display: 'grid', gap: 16, maxWidth: 720 }}>
        <h2>不需要登录，也不会上传数据</h2>
        <p className="secondary-text">同步包只包含学习进度，不包含录音和教材文件。导入时按更新时间合并，较新的记录优先。</p>
        <div className="recording-actions">
          <button className="primary-button" disabled={busy} onClick={() => void exportProgress()}>导出学习进度</button>
          <button className="secondary-button" disabled={busy} onClick={() => input.current?.click()}>导入学习进度</button>
          <input ref={input} type="file" accept="application/json,.json" hidden onChange={event => {
            const file = event.target.files?.[0]
            if (file) void importProgress(file)
          }} />
        </div>
        {notice ? <p role="status" className="recording-notice">{notice}</p> : null}
        {error ? <p role="alert" className="recording-error">{error}</p> : null}
      </section>
    </section>
  )
}
