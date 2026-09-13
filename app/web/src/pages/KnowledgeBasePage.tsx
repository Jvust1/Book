import { useEffect, useState } from 'react'

import { ApiError, bookApi } from '../api/client'
import type { CourseResponse, LibraryResponse } from '../api/types'

const errorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : '知识库加载失败，请稍后重试'

export function KnowledgeBasePage() {
  const [library, setLibrary] = useState<LibraryResponse | null>(null)
  const [courses, setCourses] = useState<CourseResponse[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    bookApi.getLibrary()
      .then(async (value) => {
        if (!active) return
        setLibrary(value)
        const details = await Promise.all(value.courses.map((course) => bookApi.getCourse(course.course_id)))
        if (active) setCourses(details)
      })
      .catch((reason: unknown) => { if (active) setError(errorMessage(reason)) })
    return () => { active = false }
  }, [])

  if (error) return <section className="status-panel" role="alert"><h1>知识库加载失败</h1><p>{error}</p></section>
  if (!library) return <p role="status">正在读取知识库…</p>

  return (
    <section className="page-stack knowledge-page">
      <header className="page-heading">
        <p className="eyebrow">EXPLORE · 知识脉络</p>
        <h1>知识库</h1>
        <p>展开课程脉络，找到下一处想深入的知识。</p>
      </header>
      {courses.map((course) => (
        <section className="content-card knowledge-course" key={course.course.course_id}>
          <div>
            <p className="eyebrow">{course.course.runtime_status}</p>
            <h2>{course.course.name_zh}</h2>
            {course.course.name_en ? <p className="secondary-text">{course.course.name_en}</p> : null}
            <p className="secondary-text">{course.course.authors.join(' · ')} · {course.section_count} 个小节</p>
          </div>
          <div className="knowledge-chapters">
            {course.chapters.map((chapter) => (
              <div className="knowledge-chapter" key={chapter.chapter_id}>
                <strong>{chapter.number ? `第 ${chapter.number} 章` : '章节'} · {chapter.title_zh || '中文标题暂未提供'}</strong>
                {chapter.title_en ? <span>{chapter.title_en}</span> : null}
                <span className="secondary-text">{chapter.section_count} 个小节</span>
              </div>
            ))}
          </div>
        </section>
      ))}
    </section>
  )
}
