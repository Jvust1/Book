import { useState } from 'react'
import type { ReactNode } from 'react'
import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { createReaderQueryClient } from './readerQueries'

export function ReaderQueryProvider({ children, client }: { children: ReactNode; client?: QueryClient }) {
  const [owned] = useState(() => client ?? createReaderQueryClient())
  // No persistence, hydration, broadcast, global singleton, or mutation integration.
  return <QueryClientProvider client={client ?? owned}>{children}</QueryClientProvider>
}
