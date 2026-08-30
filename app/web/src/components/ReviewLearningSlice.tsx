import type {
  ModeItem,
  ReviewLearningSlicePresentation,
  ReviewPresetId,
  SourceRef,
} from '../api/types'
import { SourceLink } from './SourceLink'

const MISSING_CONTENT = '本段中文学习内容暂未提供'
const UNAVAILABLE_MESSAGE = '学习内容暂不可用'

export interface ReviewLearningSliceProps {
  courseId: string
  items: ModeItem[]
  presentation: ReviewLearningSlicePresentation
  selectedPresetId: ReviewPresetId
  expandedSourceIds: string[]
  onPresetChange: (presetId: ReviewPresetId) => void
  onExpandedChange: (sourceId: string, expanded: boolean) => void
  onBeforeSourceNavigate: (sourceId: string) => void
}

const sourceKey = (ref: SourceRef): string => `${ref.kind}:${ref.source_id}`

export function ReviewLearningSlice({
  courseId,
  items,
  presentation,
  selectedPresetId,
  expandedSourceIds,
  onPresetChange,
  onExpandedChange,
  onBeforeSourceNavigate,
}: ReviewLearningSliceProps) {
  const preset = presentation.presets.find((candidate) => candidate.id === selectedPresetId)
  const itemByKey = new Map(items.map((item) => [sourceKey(item), item]))
  const promptByKey = new Map(
    presentation.prompts.map((prompt) => [sourceKey(prompt.source_ref), prompt]),
  )

  const selectedRows = preset?.source_refs.map((ref) => ({
    ref,
    item: itemByKey.get(sourceKey(ref)),
    prompt: promptByKey.get(sourceKey(ref)),
  }))
  const valid =
    presentation.mode === 'review' &&
    preset !== undefined &&
    selectedRows !== undefined &&
    selectedRows.every(
      ({ ref, item, prompt }) =>
        ref.kind === 'object' && item !== undefined && prompt !== undefined,
    )

  if (!valid || !selectedRows) {
    return (
      <div className="status-panel" role="alert">
        <p>{UNAVAILABLE_MESSAGE}</p>
      </div>
    )
  }

  return (
    <section className="review-learning-slice page-stack" aria-labelledby="review-learning-title">
      <header className="learning-slice-heading">
        <p className="eyebrow">确定性复习范围</p>
        <h2 id="review-learning-title">复习计划</h2>
        <p className="secondary-text">先回忆，再按需显示教材原文。</p>
      </header>

      <div className="mode-tabs review-preset-tabs" role="group" aria-label="复习范围">
        {presentation.presets.map((candidate) => (
          <button
            aria-pressed={candidate.id === selectedPresetId}
            className="mode-tab"
            data-active={candidate.id === selectedPresetId ? 'true' : 'false'}
            key={candidate.id}
            onClick={() => onPresetChange(candidate.id)}
            type="button"
          >
            {candidate.label}
          </button>
        ))}
      </div>

      {selectedRows.length === 0 ? (
        <p className="empty-state">本节暂无可复习的教材核心对象</p>
      ) : (
        <div className="learning-list">
          {selectedRows.map(({ ref, item, prompt }) => {
            if (!item || !prompt) return null
            const expanded = expandedSourceIds.includes(item.source_id)
            const title = item.title_zh || item.number || item.type_zh || '教材对象'
            const content = item.content_zh || MISSING_CONTENT

            return (
              <article className="learning-card" key={sourceKey(ref)}>
                <header className="learning-card-header">
                  <div>
                    <p className="object-type">
                      <span>{item.type_zh || '教材对象'}</span>
                      {item.number ? <span> · {item.number}</span> : null}
                    </p>
                    <h3>{title}</h3>
                    {item.title_en ? <p className="secondary-text">{item.title_en}</p> : null}
                  </div>
                  <SourceLink
                    courseId={courseId}
                    kind={item.kind}
                    onNavigate={() => onBeforeSourceNavigate(item.source_id)}
                    sourceId={item.source_id}
                  />
                </header>

                <p className="review-recall-prompt">{prompt.text}</p>

                <button
                  className="secondary-button"
                  onClick={() => onExpandedChange(item.source_id, !expanded)}
                  type="button"
                >
                  {expanded ? '收起教材内容' : '显示教材内容'}
                </button>

                {expanded ? (
                  <div className="review-source-content">
                    {item.formula ? <div className="formula-block">{item.formula}</div> : null}
                    <p className="learning-content">{content}</p>
                  </div>
                ) : null}
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
