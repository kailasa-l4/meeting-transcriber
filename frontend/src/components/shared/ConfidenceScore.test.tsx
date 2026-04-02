import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConfidenceScore } from './ConfidenceScore'

describe('ConfidenceScore', () => {
  it('renders score as percentage', () => {
    render(<ConfidenceScore score={0.85} />)
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('renders 0 score as 0%', () => {
    render(<ConfidenceScore score={0} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('renders 1.0 score as 100%', () => {
    render(<ConfidenceScore score={1} />)
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('shows green for high confidence', () => {
    const { container } = render(<ConfidenceScore score={0.9} />)
    const span = container.querySelector('span')
    // JSDOM normalizes hex to rgb
    expect(span?.style.color).toBe('rgb(22, 163, 74)')
  })

  it('shows amber for medium confidence', () => {
    const { container } = render(<ConfidenceScore score={0.6} />)
    const span = container.querySelector('span')
    expect(span?.style.color).toBe('rgb(217, 119, 6)')
  })

  it('shows red for low confidence', () => {
    const { container } = render(<ConfidenceScore score={0.3} />)
    const span = container.querySelector('span')
    expect(span?.style.color).toBe('rgb(220, 38, 38)')
  })

  it('shows green at 0.8 boundary', () => {
    const { container } = render(<ConfidenceScore score={0.8} />)
    const span = container.querySelector('span')
    expect(span?.style.color).toBe('rgb(22, 163, 74)')
  })

  it('shows amber at 0.5 boundary', () => {
    const { container } = render(<ConfidenceScore score={0.5} />)
    const span = container.querySelector('span')
    expect(span?.style.color).toBe('rgb(217, 119, 6)')
  })

  it('shows red for zero', () => {
    const { container } = render(<ConfidenceScore score={0} />)
    const span = container.querySelector('span')
    expect(span?.style.color).toBe('rgb(220, 38, 38)')
  })

  it('renders with bold font weight', () => {
    const { container } = render(<ConfidenceScore score={0.85} />)
    const span = container.querySelector('span')
    expect(span?.style.fontWeight).toBe('700')
  })
})
