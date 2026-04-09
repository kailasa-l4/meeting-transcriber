import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it('renders the status text', () => {
    render(<StatusBadge status="completed" />)
    expect(screen.getByText('completed')).toBeInTheDocument()
  })

  it('replaces underscores with spaces', () => {
    render(<StatusBadge status="waiting_for_approval" />)
    expect(screen.getByText('waiting for approval')).toBeInTheDocument()
  })

  it('renders unknown statuses with default color', () => {
    render(<StatusBadge status="unknown_status" />)
    expect(screen.getByText('unknown status')).toBeInTheDocument()
  })

  it('renders running status', () => {
    render(<StatusBadge status="running" />)
    expect(screen.getByText('running')).toBeInTheDocument()
  })

  it('renders queued status', () => {
    render(<StatusBadge status="queued" />)
    expect(screen.getByText('queued')).toBeInTheDocument()
  })

  it('renders failed status', () => {
    render(<StatusBadge status="failed" />)
    expect(screen.getByText('failed')).toBeInTheDocument()
  })

  it('renders seeding_knowledge with spaces', () => {
    render(<StatusBadge status="seeding_knowledge" />)
    expect(screen.getByText('seeding knowledge')).toBeInTheDocument()
  })

  it('applies correct background color for completed', () => {
    const { container } = render(<StatusBadge status="completed" />)
    const span = container.querySelector('span')
    // JSDOM normalizes hex to rgb
    expect(span?.style.backgroundColor).toBe('rgb(22, 163, 74)')
  })

  it('applies correct background color for failed', () => {
    const { container } = render(<StatusBadge status="failed" />)
    const span = container.querySelector('span')
    expect(span?.style.backgroundColor).toBe('rgb(220, 38, 38)')
  })

  it('applies correct background color for running', () => {
    const { container } = render(<StatusBadge status="running" />)
    const span = container.querySelector('span')
    expect(span?.style.backgroundColor).toBe('rgb(59, 130, 246)')
  })

  it('applies default gray for unknown status', () => {
    const { container } = render(<StatusBadge status="made_up_status" />)
    const span = container.querySelector('span')
    expect(span?.style.backgroundColor).toBe('rgb(107, 114, 128)')
  })

  it('renders as inline-block span', () => {
    const { container } = render(<StatusBadge status="completed" />)
    const span = container.querySelector('span')
    expect(span?.style.display).toBe('inline-block')
  })
})
