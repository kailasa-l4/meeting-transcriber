import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StructuredFeedbackForm } from './StructuredFeedbackForm'

describe('StructuredFeedbackForm', () => {
  it('renders all 7 feedback categories', () => {
    render(<StructuredFeedbackForm onSubmit={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByLabelText(/tone adjustment/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/missing information/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/factual error/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/too long/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/wrong template/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/personalization/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/other/i)).toBeInTheDocument()
  })

  it('submit button is disabled until category selected and comments filled', () => {
    render(<StructuredFeedbackForm onSubmit={vi.fn()} onCancel={vi.fn()} />)
    const submitBtn = screen.getByRole('button', { name: /submit/i })
    expect(submitBtn).toBeDisabled()
  })

  it('enables submit after selecting category and typing comments', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<StructuredFeedbackForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    await user.click(screen.getByLabelText(/tone adjustment/i))
    await user.type(screen.getByPlaceholderText(/additional/i), 'Make it more formal')

    const submitBtn = screen.getByRole('button', { name: /submit/i })
    expect(submitBtn).not.toBeDisabled()
  })

  it('calls onSubmit with correct data when form is submitted', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<StructuredFeedbackForm onSubmit={onSubmit} onCancel={vi.fn()} />)

    await user.click(screen.getByLabelText(/tone adjustment/i))
    await user.click(screen.getByLabelText(/missing information/i))
    await user.type(screen.getByPlaceholderText(/additional/i), 'Needs more detail')
    await user.type(screen.getByPlaceholderText(/specific phrases/i), 'Include UAN mandate')

    await user.click(screen.getByRole('button', { name: /submit/i }))

    expect(onSubmit).toHaveBeenCalledWith({
      action: 'request_changes',
      structured_feedback_categories: ['tone_adjustment', 'missing_information'],
      comments: 'Needs more detail',
      guidance: 'Include UAN mandate',
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    const onCancel = vi.fn()
    render(<StructuredFeedbackForm onSubmit={vi.fn()} onCancel={onCancel} />)

    await user.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onCancel).toHaveBeenCalled()
  })

  it('keeps submit disabled when only category is selected (no comments)', async () => {
    const user = userEvent.setup()
    render(<StructuredFeedbackForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    await user.click(screen.getByLabelText(/factual error/i))

    const submitBtn = screen.getByRole('button', { name: /submit/i })
    expect(submitBtn).toBeDisabled()
  })

  it('keeps submit disabled when only comments are filled (no category)', async () => {
    const user = userEvent.setup()
    render(<StructuredFeedbackForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    await user.type(screen.getByPlaceholderText(/additional/i), 'Some feedback')

    const submitBtn = screen.getByRole('button', { name: /submit/i })
    expect(submitBtn).toBeDisabled()
  })

  it('allows toggling categories on and off', async () => {
    const user = userEvent.setup()
    render(<StructuredFeedbackForm onSubmit={vi.fn()} onCancel={vi.fn()} />)

    const checkbox = screen.getByLabelText(/tone adjustment/i)
    await user.click(checkbox)
    expect(checkbox).toBeChecked()

    await user.click(checkbox)
    expect(checkbox).not.toBeChecked()
  })
})
