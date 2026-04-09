import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorBoundary } from './ErrorBoundary'

function ThrowError() {
  throw new Error('Test error')
}

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(<ErrorBoundary><div>Content</div></ErrorBoundary>)
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders error fallback when error thrown', () => {
    // Suppress console.error for expected error
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<ErrorBoundary><ThrowError /></ErrorBoundary>)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Test error')).toBeInTheDocument()
    spy.mockRestore()
  })

  it('shows try again button', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<ErrorBoundary><ThrowError /></ErrorBoundary>)
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    spy.mockRestore()
  })
})
