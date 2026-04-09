export const queryKeys = {
  sessions: {
    all: ['sessions'] as const,
    detail: (id: string) => ['sessions', id] as const,
  },
  leads: {
    all: ['leads'] as const,
    bySession: (sessionId: string) => ['leads', 'session', sessionId] as const,
    detail: (id: string) => ['leads', id] as const,
  },
  approvals: {
    pending: ['approvals', 'pending'] as const,
    draft: (id: string) => ['approvals', 'draft', id] as const,
  },
}
