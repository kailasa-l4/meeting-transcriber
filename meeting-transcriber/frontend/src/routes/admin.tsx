import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { adminApi, type AdminUser, type UserStatus } from "@/lib/api";

export const Route = createFileRoute("/admin")({
  component: AdminPage,
});

const TABS: { key: UserStatus; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "revoked", label: "Revoked" },
  { key: "deleted", label: "Deleted" },
];

function AdminPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<UserStatus>("pending");
  const [confirmDelete, setConfirmDelete] = useState<AdminUser | null>(null);
  const queryClient = useQueryClient();

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["admin-users", tab],
    queryFn: () => adminApi.listUsers(tab),
  });

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });
  };

  const approveMutation = useMutation({
    mutationFn: adminApi.approveUser,
    onSuccess: invalidateAll,
  });

  const revokeMutation = useMutation({
    mutationFn: adminApi.revokeUser,
    onSuccess: invalidateAll,
  });

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => {
      invalidateAll();
      setConfirmDelete(null);
    },
  });

  return (
    <div className="p-6 max-w-5xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">User Management</h1>
        <p className="text-muted-foreground">
          Approve, revoke, or delete users.
        </p>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as UserStatus)}>
        <TabsList>
          {TABS.map((t) => (
            <TabsTrigger key={t.key} value={t.key}>
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {TABS.map((t) => (
          <TabsContent key={t.key} value={t.key}>
            <Card>
              <CardHeader>
                <CardTitle>{t.label} users</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p className="text-muted-foreground">Loading...</p>
                ) : users.length === 0 ? (
                  <p className="text-muted-foreground">No {t.label.toLowerCase()} users.</p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {users.map((u) => {
                      const isSelf = u.id === user?.user_id;
                      return (
                        <div
                          key={u.id}
                          className="flex items-center justify-between gap-3 p-3 border border-border rounded-md"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium truncate">
                                {u.display_name}
                              </span>
                              <Badge variant="outline">{u.username}</Badge>
                              {isSelf && <Badge>you</Badge>}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Registered {new Date(u.created_at).toLocaleString()}
                              {u.approved_at &&
                                ` · Approved ${new Date(u.approved_at).toLocaleString()}`}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            {t.key === "pending" && (
                              <Button
                                size="sm"
                                onClick={() => approveMutation.mutate(u.id)}
                                disabled={approveMutation.isPending}
                              >
                                Approve
                              </Button>
                            )}
                            {t.key === "approved" && !isSelf && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => revokeMutation.mutate(u.id)}
                                disabled={revokeMutation.isPending}
                              >
                                Revoke
                              </Button>
                            )}
                            {t.key === "revoked" && (
                              <Button
                                size="sm"
                                onClick={() => approveMutation.mutate(u.id)}
                                disabled={approveMutation.isPending}
                              >
                                Approve
                              </Button>
                            )}
                            {t.key !== "deleted" && !isSelf && (
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => setConfirmDelete(u)}
                              >
                                Delete
                              </Button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      <Dialog
        open={!!confirmDelete}
        onOpenChange={(open) => !open && setConfirmDelete(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete user?</DialogTitle>
            <DialogDescription>
              {confirmDelete &&
                `Soft-delete ${confirmDelete.display_name} (@${confirmDelete.username}). Their meetings and transcriptions will be preserved, and the username will be freed for reuse. This can't be undone from the UI.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmDelete(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                confirmDelete && deleteMutation.mutate(confirmDelete.id)
              }
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
