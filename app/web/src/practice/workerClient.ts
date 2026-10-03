import type { CalculationOutcome } from './calculator'

const ENGINE = 'mathjs@15.2.0'
let sequence = 0
export interface CalculationTask { result: Promise<CalculationOutcome>; cancel: () => void }

function validOutcome(value: unknown): value is CalculationOutcome {
  if (!value || typeof value !== 'object') return false
  const data = value as Record<string, unknown>
  if (data.status === 'ok') return data.engine === ENGINE && typeof data.expression === 'string' && data.expression.length <= 2048 &&
    typeof data.formatted === 'string' && data.formatted.length <= 4096 && ['number', 'complex', 'array'].includes(String(data.kind))
  return data.status === 'error' && ['invalid_expression', 'unsupported_expression', 'non_finite_result', 'unavailable', 'timeout', 'cancelled'].includes(String(data.code))
}

export function startCalculation(expression: string, options: { timeoutMs?: number; makeWorker?: () => Worker } = {}): CalculationTask {
  const id = ++sequence
  const timeoutMs = options.timeoutMs ?? 5000
  let cancel = () => {}
  const result = new Promise<CalculationOutcome>(resolve => {
    let worker: Worker
    try { worker = options.makeWorker ? options.makeWorker() : new Worker(new URL('./calculator.worker.ts', import.meta.url), { type: 'module' }) }
    catch { resolve({ status: 'error', code: 'unavailable' }); return }
    let settled = false
    let timer: ReturnType<typeof setTimeout>
    const finish = (outcome: CalculationOutcome) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      worker.onmessage = null
      worker.onerror = null
      worker.terminate()
      resolve(outcome)
    }
    cancel = () => finish({ status: 'error', code: 'cancelled' })
    timer = setTimeout(() => finish({ status: 'error', code: 'timeout' }), Number.isFinite(timeoutMs) && timeoutMs > 0 ? Math.min(timeoutMs, 30_000) : 5000)
    worker.onmessage = event => {
      const data = event.data as { id?: unknown; outcome?: unknown }
      if (data?.id !== id) return
      if (!validOutcome(data.outcome) || (data.outcome.status === 'ok' && data.outcome.expression !== expression)) {
        finish({ status: 'error', code: 'unavailable' }); return
      }
      finish(data.outcome)
    }
    worker.onerror = () => finish({ status: 'error', code: 'unavailable' })
    try { worker.postMessage({ id, expression }) } catch { finish({ status: 'error', code: 'unavailable' }) }
  })
  return { result, cancel: () => cancel() }
}
