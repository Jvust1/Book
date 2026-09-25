export type SavedRecording = {
  id: string
  name: string
  createdAt: number
  mimeType: string
  blob: Blob
  durationMs?: number
  size?: number
  archived?: boolean
  interrupted?: boolean
}

const DB_NAME = 'book-recordings'
const STORE_NAME = 'recordings'

const openDatabase = (): Promise<IDBDatabase> =>
  new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('当前环境不支持本地录音存储'))
      return
    }
    const request = indexedDB.open(DB_NAME, 2)
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(STORE_NAME)) request.result.createObjectStore(STORE_NAME, { keyPath: 'id' })
      if (!request.result.objectStoreNames.contains('drafts')) request.result.createObjectStore('drafts', { keyPath: 'id' })
      if (!request.result.objectStoreNames.contains('chunks')) request.result.createObjectStore('chunks', { keyPath: ['id', 'sequence'] })
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('无法打开录音存储'))
  })

export const listRecordings = async (): Promise<SavedRecording[]> => {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).getAll()
    request.onsuccess = () => {
      resolve((request.result as SavedRecording[]).sort((a, b) => b.createdAt - a.createdAt))
      db.close()
    }
    request.onerror = () => {
      reject(request.error ?? new Error('无法读取录音'))
      db.close()
    }
  })
}

export const saveRecording = async (recording: SavedRecording): Promise<void> => {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME, 'drafts', 'chunks'], 'readwrite')
    transaction.objectStore(STORE_NAME).put(recording)
    transaction.objectStore('drafts').delete(recording.id)
    transaction.objectStore('chunks').delete(IDBKeyRange.bound([recording.id, 0], [recording.id, Number.MAX_SAFE_INTEGER]))
    transaction.oncomplete = () => { db.close(); resolve() }
    transaction.onabort = () => { db.close(); reject(transaction.error ?? new Error('无法保存录音')) }
  })
}

export const checkpointRecording = async (draft: Omit<SavedRecording, 'blob'>, chunk: Blob, sequence: number): Promise<void> => {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(['drafts', 'chunks'], 'readwrite')
    tx.objectStore('drafts').put(draft)
    tx.objectStore('chunks').put({ id: draft.id, sequence, blob: chunk })
    tx.oncomplete = () => { db.close(); resolve() }
    tx.onabort = () => { db.close(); reject(tx.error ?? new Error('录音备份失败')) }
  })
}

export const recoverRecordings = async (activeId?: string): Promise<void> => {
  const db = await openDatabase()
  const drafts = await new Promise<SavedRecording[]>((resolve, reject) => {
    const request = db.transaction('drafts').objectStore('drafts').getAll()
    request.onsuccess = () => resolve(request.result as SavedRecording[])
    request.onerror = () => reject(request.error)
  })
  try {
    for (const draft of drafts) {
      if (draft.id === activeId) continue
      const chunks = await new Promise<Array<{ blob: Blob }>>((resolve, reject) => {
        const request = db.transaction('chunks').objectStore('chunks').getAll(IDBKeyRange.bound([draft.id, 0], [draft.id, Number.MAX_SAFE_INTEGER]))
        request.onsuccess = () => resolve(request.result)
        request.onerror = () => reject(request.error)
      })
      const blob = new Blob(chunks.map(chunk => chunk.blob), { type: draft.mimeType })
      if (blob.size) await saveRecording({ ...draft, blob, size: blob.size, interrupted: true })
    }
  } finally { db.close() }
}

export const deleteRecording = async (id: string): Promise<void> => {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).delete(id)
    request.onsuccess = () => { db.close(); resolve() }
    request.onerror = () => { db.close(); reject(request.error ?? new Error('无法删除录音')) }
  })
}
