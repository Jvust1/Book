import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type {
  ModeItem,
  ReviewLearningSlicePresentation,
} from '../api/types'
import { ReviewLearningSlice } from './ReviewLearningSlice'

const definitionItem: ModeItem = {
  kind: 'object',
  source_id: 'def_review',
  object_type: 'definition',
  type_zh: '定义',
  number: '1.1',
  title_zh: '复习定义',
  title_en: null,
  formula: null,
  printed_page: 2,
  pdf_page: 21,
  content_zh: '定义教材正文。',
  translation_available: true,
}

const theoremItem: ModeItem = {
  kind: 'object',
  source_id: 'thm_review',
  object_type: 'theorem',
  type_zh: '定理',
  number: '1.2',
  title_zh: '复习定理',
  title_en: null,
  formula: null,
  printed_page: 3,
  pdf_page: 22,
  content_zh: '定理教材正文。',
  translation_available: true,
}

const formulaItem: ModeItem = {
  kind: 'object',
  source_id: 'formula_review',
  object_type: 'formula',
  type_zh: '公式',
  number: '(1.3)',
  title_zh: '复习公式',
  title_en: null,
  formula: '||f||_p < ∞',
  printed_page: 3,
  pdf_page: 22,
  content_zh: '公式教材正文。',
  translation_available: true,
}

const presentation: ReviewLearningSlicePresentation = {
  schema_version: 'learning_slice_v1',
  mode: 'review',
  presets: [
    {
      id: 'one_minute',
      label: '1 分钟',
      source_refs: [{ kind: 'object', source_id: 'def_review' }],
    },
    {
      id: 'five_minute',
      label: '5 分钟',
      source_refs: [
        { kind: 'object', source_id: 'def_review' },
        { kind: 'object', source_id: 'formula_review' },
      ],
    },
    {
      id: 'full',
      label: '完整复习',
      source_refs: [
        { kind: 'object', source_id: 'def_review' },
        { kind: 'object', source_id: 'thm_review' },
        { kind: 'object', source_id: 'formula_review' },
      ],
    },
  ],
  prompts: [
    {
      text: '先回忆「复习定义」的定义，再显示教材内容。',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'def_review' },
    },
    {
      text: '先回忆「复习定理」的条件和结论，再显示教材内容。',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'thm_review' },
    },
    {
      text: '先尝试写出「复习公式」，再显示教材公式。',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'formula_review' },
    },
  ],
}

function renderReview(
  overrides: Partial<React.ComponentProps<typeof ReviewLearningSlice>> = {},
) {
  const props: React.ComponentProps<typeof ReviewLearningSlice> = {
    courseId: 'functional_analysis_course',
    items: [definitionItem, theoremItem, formulaItem],
    presentation,
    selectedPresetId: 'full',
    expandedSourceIds: [],
    onPresetChange: vi.fn(),
    onExpandedChange: vi.fn(),
    onBeforeSourceNavigate: vi.fn(),
    ...overrides,
  }

  render(
    <MemoryRouter>
      <ReviewLearningSlice {...props} />
    </MemoryRouter>,
  )
  return props
}

describe('ReviewLearningSlice', () => {
  it('shows the three exact preset controls and reports the selected preset', async () => {
    const user = userEvent.setup()
    const props = renderReview({ selectedPresetId: 'five_minute' })

    expect(screen.getByRole('button', { name: '1 分钟' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
    expect(screen.getByRole('button', { name: '5 分钟' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: '完整复习' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )

    await user.click(screen.getByRole('button', { name: '1 分钟' }))
    expect(props.onPresetChange).toHaveBeenCalledWith('one_minute')
  })

  it('renders exactly the selected preset refs and presents recall prompts before reveal', () => {
    renderReview({ selectedPresetId: 'five_minute' })

    expect(screen.getByText('先回忆「复习定义」的定义，再显示教材内容。')).toBeInTheDocument()
    expect(screen.getByText('先尝试写出「复习公式」，再显示教材公式。')).toBeInTheDocument()
    expect(
      screen.queryByText('先回忆「复习定理」的条件和结论，再显示教材内容。'),
    ).not.toBeInTheDocument()
    expect(screen.queryByText('定义教材正文。')).not.toBeInTheDocument()
    expect(screen.queryByText('||f||_p < ∞')).not.toBeInTheDocument()
  })

  it('reveals only the current ModeItem through expandedSourceIds', async () => {
    const user = userEvent.setup()
    const onExpandedChange = vi.fn()
    const { rerender } = render(
      <MemoryRouter>
        <ReviewLearningSlice
          courseId="functional_analysis_course"
          expandedSourceIds={[]}
          items={[definitionItem, theoremItem, formulaItem]}
          onBeforeSourceNavigate={vi.fn()}
          onExpandedChange={onExpandedChange}
          onPresetChange={vi.fn()}
          presentation={presentation}
          selectedPresetId="one_minute"
        />
      </MemoryRouter>,
    )

    expect(screen.queryByText('定义教材正文。')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '显示教材内容' }))
    expect(onExpandedChange).toHaveBeenCalledWith('def_review', true)

    rerender(
      <MemoryRouter>
        <ReviewLearningSlice
          courseId="functional_analysis_course"
          expandedSourceIds={['def_review']}
          items={[definitionItem, theoremItem, formulaItem]}
          onBeforeSourceNavigate={vi.fn()}
          onExpandedChange={onExpandedChange}
          onPresetChange={vi.fn()}
          presentation={presentation}
          selectedPresetId="one_minute"
        />
      </MemoryRouter>,
    )
    expect(screen.getByText('定义教材正文。')).toBeInTheDocument()
  })

  it('preserves source navigation through the supplied callback', async () => {
    const user = userEvent.setup()
    const onBeforeSourceNavigate = vi.fn()
    renderReview({ selectedPresetId: 'one_minute', onBeforeSourceNavigate })

    await user.click(screen.getByRole('link', { name: '查看教材来源' }))
    expect(onBeforeSourceNavigate).toHaveBeenCalledWith('def_review')
  })

  it('fails closed when a selected presentation ref is not in current mode items', () => {
    renderReview({
      presentation: {
        ...presentation,
        presets: presentation.presets.map((preset) =>
          preset.id === 'one_minute'
            ? {
                ...preset,
                source_refs: [{ kind: 'object', source_id: 'missing_source' }],
              }
            : preset,
        ),
      },
      selectedPresetId: 'one_minute',
    })

    expect(screen.getByRole('alert')).toHaveTextContent('学习内容暂不可用')
  })
})
