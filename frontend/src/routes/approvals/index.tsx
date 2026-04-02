import { createFileRoute } from '@tanstack/react-router'
import { mockDrafts } from '~/mocks/fixtures/drafts'
import { mockLeads } from '~/mocks/fixtures/leads'
import { mockSessions } from '~/mocks/fixtures/sessions'
import { ApprovalInbox } from '~/components/approvals/ApprovalInbox'
import { EmptyState } from '~/components/shared/EmptyState'

export const Route = createFileRoute('/approvals/')({
  component: ApprovalsPage,
})

function ApprovalsPage() {
  // Filter to only pending drafts
  const pendingDrafts = mockDrafts.filter(
    (d) => d.status === 'pending_review' || d.status === 'draft_regenerated'
  )

  // Build a lead lookup for the inbox table
  const leadLookup: Record<string, {
    name: string
    company_name?: string
    country: string
    confidence_score: number
  }> = {}

  for (const lead of mockLeads) {
    const session = mockSessions.find((s) => s.id === lead.country_job_id)
    leadLookup[lead.id] = {
      name: lead.name,
      company_name: lead.company_name,
      country: session?.country ?? lead.country_job_id,
      confidence_score: lead.confidence_score,
    }
  }

  function handleQuickApprove(draftId: string) {
    // In production, this would call approveDraft server function
    // For now, log to console as a placeholder
    console.log('Quick approve draft:', draftId)
    alert(`Draft ${draftId} approved (mock). In production this would call the API.`)
  }

  return (
    <div>
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
