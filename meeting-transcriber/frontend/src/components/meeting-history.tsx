import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { TranscriptLine } from "./transcript-line";
import type { MeetingDetail } from "@/lib/api";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "Unknown duration";
  const m = Math.floor(seconds / 60);
  return `${m} min`;
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

interface MeetingHistoryProps {
  data: MeetingDetail;
}

export function MeetingHistory({ data }: MeetingHistoryProps) {
  const { meeting, transcripts, summaries } = data;
  const chunkSummaries = summaries.filter((s) => s.type === "chunk");
  const finalSummary = summaries.find((s) => s.type === "final");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <SidebarTrigger className="md:hidden" />
          <div className="flex-1">
            <h1 className="font-semibold text-lg">{meeting.title || `Meeting ${meeting.session_id}`}</h1>
            <p className="text-sm text-muted-foreground">
              {formatDate(meeting.started_at)} &middot; {formatDuration(meeting.duration_seconds)}
            </p>
          </div>
          <Badge variant={meeting.status === "completed" ? "secondary" : "destructive"}>
            {meeting.status}
          </Badge>
        </div>
      </div>

      {/* Tabbed content */}
      <Tabs defaultValue="summary" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="mx-4 mt-4">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="flex-1 overflow-auto p-4 space-y-4">
          {finalSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Final Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm whitespace-pre-wrap">{finalSummary.content}</div>
              </CardContent>
            </Card>
          )}

          {chunkSummaries.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">Interim Summaries</h3>
              {chunkSummaries.map((s, i) => (
                <Card key={i}>
                  <CardHeader className="py-2 px-3">
                    <CardTitle className="text-xs">
                      <Badge variant="outline">{s.time_range || `Chunk ${i + 1}`}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="px-3 pb-3 pt-0">
                    <p className="text-sm whitespace-pre-wrap">{s.content}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!finalSummary && chunkSummaries.length === 0 && (
            <p className="text-muted-foreground text-sm">No summaries available for this meeting.</p>
          )}
        </TabsContent>

        <TabsContent value="transcript" className="flex-1 overflow-hidden p-4">
          <ScrollArea className="h-full">
            {transcripts.length === 0 ? (
              <p className="text-muted-foreground text-sm">No transcript available.</p>
            ) : (
              transcripts.map((t, i) => (
                <TranscriptLine key={i} speaker={t.speaker} text={t.text} isFinal={true} />
              ))
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
