import { createBrowserRouter } from 'react-router-dom'

import { AppShell } from '../components/AppShell'
import { ChapterPage } from '../pages/ChapterPage'
import { CoursePage } from '../pages/CoursePage'
import { LibraryPage } from '../pages/LibraryPage'
import { KnowledgeBasePage } from '../pages/KnowledgeBasePage'
import { QAPage } from '../pages/QAPage'
import { RecordingPage } from '../pages/RecordingPage'
import { SearchPage } from '../pages/SearchPage'
import { SectionPage } from '../pages/SectionPage'
import { SourcePage } from '../pages/SourcePage'
import { SyncPage } from '../pages/SyncPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <LibraryPage /> },
      { path: 'knowledge-base', element: <KnowledgeBasePage /> },
      { path: 'sync', element: <SyncPage /> },
      { path: 'recording', element: <RecordingPage /> },
      {
        path: 'courses/:courseId',
        element: <CoursePage />,
      },
      {
        path: 'courses/:courseId/search',
        element: <SearchPage />,
      },
      {
        path: 'courses/:courseId/qa',
        element: <QAPage />,
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
