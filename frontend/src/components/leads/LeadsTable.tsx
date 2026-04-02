import { useState, useMemo } from 'react'
import { Link } from '@tanstack/react-router'
import { ConfidenceScore } from '~/components/shared/ConfidenceScore'
import { formatDate } from '~/utils/formatters'
import type { Lead, LeadVerificationStatus } from '~/utils/types'

type SortField =
  | 'name'
  | 'role_title'
  | 'company_name'
  | 'email'
  | 'phone'
  | 'confidence_score'
  | 'verification_status'

type SortDir = 'asc' | 'desc'

const verificationStatusColors: Record<LeadVerificationStatus, string> = {
  discovered: '#6b7280',
  normalized: '#8b5cf6',
  verified: '#16a34a',
  needs_review: '#f59e0b',
  rejected: '#dc2626',
}

function VerificationBadge({ status }: { status: LeadVerificationStatus }) {
  const color = verificationStatusColors[status] || '#6b7280'
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: 4,
        fontSize: 11,
        fontWeight: 600,
        color: 'white',
        backgroundColor: color,
        textTransform: 'capitalize',
      }}
    >
      {status.replace(/_/g, ' ')}
    </span>
  )
}

interface ColumnDef {
  key: SortField
  label: string
  show?: boolean
}

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '10px 12px',
  fontSize: 12,
  fontWeight: 600,
  color: '#6b7280',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  borderBottom: '2px solid #e5e7eb',
  cursor: 'pointer',
  userSelect: 'none',
  whiteSpace: 'nowrap',
}

const tdStyle: React.CSSProperties = {
  padding: '10px 12px',
  fontSize: 13,
  color: '#374151',
  borderBottom: '1px solid #f3f4f6',
  verticalAlign: 'middle',
}

export function LeadsTable({
  leads,
  showCountryColumn = false,
  countryMap,
}: {
  leads: Lead[]
  showCountryColumn?: boolean
  countryMap?: Record<string, string>
}) {
  const [sortField, setSortField] = useState<SortField>('confidence_score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const columns: ColumnDef[] = [
    { key: 'name', label: 'Name' },
    { key: 'role_title', label: 'Role / Title' },
    { key: 'company_name', label: 'Company' },
    { key: 'email', label: 'Email' },
    { key: 'phone', label: 'Phone' },
    { key: 'confidence_score', label: 'Confidence' },
    { key: 'verification_status', label: 'Verification' },
  ]

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir(field === 'confidence_score' ? 'desc' : 'asc')
    }
  }

  const sorted = useMemo(() => {
    return [...leads].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      const aVal = a[sortField] ?? ''
      const bVal = b[sortField] ?? ''
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return (aVal - bVal) * dir
      }
      return String(aVal).localeCompare(String(bVal)) * dir
    })
  }, [leads, sortField, sortDir])

  const sortIndicator = (field: SortField) => {
    if (field !== sortField) return ''
    return sortDir === 'asc' ? ' \u25B2' : ' \u25BC'
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} style={thStyle} onClick={() => handleSort(col.key)}>
                {col.label}
                {sortIndicator(col.key)}
              </th>
            ))}
            {showCountryColumn && (
              <th style={thStyle}>Country</th>
            )}
          </tr>
        </thead>
        <tbody>
          {sorted.map((lead) => (
            <tr
              key={lead.id}
              style={{ transition: 'background 0.15s' }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f9fafb'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              <td style={tdStyle}>
                <Link
                  to="/leads/$leadId"
                  params={{ leadId: lead.id }}
                  style={{
                    color: '#2563eb',
                    textDecoration: 'none',
                    fontWeight: 600,
                    fontSize: 13,
                  }}
                >
                  {lead.name}
                </Link>
              </td>
              <td style={tdStyle}>{lead.role_title || '\u2014'}</td>
              <td style={tdStyle}>{lead.company_name || '\u2014'}</td>
              <td style={tdStyle}>
                {lead.email ? (
                  <a
                    href={`mailto:${lead.email}`}
                    style={{ color: '#2563eb', textDecoration: 'none', fontSize: 12 }}
                  >
                    {lead.email}
                  </a>
                ) : (
                  '\u2014'
                )}
              </td>
              <td style={{ ...tdStyle, whiteSpace: 'nowrap' }}>
                {lead.phone || '\u2014'}
              </td>
              <td style={tdStyle}>
                <ConfidenceScore score={lead.confidence_score} />
              </td>
              <td style={tdStyle}>
                <VerificationBadge status={lead.verification_status} />
              </td>
              {showCountryColumn && (
                <td style={tdStyle}>
                  {countryMap?.[lead.country_job_id] || lead.country_job_id}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
