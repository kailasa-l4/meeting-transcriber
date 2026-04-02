import { confidenceTier, confidenceColors } from '~/utils/formatters'

const dimensionLabels: Record<string, string> = {
  entity: 'Entity Match',
  contact: 'Contact Validity',
  source_quality: 'Source Quality',
  dedup: 'Deduplication',
}

export function ConfidenceBreakdown({ breakdown }: { breakdown: Record<string, number> }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {Object.entries(breakdown).map(([dimension, score]) => {
        const tier = confidenceTier(score)
        const color = confidenceColors[tier]
        const pct = Math.round(score * 100)

        return (
          <div key={dimension} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span
              style={{
                width: 120,
                fontSize: 13,
                fontWeight: 500,
                color: '#374151',
                textTransform: 'capitalize',
                flexShrink: 0,
              }}
            >
              {dimensionLabels[dimension] || dimension}
            </span>

            <div
              style={{
                flex: 1,
                height: 20,
                backgroundColor: '#e5e7eb',
                borderRadius: 4,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <div
                style={{
                  width: `${pct}%`,
                  height: '100%',
                  backgroundColor: color,
                  borderRadius: 4,
                  transition: 'width 0.3s ease',
                }}
              />
            </div>

            <span
              style={{
                width: 40,
                textAlign: 'right',
                fontSize: 13,
                fontWeight: 700,
                color,
                flexShrink: 0,
              }}
            >
              {pct}%
            </span>
          </div>
        )
      })}
    </div>
  )
}
