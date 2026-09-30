import { QueryClient, queryOptions, useQuery, useQueryClient } from '@tanstack/react-query'
import { bookApi, ApiError } from '../api/client'

export const READER_CACHE_ENGINE = '@tanstack/react-query@5.104.0'
export const READER_STALE_MS = 30_000
export const READER_GC_MS = 60_000

export function createReaderQueryClient(gcTime = READER_GC_MS): QueryClient {
  return new QueryClient({ defaultOptions: {
    queries: { staleTime: READER_STALE_MS, gcTime, retry: false, networkMode: 'always',
      refetchOnWindowFocus: false, refetchOnReconnect: false },
    mutations: { retry: false },
  } })
}

export const readerSourceOptions = (courseId: string, kind: string, sourceId: string) => {
  const sourceKind = kind.trim().toLowerCase()
  return queryOptions({
    queryKey: ['book-reader', 'source', courseId, sourceKind, sourceId] as const,
    queryFn: ({ signal }) => bookApi.getSource(courseId, sourceKind, sourceId, signal),
    enabled: Boolean(courseId && sourceKind && sourceId),
  })
}
export const readerSearchOptions = (courseId: string, query: string, limit = 30) => {
  const text = query.trim()
  return queryOptions({
    queryKey: ['book-reader', 'search', courseId, text, limit] as const,
    queryFn: ({ signal }) => bookApi.searchCourse(courseId, text, limit, signal),
    enabled: Boolean(courseId && text),
  })
}

/** Only network-level failures may show labeled old data. Any API/schema rejection hides it. */
export function visibleReaderData<T>(data: T | undefined, error: unknown): T | undefined {
  if (!error) return data
  if (error instanceof ApiError) return undefined
  return error instanceof TypeError ? data : undefined
}

export function useReaderSource(courseId: string, kind: string, sourceId: string) {
  const client = useQueryClient()
  const options = readerSourceOptions(courseId, kind, sourceId)
  const query = useQuery(options)
  return { query, data: visibleReaderData(query.data, query.error),
    refresh: () => { void query.refetch({ cancelRefetch: false }) },
    cancel: () => { void client.cancelQueries({ queryKey: options.queryKey, exact: true }) },
  }
}
export function useReaderSearch(courseId: string, text: string) {
  const client = useQueryClient()
  const options = readerSearchOptions(courseId, text)
  const query = useQuery(options)
  return { query, data: visibleReaderData(query.data, query.error),
    refresh: () => { void query.refetch({ cancelRefetch: false }) },
    cancel: () => { void client.cancelQueries({ queryKey: options.queryKey, exact: true }) },
  }
}
