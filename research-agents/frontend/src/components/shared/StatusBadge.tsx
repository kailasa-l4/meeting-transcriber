import { statusColors } from '~/utils/formatters'

export function StatusBadge({ status }: { status: string }) {
  const color = (statusColors as Record<string, string>)[status] || '#6b7280'
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 4,
      fontSize: 12, fontWeight: 600, color: 'white', backgroundColor: color,
    }}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}
