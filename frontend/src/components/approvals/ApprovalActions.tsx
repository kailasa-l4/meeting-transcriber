import { useState } from 'react'
import type { OutreachStatus } from '~/utils/types'

interface ApprovalActionsProps {
  status: OutreachStatus
  onApprove: () => void
  onRequestChanges: () => void
  onReject: () => void
  isLoading?: boolean
}

type ConfirmState = 'none' | 'approve' | 'reject'

export function ApprovalActions({
  status,
  onApprove,
  onRequestChanges,
  onReject,
  isLoading = false,
}: ApprovalActionsProps) {
  const [confirmState, setConfirmState] = useState<ConfirmState>('none')

  const isActionable = status === 'pending_review' || status === 'draft_regenerated'
  const disabled = isLoading || !isActionable

  if (!isActionable) {
    return (
      <div style={{
        padding: '12px 16px',
        borderRadius: 8,
        backgroundColor: '#f3f4f6',
        fontSize: 14,
        color: '#6b7280',
        textAlign: 'center',
      }}>
        This draft is not awaiting review (status: {status.replace(/_/g, ' ')})
      </div>
    )
  }

  // Confirmation overlay for approve
  if (confirmState === 'approve') {
    return (
      <div style={{
        padding: 16,
        border: '2px solid #16a34a',
        borderRadius: 8,
        backgroundColor: '#f0fdf4',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#166534', marginBottom: 12 }}>
          Approve and queue this draft for sending?
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
          <button
            onClick={() => setConfirmState('none')}
            disabled={isLoading}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              backgroundColor: 'white',
              fontSize: 14,
              cursor: 'pointer',
              color: '#374151',
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => { onApprove(); setConfirmState('none') }}
            disabled={isLoading}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: 6,
              backgroundColor: '#16a34a',
              color: 'white',
              fontSize: 14,
              fontWeight: 600,
              cursor: isLoading ? 'wait' : 'pointer',
            }}
          >
            {isLoading ? 'Approving...' : 'Confirm Approve'}
          </button>
        </div>
      </div>
    )
  }

  // Confirmation overlay for reject
  if (confirmState === 'reject') {
    return (
      <div style={{
        padding: 16,
        border: '2px solid #dc2626',
        borderRadius: 8,
        backgroundColor: '#fef2f2',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#991b1b', marginBottom: 12 }}>
          Reject this draft? It will not be sent.
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
          <button
            onClick={() => setConfirmState('none')}
            disabled={isLoading}
            style={{
              padding: '8px 16px',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              backgroundColor: 'white',
              fontSize: 14,
              cursor: 'pointer',
              color: '#374151',
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => { onReject(); setConfirmState('none') }}
            disabled={isLoading}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: 6,
              backgroundColor: '#dc2626',
              color: 'white',
              fontSize: 14,
              fontWeight: 600,
              cursor: isLoading ? 'wait' : 'pointer',
            }}
          >
            {isLoading ? 'Rejecting...' : 'Confirm Reject'}
          </button>
        </div>
      </div>
    )
  }

  // Default action buttons
  return (
    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
      <button
        onClick={() => setConfirmState('approve')}
        disabled={disabled}
        style={{
          padding: '10px 20px',
          border: 'none',
          borderRadius: 6,
          backgroundColor: disabled ? '#d1d5db' : '#16a34a',
          color: 'white',
          fontSize: 14,
          fontWeight: 600,
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        Approve & Send
      </button>
      <button
        onClick={onRequestChanges}
        disabled={disabled}
        style={{
          padding: '10px 20px',
          border: 'none',
          borderRadius: 6,
          backgroundColor: disabled ? '#d1d5db' : '#d97706',
          color: 'white',
          fontSize: 14,
          fontWeight: 600,
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        Request Changes
      </button>
      <button
        onClick={() => setConfirmState('reject')}
        disabled={disabled}
        style={{
          padding: '10px 20px',
          border: 'none',
          borderRadius: 6,
          backgroundColor: disabled ? '#d1d5db' : '#dc2626',
          color: 'white',
          fontSize: 14,
          fontWeight: 600,
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        Reject
      </button>
    </div>
  )
}
