import type {
  ChapterResponse,
  CourseResponse,
  LearningMode,
  LibraryResponse,
  ModeResponse,
  SectionResponse,
  SourceResponse,
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

async function request<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    headers: { Accept: 'application/json' },
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

  getSource(courseId: string, kind: string, sourceId: string): Promise<SourceResponse> {
    return request<SourceResponse>(
      `/api/courses/${segment(courseId)}/sources/${segment(kind)}/${segment(sourceId)}`,
    )
  },
}
