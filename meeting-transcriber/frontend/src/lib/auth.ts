const TOKEN_KEY = "mt_token";
const USER_KEY = "mt_user";

const isBrowser = typeof window !== "undefined";

export type UserStatus = "pending" | "approved" | "revoked" | "deleted";

export interface User {
  user_id: number;
  username: string;
  display_name: string;
  status: UserStatus;
  is_admin: boolean;
}

export function getToken(): string | null {
  if (!isBrowser) return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuth(token: string, user: User): void {
  if (!isBrowser) return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): User | null {
  if (!isBrowser) return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  if (!isBrowser) return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
