import { useState, useEffect } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { mockSessions, mockLeads, mockDrafts } from '~/mocks/fixtures'
import { StatusBadge } from '~/components/shared/StatusBadge'
import { DemoBanner } from '~/components/shared/DemoBanner'
import { LoadingSpinner } from '~/components/shared/LoadingSpinner'
import { apiGet } from '~/utils/api-client'

export const Route = createFileRoute('/')({
  component: Dashboard,
})

function Dashboard() {
  const [sessions, setSessions] = useState(mockSessions)
  const [leads, setLeads] = useState(mockLeads)
  const [drafts, setDrafts] = useState(mockDrafts)
  const [isDemo, setIsDemo] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        const [jobsData, leadsData, approvalsData] = await Promise.all([
          apiGet<typeof mockSessions>('/api/jobs'),
          apiGet<typeof mockLeads>('/api/leads'),
          apiGet<typeof mockDrafts>('/api/approvals/pending'),
        ])
        if (!cancelled) {
          setSessions(jobsData)
          setLeads(leadsData)
          setDrafts(approvalsData)
          setIsDemo(false)
        }
      } catch {
        // Keep mock data, show demo banner
        if (!cancelled) setIsDemo(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => { cancelled = true }
  }, [])

  if (loading) return <LoadingSpinner message="Loading dashboard..." />

  const totalSessions = sessions.length
  const activeSessions = sessions.filter(
    (s) => s.status === 'running' || s.status === 'seeding_knowledge' || s.status === 'queued'
  ).length
  const totalLeads = leads.length
  const verifiedLeads = leads.filter((l) => l.verification_status === 'verified').length
  const pendingApprovals = drafts.filter((d) => d.status === 'pending_review').length
  const recentSessions = [...sessions]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 4)

  return (
    <div>
      {isDemo && <DemoBanner />}

      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Dashboard</h1>
      <p style={{ color: '#6b7280', marginBottom: 24 }}>
        Gold Lead Research System -- Operator Control Tower
      </p>

      {/* Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 16,
        marginBottom: 32,
      }}>
        <StatCard label="Total Sessions" value={totalSessions} color="#3b82f6" />
        <StatCard label="Active Runs" value={activeSessions} color="#8b5cf6" />
        <StatCard label="Total Leads" value={totalLeads} color="#059669" />
        <StatCard label="Verified Leads" value={verifiedLeads} color="#16a34a" />
        <StatCard label="Pending Approvals" value={pendingApprovals} color="#f59e0b" />
      </div>

      {/* Recent Sessions */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Recent Sessions</h2>
          <Link to="/sessions" style={{ color: '#2563eb', textDecoration: 'none', fontSize: 14 }}>
            View all &rarr;
          </Link>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
          {recentSessions.map((session) => (
            <Link
              key={session.id}
              to="/sessions/$sessionId"
              params={{ sessionId: session.id }}
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <div style={{
                padding: 16,
                border: '1px solid #e2e8f0',
                borderRadius: 8,
                transition: 'border-color 0.15s',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: 15 }}>{session.country}</span>
                  <StatusBadge status={session.status} />
                </div>
                <div style={{ fontSize: 13, color: '#6b7280' }}>
                  <span>{session.summary_counts?.leads_discovered ?? 0} discovered</span>
                  <span style={{ margin: '0 6px' }}>|</span>
                  <span>{session.summary_counts?.leads_verified ?? 0} verified</span>
                  <span style={{ margin: '0 6px' }}>|</span>
                  <span>{session.summary_counts?.drafts_sent ?? 0} sent</span>
                </div>
                {session.current_stage && (
                  <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 6 }}>
                    Stage: {session.current_stage.replace(/_/g, ' ')}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{
      padding: 16,
      border: '1px solid #e2e8f0',
      borderRadius: 8,
      borderLeft: `4px solid ${color}`,
    }}>
      <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 4 }}>{label}</p>
      <p style={{ fontSize: 28, fontWeight: 700, color: '#1e293b' }}>{value}</p>
    </div>
  )
}
