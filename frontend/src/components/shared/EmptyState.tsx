export function EmptyState({
  title = 'No data found',
  description,
  action,
}: {
  title?: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 48,
      gap: 8,
      border: '1px dashed #d1d5db',
      borderRadius: 8,
      backgroundColor: '#f9fafb',
    }}>
      <p style={{ fontSize: 16, fontWeight: 600, color: '#374151' }}>{title}</p>
      {description && (
        <p style={{ fontSize: 14, color: '#6b7280', textAlign: 'center', maxWidth: 400 }}>
          {description}
        </p>
      )}
      {action && <div style={{ marginTop: 12 }}>{action}</div>}
    </div>
  )
}
