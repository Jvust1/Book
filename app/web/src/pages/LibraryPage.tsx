import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { LibraryResponse } from '../api/types'

const errorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : '教材库加载失败，请稍后重试'

export function LibraryPage() {
  const [library, setLibrary] = useState<LibraryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const controller = new AbortController()
    bookApi
      .getLibrary(controller.signal)
      .then((value) => {
        if (active) setLibrary(value)
      })
      .catch((reason: unknown) => {
        if (active) setError(errorMessage(reason))
      })
    return () => {
      active = false
      controller.abort()
    }
  }, [])

  if (error) {
    return (
      <section className="status-panel" role="alert">
        <h1>教材库加载失败</h1>
        <p>{error}</p>
      </section>
    )
  }

  if (!library) {
    return <p role="status">正在读取教材库…</p>
  }

  return (
    <section className="page-stack">
      <header className="page-heading">
        <p className="eyebrow">Book 学习</p>
        <h1>教材库</h1>
        <p>选择一门课程进入教材学习。</p>
      </header>

      <div className="card-grid">
        {library.courses.map((course) => (
          <article className="content-card" key={course.course_id}>
            <div>
              <p className="eyebrow">{course.runtime_status === 'READY' ? '教材已就绪' : course.runtime_status}</p>
              <h2>{course.name_zh}</h2>
              {course.name_en ? <p className="secondary-text">{course.name_en}</p> : null}
              {course.authors.length ? (
                <p className="secondary-text">{course.authors.join(' · ')}</p>
              ) : null}
            </div>
            <div className="card-footer">
              <span>{course.chapter_count} 章 · {course.section_count} 节</span>
              <Link className="primary-link" to={`/courses/${encodeURIComponent(course.course_id)}`}>
                进入课程
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
