import { RouterProvider } from 'react-router-dom'

import { ReaderQueryProvider } from './state/ReaderQueryProvider'

import { router } from './routes/router'

export function App() {
  return <ReaderQueryProvider><RouterProvider router={router} /></ReaderQueryProvider>
}
