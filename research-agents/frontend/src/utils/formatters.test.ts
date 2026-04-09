import { describe, it, expect } from 'vitest'
import { formatConfidence, confidenceTier, formatDate } from './formatters'

describe('formatConfidence', () => {
  it('formats 0.85 as 85%', () => expect(formatConfidence(0.85)).toBe('85%'))
  it('formats 0 as 0%', () => expect(formatConfidence(0)).toBe('0%'))
  it('formats 1 as 100%', () => expect(formatConfidence(1)).toBe('100%'))
  it('formats 0.5 as 50%', () => expect(formatConfidence(0.5)).toBe('50%'))
  it('formats 0.123 as 12%', () => expect(formatConfidence(0.123)).toBe('12%'))
  it('formats 0.999 as 100%', () => expect(formatConfidence(0.999)).toBe('100%'))
  it('formats 0.001 as 0%', () => expect(formatConfidence(0.001)).toBe('0%'))
})

describe('confidenceTier', () => {
  it('returns high for >= 0.8', () => expect(confidenceTier(0.8)).toBe('high'))
  it('returns medium for 0.5-0.79', () => expect(confidenceTier(0.5)).toBe('medium'))
  it('returns low for < 0.5', () => expect(confidenceTier(0.3)).toBe('low'))
  it('returns high for 1.0', () => expect(confidenceTier(1.0)).toBe('high'))
  it('returns low for 0.0', () => expect(confidenceTier(0.0)).toBe('low'))
  it('returns high for 0.9', () => expect(confidenceTier(0.9)).toBe('high'))
  it('returns medium for 0.79', () => expect(confidenceTier(0.79)).toBe('medium'))
  it('returns medium for 0.5 exactly', () => expect(confidenceTier(0.5)).toBe('medium'))
  it('returns low for 0.49', () => expect(confidenceTier(0.49)).toBe('low'))
})

describe('formatDate', () => {
  it('formats an ISO date string', () => {
    const result = formatDate('2024-01-15T10:30:00Z')
    expect(result).toBeTruthy()
    expect(typeof result).toBe('string')
  })

  it('returns a non-empty string for valid date', () => {
    const result = formatDate('2026-03-28T09:15:00Z')
    expect(result.length).toBeGreaterThan(0)
  })

  it('handles different ISO date formats', () => {
    const result = formatDate('2026-12-31T23:59:59Z')
    expect(result).toBeTruthy()
    expect(typeof result).toBe('string')
  })
})
