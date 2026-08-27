import { createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../components/AppShell'
import { ChapterPage } from '../pages/ChapterPage'
import { CoursePage } from '../pages/CoursePage'
import { LibraryPage } from '../pages/LibraryPage'
import { SearchPage } from '../pages/SearchPage'
import { SectionPage } from '../pages/SectionPage'
import { SourcePage } from '../pages/SourcePage'

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
        path: 'courses/:courseId/search',
        element: <SearchPage />,
      },
      {
        path: 'courses/:courseId/chapters/:chapterId',
        element: <ChapterPage />,
      },
      {
        path: 'courses/:courseId/sections/:sectionId',
        element: <SectionPage />,
      },
      {
        path: 'courses/:courseId/sources/:kind/:sourceId',
        element: <SourcePage />,
      },
    ],
  },
])
