import { z } from 'zod'

export const MAX_ERROR_RESPONSE_BYTES = 64 * 1024
export const MAX_ERROR_MESSAGE_UNITS = 1024
const nonblank = (limit: number) => z.string().max(limit).refine(value => !!value.trim())
// The Book API's public error DTO deliberately has no exception detail/stack.
// Reject the whole envelope if it cannot be trusted; never log or truncate it.
export const errorEnvelopeSchema = z.strictObject({ error: z.strictObject({
  code: nonblank(128), message: nonblank(MAX_ERROR_MESSAGE_UNITS),
}) })
