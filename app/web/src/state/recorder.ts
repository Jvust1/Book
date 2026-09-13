import { useEffect, useState } from 'react'
import { checkpointRecording, listRecordings, recoverRecordings, saveRecording, type SavedRecording } from './recordingStore'

type Status = 'idle' | 'requesting' | 'recording' | 'paused' | 'saving' | 'unsaved'
export type RecorderState = { status: Status; durationMs: number; level: number; name: string; error: string | null }
export type Recording = Omit<SavedRecording, 'blob'> & { blob?: Blob; native?: boolean }
declare global { interface Window { BookNative?: { request: (json: string) => void }; BookDesktop?: { platform: string } } }
export const isNativeRecorder = () => !!window.BookNative
export const isDesktopRecorder = () => !!window.BookDesktop
let state: RecorderState = { status: 'idle', durationMs: 0, level: 0, name: '', error: null }
const listeners = new Set<() => void>()
const update = (patch: Partial<RecorderState>) => { state = { ...state, ...patch }; listeners.forEach(fn => fn()) }
let poll: ReturnType<typeof setInterval> | undefined
let polling = false
let recorder: MediaRecorder | null = null
let stream: MediaStream | null = null
let chunks: Blob[] = []
let activeId: string | undefined
let accumulated = 0
let segmentStart = 0
let audioContext: AudioContext | null = null
let analyser: AnalyserNode | null = null
let checkpointQueue: Promise<void> = Promise.resolve()
let pendingSave: SavedRecording | null = null
let starting = false
let savePromise: Promise<void> | null = null
const pending = new Map<string, { resolve: (value: unknown) => void; reject: (error: Error) => void; timer: ReturnType<typeof setTimeout> }>()
let sequence = 0
window.addEventListener('book-native-response', event => {
  const { id, result, error } = (event as CustomEvent).detail
  const request = pending.get(id)
  if (!request) return
  clearTimeout(request.timer); pending.delete(id)
  if (error) request.reject(new Error(error)); else request.resolve(result)
})
export function nativeCommand<T = unknown>(action: string, args: Record<string, unknown> = {}): Promise<T> {
  const id = String(++sequence)
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('操作未收到回应，请返回录音页查看状态。')) }, ['export', 'export-web', 'start'].includes(action) ? 180000 : 15000)
    pending.set(id, { resolve: value => resolve(value as T), reject, timer })
    try { window.BookNative!.request(JSON.stringify({ ...args, id, action })) }
    catch (error) { clearTimeout(timer); pending.delete(id); reject(error) }
  })
}
const duration = () => accumulated + (recorder?.state === 'recording' ? performance.now() - segmentStart : 0)
async function tick() {
  if (polling) return
  polling = true
  try {
    if (isNativeRecorder()) {
      if (!starting) update(await nativeCommand<RecorderState>('state'))
    } else if (recorder && ['recording', 'paused'].includes(state.status)) {
      let level = 0
      if (analyser && recorder.state === 'recording') {
        const data = new Uint8Array(analyser.fftSize); analyser.getByteTimeDomainData(data)
        level = Math.min(1, Math.sqrt(data.reduce((sum, value) => sum + (value - 128) ** 2, 0) / data.length) / 45)
      }
      update({ durationMs: duration(), level })
    }
  } catch (error) { update({ error: message(error) }) }
  finally { polling = false }
}
export function useRecorder() {
  const [value, setValue] = useState(state)
  useEffect(() => {
    const listener = () => setValue(state)
    listeners.add(listener)
    if (!poll) poll = setInterval(() => { void tick() }, 300)
    void tick()
    return () => { listeners.delete(listener); if (!listeners.size && poll) { clearInterval(poll); poll = undefined } }
  }, [])
  return value
}
const message = (error: unknown) => error instanceof Error ? error.message : '操作失败，请重试'
function releaseMedia() {
  stream?.getTracks().forEach(track => track.stop()); stream = null
  void audioContext?.close().catch(() => {}); audioContext = null; analyser = null; recorder = null
}
export async function startRecording(name: string) {
  if (isDesktopRecorder()) {
    update({ error: '桌面版不启用麦克风录音，请在手机端录音后导出。' })
    return
  }
  if (state.status !== 'idle' || starting) return
  starting = true; update({ status: 'requesting', error: null, name, durationMs: 0 })
  try {
    if (isNativeRecorder()) {
      await nativeCommand('start', { name })
      // The service starts asynchronously; wait until it has published a state.
      await new Promise(resolve => setTimeout(resolve, 350))
      update(await nativeCommand<RecorderState>('state'))
      return
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') throw new Error('当前浏览器不支持录音，请使用新版浏览器或 Android App。')
    stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'].find(type => MediaRecorder.isTypeSupported(type))
    const localRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    recorder = localRecorder; chunks = []; accumulated = 0; activeId = crypto.randomUUID()
    const id = activeId, createdAt = Date.now()
    let chunkNumber = 0
    checkpointQueue = Promise.resolve()
    localRecorder.ondataavailable = event => {
      if (!event.data.size) return
      chunks.push(event.data)
      const draft = { id, name, createdAt, durationMs: duration(), mimeType: localRecorder.mimeType || event.data.type }
      const index = chunkNumber++
      checkpointQueue = checkpointQueue.then(() => checkpointRecording(draft, event.data, index)).catch(() => {
        update({ error: '临时备份失败，请停止录音并导出，避免关闭页面。' })
      })
    }
    localRecorder.onstop = () => {
      const elapsed = Math.max(accumulated, state.durationMs)
      update({ status: 'saving', durationMs: elapsed, level: 0 })
      const blob = new Blob(chunks, { type: localRecorder.mimeType || chunks[0]?.type || 'audio/webm' })
      pendingSave = { id, name, createdAt, durationMs: elapsed, blob, mimeType: blob.type, size: blob.size }
      releaseMedia(); void retrySave()
    }
    localRecorder.onerror = () => {
      update({ error: '麦克风连接中断，正在保存已经录到的音频。' })
      if (localRecorder.state !== 'inactive') stopRecording()
    }
    stream.getAudioTracks().forEach(track => track.addEventListener('ended', () => { if (localRecorder.state !== 'inactive') stopRecording() }))
    try { audioContext = new AudioContext(); analyser = audioContext.createAnalyser(); analyser.fftSize = 256; audioContext.createMediaStreamSource(stream).connect(analyser) } catch { /* Audio capture still works without a meter. */ }
    localRecorder.start(3000); segmentStart = performance.now()
    update({ status: 'recording' })
  } catch (error) {
    releaseMedia(); update({ status: 'idle', error: (error as DOMException)?.name === 'NotAllowedError' ? '麦克风权限未开启，请允许录音后重试。' : message(error) })
  } finally { starting = false }
}
export async function pauseRecording() {
  try {
    if (isNativeRecorder()) { await nativeCommand(state.status === 'paused' ? 'resume' : 'pause'); await tick(); return }
    if (recorder?.state === 'recording') {
      accumulated = duration(); recorder.pause(); update({ status: 'paused', durationMs: accumulated, level: 0 })
    } else if (recorder?.state === 'paused') {
      recorder.resume(); segmentStart = performance.now(); update({ status: 'recording' })
    }
  } catch (error) { update({ error: message(error) }) }
}
export function stopRecording() {
  if (isNativeRecorder()) { void nativeCommand('stop').then(() => tick()).catch(error => update({ error: message(error) })); return }
  if (recorder && recorder.state !== 'inactive') {
    accumulated = duration(); update({ status: 'saving', durationMs: accumulated }); recorder.stop()
  }
}
export function retrySave(): Promise<void> {
  if (savePromise) return savePromise
  if (!pendingSave) return Promise.resolve()
  const recording = pendingSave
  if (!recording.blob.size) {
    pendingSave = null; activeId = undefined; chunks = []
    update({ status: 'idle', error: '没有收到音频，请检查麦克风后重新录制。' })
    return Promise.resolve()
  }
  savePromise = (async () => {
    update({ status: 'saving' })
    try {
      await checkpointQueue; await saveRecording(recording)
      pendingSave = null; activeId = undefined; chunks = []
      update({ status: 'idle', error: null })
    } catch (error) { update({ status: 'unsaved', error: '保存失败：' + message(error) + ' 音频仍在本页，可重试或先导出。' }) }
    finally { savePromise = null }
  })()
  return savePromise
}
export const extension = (mime: string) => mime.includes('mp4') ? 'm4a' : mime.includes('wav') ? 'wav' : mime.includes('ogg') ? 'ogg' : 'webm'
export function downloadBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob), link = document.createElement('a')
  link.href = url; link.download = `${name.replace(/[\\/:*?"<>|]/g, '_')}.${extension(blob.type)}`
  document.body.appendChild(link); link.click(); link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 60000)
}
let exportingBlob = false
export async function exportBlob(blob: Blob, name: string) {
  if (!isNativeRecorder()) { downloadBlob(blob, name); return }
  if (exportingBlob) throw new Error('已有导出正在进行')
  exportingBlob = true
  try {
    const { token } = await nativeCommand<{ token: string }>('begin-web-export', { name, mimeType: blob.type })
    for (let offset = 0; offset < blob.size; offset += 98304) {
      const chunk = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(String(reader.result).split(',')[1])
        reader.onerror = () => reject(reader.error)
        reader.readAsDataURL(blob.slice(offset, offset + 98304))
      })
      await nativeCommand('append-web-export', { token, offset, chunk })
    }
    await nativeCommand('export-web', { token, size: blob.size })
  } finally { exportingBlob = false }
}
export const exportUnsaved = () => { if (pendingSave) void exportBlob(pendingSave.blob, pendingSave.name).catch(error => update({ error: message(error) })) }
export async function getRecordings(): Promise<Recording[]> {
  await recoverRecordings(activeId)
  const web = await listRecordings()
  const native = isNativeRecorder() ? await nativeCommand<Recording[]>('list') : []
  return [...native, ...web].sort((a, b) => b.createdAt - a.createdAt)
}
export async function changeRecording(item: Recording, patch: { name?: string; archived?: boolean }) {
  if (item.native) await nativeCommand(patch.name !== undefined ? 'rename' : 'archive', { recordingId: item.id, ...patch })
  else if (item.blob) await saveRecording({ ...item, ...patch, blob: item.blob })
}
window.addEventListener('beforeunload', event => {
  if (!isNativeRecorder() && state.status !== 'idle') { event.preventDefault(); event.returnValue = '' }
})
window.addEventListener('pagehide', () => { if (!isNativeRecorder()) stopRecording() })
