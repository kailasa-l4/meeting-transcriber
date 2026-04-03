import { useState, useMemo, useEffect } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { mockLeads } from '~/mocks/fixtures/leads'
import { mockSessions } from '~/mocks/fixtures/sessions'
import { LeadsTable } from '~/components/leads/LeadsTable'
import { EmptyState } from '~/components/shared/EmptyState'
import { DemoBanner } from '~/components/shared/DemoBanner'
import { LoadingSpinner } from '~/components/shared/LoadingSpinner'
import { apiGet } from '~/utils/api-client'
import type { Lead, LeadVerificationStatus } from '~/utils/types'

export const Route = createFileRoute('/leads/')({
  component: LeadsPage,
})

const verificationOptions: { label: string; value: string }[] = [
  { label: 'All Statuses', value: '' },
  { label: 'Verified', value: 'verified' },
  { label: 'Normalized', value: 'normalized' },
  { label: 'Discovered', value: 'discovered' },
  { label: 'Needs Review', value: 'needs_review' },
  { label: 'Rejected', value: 'rejected' },
]

function LeadsPage() {
  const [search, setSearch] = useState('')
  const [minConfidence, setMinConfidence] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [allLeads, setAllLeads] = useState<Lead[]>(mockLeads)
  const [sessions, setSessions] = useState(mockSessions)
  const [isDemo, setIsDemo] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        const [leadsData, sessionsData] = await Promise.all([
          apiGet<Lead[]>('/api/leads'),
          apiGet<typeof mockSessions>('/api/jobs'),
        ])
        if (!cancelled) {
          setAllLeads(leadsData)
          setSessions(sessionsData)
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
  }, [])

  const countryMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const s of sessions) {
      map[s.id] = s.country
    }
    return map
  }, [sessions])

  const filtered = useMemo(() => {
    let result: Lead[] = [...allLeads]

    if (search.trim()) {
      const q = search.toLowerCase()
      result = result.filter(
        (l) =>
          l.name.toLowerCase().includes(q) ||
          (l.company_name && l.company_name.toLowerCase().includes(q)) ||
          (l.email && l.email.toLowerCase().includes(q)),
      )
    }

    if (minConfidence > 0) {
      result = result.filter((l) => l.confidence_score >= minConfidence / 100)
    }

    if (statusFilter) {
      result = result.filter((l) => l.verification_status === statusFilter)
    }

    return result
  }, [allLeads, search, minConfidence, statusFilter])

  if (loading) return <LoadingSpinner message="Loading leads..." />

  return (
    <div>
      {isDemo && <DemoBanner />}

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: '#111827',
              margin: 0,
            }}
          >
            All Leads
          </h1>
          <p style={{ fontSize: 13, color: '#6b7280', margin: '4px 0 0' }}>
            {filtered.length === allLeads.length
              ? `${allLeads.length} leads across all sessions`
              : `${filtered.length} of ${allLeads.length} leads`}
          </p>
        </div>
      </div>

      {/* Filter controls */}
      <div
        style={{
          display: 'flex',
          gap: 16,
          alignItems: 'flex-end',
          marginBottom: 20,
          padding: 16,
          backgroundColor: '#f8fafc',
          borderRadius: 8,
          border: '1px solid #e5e7eb',
          flexWrap: 'wrap',
        }}
      >
        {/* Search input */}
        <div style={{ flex: 1, minWidth: 200 }}>
          <label
            style={{
              display: 'block',
              fontSize: 12,
              fontWeight: 600,
              color: '#6b7280',
              marginBottom: 4,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Search
          </label>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Name, company, or email..."
            style={{
              width: '100%',
              padding: '8px 12px',
              fontSize: 13,
              border: '1px solid #d1d5db',
              borderRadius: 6,
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Min confidence slider */}
        <div style={{ minWidth: 200 }}>
          <label
            style={{
              display: 'block',
              fontSize: 12,
              fontWeight: 600,
              color: '#6b7280',
              marginBottom: 4,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Min Confidence: {minConfidence}%
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={minConfidence}
            onChange={(e) => setMinConfidence(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>

        {/* Verification status dropdown */}
        <div style={{ minWidth: 160 }}>
          <label
            style={{
              display: 'block',
              fontSize: 12,
              fontWeight: 600,
              color: '#6b7280',
              marginBottom: 4,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Verification Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              fontSize: 13,
              border: '1px solid #d1d5db',
              borderRadius: 6,
              outline: 'none',
              backgroundColor: 'white',
            }}
          >
            {verificationOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Clear filters */}
        {(search || minConfidence > 0 || statusFilter) && (
          <button
            onClick={() => {
              setSearch('')
              setMinConfidence(0)
              setStatusFilter('')
            }}
            style={{
              padding: '8px 16px',
              fontSize: 13,
              fontWeight: 500,
              color: '#6b7280',
              backgroundColor: 'white',
              border: '1px solid #d1d5db',
              borderRadius: 6,
              cursor: 'pointer',
            }}
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Results */}
      {filtered.length > 0 ? (
        <LeadsTable leads={filtered} showCountryColumn countryMap={countryMap} />
      ) : (
        <EmptyState
          title="No leads match your filters"
          description="Try adjusting the search term, confidence threshold, or verification status filter."
        />
      )}
    </div>
  )
}
