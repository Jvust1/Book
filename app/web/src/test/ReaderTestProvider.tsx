import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { ReaderQueryProvider } from '../state/ReaderQueryProvider'
import { createReaderQueryClient } from '../state/readerQueries'

/** One real QueryClient per test tree; no cache or timers leak into another case. */
export function ReaderTestProvider({ children }: { children: ReactNode }) {
  const [client] = useState(() => createReaderQueryClient(Infinity))
  useEffect(() => () => client.clear(), [client])
  return <ReaderQueryProvider client={client}>{children}</ReaderQueryProvider>
}
