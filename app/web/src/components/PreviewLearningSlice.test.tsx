import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type {
  ModeItem,
  PreviewLearningSlicePresentation,
} from '../api/types'
import { PreviewLearningSlice } from './PreviewLearningSlice'

const definitionItem: ModeItem = {
  kind: 'object',
  source_id: 'def_lp',
  object_type: 'definition',
  type_zh: '定义',
  number: '1.1',
  title_zh: 'L^p 空间',
  title_en: 'Lp spaces',
  formula: null,
  printed_page: 2,
  pdf_page: 21,
  content_zh: '设 f 为可测函数，并满足相应的 p 次可积条件。',
  translation_available: true,
}

const formulaItem: ModeItem = {
  kind: 'object',
  source_id: 'formula_lp',
  object_type: 'formula',
  type_zh: '公式',
  number: '(1)',
  title_zh: 'L^p 范数',
  title_en: null,
  formula: '||f||_p < ∞',
  printed_page: 2,
  pdf_page: 21,
  content_zh: null,
  translation_available: true,
}

const figureItem: ModeItem = {
  kind: 'figure',
  source_id: 'fig_lp',
  object_type: null,
  type_zh: '教材图示',
  number: '图 1',
  title_zh: '示意图',
  title_en: null,
  formula: null,
  printed_page: 3,
  pdf_page: 22,
  content_zh: null,
  translation_available: false,
}

const presentation: PreviewLearningSlicePresentation = {
  schema_version: 'learning_slice_v1',
  mode: 'preview',
  overview: {
    object_count: 2,
    figure_count: 1,
    translation_available: true,
  },
  object_counts: [
    { object_type: 'definition', count: 1 },
    { object_type: 'formula', count: 1 },
  ],
  objectives: [
    {
      text: '理解并能复述：L^p 空间',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'def_lp' },
    },
  ],
  prerequisites: { status: 'unavailable', items: [] },
  core_definitions: [{ kind: 'object', source_id: 'def_lp' }],
  core_formulas: [{ kind: 'object', source_id: 'formula_lp' }],
  key_figures: [{ kind: 'figure', source_id: 'fig_lp' }],
  quick_checks: [
    {
      text: '你能说出「L^p 空间」的定义吗？',
      derivation: 'deterministic_template',
      source_ref: { kind: 'object', source_id: 'def_lp' },
    },
  ],
}

const renderPreview = (
  overrides: Partial<React.ComponentProps<typeof PreviewLearningSlice>> = {},
) => {
  const props: React.ComponentProps<typeof PreviewLearningSlice> = {
    courseId: 'functional_analysis_course',
    items: [definitionItem, formulaItem, figureItem],
    presentation,
    expandedSourceIds: [],
    onExpandedChange: vi.fn(),
    onBeforeSourceNavigate: vi.fn(),
    ...overrides,
  }

  return {
    ...render(
      <MemoryRouter>
        <PreviewLearningSlice {...props} />
      </MemoryRouter>,
    ),
    props,
  }
}

describe('PreviewLearningSlice', () => {
  it('renders the source-derived overview and labels guidance as non-textbook learning guidance', () => {
    renderPreview()

    expect(screen.getByRole('heading', { name: '预习概览' })).toBeInTheDocument()
    expect(screen.getByText('教材对象 2')).toBeInTheDocument()
    expect(screen.getByText('教材图示 1')).toBeInTheDocument()
    expect(screen.getByText('中文学习层可用')).toBeInTheDocument()
    expect(
      screen.getByText('以下学习目标与自检问题为系统学习引导，不是教材原文。'),
    ).toBeInTheDocument()
  })

  it('renders objective text with a canonical source link and fires the navigation callback', async () => {
    const user = userEvent.setup()
    const { props } = renderPreview()

    expect(screen.getByText('理解并能复述：L^p 空间')).toBeInTheDocument()
    const objective = screen.getByText('理解并能复述：L^p 空间').closest('li')
    expect(objective).not.toBeNull()
    const link = objective!.querySelector('a')
    expect(link).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/sources/object/def_lp',
    )
    await user.click(link!)
    expect(props.onBeforeSourceNavigate).toHaveBeenCalledWith('def_lp')
  })

  it('shows the unavailable prerequisite notice and non-empty reference sections only', () => {
    renderPreview()

    expect(screen.getByText('暂无可验证的前置知识关系')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '核心定义' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '核心公式' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '教材图示' })).toBeInTheDocument()

    renderPreview({
      presentation: {
        ...presentation,
        core_definitions: [],
        core_formulas: [],
        key_figures: [],
      },
    })

    expect(screen.getAllByRole('heading', { name: '核心定义' })).toHaveLength(1)
    expect(screen.getAllByRole('heading', { name: '核心公式' })).toHaveLength(1)
    expect(screen.getAllByRole('heading', { name: '教材图示' })).toHaveLength(1)
  })

  it('keeps quick-check textbook content hidden until reveal and reuses expanded-source state', async () => {
    const user = userEvent.setup()
    const onExpandedChange = vi.fn()
    const { rerender } = renderPreview({ onExpandedChange })

    expect(screen.getByText('你能说出「L^p 空间」的定义吗？')).toBeInTheDocument()
    expect(
      screen.queryByText('设 f 为可测函数，并满足相应的 p 次可积条件。'),
    ).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '显示教材内容' }))
    expect(onExpandedChange).toHaveBeenCalledWith('def_lp', true)

    rerender(
      <MemoryRouter>
        <PreviewLearningSlice
          courseId="functional_analysis_course"
          items={[definitionItem, formulaItem, figureItem]}
          presentation={presentation}
          expandedSourceIds={['def_lp']}
          onExpandedChange={onExpandedChange}
          onBeforeSourceNavigate={vi.fn()}
        />
      </MemoryRouter>,
    )
    expect(
      screen.getByText('设 f 为可测函数，并满足相应的 p 次可积条件。'),
    ).toBeInTheDocument()
  })

  it('fails closed with a generic message when any presentation reference is missing', () => {
    renderPreview({
      presentation: {
        ...presentation,
        objectives: [
          {
            text: '理解并能复述：缺失来源',
            derivation: 'deterministic_template',
            source_ref: { kind: 'object', source_id: 'missing_source' },
          },
        ],
      },
    })

    expect(screen.getByRole('alert')).toHaveTextContent('学习内容暂不可用')
    expect(screen.queryByText('missing_source')).not.toBeInTheDocument()
  })
})
