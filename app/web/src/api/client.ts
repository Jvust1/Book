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

type ErrorPayload = {
  error?: {
    code?: unknown
    message?: unknown
  }
}

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

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
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
      const payload = (await response.json()) as ErrorPayload
      const rawMessage = payload.error?.message
      const rawCode = payload.error?.code
      if (typeof rawMessage === 'string' && rawMessage.trim()) {
        message = rawMessage
      }
      if (typeof rawCode === 'string' && rawCode.trim()) {
        code = rawCode
      }
    } catch {
      // Keep the stable Chinese fallback; never expose parser or server internals.
    }

    throw new ApiError(message, response.status, code)
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
    )
  },

  getMode(
    courseId: string,
    sectionId: string,
    mode: LearningMode,
  ): Promise<ModeResponse> {
    return request<ModeResponse>(
      `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}/${mode}`,
    )
  },

  touchStudy(
    courseId: string,
    sectionId: string,
    mode: LearningMode,
  ): Promise<StudyRecord> {
    return request<StudyRecord>(
      `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}/study/${mode}/touch`,
      { method: 'POST' },
    )
  },

  completeStudy(
    courseId: string,
    sectionId: string,
    mode: LearningMode,
  ): Promise<StudyRecord> {
    return request<StudyRecord>(
      `/api/courses/${segment(courseId)}/sections/${segment(sectionId)}/study/${mode}/complete`,
      { method: 'POST' },
    )
  },

  getCourseStudyRecords(courseId: string): Promise<StudyRecordListResponse> {
    return request<StudyRecordListResponse>(
      `/api/courses/${segment(courseId)}/study-records`,
    )
  },

  getRecentStudy(): Promise<StudyRecord | null> {
    return request<StudyRecord | null>('/api/study/recent')
  },

  searchCourse(courseId: string, query: string, limit = 30): Promise<SearchResponse> {
    const params = new URLSearchParams({
      q: query,
      limit: String(limit),
    })
    return request<SearchResponse>(
      `/api/courses/${segment(courseId)}/search?${params.toString()}`,
    )
  },

  askCourse(courseId: string, qaRequest: QARequest): Promise<QAResponse> {
    return request<QAResponse>(`/api/courses/${segment(courseId)}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(qaRequest),
    })
  },

  getSource(courseId: string, kind: string, sourceId: string): Promise<SourceResponse> {
    return request<SourceResponse>(
      `/api/courses/${segment(courseId)}/sources/${segment(kind)}/${segment(sourceId)}`,
    )
  },
}
