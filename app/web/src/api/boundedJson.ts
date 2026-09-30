export const MAX_VALIDATED_RESPONSE_BYTES = 2 * 1024 * 1024

/** Bound source-bearing HTTP data before JSON parsing and schema validation. */
export async function readBoundedJson(response: Response): Promise<unknown> {
  const type = response.headers.get('content-type')?.split(';')[0].trim().toLowerCase()
  if (type !== 'application/json' || !response.body) {
    void response.body?.cancel().catch(() => {})
    throw new Error('invalid response encoding')
  }
  const declared = response.headers.get('content-length')
  if (declared !== null && Number(declared) > MAX_VALIDATED_RESPONSE_BYTES) {
    void response.body.cancel().catch(() => {})
    throw new Error('response byte budget')
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8', { fatal: true })
  let bytes = 0
  let text = ''
  try {
    while (true) {
      const chunk = await reader.read()
      if (chunk.done) break
      bytes += chunk.value.byteLength
      if (bytes > MAX_VALIDATED_RESPONSE_BYTES) throw new Error('response byte budget')
      text += decoder.decode(chunk.value, { stream: true })
    }
    text += decoder.decode()
    return JSON.parse(text) as unknown
  } finally {
    void reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}
