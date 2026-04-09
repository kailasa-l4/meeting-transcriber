import { formatConfidence, confidenceTier, confidenceColors } from '~/utils/formatters'

export function ConfidenceScore({ score }: { score: number }) {
  const tier = confidenceTier(score)
  return (
    <span style={{ fontWeight: 700, color: confidenceColors[tier] }}>
      {formatConfidence(score)}
    </span>
  )
}
