/// <reference types="vite/client" />
import { useState, useCallback, useEffect } from 'react'
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRouteWithContext,
  useNavigate,
  useLocation,
} from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { AuthContext } from '@/hooks/use-auth'
import { getStoredUser, setAuth, clearAuth, isAuthenticated } from '@/lib/auth'
import type { User } from '@/lib/auth'
import appCss from '../styles/app.css?url'

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1.0, user-scalable=no' },
      { name: 'theme-color', content: '#0f1117' },
      { name: 'apple-mobile-web-app-capable', content: 'yes' },
      { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
      { title: 'Meeting Transcriber' },
    ],
    links: [
      { rel: 'stylesheet', href: appCss },
      { rel: 'manifest', href: '/manifest.json' },
    ],
  }),
  component: RootComponent,
})

function RootComponent() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<User | null>(null)
  const [hydrated, setHydrated] = useState(false)

  // Hydrate auth state from localStorage only on client
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

  // Auth guard: only redirect after hydration on client
  useEffect(() => {
    if (!hydrated) return
    const publicPaths = ['/login', '/register']
    if (!authed && !publicPaths.includes(location.pathname)) {
      navigate({ to: '/login' })
    }
  }, [hydrated, authed, location.pathname, navigate])

  const isPublicPage = ['/login', '/register'].includes(location.pathname)

  return (
    <RootDocument>
      <QueryClientProvider client={Route.useRouteContext().queryClient}>
        <AuthContext.Provider value={{ user, login, logout, isAuthenticated: authed }}>
          {authed && !isPublicPage ? (
            <SidebarProvider>
              <AppSidebar />
              <main className="flex-1 flex flex-col min-h-dvh overflow-hidden">
                <Outlet />
              </main>
            </SidebarProvider>
          ) : (
            <Outlet />
          )}
        </AuthContext.Provider>
      </QueryClientProvider>
    </RootDocument>
  )
}

function RootDocument({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <head>
        <HeadContent />
      </head>
      <body className="min-h-dvh bg-background text-foreground">
        {children}
        <Scripts />
      </body>
    </html>
  )
}
