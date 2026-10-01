import { errorEnvelopeSchema, MAX_ERROR_RESPONSE_BYTES } from './errorContracts'
import { STUDY_RECEIPT_MESSAGE, validateCourseStudyRecords, validateRecentStudy, validateStudyReceipt } from './studyContracts'
import { validateModeResponse, validateSectionResponse } from './learningContracts'
import { readBoundedJson } from './boundedJson'
import { validateQAResponse, validateSearchResponse, validateSourceResponse } from './sourceContracts'
import type {
  ChapterResponse,
  CourseResponse,
  LearningMode,
  LibraryResponse,
  ModeResponse,
  QARequest,
  QAResponse,
  SearchResponse,
  SectionResponse,
  SourceResponse,
  StudyRecord,
  StudyRecordListResponse,
} from './types'

const GENERIC_ERROR_MESSAGE = '请求失败，请稍后重试'

export class ApiError extends Error {
  readonly code: string | null
  readonly status: number

  constructor(message: string, status: number, code: string | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function request<T>(path: string, init: RequestInit = {}, validate?: (value: unknown) => T, validationMessage = '教材响应校验失败，请刷新后重试'): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (init.headers) {
    new Headers(init.headers).forEach((value, key) => {
      headers[key] = value
    })
  }

  const response = await fetch(path, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let message = GENERIC_ERROR_MESSAGE
    let code: string | null = null

    try {
      const payload = errorEnvelopeSchema.parse(await readBoundedJson(response, MAX_ERROR_RESPONSE_BYTES))
      message = payload.error.message
      code = payload.error.code
    } catch {
      if (init.signal?.aborted) throw new DOMException('Cancelled', 'AbortError')
      // Stable fallback for malformed/oversized/non-JSON errors; no raw body,
      // parser exception, server detail, partial envelope or automatic replay.
    }
    if (init.signal?.aborted) throw new DOMException('Cancelled', 'AbortError')

    throw new ApiError(message, response.status, code)
  }

  if (validate) {
    try { return validate(await readBoundedJson(response)) }
    catch {
      if (init.signal?.aborted) throw new DOMException('Cancelled', 'AbortError')
      throw new ApiError(validationMessage, response.status, 'invalid_response')
    }
  }
  return (await response.json()) as T
}

const segment = (value: string): string => encodeURIComponent(value)

export const bookApi = {
  getLibrary(): Promise<LibraryResponse> {
    return request<LibraryResponse>('/api/library')
  },

  getCourse(courseId: string): Promise<CourseResponse> {
    return request<CourseResponse>(`/api/courses/${segment(courseId)}`)
  },

  getChapter(courseId: string, chapterId: string): Promise<ChapterResponse> {
    return request<ChapterResponse>(
      `/api/courses/${segment(courseId)}/chapters/${segment(chapterId)}`,
    )
  },

  getSection(courseId: string, sectionId: string): Promise<SectionResponse> {
    return request<SectionResponse>(
      `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}`,
      {}, value => validateSectionResponse(value, courseId, sectionId),
    )
  },

  getMode(
    courseId: string,
    sectionId: string,
    mode: LearningMode,
  ): Promise<ModeResponse> {
    return request<ModeResponse>(
      `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}/${mode}`,
      {}, value => validateModeResponse(value, courseId, sectionId, mode),
    )
  },

  touchStudy(
    courseId: string,
    sectionId: string,
    mode: LearningMode,
  ): Promise<StudyRecord> {
    return request<StudyRecord>(
      `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}/study/${mode}/touch`,
      { method: 'POST' }, value => validateStudyReceipt(value, courseId, sectionId, mode), STUDY_RECEIPT_MESSAGE,
    )
  },

  completeStudy(
    courseId: string,
    sectionId: string,
    mode: LearningMode,
  ): Promise<StudyRecord> {
    return request<StudyRecord>(
      `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}/study/${mode}/complete`,
      { method: 'POST' }, value => validateStudyReceipt(value, courseId, sectionId, mode, { completed: true }), STUDY_RECEIPT_MESSAGE,
    )
  },

  getCourseStudyRecords(courseId: string): Promise<StudyRecordListResponse> {
    return request<StudyRecordListResponse>(
      `/api/courses/${segment(courseId)}/study-records`,
      {}, value => validateCourseStudyRecords(value, courseId), STUDY_RECEIPT_MESSAGE,
    )
  },

  getRecentStudy(): Promise<StudyRecord | null> {
    return request<StudyRecord | null>('/api/study/recent', {}, validateRecentStudy, STUDY_RECEIPT_MESSAGE)
  },

  searchCourse(courseId: string, query: string, limit = 30, signal?: AbortSignal): Promise<SearchResponse> {
    const params = new URLSearchParams({
      q: query,
      limit: String(limit),
    })
    return request<SearchResponse>(
      `/api/courses/${segment(courseId)}/search?${params.toString()}`,
      { signal }, value => validateSearchResponse(value, courseId, query, limit),
    )
  },

  askCourse(courseId: string, qaRequest: QARequest): Promise<QAResponse> {
    return request<QAResponse>(`/api/courses/${segment(courseId)}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(qaRequest),
    }, value => validateQAResponse(value, courseId, qaRequest))
  },

  getSource(courseId: string, kind: string, sourceId: string, signal?: AbortSignal): Promise<SourceResponse> {
    return request<SourceResponse>(
      `/api/courses/${segment(courseId)}/sources/${segment(kind)}/${segment(sourceId)}`,
      { signal }, value => validateSourceResponse(value, courseId, kind, sourceId),
    )
  },
}
