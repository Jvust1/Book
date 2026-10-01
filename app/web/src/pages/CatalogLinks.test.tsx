import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { expect, it, vi } from 'vitest'
import { bookApi } from '../api/client'
import { LibraryPage } from './LibraryPage'
import { CoursePage } from './CoursePage'
import { ChapterPage } from './ChapterPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return { ...actual, bookApi: { ...actual.bookApi, getLibrary: vi.fn(), getCourse: vi.fn(), getChapter: vi.fn() } }
})
const course = { course_id: '原创 ?#%', name_zh: 'Original course', name_en: null, authors: [],
  book_id: 'original', chapter_count: 1, section_count: 1, runtime_status: 'READY' }
const chapter = { chapter_id: 'chapter ?#%', number: null, title_zh: 'Original chapter', title_en: null, section_count: 1 }
const coursePath = `/courses/${encodeURIComponent(course.course_id)}`
const chapterPath = `${coursePath}/chapters/${encodeURIComponent(chapter.chapter_id)}`
it('encodes the Library course link as one path segment', async () => {
  vi.mocked(bookApi.getLibrary).mockResolvedValue({ library_id: 'original', name: 'Original', courses: [course] })
  render(<MemoryRouter><LibraryPage /></MemoryRouter>)
  expect(await screen.findByRole('link', { name: '进入课程' })).toHaveAttribute('href', coursePath)
})
it('preserves decoded course identity and encodes Course links', async () => {
  vi.mocked(bookApi.getCourse).mockResolvedValue({ course, chapters: [chapter], section_count: 1 })
  render(<MemoryRouter initialEntries={[coursePath]}><Routes><Route path="/courses/:courseId" element={<CoursePage />} /></Routes></MemoryRouter>)
  expect(await screen.findByRole('link', { name: '进入章节' })).toHaveAttribute('href', chapterPath)
  expect(screen.getByRole('link', { name: '教材问答' })).toHaveAttribute('href', `${coursePath}/qa`)
  expect(bookApi.getCourse).toHaveBeenCalledWith(course.course_id, expect.any(AbortSignal))
})
it('preserves decoded Chapter identity and encodes Section/back links', async () => {
  const sectionId = 'section ?#%'
  vi.mocked(bookApi.getChapter).mockResolvedValue({ course_id: course.course_id, book_id: course.book_id, chapter,
    sections: [{ section_id: sectionId, number: null, title_zh: 'Original section', title_en: null,
      printed_page_start: 'iv', printed_page_end: 'v', pdf_page_start: 2, pdf_page_end: 3 }] })
  render(<MemoryRouter initialEntries={[chapterPath]}><Routes><Route path="/courses/:courseId/chapters/:chapterId" element={<ChapterPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByRole('link', { name: '进入本节' })).toHaveAttribute('href', `${coursePath}/sections/${encodeURIComponent(sectionId)}`)
  expect(screen.getByRole('link', { name: '← 返回课程' })).toHaveAttribute('href', coursePath)
  expect(screen.getByText('教材页 iv–v · PDF 2–3')).toBeInTheDocument()
  expect(bookApi.getChapter).toHaveBeenCalledWith(course.course_id, chapter.chapter_id, expect.any(AbortSignal))
})
