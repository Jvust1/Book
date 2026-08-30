import type {
  LearningSliceDerivedPrompt,
  ModeItem,
  PreviewLearningSlicePresentation,
  SourceRef,
} from '../api/types'
import { SourceLink } from './SourceLink'

const MISSING_CONTENT = '本段中文学习内容暂未提供'
const UNAVAILABLE = '学习内容暂不可用'

export interface PreviewLearningSliceProps {
  courseId: string
  items: ModeItem[]
  presentation: PreviewLearningSlicePresentation
  expandedSourceIds: string[]
  onExpandedChange: (sourceId: string, expanded: boolean) => void
  onBeforeSourceNavigate: (sourceId: string) => void
}

const sourceKey = ({ kind, source_id }: SourceRef): string => `${kind}:${source_id}`

const itemLabel = (item: ModeItem): string =>
  item.title_zh || item.number || item.type_zh || item.title_en || '教材对象'

export function PreviewLearningSlice({
  courseId,
  items,
  presentation,
  expandedSourceIds,
  onExpandedChange,
  onBeforeSourceNavigate,
}: PreviewLearningSliceProps) {
  const itemMap = new Map(items.map((item) => [sourceKey(item), item]))
  const refs: SourceRef[] = [
    ...presentation.objectives.map((prompt) => prompt.source_ref),
    ...presentation.prerequisites.items,
    ...presentation.core_definitions,
    ...presentation.core_formulas,
    ...presentation.key_figures,
    ...presentation.quick_checks.map((prompt) => prompt.source_ref),
  ]

  if (refs.some((ref) => !itemMap.has(sourceKey(ref)))) {
    return (
      <section className="status-panel" role="alert">
        <p>{UNAVAILABLE}</p>
      </section>
    )
  }

  const resolve = (ref: SourceRef): ModeItem => itemMap.get(sourceKey(ref))!

  const sourceLink = (ref: SourceRef) => (
    <SourceLink
      courseId={courseId}
      kind={ref.kind}
      onNavigate={() => onBeforeSourceNavigate(ref.source_id)}
      sourceId={ref.source_id}
    />
  )

  const renderReferenceSection = (
    heading: string,
    refsForSection: SourceRef[],
    renderDetail?: (item: ModeItem) => React.ReactNode,
  ) => {
    if (refsForSection.length === 0) return null
    return (
      <section className="preview-block">
        <h3>{heading}</h3>
        <div className="preview-reference-list">
          {refsForSection.map((ref) => {
            const item = resolve(ref)
            return (
              <article className="preview-reference-card" key={sourceKey(ref)}>
                <div>
                  <p className="object-type">
                    {item.type_zh || item.object_type || '教材对象'}
                    {item.number ? ` · ${item.number}` : ''}
                  </p>
                  <p className="preview-reference-title">{itemLabel(item)}</p>
                  {renderDetail?.(item)}
                </div>
                {sourceLink(ref)}
              </article>
            )
          })}
        </div>
      </section>
    )
  }

  const renderPromptList = (prompts: LearningSliceDerivedPrompt[]) => {
    if (prompts.length === 0) return null
    return (
      <ul className="preview-prompt-list">
        {prompts.map((prompt) => (
          <li key={`${sourceKey(prompt.source_ref)}:${prompt.text}`}>
            <span>{prompt.text}</span>
            {sourceLink(prompt.source_ref)}
          </li>
        ))}
      </ul>
    )
  }

  return (
    <div className="preview-learning-slice">
      <section className="preview-panel">
        <div className="preview-panel-heading">
          <div>
            <p className="eyebrow">Preview · learning_slice_v1</p>
            <h2>预习概览</h2>
          </div>
          <div className="preview-overview-row" aria-label="预习教材概览">
            <span className="count-chip">教材对象 {presentation.overview.object_count}</span>
            <span className="count-chip">教材图示 {presentation.overview.figure_count}</span>
            <span className="count-chip">
              {presentation.overview.translation_available ? '中文学习层可用' : '中文学习层暂不可用'}
            </span>
          </div>
        </div>

        {presentation.object_counts.length > 0 ? (
          <div className="preview-summary" aria-label="教材对象类型统计">
            {presentation.object_counts.map(({ object_type, count }) => (
              <span className="count-chip" key={object_type}>
                {object_type} {count}
              </span>
            ))}
          </div>
        ) : null}

        <p className="preview-guidance">
          以下学习目标与自检问题为系统学习引导，不是教材原文。
        </p>
      </section>

      {presentation.objectives.length > 0 ? (
        <section className="preview-block">
          <h3>学习目标</h3>
          {renderPromptList(presentation.objectives)}
        </section>
      ) : null}

      <section className="preview-block">
        <h3>前置知识</h3>
        <p className="secondary-text">暂无可验证的前置知识关系</p>
      </section>

      {renderReferenceSection('核心定义', presentation.core_definitions)}
      {renderReferenceSection('核心公式', presentation.core_formulas, (item) =>
        item.formula ? <div className="formula-block">{item.formula}</div> : null,
      )}
      {renderReferenceSection('教材图示', presentation.key_figures)}

      {presentation.quick_checks.length > 0 ? (
        <section className="preview-block">
          <h3>快速自检</h3>
          <div className="quick-check-list">
            {presentation.quick_checks.map((prompt) => {
              const item = resolve(prompt.source_ref)
              const expanded = expandedSourceIds.includes(item.source_id)
              const normalizedType = (item.object_type || '').trim().toLowerCase()
              const revealed =
                normalizedType === 'formula' && item.formula
                  ? item.formula
                  : item.content_zh || item.formula || MISSING_CONTENT

              return (
                <article className="quick-check-card" key={`${sourceKey(prompt.source_ref)}:${prompt.text}`}>
                  <p className="quick-check-question">{prompt.text}</p>
                  <div className="quick-check-actions">
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => onExpandedChange(item.source_id, !expanded)}
                    >
                      {expanded ? '收起教材内容' : '显示教材内容'}
                    </button>
                    {sourceLink(prompt.source_ref)}
                  </div>
                  {expanded ? (
                    normalizedType === 'formula' && item.formula ? (
                      <div className="formula-block">{revealed}</div>
                    ) : (
                      <p className="learning-content">{revealed}</p>
                    )
                  ) : null}
                </article>
              )
            })}
          </div>
        </section>
      ) : null}
    </div>
  )
}
