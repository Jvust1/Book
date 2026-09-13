import type {
  ModeItem,
  PracticeFilterId,
  PracticeLearningSlicePresentation,
  SourceRef,
} from '../api/types'
import { SourceLink } from './SourceLink'

const MISSING_CONTENT = '本段中文学习内容暂未提供'
const UNAVAILABLE_MESSAGE = '学习内容暂不可用'
const SOLUTION_UNAVAILABLE = '教材数据中暂未提供可验证解析'

export interface PracticeLearningSliceProps {
  courseId: string
  items: ModeItem[]
  presentation: PracticeLearningSlicePresentation
  selectedFilterId: PracticeFilterId
  onFilterChange: (filterId: PracticeFilterId) => void
  onBeforeSourceNavigate: (sourceId: string) => void
}

const sourceKey = (ref: SourceRef): string => `${ref.kind}:${ref.source_id}`

export function PracticeLearningSlice({
  courseId,
  items,
  presentation,
  selectedFilterId,
  onFilterChange,
  onBeforeSourceNavigate,
}: PracticeLearningSliceProps) {
  const itemByKey = new Map(items.map((item) => [sourceKey(item), item]))
  const statusByKey = new Map(
    presentation.items.map((item) => [sourceKey(item.source_ref), item.solution_status]),
  )
  const selectedFilter = presentation.filters.find(
    (candidate) => candidate.id === selectedFilterId,
  )
  const selectedRows = selectedFilter?.source_refs.map((ref) => ({
    ref,
    item: itemByKey.get(sourceKey(ref)),
    solutionStatus: statusByKey.get(sourceKey(ref)),
  }))

  const allRefsValid =
    presentation.mode === 'practice' &&
    presentation.filters.every((filter) =>
      filter.source_refs.every(
        (ref) => ref.kind === 'object' && itemByKey.has(sourceKey(ref)),
      ),
    ) &&
    presentation.items.every(
      (item) =>
        item.source_ref.kind === 'object' &&
        itemByKey.has(sourceKey(item.source_ref)) &&
        item.solution_status === 'unavailable',
    )
  const selectedValid =
    selectedFilter !== undefined &&
    selectedRows !== undefined &&
    selectedRows.every(
      ({ item, solutionStatus }) => item !== undefined && solutionStatus === 'unavailable',
    )

  if (!allRefsValid || !selectedValid || !selectedRows) {
    return (
      <div className="status-panel" role="alert">
        <p>{UNAVAILABLE_MESSAGE}</p>
      </div>
    )
  }

  return (
    <section className="practice-learning-slice page-stack" aria-labelledby="practice-learning-title">
      <header className="learning-slice-heading">
        <p className="eyebrow">教材原题范围</p>
        <h2 id="practice-learning-title">练习与习题</h2>
        <p className="secondary-text">仅按教材对象类型筛选，不推断答案或解析。</p>
      </header>

      <div className="mode-tabs practice-filter-tabs" role="group" aria-label="练习范围">
        {presentation.filters.map((filter) => (
          <button
            aria-pressed={filter.id === selectedFilterId}
            className="mode-tab"
            data-active={filter.id === selectedFilterId ? 'true' : 'false'}
            key={filter.id}
            onClick={() => onFilterChange(filter.id)}
            type="button"
          >
            {filter.label}
          </button>
        ))}
      </div>

      <p className="secondary-text">显示 {selectedRows.length} / {presentation.items.length}</p>

      {selectedRows.length === 0 ? (
        <p className="empty-state">本节暂无教材练习或习题</p>
      ) : (
        <div className="learning-list">
          {selectedRows.map(({ ref, item }) => {
            if (!item) return null
            const title = item.title_zh || item.number || item.type_zh || '教材题目'
            const content = item.content_zh || MISSING_CONTENT

            return (
              <article className="learning-card" key={sourceKey(ref)}>
                <header className="learning-card-header">
                  <div>
                    <p className="object-type">
                      <span>{item.type_zh || '教材题目'}</span>
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

                {item.formula ? <div className="formula-block">{item.formula}</div> : null}
                <p className="learning-content">{content}</p>
                <p className="practice-explanation">{SOLUTION_UNAVAILABLE}</p>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
