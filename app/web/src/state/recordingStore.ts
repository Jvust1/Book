export type SavedRecording = {
  id: string
  name: string
  createdAt: number
  mimeType: string
  blob: Blob
}

const DB_NAME = 'book-recordings'
const STORE_NAME = 'recordings'

const openDatabase = (): Promise<IDBDatabase> =>
  new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('当前环境不支持本地录音存储'))
      return
    }
    const request = indexedDB.open(DB_NAME, 1)
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE_NAME, { keyPath: 'id' })
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
    const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put(recording)
    request.onsuccess = () => { db.close(); resolve() }
    request.onerror = () => { db.close(); reject(request.error ?? new Error('无法保存录音')) }
  })
}

export const deleteRecording = async (id: string): Promise<void> => {
  const db = await openDatabase()
  return new Promise((resolve, reject) => {
    const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).delete(id)
    request.onsuccess = () => { db.close(); resolve() }
    request.onerror = () => { db.close(); reject(request.error ?? new Error('无法删除录音')) }
  })
}
