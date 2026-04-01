import { createFileRoute, Link } from '@tanstack/react-router'
import { mockSessions } from '~/mocks/fixtures'
import { StatusBadge } from '~/components/shared/StatusBadge'
import { formatDate } from '~/utils/formatters'

export const Route = createFileRoute('/sessions/')({
  component: SessionsPage,
})

function SessionsPage() {
  const sessions = mockSessions

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700 }}>Sessions</h1>
        <Link
          to="/country/new"
          style={{
            display: 'inline-block',
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            borderRadius: 6,
            textDecoration: 'none',
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          + New Country Run
        </Link>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left' }}>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Country</th>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Status</th>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Stage</th>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151', textAlign: 'right' }}>Discovered</th>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151', textAlign: 'right' }}>Verified</th>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151', textAlign: 'right' }}>Sent</th>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151', textAlign: 'right' }}>Cost</th>
              <th style={{ padding: '8px 12px', fontWeight: 600, color: '#374151' }}>Created</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr
                key={session.id}
                style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}
              >
                <td style={{ padding: '10px 12px' }}>
                  <Link
                    to="/sessions/$sessionId"
                    params={{ sessionId: session.id }}
                    style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}
                  >
                    {session.country}
                  </Link>
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <StatusBadge status={session.status} />
                </td>
                <td style={{ padding: '10px 12px', color: '#6b7280' }}>
                  {session.current_stage?.replace(/_/g, ' ') || '-'}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  {session.summary_counts?.leads_discovered ?? 0}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  {session.summary_counts?.leads_verified ?? 0}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  {session.summary_counts?.drafts_sent ?? 0}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right', color: '#6b7280' }}>
                  ${session.estimated_cost.toFixed(2)}
                </td>
                <td style={{ padding: '10px 12px', color: '#6b7280', fontSize: 13 }}>
                  {formatDate(session.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
