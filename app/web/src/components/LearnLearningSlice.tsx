import type {
  LearnLearningSlicePresentation,
  LearningSliceGroup,
  ModeItem,
  SourceRef,
} from '../api/types'
import { FigureReferenceCard } from './FigureReferenceCard'
import { LearningObjectCard } from './LearningObjectCard'
import { SourceLink } from './SourceLink'

const UNAVAILABLE_MESSAGE = '学习内容暂不可用'

export interface LearnLearningSliceProps {
  courseId: string
  items: ModeItem[]
  presentation: LearnLearningSlicePresentation
  expandedSourceIds: string[]
  onExpandedChange: (sourceId: string, expanded: boolean) => void
  onBeforeSourceNavigate: (sourceId: string) => void
}

const sourceKey = ({ kind, source_id }: SourceRef): string => kind + ':' + source_id

function TranslationReferenceCard({
  courseId,
  item,
  onBeforeSourceNavigate,
}: {
  courseId: string
  item: ModeItem
  onBeforeSourceNavigate: (sourceId: string) => void
}) {
  return (
    <article
      className="learning-card translation-reference-card"
      data-testid={'translation-reference-' + item.source_id}
    >
      <header className="learning-card-header">
        <div>
          <p className="object-type">中文学习层</p>
          <h3>中文学习层</h3>
          <p className="secondary-text">
            {item.translation_available ? '中文学习层可用' : '中文学习层暂不可用'}
          </p>
        </div>
        <SourceLink
          courseId={courseId}
          kind={item.kind}
          onNavigate={() => onBeforeSourceNavigate(item.source_id)}
          sourceId={item.source_id}
        />
      </header>
    </article>
  )
}

function validGroupRef(group: LearningSliceGroup, ref: SourceRef, item: ModeItem): boolean {
  if (item.kind !== ref.kind) return false
  if (group.id === 'figures') return ref.kind === 'figure'
  if (group.id === 'translations') return ref.kind === 'translation'
  return ref.kind === 'object'
}

export function LearnLearningSlice({
  courseId,
  items,
  presentation,
  expandedSourceIds,
  onExpandedChange,
  onBeforeSourceNavigate,
}: LearnLearningSliceProps) {
  const itemByKey = new Map(items.map((item) => [sourceKey(item), item]))
  const refs = presentation.groups.flatMap((group) => group.source_refs)
  const seen = new Set<string>()
  const valid =
    presentation.mode === 'learn' &&
    presentation.groups.every((group) =>
      group.source_refs.every((ref) => {
        const key = sourceKey(ref)
        const item = itemByKey.get(key)
        if (!item || seen.has(key) || !validGroupRef(group, ref, item)) return false
        seen.add(key)
        return true
      }),
    )

  if (!valid) {
    return (
      <div className="status-panel" role="alert">
        <p>{UNAVAILABLE_MESSAGE}</p>
      </div>
    )
  }

  return (
    <section className="learn-learning-slice page-stack" aria-labelledby="learn-learning-title">
      <header className="learning-slice-heading">
        <p className="eyebrow">教材结构化学习</p>
        <h2 id="learn-learning-title">学习分组</h2>
        <p className="secondary-text">按教材对象类型组织，内容仍来自当前教材来源。</p>
      </header>

      {refs.length === 0 ? (
        <p className="empty-state">本节暂无可学习的教材对象</p>
      ) : (
        <div className="learn-groups">
          {presentation.groups.map((group) => (
            <section className="learn-group" data-group-id={group.id} key={group.id}>
              <h2>{group.label}</h2>
              <div className="learning-list">
                {group.source_refs.map((ref) => {
                  const item = itemByKey.get(sourceKey(ref))
                  if (!item) return null
                  if (ref.kind === 'figure') {
                    return (
                      <FigureReferenceCard
                        courseId={courseId}
                        item={item}
                        key={sourceKey(ref)}
                        onBeforeSourceNavigate={onBeforeSourceNavigate}
                      />
                    )
                  }
                  if (ref.kind === 'translation') {
                    return (
                      <TranslationReferenceCard
                        courseId={courseId}
                        item={item}
                        key={sourceKey(ref)}
                        onBeforeSourceNavigate={onBeforeSourceNavigate}
                      />
                    )
                  }
                  return (
                    <LearningObjectCard
                      courseId={courseId}
                      expanded={expandedSourceIds.includes(item.source_id)}
                      item={item}
                      key={sourceKey(ref)}
                      mode="learn"
                      onBeforeSourceNavigate={() => onBeforeSourceNavigate(item.source_id)}
                      onExpandedChange={(expanded) =>
                        onExpandedChange(item.source_id, expanded)
                      }
                    />
                  )
                })}
              </div>
            </section>
          ))}
        </div>
      )}
    </section>
  )
}
