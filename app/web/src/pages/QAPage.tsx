import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import { QAAnswerContent } from '../components/QAAnswerContent'
import type {
  CourseResponse,
  QACitationItem,
  QAResponse,
  SectionResponse,
} from '../api/types'
import {
  loadQASessionState,
  saveQASessionState,
} from '../state/qaSessionState'
import type { QASessionMessage } from '../state/qaSessionState'

const qaErrorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : '教材问答失败，请稍后重试'

const citationTitle = (citation: QACitationItem): string =>
  citation.title_zh || citation.title_en || '教材来源'

const answerStyleLabel = (response: QAResponse): string | null => {
  const labels = {
    brief: '简要',
    explain: '解释',
    compare: '比较',
    proof: '证明',
  } as const
  return response.answer_style ? labels[response.answer_style] : null
}

const scopeLabel = (response: QAResponse): string => {
  if (response.scope_requested === 'section_then_book') {
    return response.scope_used === 'section'
      ? '回答依据：当前小节'
      : '回答依据：本节 + 教材其他章节'
  }
  return '回答依据：整本教材'
}

let messageSequence = 0
const nextMessageId = (role: 'user' | 'assistant'): string => {
  messageSequence += 1
  return `${role}-${messageSequence}`
}

export function QAPage() {
  const { courseId } = useParams()
  const location = useLocation()
  const sectionId = new URLSearchParams(location.search).get('section')?.trim() || null
  const initialSession = courseId ? loadQASessionState(courseId) : null
  const [course, setCourse] = useState<CourseResponse | null>(null)
  const [courseError, setCourseError] = useState<string | null>(null)
  const [section, setSection] = useState<SectionResponse | null>(null)
  const [sectionError, setSectionError] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<QASessionMessage[]>(
    initialSession?.messages ?? [],
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const restoredScrollRef = useRef(false)

  const currentRoute = `${location.pathname}${location.search}`

  useEffect(() => {
    if (!courseId) {
      setCourseError('课程地址无效')
      return
    }

    let active = true
    setCourseError(null)
    bookApi
      .getCourse(courseId)
      .then((value) => {
        if (active) setCourse(value)
      })
      .catch((reason: unknown) => {
        if (!active) return
        setCourseError(reason instanceof ApiError ? reason.message : '课程加载失败，请稍后重试')
      })

    return () => {
      active = false
    }
  }, [courseId])

  useEffect(() => {
    if (!courseId || !sectionId) {
      setSection(null)
      setSectionError(null)
      return
    }

    let active = true
    setSection(null)
    setSectionError(null)
    bookApi
      .getSection(courseId, sectionId)
      .then((value) => {
        if (active) setSection(value)
      })
      .catch((reason: unknown) => {
        if (!active) return
        setSectionError(
          reason instanceof ApiError ? reason.message : '小节加载失败，请稍后重试',
        )
      })

    return () => {
      active = false
    }
  }, [courseId, sectionId])

  useEffect(() => {
    restoredScrollRef.current = false
  }, [courseId, currentRoute])

  useEffect(() => {
    if (!courseId || restoredScrollRef.current) return
    const saved = loadQASessionState(courseId)
    if (!saved || saved.route !== currentRoute || saved.messages.length === 0) return
    restoredScrollRef.current = true
    window.scrollTo(0, saved.scrollY)
  }, [courseId, currentRoute, messages])

  const persistMessages = (
    nextMessages: QASessionMessage[],
    activeCitationSourceId: string | null = null,
    scrollY = window.scrollY,
  ) => {
    if (!courseId) return
    saveQASessionState(courseId, {
      route: currentRoute,
      messages: nextMessages,
      scrollY,
      activeCitationSourceId,
    })
  }

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!courseId || loading) return

    const question = input.trim()
    if (!question) {
      setError('请输入教材问题')
      return
    }

    const priorMessages = messages
    const userMessage: QASessionMessage = {
      id: nextMessageId('user'),
      role: 'user',
      content: question,
    }
    const messagesWithUser = [...priorMessages, userMessage]
    const history = priorMessages.map(({ role, content }) => ({ role, content }))

    setMessages(messagesWithUser)
    persistMessages(messagesWithUser)
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await bookApi.askCourse(courseId, {
        question,
        section_id: sectionId,
        history,
      })
      const assistantContent = response.answer ?? response.message ?? ''
      const assistantMessage: QASessionMessage = {
        id: nextMessageId('assistant'),
        role: 'assistant',
        content: assistantContent,
        response,
      }
      const nextMessages = [...messagesWithUser, assistantMessage]
      setMessages(nextMessages)
      persistMessages(nextMessages)
    } catch (reason: unknown) {
      setError(qaErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  const rememberCitation = (citation: QACitationItem) => {
    persistMessages(messages, citation.source_id, window.scrollY)
  }

  if (!courseId) {
    return (
      <section className="status-panel" role="alert">
        <h1>课程地址无效</h1>
      </section>
    )
  }

  const savedSession = loadQASessionState(courseId)
  const activeCitationSourceId = savedSession?.activeCitationSourceId ?? null

  return (
    <section className="qa-page page-stack">
      <Link className="back-link" to={`/courses/${encodeURIComponent(courseId)}`}>
        ← 返回课程
      </Link>

      <header className="page-heading">
        <p className="eyebrow">当前课程 · 来源约束问答</p>
        <h1>教材问答</h1>
        {course ? <p>{course.course.name_zh}</p> : null}
        {courseError ? <p role="alert">{courseError}</p> : null}
      </header>

      <div className="empty-state qa-guidance">
        {sectionId ? (
          section ? (
            <>
              <p>
                当前范围：{section.section.number ? `${section.section.number} · ` : ''}
                {section.section.title_zh || section.section.title_en || section.section.section_id}
              </p>
              <p>优先本节，必要时扩展到全书</p>
            </>
          ) : sectionError ? (
            <p role="alert">{sectionError}</p>
          ) : (
            <p role="status">正在读取当前小节…</p>
          )
        ) : (
          <p>当前范围：整本教材</p>
        )}
        <p>回答只依据当前教材可验证来源。</p>
      </div>

      {messages.length > 0 ? (
        <section className="qa-result page-stack" aria-label="教材问答会话">
          {messages.map((message) => {
            if (message.role === 'user') {
              return (
                <article className="learning-card qa-question-card" key={message.id}>
                  <p className="eyebrow">你的问题</p>
                  <p className="learning-content">{message.content}</p>
                </article>
              )
            }

            const response = message.response
            const style = answerStyleLabel(response)
            return (
              <article className="qa-turn page-stack" key={message.id}>
                <section className="learning-card qa-answer-card">
                  {response.answer_kind === 'generated' ? (
                    <p className="qa-generated-label">AI 生成回答，依据下方教材来源</p>
                  ) : (
                    <p className="eyebrow">教材证据状态：不足</p>
                  )}
                  <p>{scopeLabel(response)}</p>
                  {style ? <p>回答方式：{style}</p> : null}
                  {response.answer_kind === 'generated' ? <QAAnswerContent text={message.content} /> : <p className="learning-content">{message.content}</p>}
                </section>

                {response.citations.length > 0 ? (
                  <div className="qa-citations" aria-label="教材来源">
                    <h2>教材来源</h2>
                    {response.citations.map((citation) => {
                      const sourcePath = `/courses/${encodeURIComponent(courseId)}/sources/${encodeURIComponent(citation.source_kind)}/${encodeURIComponent(citation.source_id)}`
                      const typeAndNumber = [citation.type_zh, citation.number]
                        .filter(Boolean)
                        .join(' · ')
                      return (
                        <article
                          className="learning-card qa-citation-card"
                          key={`${message.id}:${citation.evidence_id}`}
                          aria-current={
                            activeCitationSourceId === citation.source_id ? 'true' : undefined
                          }
                        >
                          <div>
                            {typeAndNumber ? (
                              <p className="object-type">{typeAndNumber}</p>
                            ) : null}
                            <h2>{citationTitle(citation)}</h2>
                            {citation.title_en && citation.title_zh ? (
                              <p className="secondary-text">{citation.title_en}</p>
                            ) : null}
                          </div>
                          <div className="search-result-meta">
                            <span>教材页：{citation.printed_page ?? '暂缺'}</span>
                            <span>PDF 页：{citation.pdf_page ?? '暂缺'}</span>
                          </div>
                          <p>{citation.source_anchor || '教材锚点暂未提供'}</p>
                          <Link
                            className="source-link"
                            to={sourcePath}
                            onClick={() => rememberCitation(citation)}
                          >
                            查看教材来源
                          </Link>
                        </article>
                      )
                    })}
                  </div>
                ) : null}
              </article>
            )
          })}
        </section>
      ) : null}

      <form className="qa-form" onSubmit={submit}>
        <textarea
          aria-label="教材问题"
          className="qa-input"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="例如：什么是巴拿赫空间？"
          rows={5}
          maxLength={1000}
        />
        <button className="secondary-button" type="submit" disabled={loading}>
          {loading ? '正在查找教材依据…' : '提问'}
        </button>
      </form>

      {error ? (
        <section className="status-panel" role="alert">
          <h2>问答暂未完成</h2>
          <p>{error}</p>
        </section>
      ) : null}
    </section>
  )
}
