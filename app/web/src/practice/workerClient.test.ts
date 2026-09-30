import { afterEach, describe, expect, it, vi } from 'vitest'
import { startCalculation } from './workerClient'

class FakeWorker {
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: (() => void) | null = null
  terminate = vi.fn()
  postMessage = vi.fn()
  reply(id: number, outcome: unknown) { this.onmessage?.({ data: { id, outcome } } as MessageEvent) }
  asWorker() { return this as unknown as Worker }
}
afterEach(() => { vi.useRealTimers() })

describe('cancellable worker transport', () => {
  it('accepts only the matching expression/id and terminates after a valid result', async () => {
    const worker = new FakeWorker()
    const task = startCalculation('1+1', { makeWorker: () => worker.asWorker() })
    const { id } = worker.postMessage.mock.calls[0][0]
    worker.reply(id - 1, { status: 'ok' })
    expect(worker.terminate).not.toHaveBeenCalled()
    worker.reply(id, { status: 'ok', engine: 'mathjs@15.2.0', expression: '1+1', kind: 'number', formatted: '2' })
    await expect(task.result).resolves.toMatchObject({ status: 'ok', formatted: '2' })
    expect(worker.terminate).toHaveBeenCalledOnce()
    task.cancel()
    expect(worker.terminate).toHaveBeenCalledOnce()
  })

  it('times out and clears the worker without blocking the caller', async () => {
    vi.useFakeTimers()
    const worker = new FakeWorker()
    const task = startCalculation('1', { timeoutMs: 100, makeWorker: () => worker.asWorker() })
    await vi.advanceTimersByTimeAsync(100)
    await expect(task.result).resolves.toEqual({ status: 'error', code: 'timeout' })
    expect(worker.terminate).toHaveBeenCalledOnce()
    expect(vi.getTimerCount()).toBe(0)
  })

  it('cancels idempotently and removes callbacks/timers', async () => {
    vi.useFakeTimers()
    const worker = new FakeWorker()
    const task = startCalculation('1', { makeWorker: () => worker.asWorker() })
    task.cancel(); task.cancel()
    await expect(task.result).resolves.toEqual({ status: 'error', code: 'cancelled' })
    expect(worker.terminate).toHaveBeenCalledOnce()
    expect(worker.onmessage).toBeNull()
    expect(vi.getTimerCount()).toBe(0)
  })

  it.each([
    { status: 'ok', engine: 'unverified', expression: '1', kind: 'number', formatted: '1' },
    { status: 'ok', engine: 'mathjs@15.2.0', expression: 'different', kind: 'number', formatted: '1' },
    { status: 'ok', engine: 'mathjs@15.2.0', expression: '1', kind: 'number', formatted: 'x'.repeat(4097) },
    { status: 'error', code: 'unknown' },
  ])('rejects a malformed worker response', async outcome => {
    const worker = new FakeWorker()
    const task = startCalculation('1', { makeWorker: () => worker.asWorker() })
    const { id } = worker.postMessage.mock.calls[0][0]
    worker.reply(id, outcome)
    await expect(task.result).resolves.toEqual({ status: 'error', code: 'unavailable' })
  })

  it('handles worker startup and script errors', async () => {
    await expect(startCalculation('1', { makeWorker: () => { throw new Error('no worker') } }).result).resolves.toEqual({ status: 'error', code: 'unavailable' })
    const worker = new FakeWorker()
    const task = startCalculation('1', { makeWorker: () => worker.asWorker() })
    worker.onerror?.()
    await expect(task.result).resolves.toEqual({ status: 'error', code: 'unavailable' })
  })
})
