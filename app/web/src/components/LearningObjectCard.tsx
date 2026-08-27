import { useEffect, useState } from 'react'

import type { LearningMode, ModeItem } from '../api/types'
import { SourceLink } from './SourceLink'

const MISSING_CONTENT = '本段中文学习内容暂未提供'

export interface LearningObjectCardProps {
  courseId: string
  item: ModeItem
  mode: LearningMode
}

export function LearningObjectCard({ courseId, item, mode }: LearningObjectCardProps) {
  const [reviewExpanded, setReviewExpanded] = useState(false)

  useEffect(() => {
    setReviewExpanded(false)
  }, [item.source_id, mode])

  const title = item.title_zh || item.number || item.type_zh || '教材对象'
  const content = item.content_zh || MISSING_CONTENT
  const showBody = mode === 'learn' || mode === 'practice' || (mode === 'review' && reviewExpanded)

  return (
    <article className="learning-card">
      <header className="learning-card-header">
        <div>
          <p className="object-type">
            {item.type_zh || '教材对象'}
            {item.number ? ` · ${item.number}` : ''}
          </p>
          <h2>{title}</h2>
          {item.title_en ? <p className="secondary-text">{item.title_en}</p> : null}
        </div>
        <SourceLink courseId={courseId} kind={item.kind} sourceId={item.source_id} />
      </header>

      {item.formula ? <div className="formula-block">{item.formula}</div> : null}

      {mode === 'review' && !reviewExpanded ? (
        <button className="secondary-button" type="button" onClick={() => setReviewExpanded(true)}>
          显示内容
        </button>
      ) : null}

      {showBody ? <p className="learning-content">{content}</p> : null}

      {mode === 'practice' ? (
        <p className="practice-explanation">教材数据中暂未提供解析</p>
      ) : null}
    </article>
  )
}
