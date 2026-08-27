import { FormEvent, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { CourseResponse, SearchResponse, SearchResultItem } from '../api/types'

const searchErrorMessage = (error: unknown): { message: string; unavailable: boolean } => {
  if (error instanceof ApiError) {
    return {
      message: error.message,
      unavailable: error.code === 'search_unavailable',
    }
  }
  return { message: '教材搜索失败，请稍后重试', unavailable: false }
}

const resultTitle = (item: SearchResultItem): string =>
  item.title_zh || '中文内容暂未提供'

export function SearchPage() {
  const { courseId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const query = (searchParams.get('q') || '').trim()
  const [input, setInput] = useState(query)
  const [course, setCourse] = useState<CourseResponse | null>(null)
  const [courseError, setCourseError] = useState<string | null>(null)
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    setInput(query)
  }, [query])

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
      .catch((error: unknown) => {
        if (!active) return
        setCourseError(error instanceof ApiError ? error.message : '课程加载失败，请稍后重试')
      })
    return () => {
      active = false
    }
  }, [courseId])

  useEffect(() => {
    if (!courseId || !query) {
      setResults(null)
      setSearchError(null)
      setUnavailable(false)
      setLoading(false)
      return
    }

    let active = true
    setResults(null)
    setSearchError(null)
    setUnavailable(false)
    setLoading(true)
    bookApi
      .searchCourse(courseId, query)
      .then((value) => {
        if (!active) return
        setResults(value)
        setLoading(false)
      })
      .catch((error: unknown) => {
        if (!active) return
        const state = searchErrorMessage(error)
        setSearchError(state.message)
        setUnavailable(state.unavailable)
        setLoading(false)
      })

    return () => {
      active = false
    }
  }, [courseId, query])

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextQuery = input.trim()
    setSearchParams(nextQuery ? { q: nextQuery } : {})
  }

  if (!courseId) {
    return (
      <section className="status-panel" role="alert">
        <h1>课程地址无效</h1>
      </section>
    )
  }

  return (
    <section className="search-page page-stack">
      <Link className="back-link" to={`/courses/${encodeURIComponent(courseId)}`}>
        ← 返回课程
      </Link>

      <header className="page-heading">
        <p className="eyebrow">当前课程教材内搜索</p>
        <h1>搜索教材</h1>
        {course ? <p>{course.course.name_zh}</p> : null}
        {courseError ? <p role="alert">{courseError}</p> : null}
      </header>

      <form className="search-form" role="search" onSubmit={submit}>
        <input
          aria-label="教材搜索词"
          className="search-input"
          type="search"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="例如：巴拿赫空间、Hölder、1/p + 1/q"
        />
        <button className="secondary-button" type="submit">搜索</button>
      </form>

      {!query ? (
        <div className="empty-state">
          <p>输入中文、英文、定理、公式或题目关键词开始搜索</p>
        </div>
      ) : null}

      {loading ? <p role="status">正在搜索教材…</p> : null}

      {searchError ? (
        <section className="status-panel" role="alert">
          <h2>{unavailable ? '教材搜索暂不可用' : '搜索失败'}</h2>
          <p>{searchError}</p>
        </section>
      ) : null}

      {results && results.result_count === 0 ? (
        <div className="empty-state">
          <p>未找到匹配教材内容</p>
        </div>
      ) : null}

      {results && results.results.length > 0 ? (
        <div className="search-results" aria-label="教材搜索结果">
          <p className="secondary-text">共 {results.result_count} 条结果</p>
          {results.results.map((item) => {
            const sourcePath = `/courses/${encodeURIComponent(courseId)}/sources/${encodeURIComponent(item.source_kind)}/${encodeURIComponent(item.source_id)}`
            const typeAndNumber = [item.object_type, item.number].filter(Boolean).join(' · ')
            return (
              <article
                className="learning-card search-result-card"
                key={`${item.source_kind}:${item.source_id}`}
                data-source-key={`${item.source_kind}:${item.source_id}`}
              >
                <div>
                  {typeAndNumber ? <p className="object-type">{typeAndNumber}</p> : null}
                  <h2>{resultTitle(item)}</h2>
                  {item.title_en ? <p className="secondary-text">{item.title_en}</p> : null}
                </div>
                {item.formula ? <div className="formula-block">{item.formula}</div> : null}
                {item.snippet && item.snippet !== item.title_zh ? (
                  <p className="learning-content">{item.snippet}</p>
                ) : null}
                <div className="search-result-meta">
                  <span>教材页：{item.printed_page ?? '暂缺'}</span>
                  <span>PDF 页：{item.pdf_page ?? '暂缺'}</span>
                </div>
                <Link className="source-link" to={sourcePath}>查看教材来源</Link>
              </article>
            )
          })}
        </div>
      ) : null}
    </section>
  )
}
