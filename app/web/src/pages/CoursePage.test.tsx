import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { bookApi } from '../api/client'
import { CoursePage } from './CoursePage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getCourse: vi.fn(),
    },
  }
})

describe('CoursePage', () => {
  beforeEach(() => {
    vi.mocked(bookApi.getCourse).mockResolvedValue({
      course: {
        course_id: 'functional_analysis_course',
        name_zh: '泛函分析：分析学进一步专题导论',
        name_en: 'Functional Analysis: Introduction to Further Topics in Analysis',
        authors: ['Elias M. Stein', 'Rami Shakarchi'],
        book_id: 'stein_shakarchi_functional_analysis_2011',
        chapter_count: 8,
        section_count: 132,
        runtime_status: 'READY',
      },
      section_count: 132,
      chapters: [
        {
          chapter_id: 'chapter_01',
          number: '1',
          title_zh: 'L^p 空间与插值',
          title_en: 'Lp Spaces and Interpolation',
          section_count: 12,
        },
        {
          chapter_id: 'chapter_02',
          number: '2',
          title_zh: '最大函数与奇异积分',
          title_en: 'Maximal Functions and Singular Integrals',
          section_count: 18,
        },
      ],
    })
  })

  it('preserves audited Chapter order and exposes the course-scoped search entry', async () => {
    render(
      <MemoryRouter initialEntries={['/courses/functional_analysis_course']}>
        <Routes>
          <Route path="/courses/:courseId" element={<CoursePage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: '泛函分析：分析学进一步专题导论' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '搜索教材' })).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/search',
    )
    const chapterTitles = screen.getAllByTestId('chapter-title')
    expect(chapterTitles.map((node) => node.textContent)).toEqual([
      'L^p 空间与插值',
      '最大函数与奇异积分',
    ])
    const links = screen.getAllByRole('link', { name: '进入章节' })
    expect(links[0]).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/chapters/chapter_01',
    )
    expect(links[1]).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/chapters/chapter_02',
    )
  })
})
