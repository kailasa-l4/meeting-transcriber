/// <reference types="vite/client" />
import {
  HeadContent,
  Link,
  Outlet,
  Scripts,
  createRootRoute,
} from '@tanstack/react-router'
import * as React from 'react'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'Gold Lead Research System' },
    ],
  }),
  component: RootComponent,
})

function RootComponent() {
  return (
    <RootLayout>
      <Outlet />
    </RootLayout>
  )
}

function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <div style={{ display: 'flex', minHeight: '100vh' }}>
          <nav
            style={{
              width: 240,
              padding: 16,
              borderRight: '1px solid #e2e8f0',
              background: '#f8fafc',
            }}
          >
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 24 }}>
              Gold Leads
            </h2>
            <ul
              style={{
                listStyle: 'none',
                padding: 0,
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              <li>
                <Link to="/" activeOptions={{ exact: true }}>
                  Dashboard
                </Link>
              </li>
              <li>
                <Link to="/sessions">Sessions</Link>
              </li>
              <li>
                <Link to="/leads">Leads</Link>
              </li>
              <li>
                <Link to="/approvals">Approvals</Link>
              </li>
              <li>
                <Link to="/country/new">New Country Run</Link>
              </li>
            </ul>
          </nav>
          <main style={{ flex: 1, padding: 24 }}>{children}</main>
        </div>
        <Scripts />
      </body>
    </html>
  )
}
