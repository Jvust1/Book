import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { CourseResponse, QACitationItem, QAResponse } from '../api/types'
import { loadQAViewState, saveQAViewState } from '../state/qaViewState'

const qaErrorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : '教材问答失败，请稍后重试'

const citationTitle = (citation: QACitationItem): string =>
  citation.title_zh || citation.title_en || '教材来源'

export function QAPage() {
  const { courseId } = useParams()
  const location = useLocation()
  const restoredCourseRef = useRef<string | null>(null)
  const savedState = courseId ? loadQAViewState(courseId) : null
  const [course, setCourse] = useState<CourseResponse | null>(null)
  const [courseError, setCourseError] = useState<string | null>(null)
  const [input, setInput] = useState(savedState?.question ?? '')
  const [result, setResult] = useState<QAResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
    if (!courseId || restoredCourseRef.current === courseId) return
    restoredCourseRef.current = courseId

    const saved = loadQAViewState(courseId)
    const question = saved?.question.trim() ?? ''
    if (!question) return

    let active = true
    setInput(saved!.question)
    setLoading(true)
    setResult(null)
    setError(null)
    bookApi
      .askCourse(courseId, question)
      .then((value) => {
        if (active) setResult(value)
      })
      .catch((reason: unknown) => {
        if (active) setError(qaErrorMessage(reason))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [courseId])

  useEffect(() => {
    if (!courseId || !result) return
    const saved = loadQAViewState(courseId)
    if (!saved || saved.question !== result.question) return
    window.scrollTo(0, saved.scrollY)
  }, [courseId, result])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!courseId || loading) return

    const question = input.trim()
    if (!question) {
      setResult(null)
      setError('请输入教材问题')
      return
    }

    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const value = await bookApi.askCourse(courseId, question)
      setResult(value)
    } catch (reason: unknown) {
      setError(qaErrorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  const rememberCitation = (citation: QACitationItem) => {
    if (!courseId || !result) return
    saveQAViewState(courseId, {
      route: `${location.pathname}${location.search}`,
      question: result.question,
      scrollY: window.scrollY,
      activeCitationKey: `${citation.source_kind}:${citation.source_id}`,
    })
  }

  if (!courseId) {
    return (
      <section className="status-panel" role="alert">
        <h1>课程地址无效</h1>
      </section>
    )
  }

  const activeCitationKey =
    savedState && result && savedState.question === result.question
      ? savedState.activeCitationKey
      : null

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
        <p>输入问题后，回答只依据当前教材可验证来源。</p>
      </div>

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

      {result ? (
        <section className="qa-result page-stack" aria-label="教材问答结果">
          <article className="learning-card qa-answer-card">
            {result.answer_kind === 'generated' ? (
              <p className="qa-generated-label">AI 生成回答，依据下方教材来源</p>
            ) : (
              <p className="eyebrow">教材证据状态：不足</p>
            )}
            <p className="learning-content">{result.answer}</p>
          </article>

          {result.citations.length > 0 ? (
            <div className="qa-citations" aria-label="教材来源">
              <h2>教材来源</h2>
              {result.citations.map((citation) => {
                const sourceKey = `${citation.source_kind}:${citation.source_id}`
                const sourcePath = `/courses/${encodeURIComponent(courseId)}/sources/${encodeURIComponent(citation.source_kind)}/${encodeURIComponent(citation.source_id)}`
                const typeAndNumber = [citation.object_type, citation.number]
                  .filter(Boolean)
                  .join(' · ')
                return (
                  <article
                    className="learning-card qa-citation-card"
                    key={citation.citation_id}
                    aria-current={activeCitationKey === sourceKey ? 'true' : undefined}
                  >
                    <div>
                      {typeAndNumber ? <p className="object-type">{typeAndNumber}</p> : null}
                      <h2>{citationTitle(citation)}</h2>
                      {citation.title_en && citation.title_zh ? (
                        <p className="secondary-text">{citation.title_en}</p>
                      ) : null}
                    </div>
                    <div className="search-result-meta">
                      <span>教材页：{citation.printed_page ?? '暂缺'}</span>
                      <span>PDF 页：{citation.pdf_page ?? '暂缺'}</span>
                    </div>
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
        </section>
      ) : null}
    </section>
  )
}
