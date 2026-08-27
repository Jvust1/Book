import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { ChapterResponse, SectionCard } from '../api/types'

const errorMessage = (error: unknown): string =>
  error instanceof ApiError ? error.message : '章节加载失败，请稍后重试'

const range = (
  printedStart: SectionCard['printed_page_start'],
  printedEnd: SectionCard['printed_page_end'],
  pdfStart: SectionCard['pdf_page_start'],
  pdfEnd: SectionCard['pdf_page_end'],
): string => {
  const printed = printedStart == null
    ? '教材页暂缺'
    : `教材页 ${printedStart}${printedEnd != null && printedEnd !== printedStart ? `–${printedEnd}` : ''}`
  const pdf = pdfStart == null
    ? 'PDF 页暂缺'
    : `PDF ${pdfStart}${pdfEnd != null && pdfEnd !== pdfStart ? `–${pdfEnd}` : ''}`
  return `${printed} · ${pdf}`
}

export function ChapterPage() {
  const { courseId, chapterId } = useParams()
  const [chapter, setChapter] = useState<ChapterResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!courseId || !chapterId) {
      setError('章节地址无效')
      return
    }
    let active = true
    bookApi
      .getChapter(courseId, chapterId)
      .then((value) => {
        if (active) setChapter(value)
      })
      .catch((reason: unknown) => {
        if (active) setError(errorMessage(reason))
      })
    return () => {
      active = false
    }
  }, [chapterId, courseId])

  if (error) {
    return (
      <section className="status-panel" role="alert">
        <h1>章节加载失败</h1>
        <p>{error}</p>
      </section>
    )
  }

  if (!chapter || !courseId) {
    return <p role="status">正在读取章节内容…</p>
  }

  return (
    <section className="page-stack">
      <Link className="back-link" to={`/courses/${courseId}`}>← 返回课程</Link>
      <header className="page-heading">
        <p className="eyebrow">{chapter.chapter.number ? `第 ${chapter.chapter.number} 章` : '章节'}</p>
        <h1>{chapter.chapter.title_zh || '中文标题暂未提供'}</h1>
        {chapter.chapter.title_en ? <p className="secondary-text">{chapter.chapter.title_en}</p> : null}
        <p>{chapter.sections.length} 节</p>
      </header>

      <div className="list-stack">
        {chapter.sections.map((section) => (
          <article className="content-card compact-card" key={section.section_id}>
            <div>
              <p className="eyebrow">{section.number || '小节'}</p>
              <h2>{section.title_zh || '中文标题暂未提供'}</h2>
              {section.title_en ? <p className="secondary-text">{section.title_en}</p> : null}
              <p className="page-range">
                {range(
                  section.printed_page_start,
                  section.printed_page_end,
                  section.pdf_page_start,
                  section.pdf_page_end,
                )}
              </p>
            </div>
            <div className="card-footer">
              <span />
              <Link
                className="primary-link"
                to={`/courses/${courseId}/sections/${section.section_id}`}
              >
                进入本节
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
