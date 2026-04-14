import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-foreground">Meeting Transcriber</h1>
        <p className="text-muted-foreground">Real-time transcription with AI summaries</p>
      </div>
    </div>
  )
}
