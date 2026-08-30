import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type {
  ModeItem,
  PracticeLearningSlicePresentation,
} from '../api/types'
import { PracticeLearningSlice } from './PracticeLearningSlice'

const exerciseItem: ModeItem = {
  kind: 'object',
  source_id: 'ex_practice',
  object_type: 'exercise',
  type_zh: '练习',
  number: '1',
  title_zh: '练习甲',
  title_en: null,
  formula: null,
  printed_page: 10,
  pdf_page: 20,
  content_zh: '练习甲教材正文。',
  translation_available: true,
}

const problemItem: ModeItem = {
  kind: 'object',
  source_id: 'prob_practice',
  object_type: 'problem',
  type_zh: '习题',
  number: '2',
  title_zh: '习题乙',
  title_en: null,
  formula: null,
  printed_page: 11,
  pdf_page: 21,
  content_zh: '习题乙教材正文。',
  translation_available: true,
}

const presentation: PracticeLearningSlicePresentation = {
  schema_version: 'learning_slice_v1',
  mode: 'practice',
  filters: [
    {
      id: 'all',
      label: '全部',
      source_refs: [
        { kind: 'object', source_id: 'ex_practice' },
        { kind: 'object', source_id: 'prob_practice' },
      ],
    },
    {
      id: 'exercise',
      label: '练习',
      source_refs: [{ kind: 'object', source_id: 'ex_practice' }],
    },
    {
      id: 'problem',
      label: '习题',
      source_refs: [{ kind: 'object', source_id: 'prob_practice' }],
    },
  ],
  items: [
    {
      source_ref: { kind: 'object', source_id: 'ex_practice' },
      solution_status: 'unavailable',
    },
    {
      source_ref: { kind: 'object', source_id: 'prob_practice' },
      solution_status: 'unavailable',
    },
  ],
}

function renderPractice(
  overrides: Partial<React.ComponentProps<typeof PracticeLearningSlice>> = {},
) {
  const props: React.ComponentProps<typeof PracticeLearningSlice> = {
    courseId: 'functional_analysis_course',
    items: [exerciseItem, problemItem],
    presentation,
    selectedFilterId: 'all',
    expandedSourceIds: [],
    onFilterChange: vi.fn(),
    onExpandedChange: vi.fn(),
    onBeforeSourceNavigate: vi.fn(),
    ...overrides,
  }

  render(
    <MemoryRouter>
      <PracticeLearningSlice {...props} />
    </MemoryRouter>,
  )
  return props
}

describe('PracticeLearningSlice', () => {
  it('renders only filters supplied by presentation and reports selected filter', async () => {
    const user = userEvent.setup()
    const props = renderPractice({
      selectedFilterId: 'exercise',
      presentation: {
        ...presentation,
        filters: presentation.filters.filter((filter) => filter.id !== 'problem'),
      },
    })

    expect(screen.getByRole('button', { name: '全部' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: '练习' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.queryByRole('button', { name: '习题' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '全部' }))
    expect(props.onFilterChange).toHaveBeenCalledWith('all')
  })

  it('renders exactly the selected filter refs and the filtered count', () => {
    renderPractice({ selectedFilterId: 'exercise' })

    expect(screen.getByText('练习甲')).toBeInTheDocument()
    expect(screen.queryByText('习题乙')).not.toBeInTheDocument()
    expect(screen.getByText('显示 1 / 2')).toBeInTheDocument()
  })

  it('shows exact unavailable-solution wording and introduces no answer controls', () => {
    renderPractice({ selectedFilterId: 'all' })

    expect(screen.getAllByText('教材数据中暂未提供可验证解析')).toHaveLength(2)
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /正确|错误|提交答案/ })).not.toBeInTheDocument()
  })

  it('uses page-level expansion and canonical source navigation only', async () => {
    const user = userEvent.setup()
    const onExpandedChange = vi.fn()
    const onBeforeSourceNavigate = vi.fn()
    renderPractice({
      selectedFilterId: 'exercise',
      onExpandedChange,
      onBeforeSourceNavigate,
    })

    await user.click(screen.getByRole('button', { name: '收起教材内容' }))
    expect(onExpandedChange).toHaveBeenCalledWith('ex_practice', false)

    await user.click(screen.getByRole('link', { name: '查看教材来源' }))
    expect(onBeforeSourceNavigate).toHaveBeenCalledWith('ex_practice')
  })

  it('fails closed when a filter ref is not in current mode items', () => {
    renderPractice({
      presentation: {
        ...presentation,
        filters: presentation.filters.map((filter) =>
          filter.id === 'exercise'
            ? {
                ...filter,
                source_refs: [{ kind: 'object', source_id: 'missing_source' }],
              }
            : filter,
        ),
      },
      selectedFilterId: 'exercise',
    })

    expect(screen.getByRole('alert')).toHaveTextContent('学习内容暂不可用')
  })
})
