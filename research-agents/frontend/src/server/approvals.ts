import { createServerFn } from '@tanstack/react-start'
import { apiGet, apiPost } from '~/utils/api-client'
import type { EmailDraft, DraftDetail, DraftReviewRequest } from '~/utils/types'

export const getPendingApprovals = createServerFn({ method: 'GET' }).handler(async () => {
  return apiGet<EmailDraft[]>('/api/approvals/pending')
})

export const getDraftDetail = createServerFn({ method: 'GET' })
  .validator((d: string) => d)
  .handler(async ({ data: draftId }) => {
    return apiGet<DraftDetail>(`/api/approvals/${draftId}`)
  })

export const approveDraft = createServerFn({ method: 'POST' })
  .validator((d: string) => d)
  .handler(async ({ data: draftId }) => {
    return apiPost<EmailDraft>(`/api/approvals/${draftId}/approve`, {})
  })

export const requestChanges = createServerFn({ method: 'POST' })
  .validator((d: { draftId: string; feedback: DraftReviewRequest }) => d)
  .handler(async ({ data }) => {
    return apiPost<EmailDraft>(`/api/approvals/${data.draftId}/request-changes`, data.feedback)
  })

export const rejectDraft = createServerFn({ method: 'POST' })
  .validator((d: string) => d)
  .handler(async ({ data: draftId }) => {
    return apiPost<EmailDraft>(`/api/approvals/${draftId}/reject`, {})
  })
