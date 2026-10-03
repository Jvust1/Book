import { z } from 'zod'

/** Shared response identity: preserve valid input exactly; never repair/remap an ID. */
export const responseIdSchema = z.string().max(512).refine(value => {
  if (!value.trim()) return false
  // JSON permits lone UTF-16 surrogates, but route encoding does not.
  try { encodeURIComponent(value); return true } catch { return false }
})
