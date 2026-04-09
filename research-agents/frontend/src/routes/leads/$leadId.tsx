import { useState, useEffect, useMemo } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { mockLeads } from '~/mocks/fixtures/leads'
import { mockDrafts } from '~/mocks/fixtures/drafts'
import { mockSessions } from '~/mocks/fixtures/sessions'
import { ConfidenceScore } from '~/components/shared/ConfidenceScore'
import { ConfidenceBreakdown } from '~/components/leads/ConfidenceBreakdown'
import { SourceEvidence } from '~/components/leads/SourceEvidence'
import { EmptyState } from '~/components/shared/EmptyState'
import { DemoBanner } from '~/components/shared/DemoBanner'
import { LoadingSpinner } from '~/components/shared/LoadingSpinner'
import { confidenceTier, confidenceColors, formatDate } from '~/utils/formatters'
import { apiGet } from '~/utils/api-client'
import type { Lead, LeadSource, VerificationDimension } from '~/utils/types'

export const Route = createFileRoute('/leads/$leadId')({
  component: LeadDetailPage,
})

// Mock sources for the detail view
const mockSources: LeadSource[] = [
  {
    id: 'src-001',
    lead_id: 'lead-001',
    source_url: 'https://www.gcb.com.gh/about/leadership',
    source_title: 'GCB Bank Leadership Team',
    source_type: 'web',
    excerpt:
      'Kwame Asante serves as Head of Precious Metals Trading at GCB Bank Limited, overseeing the bank\'s gold trading desk and commodity finance operations across the Greater Accra and Ashanti regions. Under his leadership, GCB has expanded its precious metals portfolio to include certified gold custody services.',
    collected_at: '2026-03-28T10:02:00Z',
  },
  {
    id: 'src-002',
    lead_id: 'lead-001',
    source_url: 'https://linkedin.com/in/kwameasante',
    source_title: 'Kwame Asante - LinkedIn Profile',
    source_type: 'linkedin',
    excerpt:
      'Head of Precious Metals Trading at GCB Bank Limited. 15+ years experience in commodity finance and gold trading in West Africa. Previously at Standard Chartered Bank Ghana.',
    collected_at: '2026-03-28T10:05:00Z',
  },
  {
    id: 'src-003',
    lead_id: 'lead-001',
    source_url: 'https://ghanaweb.com/gcb-gold-trading-expansion',
    source_title: 'GCB Bank Expands Gold Trading Operations',
    source_type: 'news',
    excerpt:
      'GCB Bank has announced the expansion of its precious metals trading desk, appointing Kwame Asante to lead the initiative. The expansion includes partnerships with licensed gold exporters and integration with international bullion markets.',
    collected_at: '2026-03-28T10:08:00Z',
  },
]

// Mock verification records
interface VerificationRecord {
  dimension: VerificationDimension
  score: number
  verifier_notes: string
  contradictions?: string
}

const mockVerificationRecords: VerificationRecord[] = [
  {
    dimension: 'entity',
    score: 0.95,
    verifier_notes:
      'Entity confirmed via LinkedIn profile and official GCB Bank leadership page. Name, title, and company all match across sources.',
  },
  {
    dimension: 'contact',
    score: 0.9,
    verifier_notes:
      'Email format matches GCB Bank corporate pattern (firstname.lastname@gcb.com.gh). Phone number confirmed on GCB contact page.',
  },
  {
    dimension: 'source_quality',
    score: 0.88,
    verifier_notes:
      'Three independent sources: official company website, LinkedIn, and a news article. All sources are recent (within 6 months).',
    contradictions: 'LinkedIn lists title as "Senior VP Precious Metals" while company site says "Head of Precious Metals Trading".',
  },
  {
    dimension: 'dedup',
    score: 1.0,
    verifier_notes:
      'No duplicate entries found. Unique lead with no overlapping records in the database.',
  },
]

const dimensionColors: Record<VerificationDimension, string> = {
  entity: '#3b82f6',
  contact: '#8b5cf6',
  source_quality: '#f59e0b',
  dedup: '#16a34a',
}

