import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConfidenceBreakdown } from './ConfidenceBreakdown'

describe('ConfidenceBreakdown', () => {
  it('renders all four dimensions', () => {
    render(
      <ConfidenceBreakdown
        breakdown={{ entity: 0.9, contact: 0.8, source_quality: 0.6, dedup: 1.0 }}
      />,
    )
    expect(screen.getByText(/entity/i)).toBeInTheDocument()
    expect(screen.getByText(/contact/i)).toBeInTheDocument()
    expect(screen.getByText(/source/i)).toBeInTheDocument()
    expect(screen.getByText(/dedup/i)).toBeInTheDocument()
  })

  it('shows correct percentages', () => {
    render(
      <ConfidenceBreakdown
        breakdown={{ entity: 0.85, contact: 0.7, source_quality: 0.6, dedup: 1.0 }}
      />,
    )
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('70%')).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('applies correct colors by tier', () => {
    const { container } = render(
      <ConfidenceBreakdown
        breakdown={{ entity: 0.9, contact: 0.4, source_quality: 0.6, dedup: 1.0 }}
      />,
    )
    // High confidence (>= 0.8) should use green (#16a34a)
    const percentLabels = container.querySelectorAll('span')
    const entityPct = Array.from(percentLabels).find((el) => el.textContent === '90%')
    expect(entityPct).toBeDefined()
    expect(entityPct?.style.color).toBe('rgb(22, 163, 74)')

    // Low confidence (< 0.5) should use red (#dc2626)
    const contactPct = Array.from(percentLabels).find((el) => el.textContent === '40%')
    expect(contactPct).toBeDefined()
    expect(contactPct?.style.color).toBe('rgb(220, 38, 38)')
  })

  it('renders bar widths matching percentage', () => {
    const { container } = render(
      <ConfidenceBreakdown breakdown={{ entity: 0.75 }} />,
    )
    // The inner bar div should have width: 75%
    const bars = container.querySelectorAll('div')
    const barWithWidth = Array.from(bars).find((el) => el.style.width === '75%')
    expect(barWithWidth).toBeDefined()
  })
})
