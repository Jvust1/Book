import type { ModeItem } from '../api/types'
import { SourceLink } from './SourceLink'

export interface FigureReferenceCardProps {
  courseId: string
  item: ModeItem
  onBeforeSourceNavigate: (sourceId: string) => void
}

export function FigureReferenceCard({
  courseId,
  item,
  onBeforeSourceNavigate,
}: FigureReferenceCardProps) {
  const title = item.title_zh || item.title_en || item.source_id
  const pageParts = [
    item.printed_page != null ? '教材页 ' + item.printed_page : null,
    item.pdf_page != null ? 'PDF ' + item.pdf_page : null,
  ].filter((value): value is string => value !== null)

  return (
    <article
      className="learning-card figure-reference-card"
      data-testid={'figure-reference-' + item.source_id}
    >
      <header className="learning-card-header">
        <div>
          <p className="object-type">教材图示</p>
          <h3>{title}</h3>
          {item.title_en && item.title_en !== item.title_zh ? (
            <p className="secondary-text">{item.title_en}</p>
          ) : null}
        </div>
        <SourceLink
          courseId={courseId}
          kind={item.kind}
          onNavigate={() => onBeforeSourceNavigate(item.source_id)}
          sourceId={item.source_id}
        />
      </header>
      {pageParts.length > 0 ? (
        <p className="secondary-text">{pageParts.join(' · ')}</p>
      ) : null}
    </article>
  )
}
