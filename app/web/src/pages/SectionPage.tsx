import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { LearningMode, ModeResponse, SectionResponse } from '../api/types'
import { EmptyState } from '../components/EmptyState'
import { LearningObjectCard } from '../components/LearningObjectCard'
import { ModeTabs } from '../components/ModeTabs'
import { loadSectionViewState, saveSectionViewState } from '../state/sectionViewState'

const VALID_MODES: readonly LearningMode[] = ['preview', 'learn', 'review', 'practice']

const isLearningMode = (value: string | null): value is LearningMode =>
  value !== null && VALID_MODES.includes(value as LearningMode)

const errorMessage = (error: unknown, fallback: string): string =>
  error instanceof ApiError ? error.message : fallback

const emptyMessage = (mode: LearningMode): string | null => {
  if (mode === 'review') return '本节暂无可复习的教材核心对象'
  if (mode === 'practice') return '本节暂无教材练习或习题'
  return null
}

export function SectionPage() {
  const { courseId, sectionId } = useParams()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawMode = searchParams.get('mode')
  const mode: LearningMode = isLearningMode(rawMode) ? rawMode : 'learn'

  const [section, setSection] = useState<SectionResponse | null>(null)
  const [sectionError, setSectionError] = useState<string | null>(null)
  const [payload, setPayload] = useState<ModeResponse | null>(null)
  const [modeError, setModeError] = useState<string | null>(null)
  const [expandedSourceIds, setExpandedSourceIds] = useState<string[]>([])
  const restoredKeyRef = useRef<string | null>(null)

  useEffect(() => {
    if (isLearningMode(rawMode)) return
    const next = new URLSearchParams(searchParams)
    next.set('mode', 'learn')
    setSearchParams(next, { replace: true })
  }, [rawMode, searchParams, setSearchParams])

  useEffect(() => {
    if (!courseId || !sectionId) {
      setSectionError('小节地址无效')
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
        if (active) setSectionError(errorMessage(reason, '小节加载失败，请稍后重试'))
      })

    return () => {
      active = false
    }
  }, [courseId, sectionId])

  useEffect(() => {
    if (!courseId || !sectionId) return

    let active = true
    setPayload(null)
    setModeError(null)
    bookApi
      .getMode(courseId, sectionId, mode)
      .then((value) => {
        if (active) setPayload(value)
      })
      .catch((reason: unknown) => {
        if (active) setModeError(errorMessage(reason, '学习内容加载失败，请稍后重试'))
      })

    return () => {
      active = false
    }
  }, [courseId, mode, sectionId])

  useEffect(() => {
    setExpandedSourceIds([])
    restoredKeyRef.current = null
  }, [courseId, mode, sectionId])

  useEffect(() => {
    if (!courseId || !sectionId || !payload) return
    const restoreKey = `${courseId}:${sectionId}:${mode}`
    if (restoredKeyRef.current === restoreKey) return

    const saved = loadSectionViewState(courseId, sectionId, mode)
    if (saved) {
      setExpandedSourceIds(saved.expandedSourceIds)
      window.scrollTo({ top: saved.scrollY, behavior: 'auto' })
    }
    restoredKeyRef.current = restoreKey
  }, [courseId, mode, payload, sectionId])

  const previewCounts = useMemo(() => {
    if (mode !== 'preview' || !payload) return []
    const counts = new Map<string, number>()
    for (const item of payload.items) {
      const label = item.type_zh || item.object_type || '教材对象'
      counts.set(label, (counts.get(label) || 0) + 1)
    }
    return [...counts.entries()]
  }, [mode, payload])

  const switchMode = (nextMode: LearningMode) => {
    const next = new URLSearchParams(searchParams)
    next.set('mode', nextMode)
    setSearchParams(next)
  }

  const setSourceExpanded = (sourceId: string, expanded: boolean) => {
    setExpandedSourceIds((current) => {
      if (expanded) {
        return current.includes(sourceId) ? current : [...current, sourceId]
      }
      return current.filter((value) => value !== sourceId)
    })
  }

  const saveBeforeSourceNavigation = (sourceId: string) => {
    if (!courseId || !sectionId) return
    const routeParams = new URLSearchParams(location.search)
    routeParams.set('mode', mode)
    saveSectionViewState(courseId, sectionId, mode, {
      route: `${location.pathname}?${routeParams.toString()}`,
      scrollY: window.scrollY,
      expandedSourceIds,
      activeSourceId: sourceId,
    })
  }

  if (!courseId || !sectionId) {
    return (
      <section className="status-panel" role="alert">
        <h1>小节地址无效</h1>
      </section>
    )
  }

  if (sectionError) {
    return (
      <section className="status-panel" role="alert">
        <h1>小节加载失败</h1>
        <p>{sectionError}</p>
      </section>
    )
  }

  return (
    <section className="section-page page-stack">
      {section?.chapter_id ? (
        <Link className="back-link" to={`/courses/${courseId}/chapters/${section.chapter_id}`}>
          ← 返回章节
        </Link>
      ) : (
        <Link className="back-link" to={`/courses/${courseId}`}>
          ← 返回课程
        </Link>
      )}

      <header className="page-heading section-heading">
        <p className="eyebrow">{section?.section.number || '教材小节'}</p>
        <h1>{section?.section.title_zh || (section ? '中文标题暂未提供' : '正在读取小节…')}</h1>
        {section?.section.title_en ? <p className="secondary-text">{section.section.title_en}</p> : null}
        {section ? (
          <p className="page-range">
            教材页 {section.section.printed_page_start ?? '暂缺'}
            {section.section.printed_page_end != null &&
            section.section.printed_page_end !== section.section.printed_page_start
              ? `–${section.section.printed_page_end}`
              : ''}
            {' · '}PDF {section.section.pdf_page_start ?? '暂缺'}
            {section.section.pdf_page_end != null &&
            section.section.pdf_page_end !== section.section.pdf_page_start
              ? `–${section.section.pdf_page_end}`
              : ''}
          </p>
        ) : null}
      </header>

      <ModeTabs mode={mode} onChange={switchMode} />

      {modeError ? (
        <div className="status-panel" role="alert">
          <h2>学习内容加载失败</h2>
          <p>{modeError}</p>
        </div>
      ) : null}

      {!payload && !modeError ? <p role="status">正在读取学习内容…</p> : null}

      {payload && mode === 'preview' && previewCounts.length > 0 ? (
        <div className="preview-summary" aria-label="本节教材对象统计">
          {previewCounts.map(([label, count]) => (
            <span className="count-chip" key={label}>
              {label} {count}
            </span>
          ))}
        </div>
      ) : null}

      {payload && payload.items.length === 0 && emptyMessage(mode) ? (
        <EmptyState message={emptyMessage(mode)!} />
      ) : null}

      {payload && payload.items.length > 0 ? (
        <div className="learning-list">
          {payload.items.map((item) => (
            <LearningObjectCard
              courseId={courseId}
              expanded={expandedSourceIds.includes(item.source_id)}
              item={item}
              key={`${item.kind}:${item.source_id}`}
              mode={mode}
              onBeforeSourceNavigate={() => saveBeforeSourceNavigation(item.source_id)}
              onExpandedChange={(expanded) => setSourceExpanded(item.source_id, expanded)}
            />
          ))}
        </div>
      ) : null}
    </section>
  )
}
