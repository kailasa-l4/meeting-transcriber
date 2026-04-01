import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/sessions/$sessionId')({
  component: SessionDetailPage,
})

function SessionDetailPage() {
  const { sessionId } = Route.useParams()
  return (
    <div>
      <h1>Session: {sessionId}</h1>
      <p>Coming soon...</p>
    </div>
  )
}
