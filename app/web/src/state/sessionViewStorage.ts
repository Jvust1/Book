/** Short-lived view metadata/verified QA only. Never StudyRecord, PDF bytes or search bodies. */
export const MAX_SESSION_VIEW_CHARS = 2 * 1024 * 1024
export const MAX_MEMORY_VIEW_CHARS = 4 * 1024 * 1024
export const MAX_MEMORY_VIEW_ENTRIES = 64
export const SESSION_STORAGE_NOTICE = '浏览器会话存储不可用，当前仅在页面内存临时保留近期返回位置和问答；刷新或关闭后会丢失。'

type Backend = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>
interface Limits { maxEntryChars: number; maxChars: number; maxEntries: number }
const defaults: Limits = { maxEntryChars: MAX_SESSION_VIEW_CHARS, maxChars: MAX_MEMORY_VIEW_CHARS, maxEntries: MAX_MEMORY_VIEW_ENTRIES }
const viewKey = (key: string) => /^book:(qa-session|search-view|section-view):/.test(key)

export function createSessionViewStorage(backend: () => Backend = () => window.sessionStorage, limits: Limits = defaults) {
  const recent = new Map<string, string>()
  const listeners = new Set<() => void>()
  let characters = 0
  let memoryOnly = false
  const forget = (key: string) => {
    characters -= recent.get(key)?.length ?? 0
    recent.delete(key)
  }
  const remember = (key: string, value: string | null) => {
    forget(key)
    if (value === null || value.length > limits.maxEntryChars || value.length > limits.maxChars) return
    while (recent.size && (recent.size >= limits.maxEntries || characters + value.length > limits.maxChars)) {
      forget(recent.keys().next().value!)
    }
    if (limits.maxEntries < 1) return
    recent.set(key, value)
    characters += value.length
  }
  const useMemory = () => {
    if (memoryOnly) return
    memoryOnly = true
    // A storage read can occur during initial rendering. Notify after that render.
    queueMicrotask(() => listeners.forEach(listener => listener()))
  }
  const eraseStored = (key: string) => {
    try { backend().removeItem(key) } catch { useMemory() }
  }
  return {
    read(key: string): string | null {
      if (!viewKey(key)) return null
      if (!memoryOnly) {
        try {
          const raw = backend().getItem(key)
          if (raw !== null && raw.length > limits.maxEntryChars) {
            forget(key); eraseStored(key); return null
          }
          remember(key, raw)
          return raw
        } catch { useMemory() }
      }
      const value = recent.get(key) ?? null
      remember(key, value)
      return value
    },
    write(key: string, value: string): void {
      if (!viewKey(key)) return
      if (value.length > limits.maxEntryChars || value.length > limits.maxChars) {
        forget(key); useMemory(); eraseStored(key); return
      }
      remember(key, value)
      if (!memoryOnly) {
        try { backend().setItem(key, value); return } catch { useMemory() }
      }
      // Never resurrect an older durable snapshot after a newer in-memory write.
      eraseStored(key)
    },
    remove(key: string): void {
      if (!viewKey(key)) return
      forget(key)
      eraseStored(key)
    },
    isMemoryOnly: () => memoryOnly,
    subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener) } },
  }
}

export const sessionViewStorage = createSessionViewStorage()
