// Status enums matching PRD section 35
export type CountryJobStatus =
  | 'queued' | 'seeding_knowledge' | 'running'
  | 'waiting_for_approval' | 'partially_completed'
  | 'completed' | 'failed' | 'cancelled'

export type LeadVerificationStatus =
  | 'discovered' | 'normalized' | 'verified'
  | 'needs_review' | 'rejected'

export type OutreachStatus =
  | 'not_started' | 'draft_generated' | 'pending_review'
  | 'changes_requested' | 'draft_regenerating' | 'draft_regenerated'
  | 'approved' | 'sending' | 'sent' | 'rejected' | 'send_failed'

export type VerificationDimension = 'entity' | 'contact' | 'source_quality' | 'dedup'

export type ReviewActionType = 'approve' | 'request_changes' | 'reject'

export type StructuredFeedbackCategory =
  | 'tone_adjustment' | 'missing_information' | 'factual_error'
  | 'length_issue' | 'wrong_template' | 'personalization_needed' | 'other'

// Core entities
export interface CountryJob {
  id: string
  country: string
  status: CountryJobStatus
  created_by?: string
  created_at: string
  updated_at: string
  agno_session_id?: string
  current_stage?: string
  summary_counts?: Record<string, number>
  error_message?: string
  user_context?: CountryContext
  prior_job_ids?: string[]
  total_token_count: number
  estimated_cost: number
}

export interface CountryContext {
  target_types?: string[]
  regions?: string[]
  language_preference?: string
  known_entities?: string[]
  outreach_tone?: 'formal' | 'conversational' | 'partnership'
  template_family?: string
  exclusions?: string[]
  notes?: string
}

export interface CountrySubmissionInput {
  country: string
  target_types?: string[]
  regions?: string[]
  language_preference?: string
  known_entities?: string[]
  outreach_tone?: 'formal' | 'conversational' | 'partnership'
  template_family?: string
  exclusions?: string[]
  notes?: string
  force_fresh_run?: boolean
}

export interface Lead {
  id: string
  country_job_id: string
  name: string
  role_title?: string
  whatsapp?: string
  phone?: string
  details?: string
  email?: string
  company_name?: string
  website?: string
  source_text?: string
  source_urls: string[]
  source_count: number
  verification_status: LeadVerificationStatus
  confidence_score: number
  confidence_breakdown: Record<VerificationDimension, number>
  discovery_skill_used?: string
  created_at: string
  updated_at: string
}

export interface LeadSource {
  id: string
  lead_id: string
  source_url?: string
  source_title?: string
  source_type?: string
  excerpt?: string
  collected_at?: string
}

export interface EmailDraft {
  id: string
  lead_id: string
  country_job_id: string
  version_number: number
  subject: string
  body: string
  status: OutreachStatus
  model_name?: string
  template_used?: string
  generated_at: string
}

export interface DraftReviewAction {
  id: string
  email_draft_id: string
  reviewer_id: string
  action: ReviewActionType
  structured_feedback_categories: StructuredFeedbackCategory[]
  comments?: string
  created_at: string
}

export interface DraftDetail {
  draft: EmailDraft
  lead_name: string
  company_name?: string
  country: string
  confidence_score: number
  all_versions: EmailDraft[]
  review_history: DraftReviewAction[]
}

export interface DraftReviewRequest {
  action: ReviewActionType
  structured_feedback_categories: StructuredFeedbackCategory[]
  comments?: string
  guidance?: string
}
