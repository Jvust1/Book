import { ReaderTestProvider } from '../test/ReaderTestProvider'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import { bookApi } from '../api/client'
import { saveQASessionState, loadQASessionState } from '../state/qaSessionState'
import { encodingAnswer, encodingCourse, encodingCourseResponse } from '../test/sourceEncodingFixtures'
import { QAPage } from './QAPage'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return { ...actual, bookApi: { ...actual.bookApi, getCourse: vi.fn(), askCourse: vi.fn() } }
})

beforeEach(() => {
  sessionStorage.clear()
  window.scrollTo = vi.fn()
  vi.mocked(bookApi.getCourse).mockResolvedValue(encodingCourseResponse)
})

it('disables all completed-history export controls during a new question and preserves the stored conversation', async () => {
  const response = encodingAnswer('original_source')
  saveQASessionState(encodingCourse, { route: `/courses/${encodingCourse}/qa`, scrollY: 0, activeCitationSourceId: null,
    messages: [{ id: 'user-1', role: 'user', content: response.question },
      { id: 'assistant-2', role: 'assistant', content: response.answer!, response }] })
  vi.mocked(bookApi.askCourse).mockReturnValue(new Promise(() => {}))
  render(<ReaderTestProvider><MemoryRouter initialEntries={[`/courses/${encodingCourse}/qa`]}>
    <Routes><Route path="/courses/:courseId/qa" element={<QAPage />} /></Routes>
  </MemoryRouter></ReaderTestProvider>)
  await screen.findByText('Original encoding pilot')
  const button = screen.getByRole('button', { name: '导出本次问答 ZIP' })
  expect(button).toBeEnabled()
  fireEvent.change(screen.getByRole('textbox', { name: '教材问题' }), { target: { value: 'Original next question' } })
  fireEvent.click(screen.getByRole('button', { name: '提问' }))
  expect(button).toBeDisabled()
  expect(bookApi.askCourse).toHaveBeenCalledTimes(1)
  fireEvent.click(screen.getByRole('button', { name: '停止等待' }))
  expect(button).toBeEnabled()
  const saved = loadQASessionState(encodingCourse)!
  expect(saved.messages.map(message => message.role)).toEqual(['user', 'assistant', 'user'])
  expect(saved.messages[1]).toEqual({ id: 'assistant-2', role: 'assistant', content: response.answer, response })
})
