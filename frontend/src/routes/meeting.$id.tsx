import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { meetingsApi } from "@/lib/api";
import { MeetingHistory } from "@/components/meeting-history";

export const Route = createFileRoute("/meeting/$id")({
  component: MeetingPage,
});

function MeetingPage() {
  const { id } = Route.useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["meeting", id],
    queryFn: () => meetingsApi.get(Number(id)),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading meeting...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive">Failed to load meeting</p>
      </div>
    );
  }

  return <MeetingHistory data={data} />;
}
