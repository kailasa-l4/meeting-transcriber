import { useState } from 'react'
import type { EmailDraft, DraftReviewAction, StructuredFeedbackCategory } from '~/utils/types'
import { formatDate } from '~/utils/formatters'

interface DraftVersionHistoryProps {
  versions: EmailDraft[]
  reviewHistory: DraftReviewAction[]
}

const categoryLabels: Record<StructuredFeedbackCategory, string> = {
  tone_adjustment: 'Tone',
  missing_information: 'Missing Info',
  factual_error: 'Factual Error',
  length_issue: 'Length',
  wrong_template: 'Wrong Template',
  personalization_needed: 'Personalization',
  other: 'Other',
}

function CategoryBadge({ category }: { category: StructuredFeedbackCategory }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '1px 6px',
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 500,
      color: '#b45309',
      backgroundColor: '#fef3c7',
      border: '1px solid #fde68a',
    }}>
      {categoryLabels[category] || category}
    </span>
  )
}

function ReviewActionCard({ review }: { review: DraftReviewAction }) {
  const actionColors: Record<string, { bg: string; border: string; text: string }> = {
    approve: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534' },
    request_changes: { bg: '#fffbeb', border: '#fde68a', text: '#92400e' },
    reject: { bg: '#fef2f2', border: '#fecaca', text: '#991b1b' },
  }
  const colors = actionColors[review.action] || actionColors.request_changes

  return (
    <div style={{
      padding: 10,
      border: `1px solid ${colors.border}`,
      borderRadius: 6,
      backgroundColor: colors.bg,
      marginTop: 8,
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
      }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: colors.text, textTransform: 'uppercase' }}>
          {review.action.replace(/_/g, ' ')}
        </span>
        <span style={{ fontSize: 11, color: '#9ca3af' }}>
          {formatDate(review.created_at)}
        </span>
      </div>
      {review.structured_feedback_categories.length > 0 && (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 6 }}>
          {review.structured_feedback_categories.map((cat) => (
            <CategoryBadge key={cat} category={cat} />
          ))}
        </div>
      )}
      {review.comments && (
        <p style={{ fontSize: 13, color: '#374151', lineHeight: 1.5, margin: 0 }}>
          {review.comments}
        </p>
      )}
      <p style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>
        by {review.reviewer_id}
      </p>
    </div>
  )
}

export function DraftVersionHistory({ versions, reviewHistory }: DraftVersionHistoryProps) {
  const sortedVersions = [...versions].sort((a, b) => b.version_number - a.version_number)
  const latestVersion = sortedVersions[0]?.version_number ?? 0
  const [expandedVersion, setExpandedVersion] = useState<number>(latestVersion)

  function getReviewForDraft(draftId: string): DraftReviewAction | undefined {
    return reviewHistory.find((r) => r.email_draft_id === draftId)
  }

  if (sortedVersions.length === 0) {
    return (
      <div style={{ padding: 16, color: '#6b7280', fontSize: 14 }}>
        No version history available.
      </div>
    )
  }

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: '#1e293b', marginBottom: 12 }}>
        Version History ({sortedVersions.length} version{sortedVersions.length !== 1 ? 's' : ''})
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {sortedVersions.map((version) => {
          const isExpanded = expandedVersion === version.version_number
          const isCurrent = version.version_number === latestVersion
          const review = getReviewForDraft(version.id)

          return (
            <div
              key={version.id}
              style={{
                border: isCurrent ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                borderRadius: 8,
                overflow: 'hidden',
              }}
            >
              {/* Version header (clickable) */}
              <button
                onClick={() => setExpandedVersion(isExpanded ? -1 : version.version_number)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  border: 'none',
                  backgroundColor: isCurrent ? '#eff6ff' : '#f8fafc',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: isCurrent ? '#1d4ed8' : '#374151',
                  }}>
                    v{version.version_number}
                  </span>
                  {isCurrent && (
                    <span style={{
                      fontSize: 10,
                      fontWeight: 600,
                      color: '#1d4ed8',
                      backgroundColor: '#dbeafe',
                      padding: '1px 6px',
                      borderRadius: 4,
                      textTransform: 'uppercase',
                    }}>
                      Current
                    </span>
                  )}
                  <span style={{
                    display: 'inline-block',
                    padding: '1px 6px',
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 500,
                    color: '#6b7280',
                    backgroundColor: '#f3f4f6',
                  }}>
                    {version.status.replace(/_/g, ' ')}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, color: '#9ca3af' }}>
                    {formatDate(version.generated_at)}
                  </span>
                  <span style={{ fontSize: 12, color: '#9ca3af' }}>
                    {isExpanded ? '\u25B2' : '\u25BC'}
                  </span>
                </div>
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div style={{ padding: 14, borderTop: '1px solid #e2e8f0' }}>
                  <p style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: '#1e293b',
                    marginBottom: 6,
                  }}>
                    {version.subject}
                  </p>
                  <p style={{
                    fontSize: 13,
                    color: '#6b7280',
                    lineHeight: 1.5,
                    whiteSpace: 'pre-wrap',
                  }}>
                    {version.body.length > 200
                      ? version.body.slice(0, 200) + '...'
                      : version.body}
                  </p>

                  {/* Associated review action */}
                  {review && <ReviewActionCard review={review} />}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
