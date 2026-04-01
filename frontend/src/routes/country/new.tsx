import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/country/new')({
  component: NewCountryRunPage,
})

function NewCountryRunPage() {
  return (
    <div>
      <h1>New Country Run</h1>
      <p>Coming soon...</p>
    </div>
  )
}
