import { qaResponseSchema } from '../api/sourceContracts'
import type { QAResponse } from '../api/types'

export const MAX_QA_EXPORT_BYTES = 1024 * 1024
export const QA_EXPORT_FILENAME = 'book-qa-evidence.zip'
export const QA_EXPORT_ERROR = '无法导出：请确认回答与课程一致、文字完整，且导出内容不超过 1 MiB。'

export interface QAExportInput {
  courseId: string
  bookId: string
  question: string
  content: string
  response: QAResponse
}

const README = 'Book 单次问答证据导出\n\n'
  + 'question.txt：提问原文；answer.txt：AI 回答原文；qa-response.json：回答及引用定位。\n'
  + '引用定位不证明教材版本或内容真实，也不证明 AI 结论正确。请回到原教材核对。\n'
  + '导出不额外读取或打包教材/PDF；本包不是学习进度备份，不支持导入 Book。\n'
  + '文件仅由本次明确操作在浏览器本地生成，没有自动上传或重新提问。\n'

function fail(): never { throw new Error(QA_EXPORT_ERROR) }

/** Count UTF-8 without allocating a replacement-filled encoding of malformed UTF-16. */
function utf8Size(text: string): number {
  let bytes = 0
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i)
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = text.charCodeAt(++i)
      if (!(next >= 0xdc00 && next <= 0xdfff)) fail()
      bytes += 4
    } else if (code >= 0xdc00 && code <= 0xdfff) fail()
    else bytes += code < 0x80 ? 1 : code < 0x800 ? 2 : 3
    if (bytes > MAX_QA_EXPORT_BYTES) fail()
  }
  return bytes
}

/** Bound input before the schema clone/JSON serialization as well as ZIP generation. */
function checkInput(value: unknown): void {
  const seen = new Set<object>()
  let bytes = 0
  let nodes = 0
  function visit(item: unknown, depth: number): void {
    if (++nodes > 20_000 || depth > 8) fail()
    if (typeof item === 'string') bytes += utf8Size(item)
    else if (item !== null && typeof item === 'object') {
      if (seen.has(item)) fail()
      seen.add(item)
      for (const [key, child] of Object.entries(item)) {
        bytes += utf8Size(key)
        visit(child, depth + 1)
      }
      seen.delete(item)
    } else if (item !== null && typeof item !== 'boolean' && typeof item !== 'number') fail()
    if (bytes > MAX_QA_EXPORT_BYTES) fail()
  }
  visit(value, 0)
}

/** One already-completed turn only. No network, storage, PDF access or ZIP import. */
export async function buildQAEvidenceZip(input: QAExportInput): Promise<Uint8Array> {
  try {
    checkInput(input)
    const response = qaResponseSchema.parse(input.response)
    if (response.answer_kind !== 'generated' || response.course_id !== input.courseId
      || response.book_id !== input.bookId || response.question !== input.question
      || response.answer !== input.content) fail()
    const files: Record<string, string> = {
      'README.txt': README,
      'question.txt': input.question,
      'answer.txt': input.content,
      'qa-response.json': JSON.stringify({ schema_version: 'book.qa-evidence.v1', response }, null, 2) + '\n',
    }
    let bytes = 0
    for (const text of Object.values(files)) {
      bytes += utf8Size(text)
      if (bytes > MAX_QA_EXPORT_BYTES) fail()
    }
    const { default: JSZip } = await import('jszip')
    const zip = new JSZip()
    for (const [name, text] of Object.entries(files)) {
      zip.file(name, text, { date: new Date('1980-01-01T00:00:00.000Z'), createFolders: false })
    }
    // Fixed names/date, UTF-8 text and STORE yield stable bytes, without decompression work.
    return await zip.generateAsync({ type: 'uint8array', compression: 'STORE', platform: 'DOS' })
  } catch {
    // Never expose rejected questions, answers, parser issues or upstream errors.
    throw new Error(QA_EXPORT_ERROR)
  }
}
