import { useState, useEffect } from 'react'
import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { mockDrafts, mockReviewActions } from '~/mocks/fixtures/drafts'
import { mockLeads } from '~/mocks/fixtures/leads'
import { mockSessions } from '~/mocks/fixtures/sessions'
import type { DraftDetail, DraftReviewRequest } from '~/utils/types'
import { ConfidenceScore } from '~/components/shared/ConfidenceScore'
import { DraftViewer } from '~/components/approvals/DraftViewer'
import { ApprovalActions } from '~/components/approvals/ApprovalActions'
import { StructuredFeedbackForm } from '~/components/approvals/StructuredFeedbackForm'
import { DraftVersionHistory } from '~/components/approvals/DraftVersionHistory'
import { DemoBanner } from '~/components/shared/DemoBanner'
import { LoadingSpinner } from '~/components/shared/LoadingSpinner'
import { apiGet, apiPost } from '~/utils/api-client'

export const Route = createFileRoute('/approvals/$draftId')({
  component: DraftReviewPage,
})

function buildMockDraftDetail(draftId: string): DraftDetail | null {
  const draft = mockDrafts.find((d) => d.id === draftId)
  if (!draft) return null

  const lead = mockLeads.find((l) => l.id === draft.lead_id)
  if (!lead) return null

  const session = mockSessions.find((s) => s.id === draft.country_job_id)

  // Collect all versions for this lead
  const allVersions = mockDrafts
    .filter((d) => d.lead_id === draft.lead_id)
    .sort((a, b) => b.version_number - a.version_number)

  // Collect review history for all versions of this lead's drafts
  const allDraftIds = allVersions.map((d) => d.id)
  const reviewHistory = mockReviewActions.filter((r) => allDraftIds.includes(r.email_draft_id))

  return {
    draft,
    lead_name: lead.name,
    company_name: lead.company_name,
    country: session?.country ?? lead.country_job_id,
    confidence_score: lead.confidence_score,
    all_versions: allVersions,
    review_history: reviewHistory,
  }
}

