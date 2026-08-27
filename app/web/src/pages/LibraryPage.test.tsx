import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { bookApi } from '../api/client'
import { LibraryPage } from './LibraryPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    bookApi: {
      ...actual.bookApi,
      getLibrary: vi.fn(),
    },
  }
})

describe('LibraryPage', () => {
  beforeEach(() => {
    vi.mocked(bookApi.getLibrary).mockResolvedValue({
      library_id: 'book_app_library',
      name: 'Book',
      courses: [
        {
          course_id: 'functional_analysis_course',
          name_zh: '泛函分析：分析学进一步专题导论',
          name_en: 'Functional Analysis: Introduction to Further Topics in Analysis',
          authors: ['Elias M. Stein', 'Rami Shakarchi'],
          book_id: 'stein_shakarchi_functional_analysis_2011',
          chapter_count: 8,
          section_count: 132,
          runtime_status: 'READY',
        },
      ],
    })
  })

  it('renders the real course contract and navigation link', async () => {
    render(
      <MemoryRouter>
        <LibraryPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('泛函分析：分析学进一步专题导论')).toBeInTheDocument()
    expect(screen.getByText('8 章 · 132 节')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '进入课程' })).toHaveAttribute(
      'href',
      '/courses/functional_analysis_course',
    )
  })
})
