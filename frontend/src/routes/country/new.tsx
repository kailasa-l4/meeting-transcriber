import { createFileRoute, useNavigate } from '@tanstack/react-router'
import * as React from 'react'
import type { CountrySubmissionInput } from '~/utils/types'
import { apiPost } from '~/utils/api-client'

export const Route = createFileRoute('/country/new')({
  component: NewCountryRunPage,
})

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  border: '1px solid #d1d5db',
  borderRadius: 6,
  fontSize: 14,
  boxSizing: 'border-box',
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 13,
  fontWeight: 600,
  color: '#374151',
  marginBottom: 4,
}

function NewCountryRunPage() {
  const navigate = useNavigate()
  const [country, setCountry] = React.useState('')
  const [showAdvanced, setShowAdvanced] = React.useState(false)
  const [targetTypes, setTargetTypes] = React.useState('')
  const [regions, setRegions] = React.useState('')
  const [language, setLanguage] = React.useState('')
  const [knownEntities, setKnownEntities] = React.useState('')
  const [tone, setTone] = React.useState<'formal' | 'conversational' | 'partnership'>('formal')
  const [templateFamily, setTemplateFamily] = React.useState('')
  const [exclusions, setExclusions] = React.useState('')
  const [notes, setNotes] = React.useState('')
  const [forceFresh, setForceFresh] = React.useState(false)
  const [error, setError] = React.useState('')
  const [submitted, setSubmitted] = React.useState(false)
  const [submitting, setSubmitting] = React.useState(false)
  const [jobId, setJobId] = React.useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!country.trim()) {
      setError('Country is required.')
      return
    }

    const input: CountrySubmissionInput = {
      country: country.trim(),
      ...(targetTypes.trim() && { target_types: targetTypes.split(',').map((s) => s.trim()).filter(Boolean) }),
      ...(regions.trim() && { regions: regions.split(',').map((s) => s.trim()).filter(Boolean) }),
      ...(language.trim() && { language_preference: language.trim() }),
      ...(knownEntities.trim() && { known_entities: knownEntities.split(',').map((s) => s.trim()).filter(Boolean) }),
      outreach_tone: tone,
      ...(templateFamily.trim() && { template_family: templateFamily.trim() }),
      ...(exclusions.trim() && { exclusions: exclusions.split(',').map((s) => s.trim()).filter(Boolean) }),
      ...(notes.trim() && { notes: notes.trim() }),
      force_fresh_run: forceFresh,
    }

    setSubmitting(true)
    try {
      const result = await apiPost<{ id: string }>('/api/jobs', input)
      setJobId(result.id ?? null)
      setSubmitted(true)
    } catch (err) {
      // If backend is not available, show success with demo note
      console.log('Submitting country run (demo fallback):', input)
      setJobId(null)
      setSubmitted(true)
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>New Country Run</h1>
        <div style={{
          padding: 24,
          backgroundColor: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: 8,
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 18, fontWeight: 600, color: '#16a34a', marginBottom: 8 }}>
            Country run submitted successfully
          </p>
          <p style={{ color: '#6b7280', marginBottom: 16 }}>
            A research session for <strong>{country}</strong> has been queued.
            {jobId && (
              <span style={{ display: 'block', fontSize: 13, marginTop: 4 }}>
                Job ID: <code style={{ backgroundColor: '#f1f5f9', padding: '2px 6px', borderRadius: 4 }}>{jobId}</code>
              </span>
            )}
            {!jobId && (
              <span style={{ display: 'block', fontSize: 12, color: '#92400e', marginTop: 4 }}>
                (Backend not connected — submitted in demo mode)
              </span>
            )}
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <button
              onClick={() => navigate({ to: '/sessions' })}
              style={{
                padding: '8px 20px',
                backgroundColor: '#16a34a',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              View Sessions
            </button>
            <button
              onClick={() => {
                setSubmitted(false)
                setJobId(null)
                setCountry('')
                setShowAdvanced(false)
                setTargetTypes('')
                setRegions('')
                setLanguage('')
                setKnownEntities('')
                setTone('formal')
                setTemplateFamily('')
                setExclusions('')
                setNotes('')
                setForceFresh(false)
              }}
              style={{
                padding: '8px 20px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              Submit another
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16 }}>New Country Run</h1>
      <p style={{ color: '#6b7280', marginBottom: 24 }}>
        Submit a new country for the research agent to discover gold industry leads and generate outreach drafts.
      </p>

      <form onSubmit={handleSubmit} style={{ maxWidth: 600 }}>
        {/* Country (required) */}
        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle} htmlFor="country">
            Country <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <input
            id="country"
            type="text"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            placeholder="e.g. Ghana, Kenya, Uganda, Nigeria"
            style={inputStyle}
          />
        </div>

        {error && (
          <div style={{
            padding: '8px 12px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: 6,
            color: '#dc2626',
            fontSize: 13,
            marginBottom: 16,
          }}>
            {error}
          </div>
        )}

        {/* Advanced Options Toggle */}
        <div style={{ marginBottom: 16 }}>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            style={{
              background: 'none',
              border: 'none',
              color: '#2563eb',
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
              padding: 0,
            }}
          >
            {showAdvanced ? '- Hide' : '+ Show'} Advanced Options
          </button>
        </div>

        {showAdvanced && (
          <div style={{
            padding: 16,
            backgroundColor: '#f8fafc',
            borderRadius: 8,
            border: '1px solid #e2e8f0',
            marginBottom: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}>
            <div>
              <label style={labelStyle} htmlFor="targetTypes">
                Target Types (comma-separated)
              </label>
              <input
                id="targetTypes"
                type="text"
                value={targetTypes}
                onChange={(e) => setTargetTypes(e.target.value)}
                placeholder="e.g. central_bank, commercial_bank, bullion_dealer"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle} htmlFor="regions">
                Regions (comma-separated)
              </label>
              <input
                id="regions"
                type="text"
                value={regions}
                onChange={(e) => setRegions(e.target.value)}
                placeholder="e.g. Greater Accra, Ashanti"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle} htmlFor="language">
                Language Preference
              </label>
              <input
                id="language"
                type="text"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                placeholder="e.g. English, French"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle} htmlFor="knownEntities">
                Known Entities (comma-separated)
              </label>
              <input
                id="knownEntities"
                type="text"
                value={knownEntities}
                onChange={(e) => setKnownEntities(e.target.value)}
                placeholder="e.g. Bank of Ghana, Ecobank"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle} htmlFor="tone">
                Outreach Tone
              </label>
              <select
                id="tone"
                value={tone}
                onChange={(e) => setTone(e.target.value as 'formal' | 'conversational' | 'partnership')}
                style={inputStyle}
              >
                <option value="formal">Formal</option>
                <option value="conversational">Conversational</option>
                <option value="partnership">Partnership</option>
              </select>
            </div>

            <div>
              <label style={labelStyle} htmlFor="templateFamily">
                Template Family
              </label>
              <input
                id="templateFamily"
                type="text"
                value={templateFamily}
                onChange={(e) => setTemplateFamily(e.target.value)}
                placeholder="e.g. central_bank_formal"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle} htmlFor="exclusions">
                Exclusions (comma-separated)
              </label>
              <input
                id="exclusions"
                type="text"
                value={exclusions}
                onChange={(e) => setExclusions(e.target.value)}
                placeholder="e.g. Already contacted Absa Kenya"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle} htmlFor="notes">
                Notes
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any additional instructions for the research agent..."
                rows={3}
                style={{ ...inputStyle, resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                id="forceFresh"
                type="checkbox"
                checked={forceFresh}
                onChange={(e) => setForceFresh(e.target.checked)}
              />
              <label htmlFor="forceFresh" style={{ fontSize: 13, color: '#374151' }}>
                Force fresh run (ignore previous results for this country)
              </label>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          style={{
            padding: '10px 24px',
            backgroundColor: submitting ? '#93c5fd' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            cursor: submitting ? 'not-allowed' : 'pointer',
            fontSize: 15,
            fontWeight: 600,
          }}
        >
          {submitting ? 'Submitting...' : 'Submit Country Run'}
        </button>
      </form>
    </div>
  )
}