function DraftReviewPage() {
  const { draftId } = Route.useParams()
  const navigate = useNavigate()
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isDemo, setIsDemo] = useState(true)
  const [pageLoading, setPageLoading] = useState(true)

  const mockDetail = buildMockDraftDetail(draftId)

  const [detail, setDetail] = useState<DraftDetail | null>(mockDetail)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        const data = await apiGet<DraftDetail>(`/api/approvals/${draftId}`)
        if (!cancelled) {
          setDetail(data)
          setIsDemo(false)
        }
      } catch {
        // Keep mock data
        if (!cancelled) setIsDemo(true)
      } finally {
        if (!cancelled) setPageLoading(false)
      }
    }

    fetchData()
    return () => { cancelled = true }
  }, [draftId])

  if (pageLoading) return <LoadingSpinner message="Loading draft..." />

  if (!detail) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#1e293b', marginBottom: 8 }}>
          Draft Not Found
        </h1>
        <p style={{ color: '#6b7280', marginBottom: 16 }}>
          No draft with ID "{draftId}" exists.
        </p>
        <Link
          to="/approvals"
          style={{ color: '#2563eb', textDecoration: 'none' }}
        >
          Back to Approvals
        </Link>
      </div>
    )
  }

  const { draft, lead_name, company_name, country, confidence_score, all_versions, review_history } = detail

  async function handleApprove() {
    setIsLoading(true)
    if (isDemo) {
      console.log('Approved draft (demo):', draftId)
      setTimeout(() => {
        setIsLoading(false)
        alert(`Draft approved and queued for sending (mock).`)
      }, 500)
      return
    }

    try {
      await apiPost(`/api/approvals/${draftId}/approve`, {})
      setIsLoading(false)
      alert('Draft approved and queued for sending.')
      navigate({ to: '/approvals' })
    } catch (err) {
      setIsLoading(false)
      alert(`Failed to approve: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  function handleRequestChanges() {
    setShowFeedbackForm(true)
  }

  async function handleReject() {
    setIsLoading(true)
    if (isDemo) {
      console.log('Rejected draft (demo):', draftId)
      setTimeout(() => {
        setIsLoading(false)
        alert(`Draft rejected (mock).`)
      }, 500)
      return
    }

    try {
      await apiPost(`/api/approvals/${draftId}/reject`, {})
      setIsLoading(false)
      alert('Draft rejected.')
      navigate({ to: '/approvals' })
    } catch (err) {
      setIsLoading(false)
      alert(`Failed to reject: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  async function handleFeedbackSubmit(feedback: DraftReviewRequest) {
    setIsLoading(true)
    if (isDemo) {
      console.log('Feedback submitted (demo):', feedback)
      setTimeout(() => {
        setIsLoading(false)
        setShowFeedbackForm(false)
        alert(`Feedback submitted. Draft will be regenerated (mock).`)
      }, 500)
      return
    }

    try {
      await apiPost(`/api/approvals/${draftId}/request-changes`, feedback)
      setIsLoading(false)
      setShowFeedbackForm(false)
      alert('Feedback submitted. Draft will be regenerated.')
      navigate({ to: '/approvals' })
    } catch (err) {
      setIsLoading(false)
      alert(`Failed to submit feedback: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  return (
    <div>
      {isDemo && <DemoBanner />}

      {/* Back navigation */}
      <div style={{ marginBottom: 16 }}>
        <Link
          to="/approvals"
          style={{ color: '#6b7280', textDecoration: 'none', fontSize: 14 }}
        >
          &larr; Back to Approvals
        </Link>
      </div>

      {/* Section 1: Lead Context (top bar) */}
      <div style={{
        padding: '14px 20px',
        marginBottom: 20,
        border: '1px solid #e2e8f0',
        borderRadius: 8,
        backgroundColor: '#f8fafc',
        display: 'flex',
        alignItems: 'center',
        gap: 24,
        flexWrap: 'wrap',
      }}>
        <div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 2 }}>Lead</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#1e293b' }}>{lead_name}</div>
        </div>
        {company_name && (
          <div>
            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 2 }}>Company</div>
            <div style={{ fontSize: 15, fontWeight: 600, color: '#374151' }}>{company_name}</div>
          </div>
        )}
        <div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 2 }}>Country</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: '#374151' }}>{country}</div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 2 }}>Confidence</div>
          <ConfidenceScore score={confidence_score} />
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 2 }}>Version</div>
          <div style={{ fontSize: 15, fontWeight: 600, color: '#374151' }}>
            v{draft.version_number}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 2 }}>Status</div>
          <span style={{
            display: 'inline-block',
            padding: '2px 8px',
            borderRadius: 4,
            fontSize: 12,
            fontWeight: 600,
            color: 'white',
            backgroundColor: draft.status === 'pending_review' ? '#f59e0b'
              : draft.status === 'draft_regenerated' ? '#8b5cf6'
              : '#6b7280',
          }}>
            {draft.status.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      {/* Main content layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 360px',
        gap: 20,
        alignItems: 'start',
      }}>
        {/* Left column: Email + Actions + Feedback */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Section 2: Email Preview */}
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 10 }}>
              Email Preview
            </h2>
            <DraftViewer
              subject={draft.subject}
              body={draft.body}
              templateUsed={draft.template_used}
              modelName={draft.model_name}
            />
          </div>

          {/* Section 3: Action Bar */}
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1e293b', marginBottom: 10 }}>
              Actions
            </h2>
            <ApprovalActions
              status={draft.status}
              onApprove={handleApprove}
              onRequestChanges={handleRequestChanges}
              onReject={handleReject}
              isLoading={isLoading}
            />
          </div>

          {/* Section 5: Structured Feedback Form (conditionally shown) */}
          {showFeedbackForm && (
            <StructuredFeedbackForm
              onSubmit={handleFeedbackSubmit}
              onCancel={() => setShowFeedbackForm(false)}
            />
          )}
        </div>

        {/* Right column: Version History */}
        <div style={{
          border: '1px solid #e2e8f0',
          borderRadius: 8,
          padding: 16,
          backgroundColor: 'white',
        }}>
          <DraftVersionHistory
            versions={all_versions}
            reviewHistory={review_history}
          />
        </div>
      </div>
    </div>
  )
}
