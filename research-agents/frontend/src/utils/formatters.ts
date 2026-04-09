import type { CountryJobStatus } from './types'

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

export function formatConfidence(score: number): string {
  return `${(score * 100).toFixed(0)}%`
}

export function confidenceTier(score: number): 'high' | 'medium' | 'low' {
  if (score >= 0.8) return 'high'
  if (score >= 0.5) return 'medium'
  return 'low'
}

export const confidenceColors: Record<string, string> = {
  high: '#16a34a',
  medium: '#d97706',
  low: '#dc2626',
}

export const statusColors: Record<CountryJobStatus, string> = {
  queued: '#6b7280',
  seeding_knowledge: '#8b5cf6',
  running: '#3b82f6',
  waiting_for_approval: '#f59e0b',
  partially_completed: '#d97706',
  completed: '#16a34a',
  failed: '#dc2626',
  cancelled: '#9ca3af',
}
