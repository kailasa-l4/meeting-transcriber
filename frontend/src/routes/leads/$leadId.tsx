import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/leads/$leadId')({
  component: LeadDetailPage,
})

function LeadDetailPage() {
  const { leadId } = Route.useParams()
  return (
    <div>
      <h1>Lead: {leadId}</h1>
      <p>Coming soon...</p>
    </div>
  )
}
