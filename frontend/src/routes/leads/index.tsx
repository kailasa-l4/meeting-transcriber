import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/leads/')({
  component: LeadsPage,
})

function LeadsPage() {
  return (
    <div>
      <h1>Leads</h1>
      <p>Coming soon...</p>
    </div>
  )
}
