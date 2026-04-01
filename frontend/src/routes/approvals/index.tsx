import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/approvals/')({
  component: ApprovalsPage,
})

function ApprovalsPage() {
  return (
    <div>
      <h1>Approvals</h1>
      <p>Coming soon...</p>
    </div>
  )
}
