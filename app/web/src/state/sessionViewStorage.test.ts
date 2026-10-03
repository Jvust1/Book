import { describe, expect, it, vi } from 'vitest'
import { createSessionViewStorage } from './sessionViewStorage'

function fixture(limits = { maxEntryChars: 20, maxChars: 30, maxEntries: 2 }) {
  const disk = new Map<string, string>()
  const backend = { getItem: vi.fn((key: string) => disk.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => { disk.set(key, value) }),
    removeItem: vi.fn((key: string) => { disk.delete(key) }) }
  return { store: createSessionViewStorage(() => backend, limits), disk, backend }
}
const key = 'book:qa-session:original'
const second = 'book:section-view:original:section:learn'
const third = 'book:search-view:original'
const blocked = () => { throw new DOMException('blocked', 'SecurityError') }

describe('bounded session view storage', () => {
  it('preserves existing storage keys and observes external storage clearing while healthy', () => {
    const { store, disk } = fixture()
    store.write(key, 'original')
    expect(disk.get(key)).toBe('original')
    expect(store.read(key)).toBe('original')
    disk.clear()
    expect(store.read(key)).toBeNull()
    expect(store.isMemoryOnly()).toBe(false)
  })
  it('keeps the newest value after quota failure and erases the older disk snapshot', () => {
    const { store, disk, backend } = fixture()
    store.write(key, 'old')
    backend.setItem.mockImplementation(blocked)
    store.write(key, 'new')
    expect(store.isMemoryOnly()).toBe(true)
    expect(store.read(key)).toBe('new')
    expect(disk.has(key)).toBe(false)
    expect(backend.setItem).toHaveBeenCalledTimes(2)
    store.write(second, 'next')
    expect(backend.setItem).toHaveBeenCalledTimes(2)
  })
  it('survives a blocked sessionStorage getter and provides only bounded memory recovery', () => {
    const store = createSessionViewStorage(blocked)
    expect(store.read(key)).toBeNull()
    store.write(key, 'answer')
    expect(store.read(key)).toBe('answer')
    store.remove(key)
    expect(store.read(key)).toBeNull()
  })
  it('clears memory even if disk removal fails and never rereads an old snapshot', () => {
    const { store, disk, backend } = fixture()
    store.write(key, 'old')
    backend.removeItem.mockImplementation(blocked)
    store.remove(key)
    expect(disk.get(key)).toBe('old')
    expect(store.read(key)).toBeNull()
    expect(store.isMemoryOnly()).toBe(true)
  })
  it('bounds recent entry count with LRU order while memory-only', () => {
    const { store, backend } = fixture()
    backend.getItem.mockImplementation(blocked)
    store.read(key)
    store.write(key, 'first'); store.write(second, 'second'); store.read(key); store.write(third, 'third')
    expect(store.read(second)).toBeNull()
    expect(store.read(key)).toBe('first')
    expect(store.read(third)).toBe('third')
  })
  it('bounds aggregate characters independently of entry count', () => {
    const { store, backend } = fixture()
    backend.setItem.mockImplementation(blocked)
    store.write(key, 'a'.repeat(20)); store.write(second, 'b'.repeat(20))
    expect(store.read(key)).toBeNull()
    expect(store.read(second)).toBe('b'.repeat(20))
  })
  it('discards an oversized write instead of leaving stale content accessible', () => {
    const { store, disk } = fixture()
    store.write(key, 'old'); store.write(key, 'x'.repeat(21))
    expect(store.read(key)).toBeNull()
    expect(disk.has(key)).toBe(false)
    expect(store.isMemoryOnly()).toBe(true)
  })
  it('drops oversized stored data before JSON parsing', () => {
    const { store, disk } = fixture()
    disk.set(key, 'x'.repeat(21))
    expect(store.read(key)).toBeNull()
    expect(disk.has(key)).toBe(false)
  })
  it('does not accept unrelated storage, credentials or StudyRecord keys', () => {
    const { store, backend } = fixture()
    for (const name of ['study-record', 'book:study-record:original', 'api-key']) {
      store.write(name, 'must not store'); store.remove(name); expect(store.read(name)).toBeNull()
    }
    expect(backend.getItem).not.toHaveBeenCalled()
    expect(backend.setItem).not.toHaveBeenCalled()
    expect(backend.removeItem).not.toHaveBeenCalled()
  })
  it('notifies the warning once, asynchronously, and supports unsubscription', async () => {
    const { store, backend } = fixture()
    const listener = vi.fn(); const unsubscribe = store.subscribe(listener)
    backend.getItem.mockImplementation(blocked)
    store.read(key); store.read(second)
    expect(listener).not.toHaveBeenCalled()
    await Promise.resolve()
    expect(listener).toHaveBeenCalledTimes(1)
    unsubscribe(); store.write(key, 'still safe')
    await Promise.resolve()
    expect(listener).toHaveBeenCalledTimes(1)
  })
})
