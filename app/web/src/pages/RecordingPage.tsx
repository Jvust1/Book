import { useEffect, useRef, useState } from 'react'

import { deleteRecording, listRecordings, saveRecording, type SavedRecording } from '../state/recordingStore'

const preferredMimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']

const formatDuration = (seconds: number): string =>
  `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`

export function RecordingPage() {
  const [recording, setRecording] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [recordings, setRecordings] = useState<SavedRecording[]>([])
  const [error, setError] = useState<string | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)
  const urlsRef = useRef<string[]>([])

  const refresh = () => listRecordings().then(setRecordings).catch(() => setRecordings([]))

  useEffect(() => {
    void refresh()
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current)
      streamRef.current?.getTracks().forEach((track) => track.stop())
      urlsRef.current.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [])

  const start = async () => {
    setError(null)
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError('当前设备或浏览器不支持录音，请更新系统 WebView 后重试。')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = preferredMimeTypes.find((value) => MediaRecorder.isTypeSupported(value))
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      chunksRef.current = []
      recorder.ondataavailable = (event) => { if (event.data.size) chunksRef.current.push(event.data) }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        const now = Date.now()
        void saveRecording({
          id: `recording-${now}`,
          name: `课堂录音 ${new Date(now).toLocaleString('zh-CN')}`,
          createdAt: now,
          mimeType: blob.type,
          blob,
        }).then(refresh).catch(() => setError('录音已结束，但保存到本机失败。'))
        stream.getTracks().forEach((track) => track.stop())
      }
      streamRef.current = stream
      recorderRef.current = recorder
      recorder.start()
      setRecording(true)
      setSeconds(0)
      timerRef.current = window.setInterval(() => setSeconds((value) => value + 1), 1000)
    } catch {
      setError('无法访问麦克风。请在系统设置中允许 Book 使用麦克风后重试。')
    }
  }

  const stop = () => {
    if (!recorderRef.current) return
    recorderRef.current.stop()
    recorderRef.current = null
    streamRef.current = null
    setRecording(false)
    if (timerRef.current !== null) window.clearInterval(timerRef.current)
    timerRef.current = null
  }

  const remove = async (id: string) => {
    await deleteRecording(id)
    setRecordings((items) => items.filter((item) => item.id !== id))
  }

  return (
    <section className="page-stack recording-page">
      <header className="page-heading">
        <p className="eyebrow">Learning</p>
        <h1>课堂录音</h1>
        <p>录音只保存在本机，停止后可以回放或下载；不会自动上传。</p>
      </header>

      <section className="content-card recording-panel" aria-label="录音控制">
        <div className="recording-status" aria-live="polite">
          <span className={recording ? 'recording-dot is-live' : 'recording-dot'} aria-hidden="true" />
          <strong>{recording ? `正在录音 ${formatDuration(seconds)}` : '准备录音'}</strong>
        </div>
        {recording ? (
          <button className="primary-button" type="button" onClick={stop}>停止并保存</button>
        ) : (
          <button className="primary-button" type="button" onClick={() => void start()}>开始录音</button>
        )}
        {error ? <p className="recording-error" role="alert">{error}</p> : null}
      </section>

      <section className="list-stack" aria-label="已保存录音">
        <h2>本机录音</h2>
        {recordings.length === 0 ? <p className="secondary-text">还没有录音。</p> : recordings.map((item) => {
          const url = URL.createObjectURL(item.blob)
          urlsRef.current.push(url)
          return (
            <article className="content-card compact-card recording-item" key={item.id}>
              <div><h3>{item.name}</h3><p className="secondary-text">{item.mimeType}</p></div>
              <audio controls src={url}>当前浏览器不支持音频播放。</audio>
              <div className="card-footer">
                <a className="secondary-button" href={url} download={`${item.name}.webm`}>下载</a>
                <button className="text-button" type="button" onClick={() => void remove(item.id)}>删除</button>
              </div>
            </article>
          )
        })}
      </section>
    </section>
  )
}