const sectionStyle: React.CSSProperties = {
  marginBottom: 28,
  padding: 20,
  border: '1px solid #e5e7eb',
  borderRadius: 8,
  backgroundColor: 'white',
}

const sectionTitleStyle: React.CSSProperties = {
  fontSize: 15,
  fontWeight: 700,
  color: '#111827',
  marginBottom: 16,
  paddingBottom: 8,
  borderBottom: '1px solid #f3f4f6',
}

function ContactItem({
  label,
  value,
  href,
}: {
  label: string
  value: string | undefined
  href?: string
}) {
  if (!value) return null
  return (
    <div style={{ marginBottom: 8 }}>
      <span
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: '#9ca3af',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        {label}
      </span>
      <div style={{ fontSize: 14, color: '#374151', marginTop: 2 }}>
        {href ? (
          <a
            href={href}
            target={href.startsWith('mailto:') || href.startsWith('tel:') ? undefined : '_blank'}
            rel="noopener noreferrer"
            style={{ color: '#2563eb', textDecoration: 'none' }}
          >
            {value}
          </a>
        ) : (
          value
        )}
      </div>
    </div>
  )
}

interface LeadDetailResponse {
  lead: Lead
  sources: LeadSource[]
  verification_records: VerificationRecord[]
  draft_status: {
    id: string
    lead_id: string
    subject: string
    status: string
    version_number: number
    generated_at: string
  } | null
}

