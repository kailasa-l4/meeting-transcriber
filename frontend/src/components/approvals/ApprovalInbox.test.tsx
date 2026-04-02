import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApprovalInbox } from './ApprovalInbox'
import type { EmailDraft } from '~/utils/types'

// Mock @tanstack/react-router Link to avoid router context requirement
vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, params, style, ...rest }: any) => (
    <a href={`${to}`.replace('$draftId', params?.draftId ?? '')} style={style} {...rest}>
      {children}
    </a>
  ),
}))

const mockDrafts: EmailDraft[] = [
  {
    id: 'draft-a',
    lead_id: 'lead-1',
    country_job_id: 'job-1',
    version_number: 1,
    subject: 'Partnership Opportunity with Bank Alpha',
    body: 'Draft body A',
    status: 'pending_review',
    template_used: 'formal_bank_outreach',
    generated_at: '2026-03-30T10:00:00Z',
  },
  {
    id: 'draft-b',
    lead_id: 'lead-2',
    country_job_id: 'job-1',
    version_number: 2,
    subject: 'Gold Reserve Framework Discussion',
    body: 'Draft body B',
    status: 'pending_review',
    template_used: 'central_bank_formal',
    generated_at: '2026-03-30T11:00:00Z',
  },
  {
    id: 'draft-c',
    lead_id: 'lead-3',
    country_job_id: 'job-2',
    version_number: 1,
    subject: 'Trade Finance Collaboration',
    body: 'Draft body C',
    status: 'draft_regenerated',
    generated_at: '2026-03-30T12:00:00Z',
  },
]

const leadLookup: Record<string, { name: string; company_name?: string; country: string; confidence_score: number }> = {
  'lead-1': { name: 'Kwame Asante', company_name: 'GCB Bank Limited', country: 'Ghana', confidence_score: 0.92 },
  'lead-2': { name: 'Abena Mensah', company_name: 'Bank of Ghana', country: 'Ghana', confidence_score: 0.75 },
  'lead-3': { name: 'David Kasozi', company_name: 'Stanbic Bank Uganda', country: 'Uganda', confidence_score: 0.60 },
}

describe('ApprovalInbox', () => {
  it('renders all drafts in the table', () => {
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} />)

    expect(screen.getByText('Kwame Asante')).toBeInTheDocument()
    expect(screen.getByText('Abena Mensah')).toBeInTheDocument()
    expect(screen.getByText('David Kasozi')).toBeInTheDocument()
  })

  it('sorts drafts by confidence score descending', () => {
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} />)

    const rows = screen.getAllByRole('row')
    // First data row (after header) should be the highest confidence (92%)
    const firstDataRow = rows[1]
    expect(firstDataRow).toHaveTextContent('Kwame Asante')

    // Second should be 75%
    const secondDataRow = rows[2]
    expect(secondDataRow).toHaveTextContent('Abena Mensah')

    // Third should be 60%
    const thirdDataRow = rows[3]
    expect(thirdDataRow).toHaveTextContent('David Kasozi')
  })

  it('shows company names in the table', () => {
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} />)

    expect(screen.getByText('GCB Bank Limited')).toBeInTheDocument()
    expect(screen.getByText('Bank of Ghana')).toBeInTheDocument()
    expect(screen.getByText('Stanbic Bank Uganda')).toBeInTheDocument()
  })

  it('displays confidence scores', () => {
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} />)

    expect(screen.getByText('92%')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText('60%')).toBeInTheDocument()
  })

  it('shows quick-approve button only for high confidence leads (>= 0.85)', () => {
    const onApprove = vi.fn()
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} onApprove={onApprove} />)

    // Only one Approve button should exist (for lead-1 at 92%)
    const approveButtons = screen.getAllByRole('button', { name: /approve/i })
    expect(approveButtons).toHaveLength(1)
  })

  it('calls onApprove when quick-approve button is clicked', async () => {
    const user = userEvent.setup()
    const onApprove = vi.fn()
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} onApprove={onApprove} />)

    const approveBtn = screen.getByRole('button', { name: /approve/i })
    await user.click(approveBtn)

    expect(onApprove).toHaveBeenCalledWith('draft-a')
  })

  it('renders review links for all drafts', () => {
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} />)

    const reviewLinks = screen.getAllByText('Review')
    expect(reviewLinks).toHaveLength(3)
  })

  it('shows version badges', () => {
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} />)

    expect(screen.getByText('v2')).toBeInTheDocument()
    // Two drafts with v1
    const v1Badges = screen.getAllByText('v1')
    expect(v1Badges).toHaveLength(2)
  })

  it('shows template badges', () => {
    render(<ApprovalInbox drafts={mockDrafts} leadLookup={leadLookup} />)

    expect(screen.getByText('formal bank outreach')).toBeInTheDocument()
    expect(screen.getByText('central bank formal')).toBeInTheDocument()
  })

  it('returns null when no drafts are provided', () => {
    const { container } = render(<ApprovalInbox drafts={[]} leadLookup={leadLookup} />)
    expect(container.innerHTML).toBe('')
  })
})
