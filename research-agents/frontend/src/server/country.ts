import { createServerFn } from '@tanstack/react-start'
import { apiPost } from '~/utils/api-client'
import type { CountrySubmissionInput, CountryJob } from '~/utils/types'

export const submitCountry = createServerFn({ method: 'POST' })
  .inputValidator((d: CountrySubmissionInput) => d)
  .handler(async ({ data }) => {
    return apiPost<CountryJob>('/api/jobs', data)
  })
