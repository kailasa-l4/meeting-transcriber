import { useState } from 'react'
import type { LeadSource } from '~/utils/types'

const sourceTypeColors: Record<string, string> = {
  web: '#3b82f6',
  linkedin: '#0077b5',
  news: '#f59e0b',
  government: '#16a34a',
  directory: '#8b5cf6',
  database: '#6b7280',
}

function SourceCard({ source }: { source: LeadSource }) {
  const [expanded, setExpanded] = useState(false)
  const typeColor = sourceTypeColors[source.source_type || 'web'] || '#6b7280'
  const excerpt = source.excerpt || ''
  const needsTruncation = excerpt.length > 200

  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        padding: 16,
        backgroundColor: '#fafafa',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          marginBottom: 8,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          {source.source_type && (
            <span
              style={{
                display: 'inline-block',
                padding: '2px 8px',
                borderRadius: 4,
                fontSize: 11,
                fontWeight: 600,
                color: 'white',
                backgroundColor: typeColor,
                textTransform: 'uppercase',
                flexShrink: 0,
              }}
            >
              {source.source_type}
            </span>
          )}
          <span
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: '#1f2937',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {source.source_title || source.source_url || 'Unknown source'}
          </span>
        </div>

        {source.collected_at && (
          <span style={{ fontSize: 11, color: '#9ca3af', flexShrink: 0 }}>
            {new Date(source.collected_at).toLocaleDateString()}
          </span>
        )}
      </div>

      {source.source_url && (
        <a
          href={source.source_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'block',
            fontSize: 12,
            color: '#3b82f6',
            textDecoration: 'none',
            marginBottom: excerpt ? 8 : 0,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {source.source_url}
        </a>
      )}

      {excerpt && (
        <div>
          <p style={{ fontSize: 13, color: '#4b5563', lineHeight: 1.5, margin: 0 }}>
            {expanded || !needsTruncation ? excerpt : `${excerpt.slice(0, 200)}...`}
          </p>
          {needsTruncation && (
            <button
              onClick={() => setExpanded(!expanded)}
              style={{
                marginTop: 4,
                padding: 0,
                border: 'none',
                background: 'none',
                color: '#3b82f6',
                fontSize: 12,
                cursor: 'pointer',
                fontWeight: 500,
              }}
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export function SourceEvidence({ sources }: { sources: LeadSource[] }) {
  if (sources.length === 0) {
    return (
      <p style={{ fontSize: 14, color: '#9ca3af', fontStyle: 'italic' }}>
        No source evidence collected.
      </p>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {sources.map((source) => (
        <SourceCard key={source.id} source={source} />
      ))}
    </div>
  )
}
