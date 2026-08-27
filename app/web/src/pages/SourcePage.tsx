import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { ApiError, bookApi } from '../api/client'
import type { LearningMode, SourceContextItem, SourceResponse } from '../api/types'
import { loadQASessionState } from '../state/qaSessionState'
import { loadSearchViewState } from '../state/searchViewState'
import { loadSectionViewState } from '../state/sectionViewState'

const RETURN_MODES: readonly LearningMode[] = ['preview', 'learn', 'review', 'practice']

const errorMessage = (error: unknown, fallback: string): string =>
  error instanceof ApiError ? error.message : fallback

const contextLabel = (item: SourceContextItem): string =>
  item.title_zh || item.number || item.type || `${item.kind}:${item.source_id}`

export function SourcePage() {
  const { courseId, kind, sourceId } = useParams()
  const navigate = useNavigate()
  const [source, setSource] = useState<SourceResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!courseId || !kind || !sourceId) {
      setError('教材来源地址无效')
      return
    }

    let active = true
    setSource(null)
    setError(null)
    bookApi
      .getSource(courseId, kind, sourceId)
      .then((value) => {
        if (active) setSource(value)
      })
      .catch((reason: unknown) => {
        if (active) setError(errorMessage(reason, '教材来源加载失败，请稍后重试'))
      })

    return () => {
      active = false
    }
  }, [courseId, kind, sourceId])

  const matchingQAState = (() => {
    if (!courseId || !source) return null
    const saved = loadQASessionState(courseId)
    if (saved?.activeCitationSourceId === source.source_id) return saved
    return null
  })()

  const matchingSearchState = (() => {
    if (!courseId || !source) return null
    const saved = loadSearchViewState(courseId)
    if (saved?.activeSourceKey === `${source.kind}:${source.source_id}`) return saved
    return null
  })()

  const returnToPrevious = () => {
    if (!courseId || !source) return
    const sourceKey = `${source.kind}:${source.source_id}`

    const savedQA = loadQASessionState(courseId)
    if (savedQA?.activeCitationSourceId === source.source_id) {
      navigate(savedQA.route)
      return
    }

    const savedSearch = loadSearchViewState(courseId)
    if (savedSearch?.activeSourceKey === sourceKey) {
      navigate(savedSearch.route)
      return
    }

    if (source.section_id) {
      for (const mode of RETURN_MODES) {
        const saved = loadSectionViewState(courseId, source.section_id, mode)
        if (saved?.activeSourceId === source.source_id) {
          navigate(saved.route)
          return
        }
      }
      navigate(
        `/courses/${encodeURIComponent(courseId)}/sections/${encodeURIComponent(source.section_id)}?mode=learn`,
      )
      return
    }

    navigate(`/courses/${encodeURIComponent(courseId)}`)
  }

  if (!courseId || !kind || !sourceId) {
    return (
      <section className="status-panel" role="alert">
        <h1>教材来源地址无效</h1>
      </section>
    )
  }

  if (error) {
    return (
      <section className="status-panel" role="alert">
        <h1>教材来源加载失败</h1>
        <p>{error}</p>
      </section>
    )
  }

  if (!source) {
    return <p role="status">正在读取教材来源…</p>
  }

  return (
    <section className="source-page page-stack">
      <header className="page-heading source-heading">
        <p className="eyebrow">结构化教材定位</p>
        <h1>教材来源</h1>
        <h2>{source.title_zh || source.number || source.type_zh}</h2>
        {source.title_en ? <p className="secondary-text">{source.title_en}</p> : null}
      </header>

      <div className="source-facts" aria-label="教材来源定位">
        <p>教材页：{source.printed_page ?? '暂缺'}</p>
        <p>PDF 页：{source.pdf_page ?? '暂缺'}</p>
        <p>{source.source_anchor || '教材锚点暂未提供'}</p>
        <p>结构化来源：{source.kind}:{source.source_id}</p>
        {source.source_batch ? <p>来源批次：{source.source_batch}</p> : null}
      </div>

      {source.formula ? <div className="formula-block">{source.formula}</div> : null}
      <p className="learning-content">
        {source.content_zh || '本段中文学习内容暂未提供'}
      </p>

      <section className="source-context" aria-label="来源上下文">
        {source.context_before.map((item) => (
          <article className="context-item" key={`before:${item.kind}:${item.source_id}`}>
            <p className="eyebrow">前文</p>
            <p>{contextLabel(item)}</p>
          </article>
        ))}

        <article className="context-item current-context" aria-current="true">
          <p className="eyebrow">当前来源</p>
          <p>{source.title_zh || source.number || source.type_zh}</p>
        </article>

        {source.context_after.map((item) => (
          <article className="context-item" key={`after:${item.kind}:${item.source_id}`}>
            <p className="eyebrow">后文</p>
            <p>{contextLabel(item)}</p>
          </article>
        ))}
      </section>

      <button className="secondary-button" type="button" onClick={returnToPrevious}>
        {matchingQAState ? '返回问答' : matchingSearchState ? '返回搜索' : '返回学习'}
      </button>
    </section>
  )
}
