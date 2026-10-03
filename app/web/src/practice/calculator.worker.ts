import { calculateExpression } from './calculator'

const worker = self as unknown as {
  onmessage: ((event: MessageEvent<{ id: number; expression: string }>) => void) | null
  postMessage(value: unknown): void
}
worker.onmessage = event => {
  const { id, expression } = event.data || {}
  if (!Number.isSafeInteger(id)) return
  worker.postMessage({ id, outcome: calculateExpression(expression) })
}
