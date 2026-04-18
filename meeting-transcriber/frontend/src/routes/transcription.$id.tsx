import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { transcriptionsApi } from "@/lib/api";
import { TranscriptionView } from "@/components/transcription-detail";

export const Route = createFileRoute("/transcription/$id")({
  component: TranscriptionPage,
});

function TranscriptionPage() {
  const { id } = Route.useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["transcription", id],
    queryFn: () => transcriptionsApi.get(Number(id)),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading transcription...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive">Failed to load transcription</p>
      </div>
    );
  }

  return <TranscriptionView data={data} />;
}
