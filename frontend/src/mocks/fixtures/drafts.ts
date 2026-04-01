import type { EmailDraft, DraftReviewAction } from '~/utils/types'

export const mockDrafts: EmailDraft[] = [
  {
    id: 'draft-001',
    lead_id: 'lead-001',
    country_job_id: 'job-gh-001',
    version_number: 2,
    subject: 'Partnership Opportunity: UAN Gold Reserve Programme - GCB Bank',
    body: `Dear Mr. Asante,

I am writing on behalf of the Universal Asset Network (UAN) regarding our Gold Reserve Programme, which facilitates sovereign and institutional gold transactions across the African continent.

Given GCB Bank's established role in Ghana's precious metals trading landscape, we believe there is a strong alignment between our programmes and GCB's strategic objectives in commodity-backed financial products.

We would welcome the opportunity to discuss how UAN's gold reserve framework can complement GCB Bank's treasury operations, particularly in the areas of:
- Certified gold custody and settlement services
- Inter-bank gold transfer protocols
- Reserve asset diversification strategies

Would you be available for a 30-minute introductory call next week?

Best regards,
UAN Partnerships Team`,
    status: 'sent',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'formal_bank_outreach',
    generated_at: '2026-03-28T13:00:00Z',
  },
  {
    id: 'draft-002',
    lead_id: 'lead-002',
    country_job_id: 'job-gh-001',
    version_number: 1,
    subject: 'UAN Gold Reserve Framework - Bank of Ghana Collaboration',
    body: `Dear Director Mensah,

The Universal Asset Network (UAN) respectfully seeks to engage with the Bank of Ghana's Treasury Operations division regarding our intergovernmental gold reserve framework.

As an intergovernmental body focused on gold-backed asset development, UAN works with central banks across Africa to establish standardized gold custody, valuation, and transfer protocols.

We understand the Bank of Ghana has been actively expanding its gold reserve position, and we believe our framework could support these efforts through:
- Standardized gold assay and certification protocols
- Cross-border reserve settlement mechanisms
- Technical assistance for gold reserve management

We would be honoured to arrange a formal briefing at your convenience.

With highest regards,
UAN Institutional Relations`,
    status: 'sent',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'central_bank_formal',
    generated_at: '2026-03-28T12:45:00Z',
  },
  {
    id: 'draft-003',
    lead_id: 'lead-007',
    country_job_id: 'job-ug-003',
    version_number: 1,
    subject: 'UAN Gold Programme - Bank of Uganda Engagement',
    body: `Dear Director Nalubega,

On behalf of the Universal Asset Network (UAN), I am reaching out to explore potential collaboration with the Bank of Uganda's Financial Markets division.

UAN's intergovernmental gold reserve framework is designed to support African central banks in building and managing gold reserves through internationally recognized protocols.

Key areas for collaboration include:
- Gold reserve accounting and reporting standards
- Regional gold settlement infrastructure
- Capacity building for precious metals management

Would you be available for an introductory discussion?

Respectfully,
UAN Partnerships`,
    status: 'pending_review',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'central_bank_formal',
    generated_at: '2026-03-30T15:00:00Z',
  },
  {
    id: 'draft-004',
    lead_id: 'lead-008',
    country_job_id: 'job-ug-003',
    version_number: 2,
    subject: 'Gold Trade Finance Partnership - Stanbic Uganda & UAN',
    body: `Dear Mr. Kasozi,

Following our initial outreach, I wanted to share an updated proposal for how UAN's gold reserve programme can enhance Stanbic Bank Uganda's trade finance capabilities.

With Stanbic's strong presence in Uganda's trade finance sector, we see significant opportunity to integrate gold-backed instruments into your existing product suite. Specifically:
- Gold-collateralized trade finance facilities
- Standardized gold documentation for cross-border trade
- Integration with UAN's pan-African gold settlement network

I would welcome the chance to discuss these opportunities in greater detail.

Best regards,
UAN Trade Finance Division`,
    status: 'pending_review',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'commercial_bank_partnership',
    generated_at: '2026-03-30T15:30:00Z',
  },
  {
    id: 'draft-004-v1',
    lead_id: 'lead-008',
    country_job_id: 'job-ug-003',
    version_number: 1,
    subject: 'Gold Trade Finance - Stanbic Uganda',
    body: `Dear Mr. Kasozi,

UAN would like to discuss gold trade finance opportunities with Stanbic Bank Uganda.

Best regards,
UAN`,
    status: 'changes_requested',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'commercial_bank_partnership',
    generated_at: '2026-03-30T14:00:00Z',
  },
  {
    id: 'draft-005',
    lead_id: 'lead-012',
    country_job_id: 'job-ug-003',
    version_number: 1,
    subject: 'DFCU Bank & UAN: Gold-Backed Financial Products',
    body: `Dear Ms. Namutebi,

I am writing from the Universal Asset Network (UAN) to explore how our gold reserve framework might benefit DFCU Bank's commercial strategy in Uganda.

As DFCU continues to expand its corporate banking services, gold-backed financial products represent an emerging opportunity. UAN can support this through:
- Gold custody and safekeeping services
- Gold-linked savings and investment products
- Training and certification for gold assessment

We believe a partnership would be mutually beneficial and would welcome an initial conversation.

Warm regards,
UAN Partnerships`,
    status: 'pending_review',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'commercial_bank_partnership',
    generated_at: '2026-03-30T15:45:00Z',
  },
  {
    id: 'draft-006',
    lead_id: 'lead-010',
    country_job_id: 'job-gh-001',
    version_number: 1,
    subject: 'Ecobank Ghana & UAN Gold Reserve Collaboration',
    body: `Dear Mr. Boateng,

The Universal Asset Network is reaching out to Ecobank Ghana's Precious Metals division regarding potential collaboration under our Gold Reserve Programme.

Given Ecobank's pan-African footprint and established precious metals capabilities, we see particular value in:
- Multi-country gold reserve coordination
- Ecobank's potential role as a regional gold settlement partner
- Joint development of gold-backed financial instruments

We would appreciate the opportunity to discuss this further.

Best regards,
UAN Regional Partnerships`,
    status: 'approved',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'formal_bank_outreach',
    generated_at: '2026-03-28T13:15:00Z',
  },
  {
    id: 'draft-007',
    lead_id: 'lead-014',
    country_job_id: 'job-gh-001',
    version_number: 1,
    subject: 'UAN Gold Supply Chain Partnership - Ashanti Gold Corporation',
    body: `Dear Mr. Ofori,

On behalf of UAN, I am reaching out regarding a potential supply chain partnership with Ashanti Gold Corporation.

As one of Ghana's premier gold producers, Ashanti Gold is well-positioned to participate in UAN's certified gold supply network. Benefits include:
- Access to UAN's international buyer network
- Certified gold provenance documentation
- Preferential settlement terms through UAN member banks

I look forward to discussing this opportunity.

Best regards,
UAN Supply Chain Division`,
    status: 'sent',
    model_name: 'claude-sonnet-4-20250514',
    template_used: 'mining_company_outreach',
    generated_at: '2026-03-28T13:30:00Z',
  },
]

export const mockReviewActions: DraftReviewAction[] = [
  {
    id: 'review-001',
    email_draft_id: 'draft-004-v1',
    reviewer_id: 'operator@uan.org',
    action: 'request_changes',
    structured_feedback_categories: ['length_issue', 'personalization_needed'],
    comments: 'Too brief. Needs to mention specific Stanbic trade finance capabilities and how UAN complements them.',
    created_at: '2026-03-30T14:30:00Z',
  },
  {
    id: 'review-002',
    email_draft_id: 'draft-006',
    reviewer_id: 'operator@uan.org',
    action: 'approve',
    structured_feedback_categories: [],
    comments: 'Good coverage of pan-African angle. Ready to send.',
    created_at: '2026-03-28T13:45:00Z',
  },
  {
    id: 'review-003',
    email_draft_id: 'draft-001',
    reviewer_id: 'operator@uan.org',
    action: 'approve',
    structured_feedback_categories: [],
    created_at: '2026-03-28T13:20:00Z',
  },
]
