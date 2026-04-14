import { createFileRoute } from "@tanstack/react-router";
import { MeetingRecorder } from "@/components/meeting-recorder";

export const Route = createFileRoute("/")({
  component: DashboardPage,
});

function DashboardPage() {
  return <MeetingRecorder />;
}
