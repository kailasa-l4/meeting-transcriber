import { createServerFn } from '@tanstack/react-start'
import { apiGet } from '~/utils/api-client'
import type { Lead, LeadSource } from '~/utils/types'

export const getLeads = createServerFn({ method: 'GET' })
  .validator((d: { sessionId?: string; status?: string; minConfidence?: number }) => d)
  .handler(async ({ data }) => {
    const params = new URLSearchParams()
    if (data.sessionId) params.set('job_id', data.sessionId)
    if (data.status) params.set('status', data.status)
    if (data.minConfidence) params.set('min_confidence', String(data.minConfidence))
    return apiGet<Lead[]>(`/api/leads?${params}`)
  })

export const getLeadDetail = createServerFn({ method: 'GET' })
  .validator((d: string) => d)
  .handler(async ({ data: leadId }) => {
    return apiGet<{
      lead: Lead
      sources: LeadSource[]
      verification_records: any[]
      draft_status: string | null
    }>(`/api/leads/${leadId}`)
  })
