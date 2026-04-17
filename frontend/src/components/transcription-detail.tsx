import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { TranscriptLine } from "./transcript-line";
import type { TranscriptionDetail as TranscriptionDetailType, TranscriptionSegment } from "@/lib/api";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "Unknown duration";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

interface TranscriptionViewProps {
  data: TranscriptionDetailType;
}

export function TranscriptionView({ data }: TranscriptionViewProps) {
  const segments: TranscriptionSegment[] = data.segments
    ? JSON.parse(data.segments)
    : [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <SidebarTrigger />
          <div className="flex-1">
            <h1 className="font-semibold text-lg">{data.file_name}</h1>
            <p className="text-sm text-muted-foreground">
              {formatDate(data.created_at)} &middot; {formatDuration(data.duration_seconds)}
            </p>
          </div>
          <Badge variant={data.status === "completed" ? "secondary" : "destructive"}>
            {data.status}
          </Badge>
        </div>
      </div>

      {/* Content */}
      {data.status === "failed" && (
        <div className="p-4">
          <p className="text-destructive text-sm">Error: {data.error_message}</p>
        </div>
      )}

      {data.status === "completed" && (
        <ScrollArea className="flex-1 p-4">
          {segments.length > 0 ? (
            segments.map((seg, i) => (
              <TranscriptLine
                key={i}
                speaker={seg.speaker}
                text={seg.text}
                isFinal={true}
              />
            ))
          ) : (
            <p className="text-sm whitespace-pre-wrap">{data.transcript}</p>
          )}
        </ScrollArea>
      )}
    </div>
  );
}
