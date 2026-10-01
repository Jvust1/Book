import { act, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import { ApiError, bookApi } from '../api/client'
import type { ChapterResponse, CourseResponse } from '../api/types'
import { ChapterPage } from './ChapterPage'
import { CoursePage } from './CoursePage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return { ...actual, bookApi: { ...actual.bookApi, getCourse: vi.fn(), getChapter: vi.fn() } }
})
const course = (id: string): CourseResponse => ({ course: { course_id: id, name_zh: `Original ${id}`, name_en: null,
  authors: [], book_id: `book_${id}`, chapter_count: 1, section_count: 1, runtime_status: 'READY' },
  section_count: 1, chapters: [{ chapter_id: `chapter_${id}`, number: null, title_zh: `Chapter ${id}`, title_en: null, section_count: 1 }] })
const chapter = (id: string): ChapterResponse => ({ course_id: id, book_id: `book_${id}`,
  chapter: course(id).chapters[0], sections: [{ section_id: `section_${id}`, number: null,
    title_zh: `Section ${id}`, title_en: null, printed_page_start: null, printed_page_end: null,
    pdf_page_start: null, pdf_page_end: null }] })
function Navigation({ destination }: { destination: string }) {
  const navigate = useNavigate()
  return <><button onClick={() => navigate(destination)}>Next route</button>
    <button onClick={() => navigate(-1)}>Back</button><button onClick={() => navigate(1)}>Forward</button></>
}
function mount(kind: 'course' | 'chapter') {
  const path = (id: string) => `/courses/${id}${kind === 'chapter' ? `/chapters/chapter_${id}` : ''}`
  render(<MemoryRouter initialEntries={[path('a')]}><Navigation destination={path('b')} /><Routes>
    <Route path="/courses/:courseId" element={<CoursePage />} />
    <Route path="/courses/:courseId/chapters/:chapterId" element={<ChapterPage />} />
  </Routes></MemoryRouter>)
}
beforeEach(() => vi.resetAllMocks())
for (const kind of ['course', 'chapter'] as const) {
  it(`${kind} hides old catalog content and links while a different route is pending`, async () => {
    let resolve: (value: CourseResponse | ChapterResponse) => void = () => {}
    const pending = new Promise<CourseResponse | ChapterResponse>(done => { resolve = done })
    if (kind === 'course') vi.mocked(bookApi.getCourse).mockResolvedValueOnce(course('a')).mockReturnValueOnce(pending as Promise<CourseResponse>)
    else vi.mocked(bookApi.getChapter).mockResolvedValueOnce(chapter('a')).mockReturnValueOnce(pending as Promise<ChapterResponse>)
    mount(kind)
    const oldTitle = kind === 'course' ? 'Original a' : 'Chapter a'
    expect(await screen.findByRole('heading', { name: oldTitle })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next route' }))
    expect(screen.queryByRole('heading', { name: oldTitle })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: kind === 'course' ? '进入章节' : '进入本节' })).not.toBeInTheDocument()
    await act(async () => resolve(kind === 'course' ? course('b') : chapter('b')))
    expect(await screen.findByRole('heading', { name: kind === 'course' ? 'Original b' : 'Chapter b' })).toBeInTheDocument()
  })
  it(`${kind} recovers from an old route error on successful next navigation`, async () => {
    if (kind === 'course') vi.mocked(bookApi.getCourse).mockRejectedValueOnce(new ApiError('Original missing', 404)).mockResolvedValueOnce(course('b'))
    else vi.mocked(bookApi.getChapter).mockRejectedValueOnce(new ApiError('Original missing', 404)).mockResolvedValueOnce(chapter('b'))
    mount(kind)
    expect(await screen.findByRole('alert')).toHaveTextContent('Original missing')
    fireEvent.click(screen.getByRole('button', { name: 'Next route' }))
    expect(await screen.findByRole('heading', { name: kind === 'course' ? 'Original b' : 'Chapter b' })).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
}

for (const kind of ['course', 'chapter'] as const) {
  for (const lateFailure of [false, true]) {
    it(`${kind} aborts abandoned ownership and ignores a late ${lateFailure ? 'failure' : 'response'}`, async () => {
      let resolve: (value: CourseResponse | ChapterResponse) => void = () => {}
      let reject: (reason: unknown) => void = () => {}
      const pending = new Promise<CourseResponse | ChapterResponse>((yes, no) => { resolve = yes; reject = no })
      if (kind === 'course') vi.mocked(bookApi.getCourse).mockReturnValueOnce(pending as Promise<CourseResponse>).mockResolvedValueOnce(course('b'))
      else vi.mocked(bookApi.getChapter).mockReturnValueOnce(pending as Promise<ChapterResponse>).mockResolvedValueOnce(chapter('b'))
      mount(kind)
      const abandoned = kind === 'course' ? vi.mocked(bookApi.getCourse).mock.calls[0][1] : vi.mocked(bookApi.getChapter).mock.calls[0][2]
      expect(abandoned?.aborted).toBe(false)
      fireEvent.click(screen.getByRole('button', { name: 'Next route' }))
      expect(abandoned?.aborted).toBe(true)
      const newTitle = kind === 'course' ? 'Original b' : 'Chapter b'
      expect(await screen.findByRole('heading', { name: newTitle })).toBeInTheDocument()
      await act(async () => { if (lateFailure) reject(new Error('late')); else resolve(kind === 'course' ? course('a') : chapter('a')) })
      expect(screen.getByRole('heading', { name: newTitle })).toBeInTheDocument()
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
      const link = screen.getByRole('link', { name: kind === 'course' ? '进入章节' : '进入本节' })
      expect(link.getAttribute('href')).toContain('/courses/b/')
    })
  }
  it(`${kind} renders only the current catalog during Back and Forward navigation`, async () => {
    if (kind === 'course') vi.mocked(bookApi.getCourse).mockImplementation(async id => course(id))
    else vi.mocked(bookApi.getChapter).mockImplementation(async id => chapter(id))
    mount(kind)
    for (const [button, id] of [[null, 'a'], ['Next route', 'b'], ['Back', 'a'], ['Forward', 'b']] as const) {
      if (button) fireEvent.click(screen.getByRole('button', { name: button }))
      expect(await screen.findByRole('heading', { name: kind === 'course' ? `Original ${id}` : `Chapter ${id}` })).toBeInTheDocument()
      const link = screen.getByRole('link', { name: kind === 'course' ? '进入章节' : '进入本节' })
      expect(link.getAttribute('href')).toContain(`/courses/${id}/`)
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    }
  })
}
