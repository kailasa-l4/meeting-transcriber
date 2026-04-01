import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/approvals/$draftId')({
  component: DraftReviewPage,
})

function DraftReviewPage() {
  const { draftId } = Route.useParams()
  return (
    <div>
      <h1>Draft Review: {draftId}</h1>
      <p>Coming soon...</p>
    </div>
  )
}
