import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { LibraryResponse } from '../api/types'
import { Icon } from '../components/Icon'

const errorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : '教材库加载失败，请稍后重试'

export function LibraryPage() {
  const [library, setLibrary] = useState<LibraryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    bookApi
      .getLibrary()
      .then((value) => {
        if (active) setLibrary(value)
      })
      .catch((reason: unknown) => {
        if (active) setError(errorMessage(reason))
      })
    return () => {
      active = false
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
    <section className="page-stack library-page">
      <header className="page-heading library-heading">
        <p className="eyebrow">YOUR LEARNING SPACE · 日积月累</p>
        <h1>教材库</h1>
        <p>循着一本好书，把每一个知识点读懂。</p>
      </header>

      <div className="library-intro"><div><span className="eyebrow">专注当下的一页</span><h2>学有所思，听有所记。</h2><p>预习、学习、复习、刷题。按照自己的节奏，让知识慢慢连起来。</p><Link className="primary-button" to="/recording"><Icon name="mic" />记录一堂课</Link></div><div className="book-art" aria-hidden="true"><div className="book-art-back" /><div className="book-art-front"><span>BOOK</span><svg viewBox="0 0 200 110"><path d="M10 80Q50 -35 95 55T190 20M10 92Q70 80 190 55M95 5V105" /></svg><small>让知识，生长。</small></div></div></div>

      <div className="card-grid">
        {library.courses.map((course) => (
          <article className="content-card course-cover-card" key={course.course_id}>
            <div className="course-cover-strip"><Icon name="book" /><span>COURSE / 教材课程</span></div>
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
              <Link className="primary-link" to={`/courses/${course.course_id}`}>
                进入课程
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
