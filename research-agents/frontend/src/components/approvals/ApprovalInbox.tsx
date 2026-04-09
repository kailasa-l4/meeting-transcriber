import { Link } from '@tanstack/react-router'
import type { EmailDraft } from '~/utils/types'
import { ConfidenceScore } from '~/components/shared/ConfidenceScore'
import { StatusBadge } from '~/components/shared/StatusBadge'

interface ApprovalInboxProps {
  drafts: EmailDraft[]
  leadLookup: Record<string, { name: string; company_name?: string; country: string; confidence_score: number }>
  onApprove?: (id: string) => void
  onReview?: (id: string) => void
}

function relativeTime(iso: string): string {
  const now = new Date()
  const then = new Date(iso)
  const diffMs = now.getTime() - then.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

export function ApprovalInbox({ drafts, leadLookup, onApprove }: ApprovalInboxProps) {
  // Sort by confidence score descending (highest priority first)
  const sortedDrafts = [...drafts].sort((a, b) => {
    const aLead = leadLookup[a.lead_id]
    const bLead = leadLookup[b.lead_id]
    return (bLead?.confidence_score ?? 0) - (aLead?.confidence_score ?? 0)
  })

  if (sortedDrafts.length === 0) {
    return null
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: 14,
      }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
            {['Lead Name', 'Company', 'Country', 'Subject', 'Ver', 'Template', 'Confidence', 'Awaiting Since', 'Actions'].map((header) => (
              <th
                key={header}
                style={{
                  padding: '10px 12px',
                  textAlign: 'left',
                  fontSize: 12,
                  fontWeight: 600,
                  color: '#6b7280',
                  textTransform: 'uppercase',
                  letterSpacing: 0.5,
                  whiteSpace: 'nowrap',
                }}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedDrafts.map((draft) => {
            const lead = leadLookup[draft.lead_id]
            const isHighConfidence = (lead?.confidence_score ?? 0) >= 0.85

            return (
              <tr
                key={draft.id}
                style={{
                  borderBottom: '1px solid #f1f5f9',
                  transition: 'background-color 0.1s',
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = '#f8fafc' }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = 'transparent' }}
              >
                {/* Lead Name */}
                <td style={{ padding: '10px 12px' }}>
                  <Link
                    to="/approvals/$draftId"
                    params={{ draftId: draft.id }}
                    style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 500 }}
                  >
                    {lead?.name ?? 'Unknown'}
                  </Link>
                </td>

                {/* Company */}
                <td style={{ padding: '10px 12px', color: '#374151' }}>
                  {lead?.company_name ?? '--'}
                </td>

                {/* Country */}
                <td style={{ padding: '10px 12px', color: '#374151' }}>
                  {lead?.country ?? '--'}
                </td>

                {/* Subject (truncated) */}
                <td style={{ padding: '10px 12px', color: '#374151', maxWidth: 200 }}>
                  <span style={{
                    display: 'block',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {draft.subject}
                  </span>
                </td>

                {/* Version */}
                <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '1px 6px',
                    borderRadius: 4,
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#6b7280',
                    backgroundColor: '#f3f4f6',
                  }}>
                    v{draft.version_number}
                  </span>
                </td>

                {/* Template */}
                <td style={{ padding: '10px 12px' }}>
                  {draft.template_used ? (
                    <span style={{
                      display: 'inline-block',
                      padding: '1px 6px',
                      borderRadius: 4,
                      fontSize: 11,
                      fontWeight: 500,
                      color: '#7c3aed',
                      backgroundColor: '#ede9fe',
                    }}>
                      {draft.template_used.replace(/_/g, ' ')}
                    </span>
                  ) : '--'}
                </td>

                {/* Confidence */}
                <td style={{ padding: '10px 12px' }}>
                  <ConfidenceScore score={lead?.confidence_score ?? 0} />
                </td>

                {/* Awaiting Since */}
                <td style={{ padding: '10px 12px', color: '#6b7280', fontSize: 13 }}>
                  {relativeTime(draft.generated_at)}
                </td>

                {/* Actions */}
                <td style={{ padding: '10px 12px' }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {isHighConfidence && onApprove && (
                      <button
                        onClick={() => onApprove(draft.id)}
                        title="Quick approve (high confidence lead)"
                        style={{
                          padding: '4px 10px',
                          border: 'none',
                          borderRadius: 4,
                          backgroundColor: '#16a34a',
                          color: 'white',
                          fontSize: 12,
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        Approve
                      </button>
                    )}
                    <Link
                      to="/approvals/$draftId"
                      params={{ draftId: draft.id }}
                      style={{
                        padding: '4px 10px',
                        borderRadius: 4,
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        fontSize: 12,
                        fontWeight: 600,
                        textDecoration: 'none',
                        display: 'inline-block',
                      }}
                    >
                      Review
                    </Link>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
