import { useState, useCallback, useEffect } from 'react'
import {
  Outlet,
  createRootRouteWithContext,
  useNavigate,
  useLocation,
} from '@tanstack/react-router'
import type { QueryClient } from '@tanstack/react-query'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { AuthContext } from '@/hooks/use-auth'
import { getStoredUser, setAuth, clearAuth, isAuthenticated, getToken } from '@/lib/auth'
import type { User } from '@/lib/auth'
import { authApi } from '@/lib/api'

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: RootComponent,
})

const PUBLIC_PATHS = ['/login', '/register']
const NON_APP_PATHS = ['/pending']

function RootComponent() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<User | null>(null)
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setUser(getStoredUser())
    setHydrated(true)
  }, [])

  // Refresh user from /me once after hydration so status is current
  useEffect(() => {
    if (!hydrated) return
    if (!getToken()) return
    authApi
      .me()
      .then((me) => {
        const refreshed: User = {
          user_id: me.id,
          username: me.username,
          display_name: me.display_name,
          status: me.status,
          is_admin: me.is_admin,
        }
        const token = getToken()
        if (token) {
          setAuth(token, refreshed)
          setUser(refreshed)
        }
      })
      .catch(() => {
        // 401/403 handled in api.ts (redirect to /login or /pending)
      })
  }, [hydrated])

  const login = useCallback((token: string, userData: User) => {
    setAuth(token, userData)
    setUser(userData)
  }, [])

  const logout = useCallback(() => {
    clearAuth()
    setUser(null)
    navigate({ to: '/login' })
  }, [navigate])

  const authed = hydrated && isAuthenticated() && user !== null

  useEffect(() => {
    if (!hydrated) return
    const path = location.pathname
    if (PUBLIC_PATHS.includes(path)) return
    if (!authed) {
      navigate({ to: '/login' })
      return
    }
    if (!user) return
    if (user.status !== 'approved' && path !== '/pending') {
      navigate({ to: '/pending' })
      return
    }
    if (user.status === 'approved' && path === '/pending') {
      navigate({ to: '/' })
      return
    }
    if (path === '/admin' && !user.is_admin) {
      navigate({ to: '/' })
      return
    }
  }, [hydrated, authed, user, location.pathname, navigate])

  const isPublicPage = PUBLIC_PATHS.includes(location.pathname)
  const isNonAppPage = NON_APP_PATHS.includes(location.pathname)
  const showAppShell = authed && user?.status === 'approved' && !isPublicPage && !isNonAppPage

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: authed }}>
      {showAppShell ? (
        <SidebarProvider>
          <AppSidebar />
          <main className="flex-1 flex flex-col h-dvh overflow-auto">
            <Outlet />
          </main>
        </SidebarProvider>
      ) : (
        <Outlet />
      )}
    </AuthContext.Provider>
  )
}
