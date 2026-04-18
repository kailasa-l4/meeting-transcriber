import { useEffect } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { authApi } from "@/lib/api";
import { setAuth, getToken } from "@/lib/auth";

export const Route = createFileRoute("/pending")({
  component: PendingPage,
});

function PendingPage() {
  const navigate = useNavigate();
  const { user, logout, login } = useAuth();

  const { data: me } = useQuery({
    queryKey: ["me-pending"],
    queryFn: authApi.me,
    refetchInterval: user?.status === "pending" ? 10000 : false,
    enabled: !!user && user.status !== "approved",
  });

  useEffect(() => {
    if (!me) return;
    const token = getToken();
    if (!token) return;
    const updatedUser = {
      user_id: me.id,
      username: me.username,
      display_name: me.display_name,
      status: me.status,
      is_admin: me.is_admin,
    };
    setAuth(token, updatedUser);
    login(token, updatedUser);
    if (me.status === "approved") {
      navigate({ to: "/" });
    }
  }, [me, login, navigate]);

  const status = me?.status ?? user?.status ?? "pending";

  return (
    <div className="min-h-dvh flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl">
            {status === "revoked" ? "Access Revoked" : "Awaiting Approval"}
          </CardTitle>
          <CardDescription>
            {status === "revoked"
              ? "Your access to this application has been revoked. Please contact the admin if you believe this is a mistake."
              : "Your account has been created and is pending admin approval. You'll automatically get access once it's approved."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {status === "pending" && (
            <p className="text-sm text-muted-foreground">
              This page refreshes automatically every 10 seconds.
            </p>
          )}
          <Button variant="outline" onClick={logout}>
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
