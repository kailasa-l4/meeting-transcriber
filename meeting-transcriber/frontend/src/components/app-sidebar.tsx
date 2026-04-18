import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { meetingsApi, transcriptionsApi, type Meeting } from "@/lib/api";

function groupByDate(meetings: Meeting[]): Record<string, Meeting[]> {
  const groups: Record<string, Meeting[]> = {};
  const now = new Date();
  const today = now.toDateString();
  const yesterday = new Date(now.getTime() - 86400000).toDateString();

  for (const m of meetings) {
    const d = new Date(m.started_at).toDateString();
    let label: string;
    if (d === today) label = "Today";
    else if (d === yesterday) label = "Yesterday";
    else
      label = new Date(m.started_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });

    if (!groups[label]) groups[label] = [];
    groups[label].push(m);
  }
  return groups;
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  return `${m}m`;
}

export function AppSidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data: meetings = [] } = useQuery({
    queryKey: ["meetings"],
    queryFn: meetingsApi.list,
    refetchInterval: 10000,
  });

  const { data: transcriptions = [] } = useQuery({
    queryKey: ["transcriptions"],
    queryFn: transcriptionsApi.list,
    refetchInterval: 10000,
  });

  const grouped = groupByDate(meetings);

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex items-center justify-between px-1">
          <span className="font-semibold text-base">Meetings</span>
          <SidebarTrigger />
        </div>
        <Button className="w-full" onClick={() => navigate({ to: "/" })}>
          + New Meeting
        </Button>
        <Button
          variant="outline"
          className="w-full"
          onClick={() => navigate({ to: "/transcribe" })}
        >
          Upload & Transcribe
        </Button>
        {user?.is_admin && (
          <Button
            variant="outline"
            className="w-full"
            onClick={() => navigate({ to: "/admin" })}
          >
            User Management
          </Button>
        )}
      </SidebarHeader>

      <SidebarContent>
        {Object.entries(grouped).map(([label, items]) => (
          <SidebarGroup key={label}>
            <SidebarGroupLabel>{label}</SidebarGroupLabel>
            <SidebarMenu>
              {items.map((m) => (
                <SidebarMenuItem key={m.id}>
                  {/* SidebarMenuButton doesn't implement asChild rendering;
                      render Link directly with equivalent button styles */}
                  <SidebarMenuButton>
                    <Link
                      to="/meeting/$id"
                      params={{ id: String(m.id) }}
                      className="flex w-full items-center gap-2"
                    >
                      <span className="truncate flex-1">
                        {m.title || `Meeting ${m.session_id}`}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {m.status === "recording" ? (
                          <Badge variant="destructive" className="text-xs">
                            Live
                          </Badge>
                        ) : (
                          formatDuration(m.duration_seconds)
                        )}
                      </span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        ))}

        {transcriptions.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel>Transcriptions</SidebarGroupLabel>
            <SidebarMenu>
              {transcriptions.map((t) => (
                <SidebarMenuItem key={t.id}>
                  <SidebarMenuButton>
                    <Link to="/transcription/$id" params={{ id: String(t.id) }} className="flex w-full items-center gap-2">
                      <span className="truncate flex-1">
                        {t.file_name}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {t.status === "completed" ? (
                          t.duration_seconds ? `${Math.floor(t.duration_seconds / 60)}m` : ""
                        ) : (
                          <Badge variant={t.status === "failed" ? "destructive" : "default"} className="text-xs">
                            {t.status}
                          </Badge>
                        )}
                      </span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="p-4 border-t border-border">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground truncate">
            {user?.display_name}
          </span>
          <Button variant="ghost" size="sm" onClick={logout}>
            Sign out
          </Button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
