import { createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../components/AppShell'

function RoutePlaceholder({ title }: { title: string }) {
  return (
    <section className="route-placeholder">
      <p className="eyebrow">Book App · Phase 1D</p>
      <h1>{title}</h1>
      <p>页面数据接入将在下一任务完成。</p>
    </section>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <RoutePlaceholder title="教材库" /> },
      {
        path: 'courses/:courseId',
        element: <RoutePlaceholder title="课程" />,
      },
      {
        path: 'courses/:courseId/chapters/:chapterId',
        element: <RoutePlaceholder title="章节" />,
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
