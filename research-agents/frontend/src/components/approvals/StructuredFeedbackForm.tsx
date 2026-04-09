import { useState } from 'react'
import type { DraftReviewRequest, StructuredFeedbackCategory } from '~/utils/types'

const FEEDBACK_CATEGORIES: { value: StructuredFeedbackCategory; label: string }[] = [
  { value: 'tone_adjustment', label: 'Tone adjustment (too formal / too casual / wrong register)' },
  { value: 'missing_information', label: 'Missing information (specify what)' },
  { value: 'factual_error', label: 'Factual error (specify what)' },
  { value: 'length_issue', label: 'Too long / too short' },
  { value: 'wrong_template', label: 'Wrong template / approach' },
  { value: 'personalization_needed', label: 'Personalization needed' },
  { value: 'other', label: 'Other' },
]

interface StructuredFeedbackFormProps {
  onSubmit: (feedback: DraftReviewRequest) => void
  onCancel: () => void
}

export function StructuredFeedbackForm({ onSubmit, onCancel }: StructuredFeedbackFormProps) {
  const [selectedCategories, setSelectedCategories] = useState<StructuredFeedbackCategory[]>([])
  const [comments, setComments] = useState('')
  const [guidance, setGuidance] = useState('')

  const isValid = selectedCategories.length > 0 && comments.trim().length > 0

  function handleCategoryToggle(category: StructuredFeedbackCategory) {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    )
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isValid) return
    onSubmit({
      action: 'request_changes',
      structured_feedback_categories: selectedCategories,
      comments: comments.trim(),
      guidance: guidance.trim() || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} style={{
      padding: 20,
      border: '1px solid #fbbf24',
      borderRadius: 8,
      backgroundColor: '#fffbeb',
    }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#92400e' }}>
        Request Changes
      </h3>

      {/* Feedback Categories */}
      <fieldset style={{ border: 'none', padding: 0, margin: '0 0 20px 0' }}>
        <legend style={{
          fontSize: 14,
          fontWeight: 600,
          color: '#374151',
          marginBottom: 10,
        }}>
          Feedback Categories (select at least one)
        </legend>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {FEEDBACK_CATEGORIES.map((cat) => (
            <label
              key={cat.value}
              htmlFor={`category-${cat.value}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 14,
                color: '#374151',
                cursor: 'pointer',
              }}
            >
              <input
                type="checkbox"
                id={`category-${cat.value}`}
                checked={selectedCategories.includes(cat.value)}
                onChange={() => handleCategoryToggle(cat.value)}
                style={{ width: 16, height: 16, cursor: 'pointer' }}
              />
              {cat.label}
            </label>
          ))}
        </div>
      </fieldset>

      {/* Comments */}
      <div style={{ marginBottom: 16 }}>
        <label
          htmlFor="feedback-comments"
          style={{
            display: 'block',
            fontSize: 14,
            fontWeight: 600,
            color: '#374151',
            marginBottom: 6,
          }}
        >
          Comments (required)
        </label>
        <textarea
          id="feedback-comments"
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          placeholder="Additional instructions for the AI to regenerate this draft..."
          rows={4}
          style={{
            width: '100%',
            padding: 10,
            border: '1px solid #d1d5db',
            borderRadius: 6,
            fontSize: 14,
            fontFamily: 'inherit',
            resize: 'vertical',
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Guidance */}
      <div style={{ marginBottom: 20 }}>
        <label
          htmlFor="feedback-guidance"
          style={{
            display: 'block',
            fontSize: 14,
            fontWeight: 600,
            color: '#374151',
            marginBottom: 6,
          }}
        >
          Guidance (optional)
        </label>
        <textarea
          id="feedback-guidance"
          value={guidance}
          onChange={(e) => setGuidance(e.target.value)}
          placeholder="Specific phrases to include or exclude, tone guidance, etc."
          rows={3}
          style={{
            width: '100%',
            padding: 10,
            border: '1px solid #d1d5db',
            borderRadius: 6,
            fontSize: 14,
            fontFamily: 'inherit',
            resize: 'vertical',
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <button
          type="button"
          onClick={onCancel}
          style={{
            padding: '8px 16px',
            border: '1px solid #d1d5db',
            borderRadius: 6,
            backgroundColor: 'white',
            fontSize: 14,
            cursor: 'pointer',
            color: '#374151',
          }}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!isValid}
          style={{
            padding: '8px 16px',
            border: 'none',
            borderRadius: 6,
            backgroundColor: isValid ? '#d97706' : '#e5e7eb',
            color: isValid ? 'white' : '#9ca3af',
            fontSize: 14,
            fontWeight: 600,
            cursor: isValid ? 'pointer' : 'not-allowed',
          }}
        >
          Submit Feedback
        </button>
      </div>
    </form>
  )
}
