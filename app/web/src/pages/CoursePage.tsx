import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { CourseResponse } from '../api/types'

const errorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : '课程加载失败，请稍后重试'

export function CoursePage() {
  const { courseId } = useParams()
  const [loadedCourse, setCourse] = useState<CourseResponse | null>(null)
  const [failure, setFailure] = useState<{ courseId: string; message: string } | null>(null)
  const course = loadedCourse?.course.course_id === courseId ? loadedCourse : null
  const error = !courseId ? '课程地址无效' : failure?.courseId === courseId ? failure.message : null

  useEffect(() => {
    if (!courseId) return
    let active = true
    const controller = new AbortController()
    setCourse(null)
    setFailure(null)
    bookApi
      .getCourse(courseId, controller.signal)
      .then((value) => {
        if (active) setCourse(value)
      })
      .catch((reason: unknown) => {
        if (active) setFailure({ courseId, message: errorMessage(reason) })
      })
    return () => {
      active = false
      controller.abort()
    }
  }, [courseId])

  if (error) {
    return (
      <section className="status-panel" role="alert">
        <h1>课程加载失败</h1>
        <p>{error}</p>
      </section>
    )
  }

  if (!course) {
    return <p role="status">正在读取课程目录…</p>
  }

  return (
    <section className="page-stack">
      <Link className="back-link" to="/">← 返回教材库</Link>
      <header className="page-heading">
        <p className="eyebrow">{course.course.chapter_count} 章 · {course.section_count} 节</p>
        <h1>{course.course.name_zh}</h1>
        {course.course.name_en ? <p className="secondary-text">{course.course.name_en}</p> : null}
      </header>

      <div className="course-actions">
        <Link
          className="secondary-button course-search-link"
          to={`/courses/${encodeURIComponent(course.course.course_id)}/search`}
        >
          搜索教材
        </Link>
        <Link
          className="secondary-button course-search-link"
          to={`/courses/${encodeURIComponent(course.course.course_id)}/qa`}
        >
          教材问答
        </Link>
      </div>

      <div className="list-stack">
        {course.chapters.map((chapter) => (
          <article className="content-card compact-card" key={chapter.chapter_id}>
            <div>
              <p className="eyebrow">{chapter.number ? `第 ${chapter.number} 章` : '章节'}</p>
              <h2 data-testid="chapter-title">{chapter.title_zh || '中文标题暂未提供'}</h2>
              {chapter.title_en ? <p className="secondary-text">{chapter.title_en}</p> : null}
            </div>
            <div className="card-footer">
              <span>{chapter.section_count} 节</span>
              <Link
                className="primary-link"
                to={`/courses/${encodeURIComponent(course.course.course_id)}/chapters/${encodeURIComponent(chapter.chapter_id)}`}
              >
                进入章节
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
