import { useEffect, useMemo, useState } from 'react'
import {
  changeRecording, exportBlob, exportUnsaved, getRecordings, isDesktopRecorder, isNativeRecorder,
  nativeCommand, pauseRecording, retrySave, startRecording, stopRecording, useRecorder, type Recording,
} from '../state/recorder'
import { Icon } from '../components/Icon'

export const formatDuration = (ms: number) => {
  const seconds = Math.floor(ms / 1000)
  const hours = Math.floor(seconds / 3600)
  return (hours ? String(hours).padStart(2, '0') + ':' : '') +
    String(Math.floor(seconds / 60) % 60).padStart(2, '0') + ':' + String(seconds % 60).padStart(2, '0')
}
const formatSize = (size: number) => size < 1048576 ? (size / 1024).toFixed(0) + ' KB' : (size / 1048576).toFixed(1) + ' MB'
const errorMessage = (error: unknown) => error instanceof Error ? error.message : '操作失败，请重试'

function RecordingItem({ item, onChange }: { item: Recording; onChange: () => void }) {
  const [renaming, setRenaming] = useState(false)
  const [name, setName] = useState(item.name)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [url, setUrl] = useState('')
  const [rate, setRate] = useState('1')
  useEffect(() => {
    const audioUrl = item.native ? '/__recordings/' + item.id : item.blob ? URL.createObjectURL(item.blob) : ''
    setUrl(audioUrl)
    return () => { if (audioUrl.startsWith('blob:')) URL.revokeObjectURL(audioUrl) }
  }, [item.id, item.native, item.blob])
  const action = async (fn: () => Promise<unknown>, done?: string) => {
    setBusy(true); setNotice('')
    try { await fn(); if (done) setNotice(done) }
    catch (error) { setNotice(errorMessage(error)) }
    finally { setBusy(false) }
  }
  return (
    <article className="recording-item content-card compact-card">
      <div className="recording-item-heading">
        <span className="audio-cover"><Icon name="audio" /></span>
        <div className="recording-item-title">
          <h3>{item.name}</h3>
          <p className="secondary-text">{new Date(item.createdAt).toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
        </div>
        <span className="count-chip">{formatDuration(item.durationMs || 0)}</span>
      </div>
      {item.interrupted ? <p className="recording-notice">这段录音曾中断，已恢复保存到本机的部分。</p> : null}
      <audio controls preload="metadata" src={url} aria-label={'播放 ' + item.name}
        onPlay={event => {
          document.querySelectorAll('audio').forEach(audio => { if (audio !== event.currentTarget) audio.pause() })
          event.currentTarget.playbackRate = Number(rate)
        }}
        onError={() => setNotice('音频暂时无法播放，可先导出原文件。')} />
      <div className="recording-item-tools">
        <label className="speed-select">播放速度
          <select aria-label={'播放速度 ' + item.name} value={rate} onChange={event => {
            setRate(event.target.value)
            const audio = event.currentTarget.closest('article')?.querySelector('audio')
            if (audio) audio.playbackRate = Number(event.target.value)
          }}>
            {[0.75, 1, 1.25, 1.5, 2].map(value => <option key={value} value={value}>{value}×</option>)}
          </select>
        </label>
        <span className="secondary-text">{formatSize(item.size ?? item.blob?.size ?? 0)}</span>
      </div>
      {renaming ? (
        <form className="rename-form" onSubmit={event => {
          event.preventDefault()
          if (!name.trim()) { setNotice('请填写录音名称'); return }
          void action(async () => { await changeRecording(item, { name: name.trim() }); setRenaming(false); onChange() })
        }}>
          <input aria-label="新的录音名称" value={name} maxLength={120} onChange={event => setName(event.target.value)} />
          <button className="primary-button" disabled={busy}>保存名称</button>
          <button className="text-button" type="button" onClick={() => setRenaming(false)}>取消</button>
        </form>
      ) : (
        <div className="recording-item-tools">
          <button className="secondary-button" disabled={busy} onClick={() => void action(async () => {
            if (item.native) await nativeCommand('export', { recordingId: item.id })
            else if (item.blob) await exportBlob(item.blob, item.name)
          }, isNativeRecorder() ? '已导出录音' : '已发起下载')}>
            <Icon name="download" />导出音频
          </button>
          {item.native ? <button className="text-button" disabled={busy} onClick={() => void action(() => nativeCommand('share', { recordingId: item.id }))}>分享</button> : null}
          <button className="text-button" disabled={busy} onClick={() => { setName(item.name); setRenaming(true) }}>重命名</button>
          <button className="text-button" disabled={busy} onClick={() => void action(async () => {
            await changeRecording(item, { archived: !item.archived }); onChange()
          })}>{item.archived ? '恢复到列表' : '归档'}</button>
        </div>
      )}
      {notice ? <p role="status" className="recording-notice">{notice}</p> : null}
    </article>
  )
}

export function RecordingPage() {
  const session = useRecorder()
  const [name, setName] = useState('')
  const [recordings, setRecordings] = useState<Recording[]>([])
  const [query, setQuery] = useState('')
  const [archived, setArchived] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const active = session.status === 'recording' || session.status === 'paused'
  const busy = session.status === 'requesting' || session.status === 'saving'
  const desktop = isDesktopRecorder()
  const refresh = async () => {
    try { setRecordings(await getRecordings()); setError(null) }
    catch (reason) { setError('录音列表读取失败：' + errorMessage(reason)) }
    finally { setLoading(false) }
  }
  useEffect(() => { if (session.status === 'idle') void refresh() }, [session.status])
  useEffect(() => {
    const fn = () => { if (document.visibilityState === 'visible') void refresh() }
    document.addEventListener('visibilitychange', fn)
    return () => document.removeEventListener('visibilitychange', fn)
  }, [])
  const visible = useMemo(() => recordings.filter(item => !!item.archived === archived && item.name.toLowerCase().includes(query.toLowerCase())), [recordings, archived, query])
  const total = recordings.reduce((sum, item) => sum + (item.durationMs || 0), 0)
  const labels = { idle: '准备就绪', requesting: '正在开启麦克风…', recording: '正在录音', paused: '已暂停', saving: '正在保存…', unsaved: '等待保存' }
  return (
    <section className="page-stack recording-page">
      <header className="page-heading">
        <p className="eyebrow">CAPTURE · 每一个重要时刻</p>
        <h1>课堂录音</h1>
        <p>专心听讲，让声音留下来。</p>
      </header>
      <div className="recording-workspace">
        <section className="recording-panel" aria-label="录音控制">
          <div className="recording-panel-top"><span className="eyebrow">VOICE RECORDER</span><Icon name="mic" /></div>
          <div className="recording-status" role="status">
            <span className={'recording-dot' + (session.status === 'recording' ? ' is-live' : '')} />
            <strong>{labels[session.status]}</strong>
          </div>
          <div className="recording-clock" aria-label="录音时长">{formatDuration(session.durationMs)}</div>
          <div className="waveform" aria-label="麦克风音量">
            {Array.from({ length: 41 }, (_, index) => <i key={index}
              style={{ height: (5 + session.level * (18 + 55 * Math.abs(Math.sin(index * 1.7)))) + 'px' }} />)}
          </div>
          {active ? <p className="recording-session-name">{session.name}</p> : (
            <label className="recording-name-label">录音名称
              <input value={name} maxLength={120} disabled={busy || session.status === 'unsaved'}
                onChange={event => setName(event.target.value)} placeholder="例如：泛函分析 · 第一课" />
            </label>
          )}
          <div className="recording-actions">
            {active ? <>
              <button className="secondary-button" onClick={() => void pauseRecording()}><Icon name={session.status === 'paused' ? 'play' : 'pause'} />{session.status === 'paused' ? '继续录音' : '暂停录音'}</button>
              <button className="primary-button stop-button" onClick={stopRecording}><Icon name="stop" />停止并保存</button>
            </> : session.status === 'unsaved' ? <>
              <button className="primary-button" onClick={() => void retrySave()}>重试保存</button>
              <button className="secondary-button" onClick={exportUnsaved}>先导出音频</button>
            </> : <button className="primary-button record-button" disabled={busy || desktop}
              onClick={() => void startRecording(name.trim() || '课堂录音 ' + new Date().toLocaleString('zh-CN'))}>
                <Icon name="mic" />{desktop ? '请用手机录音' : busy ? labels[session.status] : '开始录音'}
              </button>}
          </div>
          <p className="recording-hint">{desktop
            ? '电脑端不申请麦克风；请在手机端录音，学习进度在同一账号/同步包中保持一致。'
            : isNativeRecorder()
            ? '支持锁屏和切换应用；通知栏可暂停或停止。'
            : '浏览器录音时请保持此页面打开；切换 App 内页面仍可继续。'}</p>
          {session.error ? <p className="recording-error" role="alert">{session.error}</p> : null}
        </section>
        <aside className="recording-guide">
          <div><p className="eyebrow">声音笔记</p><h2>{desktop ? '手机负责记录' : '把课堂装进口袋'}</h2><p>{desktop ? '桌面端专注阅读、公式和学习进度；需要录音时请使用手机端，完成后再把音频交给 ChatGPT 整理。' : '回放难点，跟上思路。录完可直接导出原音频，自行整理或交给 ChatGPT 处理。'}</p></div>
          <div className="recording-stats"><div><strong>{recordings.length}</strong><span>段本机录音</span></div><div><strong>{formatDuration(total)}</strong><span>累计时长</span></div></div>
          <p className="recording-privacy"><Icon name="shield" />录音保存在本机；由你决定分享。</p>
        </aside>
      </div>
      <section className="page-stack" aria-label="已保存录音">
        <div className="recording-list-heading"><h2>{archived ? '已归档录音' : '本机录音'}</h2>
          <button className="text-button" onClick={() => setArchived(!archived)}>{archived ? '返回录音列表' : '查看归档'}</button>
        </div>
        <input className="recording-search" type="search" aria-label="搜索录音" placeholder="按名称查找录音…" value={query} onChange={event => setQuery(event.target.value)} />
        {error ? <div className="status-panel" role="alert"><p>{error}</p><button className="secondary-button" onClick={() => void refresh()}>重新读取</button></div> : null}
        {loading ? <p role="status">正在读取本机录音…</p> : !visible.length ? (
          <div className="recording-empty"><Icon name="audio" /><h3>{query ? '没有找到匹配录音' : archived ? '暂无归档录音' : '第一段录音，从这里开始'}</h3><p>{query ? '试试其他名称。' : '点击上方麦克风，记录今天的新收获。'}</p></div>
        ) : <div className="recording-grid">{visible.map(item => <RecordingItem key={item.id} item={item} onChange={() => void refresh()} />)}</div>}
      </section>
    </section>
  )
}
