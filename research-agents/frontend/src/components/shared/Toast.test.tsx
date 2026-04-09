import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Toast } from './Toast'

describe('Toast', () => {
  it('renders message', () => {
    render(<Toast message="Saved!" type="success" onClose={vi.fn()} />)
    expect(screen.getByText('Saved!')).toBeInTheDocument()
  })

  it('has close button', () => {
    render(<Toast message="Info" type="info" onClose={vi.fn()} />)
    expect(screen.getByText('\u00d7')).toBeInTheDocument()
  })

  it('calls onClose when close clicked', async () => {
    const onClose = vi.fn()
    render(<Toast message="Test" type="error" onClose={onClose} />)
    screen.getByText('\u00d7').click()
    expect(onClose).toHaveBeenCalled()
  })
})
