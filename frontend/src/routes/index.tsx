import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: Dashboard,
})

function Dashboard() {
  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>
        Dashboard
      </h1>
      <p>Gold Lead Research System — Operator Control Tower</p>
      <div
        style={{
          marginTop: 24,
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 16,
        }}
      >
        <div
          style={{ padding: 16, border: '1px solid #e2e8f0', borderRadius: 8 }}
        >
          <h3>Sessions</h3>
          <p style={{ fontSize: 32, fontWeight: 700 }}>--</p>
        </div>
        <div
          style={{ padding: 16, border: '1px solid #e2e8f0', borderRadius: 8 }}
        >
          <h3>Leads</h3>
          <p style={{ fontSize: 32, fontWeight: 700 }}>--</p>
        </div>
        <div
          style={{ padding: 16, border: '1px solid #e2e8f0', borderRadius: 8 }}
        >
          <h3>Pending Approvals</h3>
          <p style={{ fontSize: 32, fontWeight: 700 }}>--</p>
        </div>
      </div>
    </div>
  )
}
