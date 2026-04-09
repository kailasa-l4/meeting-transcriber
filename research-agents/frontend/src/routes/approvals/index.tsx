import { useState, useEffect } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { mockDrafts } from '~/mocks/fixtures/drafts'
import { mockLeads } from '~/mocks/fixtures/leads'
import { mockSessions } from '~/mocks/fixtures/sessions'
import { ApprovalInbox } from '~/components/approvals/ApprovalInbox'
import { EmptyState } from '~/components/shared/EmptyState'
import { DemoBanner } from '~/components/shared/DemoBanner'
import { LoadingSpinner } from '~/components/shared/LoadingSpinner'
import { apiGet, apiPost } from '~/utils/api-client'

export const Route = createFileRoute('/approvals/')({
  component: ApprovalsPage,
})

function ApprovalsPage() {
  // Build mock fallback data
  const mockPendingDrafts = mockDrafts.filter(
    (d) => d.status === 'pending_review' || d.status === 'draft_regenerated'
  )
  const mockLeadLookup: Record<string, {
    name: string
    company_name?: string
    country: string
    confidence_score: number
  }> = {}
  for (const lead of mockLeads) {
    const session = mockSessions.find((s) => s.id === lead.country_job_id)
    mockLeadLookup[lead.id] = {
      name: lead.name,
      company_name: lead.company_name,
      country: session?.country ?? lead.country_job_id,
      confidence_score: lead.confidence_score,
    }
  }

  const [pendingDrafts, setPendingDrafts] = useState(mockPendingDrafts)
  const [leadLookup, setLeadLookup] = useState(mockLeadLookup)
  const [isDemo, setIsDemo] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        const data = await apiGet<typeof mockPendingDrafts>('/api/approvals/pending')
        if (!cancelled) {
          setPendingDrafts(data)
          setIsDemo(false)

          // Try to build lead lookup from real leads
          try {
            const [leadsData, sessionsData] = await Promise.all([
              apiGet<typeof mockLeads>('/api/leads'),
              apiGet<typeof mockSessions>('/api/jobs'),
            ])
            const lookup: typeof mockLeadLookup = {}
            for (const lead of leadsData) {
              const session = sessionsData.find((s: { id: string }) => s.id === lead.country_job_id)
              lookup[lead.id] = {
                name: lead.name,
                company_name: lead.company_name,
                country: session?.country ?? lead.country_job_id,
                confidence_score: lead.confidence_score,
              }
            }
            if (!cancelled) setLeadLookup(lookup)
          } catch {
            // Non-critical: keep mock lead lookup
          }
        }
      } catch {
        if (!cancelled) setIsDemo(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => { cancelled = true }
  }, [])

  async function handleQuickApprove(draftId: string) {
    if (isDemo) {
      console.log('Quick approve draft (demo):', draftId)
      alert(`Draft ${draftId} approved (mock). In production this would call the API.`)
      return
    }

    try {
      await apiPost(`/api/approvals/${draftId}/approve`, {})
      // Remove the approved draft from the list
      setPendingDrafts((prev) => prev.filter((d) => d.id !== draftId))
      alert(`Draft ${draftId} approved and queued for sending.`)
    } catch (err) {
      alert(`Failed to approve draft: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  if (loading) return <LoadingSpinner message="Loading approvals..." />

  return (
    <div>
      {isDemo && <DemoBanner />}

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
      }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
            Approvals
          </h1>
          <p style={{ color: '#6b7280', fontSize: 14 }}>
            Review and approve AI-generated outreach drafts before sending
          </p>
        </div>

        {pendingDrafts.length > 0 && (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 14px',
            borderRadius: 20,
            backgroundColor: '#fef3c7',
            color: '#92400e',
            fontSize: 14,
            fontWeight: 600,
          }}>
            <span style={{
              display: 'inline-block',
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#f59e0b',
            }} />
            {pendingDrafts.length} draft{pendingDrafts.length !== 1 ? 's' : ''} pending review
          </span>
        )}
      </div>

      {pendingDrafts.length > 0 && (
        <div style={{
          display: 'flex',
          gap: 12,
          alignItems: 'center',
          padding: '8px 12px',
          marginBottom: 12,
          backgroundColor: '#f8fafc',
          borderRadius: 6,
          border: '1px solid #e2e8f0',
          fontSize: 13,
          color: '#64748b',
        }}>
          <span>
            <span className="keyboard-hint">&uarr;&darr;</span> or <span className="keyboard-hint">j</span>/<span className="keyboard-hint">k</span> to navigate
          </span>
          <span style={{ color: '#cbd5e1' }}>·</span>
          <span>
            <span className="keyboard-hint">Enter</span> to review
          </span>
          <span style={{ color: '#cbd5e1' }}>·</span>
          <span>
            <span className="keyboard-hint">a</span> to approve
          </span>
          <span style={{ color: '#cbd5e1' }}>·</span>
          <span>
            <span className="keyboard-hint">Esc</span> to deselect
          </span>
        </div>
      )}

      {pendingDrafts.length === 0 ? (
        <EmptyState
          title="No drafts pending review"
          description="All outreach drafts have been reviewed. New drafts will appear here when country research runs generate them."
        />
      ) : (
        <div style={{
          border: '1px solid #e2e8f0',
          borderRadius: 8,
          overflow: 'hidden',
        }}>
          <ApprovalInbox
            drafts={pendingDrafts}
            leadLookup={leadLookup}
            onApprove={handleQuickApprove}
          />
        </div>
      )}
    </div>
  )
}
