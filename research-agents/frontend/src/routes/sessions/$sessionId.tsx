import { useState, useEffect } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { mockSessions, mockLeads } from '~/mocks/fixtures'
import { StatusBadge } from '~/components/shared/StatusBadge'
import { ConfidenceScore } from '~/components/shared/ConfidenceScore'
import { EmptyState } from '~/components/shared/EmptyState'
import { DemoBanner } from '~/components/shared/DemoBanner'
import { LoadingSpinner } from '~/components/shared/LoadingSpinner'
import { formatDate } from '~/utils/formatters'
import { apiGet } from '~/utils/api-client'

export const Route = createFileRoute('/sessions/$sessionId')({
  component: SessionDetailPage,
})

const workflowStages = [
  'pending',
  'knowledge_ingestion',
  'lead_discovery',
  'lead_verification',
  'draft_generation',
  'draft_review',
  'outreach_complete',
]

function stageIndex(stage: string | undefined): number {
  if (!stage) return -1
  return workflowStages.indexOf(stage)
}

function SessionDetailPage() {
  const { sessionId } = Route.useParams()

  const mockSession = mockSessions.find((s) => s.id === sessionId) ?? null
  const mockSessionLeads = mockLeads.filter((l) => l.country_job_id === sessionId)

  const [session, setSession] = useState(mockSession)
  const [sessionLeads, setSessionLeads] = useState(mockSessionLeads)
  const [isDemo, setIsDemo] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        const [jobData, leadsData] = await Promise.all([
          apiGet<typeof mockSession>(`/api/jobs/${sessionId}`),
          apiGet<typeof mockSessionLeads>(`/api/leads?job_id=${sessionId}`),
        ])
        if (!cancelled) {
          setSession(jobData)
          setSessionLeads(leadsData)
          setIsDemo(false)
        }
      } catch {
        if (!cancelled) setIsDemo(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => { cancelled = true }
  }, [sessionId])

  if (loading) return <LoadingSpinner message="Loading session..." />

  if (!session) {
    return (
      <div>
        <Link to="/sessions" style={{ color: '#2563eb', textDecoration: 'none', fontSize: 14 }}>
          &larr; Back to sessions
        </Link>
        <EmptyState
          title="Session not found"
          description={`No session with ID "${sessionId}" was found.`}
        />
      </div>
    )
  }

  const currentIdx = stageIndex(session.current_stage)

  return (
    <div>
      {isDemo && <DemoBanner />}

      <Link to="/sessions" style={{ color: '#2563eb', textDecoration: 'none', fontSize: 14 }}>
        &larr; Back to sessions
      </Link>

      {/* Summary Panel */}
      <div style={{ marginTop: 16, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700 }}>{session.country}</h1>
          <StatusBadge status={session.status} />
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 12,
          padding: 16,
          backgroundColor: '#f8fafc',
          borderRadius: 8,
          border: '1px solid #e2e8f0',
        }}>
          <SummaryItem label="Created" value={formatDate(session.created_at)} />
          <SummaryItem label="Updated" value={formatDate(session.updated_at)} />
          <SummaryItem label="Leads Discovered" value={String(session.summary_counts?.leads_discovered ?? 0)} />
          <SummaryItem label="Leads Verified" value={String(session.summary_counts?.leads_verified ?? 0)} />
          <SummaryItem label="Drafts Sent" value={String(session.summary_counts?.drafts_sent ?? 0)} />
          <SummaryItem label="Tokens Used" value={session.total_token_count.toLocaleString()} />
          <SummaryItem label="Estimated Cost" value={`$${session.estimated_cost.toFixed(2)}`} />
        </div>

        {session.error_message && (
          <div style={{
            marginTop: 12,
            padding: 12,
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: 6,
            color: '#dc2626',
            fontSize: 14,
          }}>
            <strong>Error:</strong> {session.error_message}
          </div>
        )}
      </div>

      {/* Workflow Stage Indicator */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Workflow Progress</h2>
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          {workflowStages.map((stage, idx) => {
            const isActive = idx === currentIdx
            const isCompleted = idx < currentIdx
            const isFailed = session.status === 'failed' && idx === currentIdx
            let bgColor = '#e2e8f0'
            if (isCompleted) bgColor = '#16a34a'
            if (isActive && !isFailed) bgColor = '#3b82f6'
            if (isFailed) bgColor = '#dc2626'

            return (
              <div key={stage} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div style={{
                  width: '100%',
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: bgColor,
                }} />
                <span style={{
                  fontSize: 10,
                  color: isActive ? '#1e40af' : '#9ca3af',
                  fontWeight: isActive ? 700 : 400,
                  textAlign: 'center',
                }}>
                  {stage.replace(/_/g, ' ')}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Lead List */}
      <div>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
          Leads ({sessionLeads.length})
        </h2>
        {sessionLeads.length === 0 ? (
          <EmptyState
            title="No leads yet"
            description="Leads will appear here as the research agent discovers them."
          />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Name</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Company</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Role</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Status</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151', textAlign: 'right' }}>Confidence</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151', textAlign: 'right' }}>Sources</th>
              </tr>
            </thead>
            <tbody>
              {sessionLeads.map((lead) => (
                <tr key={lead.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 500 }}>{lead.name}</td>
                  <td style={{ padding: '10px 12px', color: '#6b7280' }}>{lead.company_name || '-'}</td>
                  <td style={{ padding: '10px 12px', color: '#6b7280' }}>{lead.role_title || '-'}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <StatusBadge status={lead.verification_status} />
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                    <ConfidenceScore score={lead.confidence_score} />
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: '#6b7280' }}>
                    {lead.source_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p style={{ fontSize: 11, color: '#6b7280', fontWeight: 500, marginBottom: 2 }}>{label}</p>
      <p style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>{value}</p>
    </div>
  )
}
