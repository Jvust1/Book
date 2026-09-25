import { useEffect, useState } from 'react'

import type { LearningMode, ModeItem } from '../api/types'
import { SourceLink } from './SourceLink'
import { FormulaBlock, RichText } from './RichText'

const MISSING_CONTENT = '本段中文学习内容暂未提供'

export interface LearningObjectCardProps {
  courseId: string
  item: ModeItem
  mode: LearningMode
  expanded?: boolean
  onExpandedChange?: (expanded: boolean) => void
  onBeforeSourceNavigate?: () => void
}

export function LearningObjectCard({
  courseId,
  item,
  mode,
  expanded,
  onExpandedChange,
  onBeforeSourceNavigate,
}: LearningObjectCardProps) {
  const [internalExpanded, setInternalExpanded] = useState(false)

  useEffect(() => {
    if (expanded === undefined) setInternalExpanded(false)
  }, [expanded, item.source_id, mode])

  const reviewExpanded = expanded ?? internalExpanded
  const title = item.title_zh || item.number || item.type_zh || '教材对象'
  const content = item.content_zh || MISSING_CONTENT
  const showBody = mode === 'learn' || mode === 'practice' || (mode === 'review' && reviewExpanded)

  const expandReview = () => {
    if (expanded === undefined) setInternalExpanded(true)
    onExpandedChange?.(true)
  }

  return (
    <article className="learning-card">
      <header className="learning-card-header">
        <div>
          <p className="object-type">
            <span>{item.type_zh || '教材对象'}</span>
            {item.number ? <span> · {item.number}</span> : null}
          </p>
          <h2>{title}</h2>
          {item.title_en ? <p className="secondary-text">{item.title_en}</p> : null}
        </div>
        <SourceLink
          courseId={courseId}
          kind={item.kind}
          onNavigate={onBeforeSourceNavigate}
          sourceId={item.source_id}
        />
      </header>

      {item.formula ? <FormulaBlock formula={item.formula} /> : null}

      {mode === 'review' && !reviewExpanded ? (
        <button className="secondary-button" type="button" onClick={expandReview}>
          显示内容
        </button>
      ) : null}

      {showBody ? <RichText content={content} /> : null}

      {mode === 'practice' ? (
        <p className="practice-explanation">教材数据中暂未提供解析</p>
      ) : null}
    </article>
  )
}