function LeadDetailPage() {
  const { leadId } = Route.useParams()

  // Compute mock fallback data
  const mockLead = useMemo(() => mockLeads.find((l) => l.id === leadId) ?? null, [leadId])
  const mockSession = useMemo(() => {
    if (!mockLead) return null
    return mockSessions.find((s) => s.id === mockLead.country_job_id) ?? null
  }, [mockLead])
  const mockDraft = useMemo(() => {
    if (!mockLead) return null
    return mockDrafts.find((d) => d.lead_id === mockLead.id) ?? null
  }, [mockLead])
  const mockSourcesForLead = useMemo(() => {
    if (!mockLead) return []
    if (mockLead.id === 'lead-001') return mockSources
    return mockLead.source_urls.map((url, i) => ({
      id: `src-gen-${mockLead.id}-${i}`,
      lead_id: mockLead.id,
      source_url: url,
      source_title: undefined,
      source_type: url.includes('linkedin') ? 'linkedin' : 'web',
      excerpt: undefined,
      collected_at: mockLead.created_at,
    })) satisfies LeadSource[]
  }, [mockLead])
  const mockVerificationForLead = useMemo((): VerificationRecord[] => {
    if (!mockLead) return []
    if (mockLead.id === 'lead-001') return mockVerificationRecords
    return Object.entries(mockLead.confidence_breakdown).map(([dim, score]) => ({
      dimension: dim as VerificationDimension,
      score,
      verifier_notes: `Automated verification scored ${Math.round(score * 100)}% for ${dim}.`,
    }))
  }, [mockLead])

  const [lead, setLead] = useState<Lead | null>(mockLead)
  const [session, setSession] = useState(mockSession)
  const [draft, setDraft] = useState(mockDraft)
  const [sources, setSources] = useState<LeadSource[]>(mockSourcesForLead)
  const [verificationRecords, setVerificationRecords] = useState<VerificationRecord[]>(mockVerificationForLead)
  const [isDemo, setIsDemo] = useState(true)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        const data = await apiGet<LeadDetailResponse>(`/api/leads/${leadId}`)
        if (!cancelled) {
          setLead(data.lead)
          setSources(data.sources ?? [])
          setVerificationRecords(data.verification_records ?? [])
          setDraft(data.draft_status as typeof mockDraft)
          setIsDemo(false)

          // Also try to get session info for the country name
          if (data.lead?.country_job_id) {
            try {
              const sessionData = await apiGet<typeof mockSession>(`/api/jobs/${data.lead.country_job_id}`)
              if (!cancelled) setSession(sessionData)
            } catch {
              // Non-critical, keep whatever we have
            }
          }
        }
      } catch {
        // Keep mock data
        if (!cancelled) setIsDemo(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchData()
    return () => { cancelled = true }
  }, [leadId])

  if (loading) return <LoadingSpinner message="Loading lead details..." />

  if (!lead) {
    return (
      <div>
        <Link
          to="/leads"
          style={{ fontSize: 13, color: '#6b7280', textDecoration: 'none', marginBottom: 16, display: 'inline-block' }}
        >
          &larr; Back to Leads
        </Link>
        <EmptyState
          title="Lead not found"
          description={`No lead found with ID "${leadId}".`}
          action={
            <Link
              to="/leads"
              style={{
                display: 'inline-block',
                padding: '8px 16px',
                fontSize: 13,
                fontWeight: 500,
                color: 'white',
                backgroundColor: '#3b82f6',
                borderRadius: 6,
                textDecoration: 'none',
              }}
            >
              View all leads
            </Link>
          }
        />
      </div>
    )
  }

  const tier = confidenceTier(lead.confidence_score)
  const tierColor = confidenceColors[tier]

  return (
    <div style={{ maxWidth: 840 }}>
      {isDemo && <DemoBanner />}

      {/* Breadcrumb */}
      <Link
        to="/leads"
        style={{
          fontSize: 13,
          color: '#6b7280',
          textDecoration: 'none',
          marginBottom: 16,
          display: 'inline-block',
        }}
      >
        &larr; Back to Leads
      </Link>

      {/* Section 1: Lead Summary Card */}
      <div style={sectionStyle}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: 24,
            flexWrap: 'wrap',
          }}
        >
          <div style={{ flex: 1, minWidth: 300 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700, color: '#111827', margin: '0 0 4px' }}>
              {lead.name}
            </h1>
            {lead.role_title && (
              <p style={{ fontSize: 15, color: '#4b5563', margin: '0 0 2px' }}>
                {lead.role_title}
              </p>
            )}
            {lead.company_name && (
              <p style={{ fontSize: 15, fontWeight: 600, color: '#1f2937', margin: '0 0 16px' }}>
                {lead.company_name}
              </p>
            )}

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                gap: '4px 24px',
              }}
            >
              <ContactItem label="Email" value={lead.email} href={lead.email ? `mailto:${lead.email}` : undefined} />
              <ContactItem label="Phone" value={lead.phone} href={lead.phone ? `tel:${lead.phone}` : undefined} />
              <ContactItem label="WhatsApp" value={lead.whatsapp} href={lead.whatsapp ? `https://wa.me/${lead.whatsapp.replace(/[^0-9+]/g, '')}` : undefined} />
              <ContactItem label="Website" value={lead.website} href={lead.website} />
              {session && <ContactItem label="Country" value={session.country} />}
            </div>

            {lead.details && (
              <p
                style={{
                  fontSize: 13,
                  color: '#6b7280',
                  lineHeight: 1.5,
                  marginTop: 12,
                  padding: 12,
                  backgroundColor: '#f9fafb',
                  borderRadius: 6,
                  border: '1px solid #f3f4f6',
                }}
              >
                {lead.details}
              </p>
            )}
          </div>

          {/* Large confidence score */}
          <div
            style={{
              textAlign: 'center',
              padding: '16px 24px',
              borderRadius: 8,
              backgroundColor: '#f9fafb',
              border: `2px solid ${tierColor}22`,
              flexShrink: 0,
            }}
          >
            <div
              style={{
                fontSize: 36,
                fontWeight: 800,
                color: tierColor,
                lineHeight: 1,
              }}
            >
              {Math.round(lead.confidence_score * 100)}%
            </div>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: tierColor,
                textTransform: 'uppercase',
                marginTop: 4,
                letterSpacing: '0.08em',
              }}
            >
              {tier} confidence
            </div>
            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 6 }}>
              {lead.source_count} source{lead.source_count !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </div>

      {/* Section 2: Confidence Breakdown */}
      <div style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Confidence Breakdown</h2>
        <ConfidenceBreakdown breakdown={lead.confidence_breakdown} />
      </div>

      {/* Section 3: Source Evidence */}
      <div style={sectionStyle}>
        <h2 style={sectionTitleStyle}>
          Source Evidence
          <span style={{ fontSize: 12, fontWeight: 400, color: '#9ca3af', marginLeft: 8 }}>
            ({sources.length} source{sources.length !== 1 ? 's' : ''})
          </span>
        </h2>
        <SourceEvidence sources={sources} />
      </div>

      {/* Section 4: Verification Notes */}
      <div style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Verification Notes</h2>
        {verificationRecords.length === 0 ? (
          <p style={{ fontSize: 13, color: '#9ca3af', fontStyle: 'italic' }}>
            No verification records available.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {verificationRecords.map((record) => {
              const dimColor = dimensionColors[record.dimension] || '#6b7280'
              const recTier = confidenceTier(record.score)
              const recColor = confidenceColors[recTier]

              return (
                <div
                  key={record.dimension}
                  style={{
                    padding: 14,
                    borderRadius: 6,
                    border: '1px solid #e5e7eb',
                    borderLeft: `4px solid ${dimColor}`,
                    backgroundColor: '#fafafa',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 6,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 13,
                        fontWeight: 700,
                        color: dimColor,
                        textTransform: 'capitalize',
                      }}
                    >
                      {record.dimension.replace(/_/g, ' ')}
                    </span>
                    <span style={{ fontSize: 13, fontWeight: 700, color: recColor }}>
                      {Math.round(record.score * 100)}%
                    </span>
                  </div>
                  <p style={{ fontSize: 13, color: '#4b5563', lineHeight: 1.5, margin: 0 }}>
                    {record.verifier_notes}
                  </p>
                  {record.contradictions && (
                    <div
                      style={{
                        marginTop: 8,
                        padding: '8px 10px',
                        backgroundColor: '#fef3c7',
                        borderRadius: 4,
                        border: '1px solid #fcd34d',
                      }}
                    >
                      <span style={{ fontSize: 11, fontWeight: 600, color: '#92400e' }}>
                        CONTRADICTION:
                      </span>
                      <span style={{ fontSize: 12, color: '#78350f', marginLeft: 6 }}>
                        {record.contradictions}
                      </span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Section 5: Draft Status */}
      <div style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Outreach Draft</h2>
        {draft ? (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: 14,
              borderRadius: 6,
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
            }}
          >
            <div>
              <p style={{ fontSize: 14, fontWeight: 600, color: '#166534', margin: '0 0 4px' }}>
                {draft.subject}
              </p>
              <p style={{ fontSize: 12, color: '#4ade80', margin: 0 }}>
                Version {draft.version_number} &middot; Status:{' '}
                <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                  {draft.status.replace(/_/g, ' ')}
                </span>
                &middot; Generated {formatDate(draft.generated_at)}
              </p>
            </div>
            <Link
              to="/approvals/$draftId"
              params={{ draftId: draft.id }}
              style={{
                padding: '8px 16px',
                fontSize: 13,
                fontWeight: 600,
                color: 'white',
                backgroundColor: '#16a34a',
                borderRadius: 6,
                textDecoration: 'none',
                flexShrink: 0,
              }}
            >
              View Draft
            </Link>
          </div>
        ) : (
          <div
            style={{
              padding: 14,
              borderRadius: 6,
              backgroundColor: '#f9fafb',
              border: '1px solid #e5e7eb',
              textAlign: 'center',
            }}
          >
            <p style={{ fontSize: 14, color: '#6b7280', margin: '0 0 4px' }}>
              No draft generated
            </p>
            <p style={{ fontSize: 12, color: '#9ca3af', margin: 0 }}>
              Outreach status: <span style={{ fontWeight: 600 }}>not started</span>
            </p>
          </div>
        )}
      </div>

      {/* Metadata footer */}
      <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 8 }}>
        Lead ID: {lead.id} &middot; Created: {formatDate(lead.created_at)} &middot; Updated:{' '}
        {formatDate(lead.updated_at)}
        {lead.discovery_skill_used && (
          <span> &middot; Discovery: {lead.discovery_skill_used}</span>
        )}
      </div>
    </div>
  )
}
