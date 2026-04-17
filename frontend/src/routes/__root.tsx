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
import { getStoredUser, setAuth, clearAuth, isAuthenticated } from '@/lib/auth'
import type { User } from '@/lib/auth'

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: RootComponent,
})

function RootComponent() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<User | null>(null)
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setUser(getStoredUser())
    setHydrated(true)
  }, [])

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
    const publicPaths = ['/login', '/register']
    if (!authed && !publicPaths.includes(location.pathname)) {
      navigate({ to: '/login' })
    }
  }, [hydrated, authed, location.pathname, navigate])

  const isPublicPage = ['/login', '/register'].includes(location.pathname)

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: authed }}>
      {authed && !isPublicPage ? (
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
