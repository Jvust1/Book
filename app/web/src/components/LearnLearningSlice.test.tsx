import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { LearningSliceGroup, ModeItem } from '../api/types'
import { LearnLearningSlice } from './LearnLearningSlice'

const makeItem = (overrides: Partial<ModeItem>): ModeItem => ({
  kind: 'object',
  source_id: 'source',
  object_type: 'remark',
  type_zh: '教材对象',
  number: null,
  title_zh: '教材对象',
  title_en: null,
  formula: null,
  printed_page: 1,
  pdf_page: 1,
  content_zh: '教材正文',
  translation_available: false,
  ...overrides,
})

const items: ModeItem[] = [
  makeItem({
    source_id: 'def_1',
    object_type: 'definition',
    type_zh: '定义',
    title_zh: '定义一',
    content_zh: '定义正文',
  }),
  makeItem({
    source_id: 'thm_1',
    object_type: 'theorem',
    type_zh: '定理',
    title_zh: '定理一',
    formula: 'T(x) = x',
    content_zh: '定理正文',
  }),
  makeItem({
    source_id: 'formula_1',
    object_type: 'formula',
    type_zh: '公式',
    title_zh: '公式一',
    formula: 'f(x) = x',
    content_zh: null,
  }),
  makeItem({
    source_id: 'example_1',
    object_type: 'example',
    type_zh: '例题',
    title_zh: '例题一',
  }),
  makeItem({
    kind: 'figure',
    source_id: 'fig_1',
    object_type: null,
    type_zh: '图示',
    title_zh: '图一',
    content_zh: null,
    printed_page: 12,
    pdf_page: 2,
  }),
  makeItem({
    kind: 'translation',
    source_id: 'b1',
    object_type: null,
    type_zh: null,
    title_zh: null,
    content_zh: null,
    translation_available: true,
  }),
]

const groups: LearningSliceGroup[] = [
  {
    id: 'definitions',
    label: '定义 / 概念入口',
    source_refs: [{ kind: 'object', source_id: 'def_1' }],
  },
  {
    id: 'theorem_family',
    label: '定理与命题',
    source_refs: [{ kind: 'object', source_id: 'thm_1' }],
  },
  {
    id: 'formulas',
    label: '公式',
    source_refs: [{ kind: 'object', source_id: 'formula_1' }],
  },
  {
    id: 'examples',
    label: '例题',
    source_refs: [{ kind: 'object', source_id: 'example_1' }],
  },
  {
    id: 'figures',
    label: '教材图示',
    source_refs: [{ kind: 'figure', source_id: 'fig_1' }],
  },
  {
    id: 'translations',
    label: '中文学习层',
    source_refs: [{ kind: 'translation', source_id: 'b1' }],
  },
]

const presentation = {
  schema_version: 'learning_slice_v1' as const,
  mode: 'learn' as const,
  groups,
  extensions: {
    supplementary: { status: 'unavailable' as const },
    lecture: { status: 'unavailable' as const },
  },
}

function renderLearn(
  onBeforeSourceNavigate = vi.fn(),
) {
  return render(
    <MemoryRouter>
      <LearnLearningSlice
        courseId="functional_analysis_course"
        expandedSourceIds={[]}
        items={items}
        onBeforeSourceNavigate={onBeforeSourceNavigate}
        onExpandedChange={vi.fn()}
        presentation={presentation}
      />
    </MemoryRouter>,
  )
}

describe('LearnLearningSlice', () => {
  it('renders non-empty groups in fixed presentation order and omits empty groups', () => {
    const { container } = renderLearn()

    expect(
      Array.from(container.querySelectorAll('.learn-group > h2')).map((node) => node.textContent),
    ).toEqual([
      '定义 / 概念入口',
      '定理与命题',
      '公式',
      '例题',
      '教材图示',
      '中文学习层',
    ])
    expect(screen.queryByRole('heading', { name: '其他教材对象' })).not.toBeInTheDocument()
  })

  it('renders formula-bearing theorem once in theorem group and explicit formula in formula group', () => {
    const { container } = renderLearn()

    const theoremGroup = container.querySelector('[data-group-id="theorem_family"]')
    const formulaGroup = container.querySelector('[data-group-id="formulas"]')
    expect(theoremGroup).not.toBeNull()
    expect(formulaGroup).not.toBeNull()
    expect(within(theoremGroup as HTMLElement).getByText('定理一')).toBeInTheDocument()
    expect(within(theoremGroup as HTMLElement).getByText('T(x) = x')).toBeInTheDocument()
    expect(within(formulaGroup as HTMLElement).getByText('公式一')).toBeInTheDocument()
    expect(within(formulaGroup as HTMLElement).getByText('f(x) = x')).toBeInTheDocument()
    expect(screen.getAllByText('定理一')).toHaveLength(1)
    expect(screen.getAllByText('T(x) = x')).toHaveLength(1)
  })

  it('renders figure metadata and translation availability without fabricating an image', () => {
    const { container } = renderLearn()

    const figure = within(container.querySelector('[data-testid="figure-reference-fig_1"]') as HTMLElement)
    expect(figure.getByText('图一')).toBeInTheDocument()
    expect(figure.getByText('教材页 12 · PDF 2')).toBeInTheDocument()
    expect(container.querySelector('img')).toBeNull()

    const translation = within(
      container.querySelector('[data-testid="translation-reference-b1"]') as HTMLElement,
    )
    expect(translation.getByText('中文学习层可用')).toBeInTheDocument()
  })

  it('uses the existing source navigation callback for figure and object links', async () => {
    const user = userEvent.setup()
    const onBeforeSourceNavigate = vi.fn()
    renderLearn(onBeforeSourceNavigate)

    const figure = screen.getByTestId('figure-reference-fig_1')
    await user.click(within(figure).getByRole('link', { name: '查看教材来源' }))
    expect(onBeforeSourceNavigate).toHaveBeenCalledWith('fig_1')

    const theorem = screen.getByText('定理一').closest('article') as HTMLElement
    await user.click(within(theorem).getByRole('link', { name: '查看教材来源' }))
    expect(onBeforeSourceNavigate).toHaveBeenCalledWith('thm_1')
  })

  it('fails closed when a Learn source reference is not present in current mode items', () => {
    render(
      <MemoryRouter>
        <LearnLearningSlice
          courseId="functional_analysis_course"
          expandedSourceIds={[]}
          items={items}
          onBeforeSourceNavigate={vi.fn()}
          onExpandedChange={vi.fn()}
          presentation={{
            ...presentation,
            groups: [
              {
                id: 'definitions',
                label: '定义 / 概念入口',
                source_refs: [{ kind: 'object', source_id: 'missing' }],
              },
            ],
          }}
        />
      </MemoryRouter>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('学习内容暂不可用')
  })
})
