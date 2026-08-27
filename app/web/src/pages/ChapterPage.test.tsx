import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { bookApi } from '../api/client'
import { ChapterPage } from './ChapterPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getChapter: vi.fn(),
    },
  }
})

describe('ChapterPage', () => {
  beforeEach(() => {
    vi.mocked(bookApi.getChapter).mockResolvedValue({
      course_id: 'functional_analysis_course',
      book_id: 'stein_shakarchi_functional_analysis_2011',
      chapter: {
        chapter_id: 'chapter_01',
        number: '1',
        title_zh: 'L^p 空间与插值',
        title_en: 'Lp Spaces and Interpolation',
        section_count: 2,
      },
      sections: [
        {
          section_id: 'ch01_s01',
          number: '1.1',
          title_zh: 'L^p 空间',
          title_en: 'Lp spaces',
          printed_page_start: 1,
          printed_page_end: 3,
          pdf_page_start: 20,
          pdf_page_end: 22,
        },
        {
          section_id: 'ch01_s02',
          number: '1.2',
          title_zh: '插值定理',
          title_en: 'Interpolation theorem',
          printed_page_start: 4,
          printed_page_end: 7,
          pdf_page_start: 23,
          pdf_page_end: 26,
        },
      ],
    })
  })

  it('renders Chinese-first Sections with page ranges and direct links', async () => {
    render(
      <MemoryRouter
        initialEntries={['/courses/functional_analysis_course/chapters/chapter_01']}
      >
        <Routes>
          <Route
            path="/courses/:courseId/chapters/:chapterId"
            element={<ChapterPage />}
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'L^p 空间与插值' })).toBeInTheDocument()
    expect(screen.getByText('Lp Spaces and Interpolation')).toBeInTheDocument()
    expect(screen.getByText('2 节')).toBeInTheDocument()
    expect(screen.getByText('教材页 1–3 · PDF 20–22')).toBeInTheDocument()
    const links = screen.getAllByRole('link', { name: '进入本节' })
    expect(links[0]).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/sections/ch01_s01',
    )
    expect(links[1]).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course/sections/ch01_s02',
    )
  })
})
