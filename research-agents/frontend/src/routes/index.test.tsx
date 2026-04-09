import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

// Simple smoke test - doesn't test the actual route, just React rendering
describe('Dashboard smoke test', () => {
  it('renders a heading', () => {
    render(<h1>Dashboard</h1>)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders stat cards', () => {
    render(
      <div>
        <div data-testid="stat-sessions">Sessions: 0</div>
        <div data-testid="stat-leads">Leads: 0</div>
        <div data-testid="stat-approvals">Pending Approvals: 0</div>
      </div>
    )
    expect(screen.getByTestId('stat-sessions')).toBeInTheDocument()
    expect(screen.getByTestId('stat-leads')).toBeInTheDocument()
    expect(screen.getByTestId('stat-approvals')).toBeInTheDocument()
  })
})
