import { createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../components/AppShell'
import { ChapterPage } from '../pages/ChapterPage'
import { CoursePage } from '../pages/CoursePage'
import { LibraryPage } from '../pages/LibraryPage'

function RoutePlaceholder({ title }: { title: string }) {
  return (
    <section className="route-placeholder">
      <p className="eyebrow">Book App · Phase 1D</p>
      <h1>{title}</h1>
      <p>页面数据接入将在后续任务完成。</p>
    </section>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <LibraryPage /> },
      {
        path: 'courses/:courseId',
        element: <CoursePage />,
      },
      {
        path: 'courses/:courseId/chapters/:chapterId',
        element: <ChapterPage />,
      },
      {
        path: 'courses/:courseId/sections/:sectionId',
        element: <RoutePlaceholder title="小节学习" />,
      },
      {
        path: 'courses/:courseId/sources/:kind/:sourceId',
        element: <RoutePlaceholder title="教材来源" />,
      },
    ],
  },
])
