import { useSyncExternalStore } from 'react'
import { SESSION_STORAGE_NOTICE, sessionViewStorage } from '../state/sessionViewStorage'

export function SessionViewStorageNotice() {
  const limited = useSyncExternalStore(sessionViewStorage.subscribe, sessionViewStorage.isMemoryOnly, () => false)
  return limited ? <aside className="session-storage-notice" role="status">{SESSION_STORAGE_NOTICE}</aside> : null
}
