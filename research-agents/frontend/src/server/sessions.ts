import { createServerFn } from '@tanstack/react-start'
import { apiGet } from '~/utils/api-client'
import type { CountryJob } from '~/utils/types'

export const getSessions = createServerFn({ method: 'GET' }).handler(async () => {
  return apiGet<CountryJob[]>('/api/jobs')
})

export const getSessionDetail = createServerFn({ method: 'GET' })
  .inputValidator((d: string) => d)
  .handler(async ({ data: sessionId }) => {
    return apiGet<CountryJob>(`/api/jobs/${sessionId}`)
  })
