import { SessionViewStorageNotice } from './components/SessionViewStorageNotice'
import { RouterProvider } from 'react-router-dom'

import { ReaderQueryProvider } from './state/ReaderQueryProvider'

import { router } from './routes/router'

export function App() {
  return <ReaderQueryProvider><SessionViewStorageNotice /><RouterProvider router={router} /></ReaderQueryProvider>
}
