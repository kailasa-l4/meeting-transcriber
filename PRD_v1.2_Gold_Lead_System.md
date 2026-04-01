# Product Requirements Document (PRD)

## Product Name

Gold Lead Research, Verification, and Outreach System

## Document Version

v1.2

## Document Status

Draft for review

## Owner

Product / Operations

## Prepared For

Internal build of an Agno-based async multi-agent system for gold lead discovery, verification, and human-approved outreach

## Changelog from v1.0

| Change | Section(s) | Rationale |
|--------|-----------|-----------|
| Gmail and Sheets integration via `gws` CLI | §23, §18, §14.5 | Replaces custom API integration with Google's official CLI tooling |
| Skills-based architecture for repetitive agent tasks | §14 (new §14.6), §13.3 | Codifies reusable agent behaviors as composable, testable skills |
| Extended country input with optional context fields | §13.1, §7.1, §20.1 | Enables richer, more targeted research from first submission |
| Knowledge base for research seeding | §14 (new §14.7) | Gives agents domain priors and avoids cold-start inefficiency |
| Confidence-scored lead ranking | §13.3 Stage 5, §19.2 Lead entity | Enables prioritized review and smarter draft ordering |
| Rate limiting and politeness controls | §15 (new §15.5) | Prevents IP bans, respects source TOS during discovery |
| Incremental country re-runs | §13 (new §13.4) | Avoids duplicate work when re-running same country |
| Draft template library | §14.4, §8.1 | Enables outreach tone/format variation without full regeneration |
| Structured feedback taxonomy for revisions | §17.3, §16.2.7 | Reduces ambiguity in reviewer-to-agent feedback loop |
| Observability and cost tracking | §21.7 | Tracks token spend per run for model economics visibility |
| **TanStack Start + Bun frontend architecture** | §11, §16, §34 | Type-safe full-stack React with SSR, server functions, file-based routing on Bun runtime |
| **Agno + uv Python backend architecture** | §11, §12, §34 | Agno AgentOS as FastAPI backend with uv for fast, reproducible Python dependency management |
| **Development skills and documentation references** | §14.6, §38 | Frontend design skill for UI, Context7 for live documentation lookup during development |
| **Comprehensive testing strategy** | §21A (new), §20.17–20.18, §29 | Vitest + Playwright + pytest + Agno Evals + Claude in Chrome for full-stack test coverage |

---

# 1. Executive Summary

This product is an internal operations system that takes a **country** as input — along with optional research context — and runs an **async, multi-stage agentic workflow** to:

1. Research gold-related leads in that country
2. Extract and normalize lead information
3. Verify the findings
4. Save only the factual lead findings to a Google Sheet
5. Draft outreach emails for verified leads
6. Present those drafts to a human reviewer inside a UI
7. Send emails only after explicit user approval
8. Allow revision loops when the reviewer requests changes

The system will use:

* **Agno** for agent, team, workflow, session, and approval orchestration — served via **AgentOS** (FastAPI) as the backend runtime, managed with **`uv`** for Python dependency and environment management
* **TanStack Start** as the full-stack React frontend framework, running on **Bun** runtime — providing SSR, type-safe file-based routing, server functions, and middleware
* **OpenRouter** as the model gateway
* **Kimi K2.5 or GLM-5** as the initial model options
* **`gws` CLI** (Google Workspace CLI) for Gmail sending and Google Sheets writes, leveraging its built-in agent skills
* **Composable agent skills** for all repetitive tasks (discovery patterns, verification checks, sheet writes, email sends, normalization)
* **Postgres** as the application database (shared between Agno sessions and app operational data)
* **A dedicated application database** as the operational source of truth

Development tooling:

* **Frontend design skill** for producing distinctive, production-grade UI components
* **Context7** for referencing up-to-date documentation for TanStack Start, Agno, and other libraries during development

This version of the PRD explicitly excludes ClickUp updates. ClickUp integration may be added in a later phase.

---

# 2. Problem Statement

The user needs a scalable system that can research gold sellers and intermediaries across countries without manually repeating the same workflow.

The current manual process is inefficient because it requires:

* Manually searching websites, directories, associations, and company pages
* Extracting contact details by hand
* Separately validating whether the lead is real or useful
* Manually drafting outreach emails
* Manually tracking what has been researched and what has been contacted

The user wants an agentic system that can do the operational work asynchronously while still preserving human control over email sending.

The main challenge is to combine autonomous research, structured lead extraction, verification, human approval, and operational visibility without turning Google Sheets into the workflow engine.

---

# 3. Product Vision

Build an internal lead-generation operations platform for the gold trade domain that:

* starts from a single country input with optional research context,
* runs async research and verification workflows using composable skills,
* produces structured lead data,
* shows every workflow session in a UI,
* and routes draft outreach through a strict human approval loop before sending.

The system should feel like an internal control tower for country-based lead discovery.

---

# 4. Goals

## 4.1 Primary Goals

1. Allow a user to submit a country — plus optional context — and start a full lead research workflow.
2. Run discovery, verification, and draft generation asynchronously using reusable agent skills.
3. Persist all workflow runs as Agno sessions for visibility and debugging.
4. Save only factual lead findings to Google Sheets via `gws` CLI.
5. Provide a UI where users can view all sessions, inspect leads, review draft emails, approve or request edits, and send only after approval.
6. Support iterative review of draft emails until the user is satisfied.

## 4.2 Secondary Goals

1. Make the system restartable and idempotent.
2. Support multiple country runs in parallel.
3. Allow future integration with ClickUp and other internal systems.
4. Make model/provider changes easy without redesigning the workflow.
5. Build a skills library that grows with usage and can be extended per-country or per-domain.

---

# 5. Non-Goals

The following are not part of v1:

1. ClickUp updates
2. Full CRM capabilities
3. Automated sending without human approval
4. Payment workflows
5. Contract generation
6. Advanced compliance adjudication or sanctions-grade screening
7. Multi-channel outreach beyond email
8. Public-facing external productization
9. End-customer self-service UI
10. Bulk campaign analytics beyond basic send status

---

# 6. Users and Personas

## 6.1 Primary User

Internal operator / researcher / deal team member

Needs: start country runs, provide research context, review leads, inspect sources, review email drafts, approve or request revisions.

## 6.2 Secondary User

Operations lead / admin

Needs: view all sessions, monitor stuck or failed workflows, audit approvals, track what has and has not been sent.

## 6.3 Future User

Compliance / reviewer role

Needs: inspect source evidence, reject risky or low-quality outreach, review approval history.

---

# 7. User Stories

## 7.1 Country Run Initiation

* As an operator, I want to enter a country and optionally provide additional context (target company types, specific regions, language preference, known contacts or companies to look for, outreach tone) so that the system begins research tailored to my requirements without additional manual prompting.

## 7.2 Session Visibility

* As an operator, I want to see all workflow sessions so that I can track active, completed, failed, and waiting-for-approval runs.

## 7.3 Lead Review

* As an operator, I want to view the extracted leads for a session so that I can understand what the system found.

## 7.4 Source Traceability

* As an operator, I want each lead to retain source evidence so that I can verify how the information was found.

## 7.5 Human Approval

* As an operator, I want every draft email to wait for my approval before sending so that I remain in control of outreach.

## 7.6 Revision Loop

* As an operator, I want to provide structured feedback on a draft and have the system regenerate it for review so that I can refine outreach quality.

## 7.7 Final Send

* As an operator, I want the approved draft to send from the system only after approval so that no unreviewed email goes out.

## 7.8 Clean Sheet Output

* As an operator, I want the Google Sheet to contain only lead findings and not operational noise so that the sheet remains usable and clean.

## 7.9 Re-Run with Deduplication (NEW)

* As an operator, I want to re-run a country and only discover net-new leads so that I don't waste time reviewing duplicates of previously found contacts.

## 7.10 Prioritized Review (NEW)

* As an operator, I want leads ranked by confidence score so that I review the most promising ones first.

---

# 8. Scope

## 8.1 In Scope

### Workflow

* Country-based workflow initiation with optional context fields
* Async lead discovery using composable skills
* Async verification using composable skills
* Email draft generation with template library support
* Human approval and revision loop with structured feedback
* Final email sending after approval via `gws` CLI

### UI

* Session list
* Session detail view
* Lead list with confidence-score sorting
* Lead detail view
* Pending draft approval inbox
* Draft review and revision UI with structured feedback options
* Send confirmation state

### Data

* Lead storage
* Source storage
* Draft storage with template metadata
* Approval state storage
* Send log storage
* Session/run metadata integration
* Cost/token tracking per session

### Integrations

* Agno
* OpenRouter
* Google Sheets (via `gws` CLI and `gws-sheets` / `gws-sheets-append` skills)
* Gmail (via `gws` CLI and `gws-gmail` skills)

### Skills

* Discovery skills per lead type (miners, brokers, exporters, directories)
* Verification skills (entity, contact, source quality, dedup)
* Normalization skill
* Sheet-write skill (wrapping `gws sheets`)
* Email-send skill (wrapping `gws gmail +send`)
* Draft generation skill with template support
* Country knowledge-seeding skill

## 8.2 Out of Scope

* ClickUp
* Full compliance platform
* Auto-negotiation / reply agents
* WhatsApp sending
* Phone calling
* Buyer-side qualification scoring beyond basic heuristics

---

# 9. Product Principles

1. **Human-controlled outreach**: no email is sent without explicit approval.
2. **Clean separation of concerns**: Agno sessions for workflow execution history, app database for operational truth, Google Sheet for clean lead output.
3. **Async by default**: long-running research and verification must not block the UI.
4. **Traceable outputs**: every lead should retain sources and provenance.
5. **Structured over free-form**: normalized fields should be used wherever possible.
6. **Restartable workflows**: failed or interrupted runs should be resumable.
7. **Operator-first UI**: clarity and control are more important than visual polish in v1.
8. **Skills-first design** (NEW): every repetitive agent behavior should be encoded as a composable, testable skill rather than inline prompt logic.
9. **Incremental value** (NEW): re-running a country should build on prior work, not restart from zero.

---

# 10. Solution Overview

The product will be built as an **Agno-based workflow system** exposed through a custom application.

A user enters a **country** and optionally provides **additional research context** (target types, regions, language, known entities, outreach tone).

The system creates a workflow session and launches an async workflow that:

1. seeds research context from a domain knowledge base and user-provided context,
2. expands the research scope for that country,
3. fans out discovery work across multiple researchers using discovery skills,
4. consolidates and normalizes candidate leads using the normalization skill,
5. verifies the candidates using verification skills,
6. scores and ranks leads by confidence,
7. writes factual lead findings to Google Sheets via `gws` CLI,
8. drafts outreach emails for verified leads using the drafting skill and template library,
9. pauses for human approval,
10. revises drafts if required using structured reviewer feedback,
11. and sends only after final approval via `gws` CLI.

The UI serves as the human control plane.

---

# 11. High-Level Architecture

## 11.1 Technology Stack

### Frontend: TanStack Start on Bun

The operator UI is built with **TanStack Start** — a full-stack React framework — running on the **Bun** runtime.

**Why TanStack Start:**

* Type-safe file-based routing (routes map directly to filesystem structure)
* Built-in server functions (`createServerFn`) for secure backend calls without a separate API client layer — the frontend can call the Agno backend directly from server functions
* SSR by default — pages are server-rendered for fast first paint, important for an operator dashboard
* First-class middleware architecture — request middleware for auth, server function middleware for per-route logic
* Deep integration with TanStack Router (type-safe navigation), TanStack Query (data fetching/caching for real-time session status), and TanStack Table (lead lists, session lists)
* Streams and long-running requests supported natively (useful for live workflow status updates)

**Why Bun:**

* Significantly faster startup and install times than Node.js — relevant for dev iteration speed
* Native TypeScript execution without a separate compile step
* Built-in test runner and bundler
* Drop-in Node.js compatibility for ecosystem libraries
* Production server via `bun run server.ts` with asset preloading and caching

**Frontend project structure (illustrative):**

```
frontend/
├── src/
│   ├── routes/
│   │   ├── __root.tsx              # Root layout with auth, nav
│   │   ├── index.tsx               # Dashboard / session list
│   │   ├── sessions/
│   │   │   ├── index.tsx           # Sessions list view
│   │   │   └── $sessionId.tsx      # Session detail view
│   │   ├── leads/
│   │   │   ├── index.tsx           # Leads list (cross-session)
│   │   │   └── $leadId.tsx         # Lead detail view
│   │   ├── approvals/
│   │   │   ├── index.tsx           # Pending approvals inbox
│   │   │   └── $draftId.tsx        # Draft review screen
│   │   └── country/
│   │       └── new.tsx             # Country submission form
│   ├── components/                 # Shared UI components
│   ├── server/                     # Server functions (call Agno backend)
│   ├── utils/                      # Helpers, types, API client
│   └── start.ts                    # Global middleware config
├── bunfig.toml                     # Bun configuration
├── app.config.ts                   # TanStack Start config
└── package.json
```

**Key patterns:**

Server functions bridge frontend to Agno backend:

```typescript
// src/server/sessions.ts
import { createServerFn } from '@tanstack/react-start'

export const getSessions = createServerFn({ method: 'GET' }).handler(async () => {
  // Calls Agno AgentOS API from server side — secrets never reach client
  const res = await fetch(`${process.env.AGNO_API_URL}/sessions`, {
    headers: { Authorization: `Bearer ${process.env.AGNO_API_KEY}` }
  })
  return res.json()
})

export const submitCountry = createServerFn({ method: 'POST' })
  .inputValidator((d: { country: string; context?: Record<string, any> }) => d)
  .handler(async ({ data }) => {
    const res = await fetch(`${process.env.AGNO_API_URL}/workflows/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${process.env.AGNO_API_KEY}` },
      body: JSON.stringify(data)
    })
    return res.json()
  })
```

Auth middleware:

```typescript
// src/start.ts
import { createStart, createMiddleware } from '@tanstack/react-start'

const authMiddleware = createMiddleware().server(async ({ next, request }) => {
  const session = await validateSession(request.headers)
  if (!session) throw new Error('Unauthorized')
  return await next({ context: { session } })
})

export const startInstance = createStart(() => ({
  requestMiddleware: [authMiddleware],
}))
```

**Development reference:** Use the **frontend-design skill** for all UI component creation to ensure distinctive, production-grade interfaces. Use **Context7** (`/websites/tanstack_start`) for up-to-date TanStack Start API references, routing patterns, and server function signatures during development.

### Backend: Agno AgentOS on uv (Python)

The backend is built with **Agno's AgentOS** — which exposes a FastAPI application — managed with **`uv`** for Python runtime and dependency management.

**Why Agno AgentOS:**

* AgentOS wraps Agno workflows, teams, and agents into a production FastAPI server with one call (`agent_os.serve()`)
* Built-in REST API endpoints for sessions, runs, agents, and workflows
* Native HITL (human-in-the-loop) with `requires_confirmation=True` — workflows pause and resume via `confirm()` / `reject()` on run output
* Async execution with `arun()` / `acontinue_run()` for non-blocking workflow steps
* Built-in CORS, authorization (RBAC), and tracing support
* PostgresDb integration for session, memory, and knowledge persistence
* Structured outputs via Pydantic `output_schema` on agents

**Why `uv`:**

* 10–100x faster than pip for dependency resolution and installation
* Built-in virtual environment management (`uv venv`, `uv sync`)
* Lockfile support (`uv.lock`) for reproducible builds across dev, CI, and production
* Drop-in replacement for pip/pip-tools — no workflow change needed
* Written in Rust — extremely fast cold starts, relevant for CI/CD and container builds

**Backend project structure (illustrative):**

```
backend/
├── pyproject.toml                  # uv-managed dependencies, project metadata
├── uv.lock                         # Reproducible lockfile
├── src/
│   ├── main.py                     # AgentOS entry point
│   ├── config.py                   # Settings, secrets, model routing
│   ├── workflows/
│   │   ├── country_workflow.py     # Main country research workflow (Agno Workflow)
│   │   └── steps/                  # Individual workflow steps
│   ├── agents/
│   │   ├── discovery/              # Discovery team agents
│   │   ├── verification/           # Verification team agents
│   │   └── outreach/               # Outreach agent
│   ├── teams/
│   │   ├── discovery_team.py       # Agno Team: discovery members
│   │   └── verification_team.py    # Agno Team: verification members
│   ├── skills/                     # Composable skill definitions
│   │   ├── discovery/
│   │   ├── verification/
│   │   ├── gws/                    # gws CLI wrapper skills
│   │   └── normalization/
│   ├── tools/                      # Agno @tool definitions wrapping skills
│   ├── models/                     # Pydantic schemas (lead, draft, etc.)
│   ├── db/                         # Database models, queries
│   ├── knowledge/                  # Country knowledge base loaders
│   └── api/                        # Custom FastAPI routes (beyond AgentOS defaults)
└── tests/
```

**Key patterns:**

AgentOS setup with workflows and teams:

```python
# src/main.py
from agno.os import AgentOS
from agno.db.postgres import PostgresDb
from src.workflows.country_workflow import country_workflow
from src.teams.discovery_team import discovery_team
from src.teams.verification_team import verification_team
from src.agents.outreach.outreach_agent import outreach_agent

db = PostgresDb(db_url="postgresql+psycopg://user:pass@localhost:5432/goldleads")

agent_os = AgentOS(
    name="Gold Lead Research System",
    workflows=[country_workflow],
    teams=[discovery_team, verification_team],
    agents=[outreach_agent],
    db=db,
    tracing=True,
    authorization=True,
    cors_allowed_origins=["http://localhost:3000"],  # TanStack Start dev server
    auto_provision_dbs=True,
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="src.main:app", host="0.0.0.0", port=8000, reload=True)
```

HITL approval pattern:

```python
# Workflow step with confirmation gate
from agno.workflow import Workflow
from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput

def send_email(step_input: StepInput) -> StepOutput:
    # Uses gws gmail +send skill — only reached after confirmation
    return StepOutput(content="Email sent")

# In workflow definition:
Steps(
    name="send_approved_email",
    steps=[Step(name="send", executor=send_email)],
    requires_confirmation=True,
    confirmation_message="Approve sending this email?",
)
```

Agent with OpenRouter and structured output:

```python
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from src.models.lead import NormalizedLead

discovery_agent = Agent(
    name="Miner Finder",
    model=OpenRouter(id="moonshotai/kimi-k2.5"),
    tools=[web_search_tool, discovery_miners_skill],
    output_schema=NormalizedLead,
    instructions="Search for gold mining companies and operators. Return structured lead data.",
    db=db,
)
```

**Development commands:**

```bash
# Setup
uv venv
uv sync                    # Install from lockfile
uv run src/main.py         # Start AgentOS dev server

# Dependency management
uv add agno openrouter     # Add packages
uv lock                    # Update lockfile
uv run pytest              # Run tests
```

**Development reference:** Use **Context7** (`/websites/agno`) for up-to-date Agno API references — workflow definitions, team setup, HITL patterns, AgentOS configuration, and tool creation during development.

### Database: Postgres (Shared)

A single **Postgres** instance serves both Agno's internal storage (sessions, memory, knowledge, traces) and the application's operational tables (leads, drafts, approvals, send logs).

Agno connects via `PostgresDb(db_url=...)`. The application's custom tables (§19) live in the same database but under a separate schema or with clear table prefixes.

### Communication: Frontend ↔ Backend

The TanStack Start frontend communicates with the Agno AgentOS backend via **HTTP/JSON**:

* TanStack Start server functions (`createServerFn`) run on the Bun server and make HTTP requests to the AgentOS FastAPI API
* All secrets (API keys, DB credentials, `gws` CLI tokens) live on the server side only — never in client bundles
* TanStack Query handles client-side caching, polling (for live session status), and optimistic updates
* For real-time status updates, the frontend polls AgentOS session endpoints via TanStack Query's `refetchInterval` — WebSocket upgrade is a future optimization

## 11.2 Layers

### A. Orchestration Layer

Built with **Agno** (AgentOS + Workflows + Teams).

Responsibilities: workflow definitions, team coordination, agent execution, session persistence, workflow state, async task execution (`arun`), pause/resume for HITL approvals (`requires_confirmation`).

### B. Skills Layer

A library of composable, versioned skill definitions (Python modules within the backend).

Responsibilities: encapsulating repetitive agent behaviors (discovery patterns, verification checks, normalization logic, `gws` CLI interactions) as reusable units that agents invoke rather than re-derive from scratch each run.

### C. Frontend Layer

Built with **TanStack Start** on **Bun**.

Responsibilities: operator UI, session monitoring, lead review, draft approval, revision feedback capture, country submission forms. Server functions proxy requests to the backend securely.

### D. Backend API Layer

Built with **Agno AgentOS** (FastAPI) on **`uv`**-managed Python.

Responsibilities: REST API for sessions, leads, drafts, approvals; workflow triggering; HITL resume endpoints; custom business logic routes beyond AgentOS defaults.

### E. Data Layer

**Postgres** — shared between Agno internals and application tables.

Responsibilities: operational source of truth for leads, drafts, approvals, sends, and feedback; session metadata; Agno session/memory/knowledge storage; search and filtering for the UI.

### F. Integration Layer

**`gws` CLI** — Google Sheets writes via `gws sheets`, Gmail sends via `gws gmail +send`.

Responsibilities: all Google Workspace interactions, future ClickUp integration.

### G. Knowledge Layer

**Agno Knowledge** (PgVector-backed) + structured config in app database.

Responsibilities: storing domain priors per country (known directories, mining registries, common company structures, regulatory bodies, language/locale hints) so agents don't start cold.

## 11.3 Deployment Topology (v1)

```
┌─────────────────────────────┐
│  Operator Browser           │
└──────────┬──────────────────┘
           │ HTTPS
┌──────────▼──────────────────┐
│  TanStack Start (Bun)       │   Port 3000
│  SSR + Server Functions     │
│  Auth Middleware             │
└──────────┬──────────────────┘
           │ HTTP/JSON (internal)
┌──────────▼──────────────────┐
│  Agno AgentOS (FastAPI/uv)  │   Port 8000
│  Workflows, Teams, Agents   │
│  HITL, Tracing, RBAC        │
│  Custom API routes          │
└──────────┬──────────────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼───┐  ┌───▼────────────┐
│Postgres│  │ gws CLI        │
│        │  │ (Gmail/Sheets) │
└────────┘  └────────────────┘
```

## 11.4 Development Toolchain

| Concern | Tool | Purpose |
|---------|------|---------|
| Frontend runtime | **Bun** | TypeScript execution, bundling, test runner, package management |
| Frontend framework | **TanStack Start** | SSR, routing, server functions, middleware |
| Frontend UI quality | **Frontend design skill** | Distinctive, production-grade components |
| Frontend unit/integration tests | **Vitest** | Component tests, server function handler tests, with Bun runner |
| Frontend E2E tests | **Playwright** | Cross-browser end-to-end flow testing (Chromium, Firefox, WebKit) |
| Frontend visual/UX validation | **Claude in Chrome** | Browser-based design coherence, layout, responsiveness, accessibility checks |
| Backend runtime | **Python (via `uv`)** | Fast dependency management, reproducible environments |
| Backend framework | **Agno AgentOS** (FastAPI) | Agent orchestration, workflow API, HITL |
| Backend unit/integration tests | **pytest** | Skill logic, API routes, DB queries, workflow step functions |
| Agent quality evals | **Agno Evals** | AccuracyEval, ReliabilityEval for agent and team quality |
| Documentation lookup | **Context7** | Live docs for TanStack Start, Agno, Playwright, gws CLI during dev |
| Database | **Postgres** | Shared operational + Agno storage |
| Google Workspace | **`gws` CLI** | Gmail, Sheets — structured JSON output for agent consumption |
| Model gateway | **OpenRouter** | Model-agnostic LLM access |

---

# 12. Agno Architecture Decision

## 12.1 Why Agno

Agno is selected because it supports: agent teams, workflows with step-level HITL (`requires_confirmation`), workflow sessions persisted to Postgres, async execution via `arun()` / `acontinue_run()`, structured outputs via Pydantic schemas, AgentOS as a production FastAPI server, built-in tracing and authorization, and OpenRouter as a model provider.

## 12.2 How Agno Should Be Used

Agno should be used as the orchestration engine, not as the only data store.

### Agno should own:

* workflow definitions (Agno `Workflow` with `Step`, `Steps`, `Loop`, `Condition`)
* team definitions (Agno `Team` with member agents)
* agent behavior and skill invocation (Agno `Agent` with `@tool` functions wrapping skills)
* session state (persisted to Postgres via `PostgresDb`)
* run history and tracing
* pause/resume control for approval-gated actions (`requires_confirmation` + `confirm()` / `reject()`)

### Agno should not be the only store for:

* lead records
* email draft lifecycle
* reviewer feedback
* operational reporting
* skill definitions and versioning

Those should live in the application database tables (same Postgres instance, separate schema/tables).

## 12.3 AgentOS as the Backend Runtime

AgentOS is the production entry point. It:

* exposes all Agno workflows, teams, and agents via auto-generated REST endpoints
* supports custom FastAPI routes via `base_app` for application-specific API needs (lead CRUD, approval actions, etc.)
* handles CORS for the TanStack Start frontend
* supports RBAC via `authorization=True` and `AuthorizationConfig`
* runs via `agent_os.serve()` — backed by Uvicorn in production

The TanStack Start frontend never talks to Agno internals directly — it calls AgentOS REST endpoints from server functions.

## 12.4 Development Workflow Integration

During development:

* **Context7** should be used to query Agno docs (`/websites/agno`) for current API patterns — workflow step definitions, HITL confirmation handling, team setup, AgentOS configuration, tool creation
* **Context7** should be used for TanStack Start docs (`/websites/tanstack_start`) for routing, server functions, middleware, Bun deployment patterns
* The **frontend-design skill** should be used for all UI component creation — session lists, lead tables, approval inbox, draft review screens — to maintain distinctive, operator-first design quality

---

# 13. Workflow Design

## 13.1 Workflow Input

The required user input is:

* `country` (required)

Optional inputs available at submission time:

* `target_types` — which lead categories to prioritize (e.g., miners, brokers, exporters, refiners)
* `regions` — specific regions, cities, or provinces within the country
* `language_preference` — preferred language for outreach drafts
* `known_entities` — specific companies or contacts to look for or use as starting points
* `outreach_tone` — formal, conversational, or partnership-oriented
* `template_family` — which outreach template set to use
* `exclusions` — companies or domains to skip
* `notes` — free-text operator instructions for the research agents

These optional fields are passed into the workflow context and available to all agents and skills throughout the run.

## 13.2 Workflow Output

The workflow produces:

1. persisted session history
2. structured lead records with confidence scores
3. verified vs rejected lead outcomes
4. draft outreach emails for eligible leads
5. approval status for each draft
6. send status after final action

## 13.3 Workflow Stages

### Stage 1: Intake

Input received: country + optional context fields.

System actions: create job record, create workflow session, initialize workflow state with user context, check for prior runs of same country (for incremental mode), mark session as queued/running.

### Stage 2: Knowledge Seeding (NEW)

The system loads domain knowledge for the target country from the knowledge base. This includes known directories, regulatory bodies, mining association URLs, locale-specific search strategies, and any learnings from prior runs.

User-provided context (known entities, target types, regions) is merged into the research plan.

### Stage 3: Discovery Planning

The orchestrator derives the research lanes for the country, informed by seeded knowledge and user context.

Examples of lanes: miners, artisanal / small-scale miners where discoverable, brokers / agents, exporters / traders, associations / chambers / mining directories, company websites and contact pages, refiners (if specified in target types).

If `target_types` were provided by the user, those lanes are prioritized. If `regions` were provided, discovery is scoped accordingly.

### Stage 4: Async Discovery Fan-Out

Discovery workers run in parallel. Each worker invokes the appropriate **discovery skill** for its lead type and source class.

Skills handle: search strategy, source parsing, candidate extraction, and rate-limit-aware request pacing.

Each worker returns candidate leads in a standardized intermediate format.

### Stage 5: Lead Normalization

All candidate leads are normalized into a single internal schema using the **normalization skill**.

The normalization skill handles: field mapping, data cleaning, format standardization (phone numbers, emails, URLs), and initial deduplication against both the current batch and prior runs.

### Stage 6: Verification Fan-Out

Verification workers validate each candidate using **verification skills**:

* **Entity verification skill**: entity plausibility checks
* **Contact verification skill**: contact format and ownership plausibility
* **Source quality skill**: source consistency and evidence strength
* **Deduplication skill**: duplicate detection against current session and historical leads

Each verification skill produces a sub-score. These are combined into an overall **confidence score** for the lead.

### Stage 7: Lead Persistence

Verified or acceptable leads are saved to:

* application database (with confidence score and full provenance)
* Google Sheet via `gws` CLI (facts only, using the `gws-sheets-append` skill)

Rejected or insufficient leads are kept in the app database for audit but not written to the sheet.

Leads are ranked by confidence score for prioritized review.

### Stage 8: Draft Generation

For each lead eligible for outreach, the outreach agent invokes the **draft generation skill**.

The skill selects or accepts a template from the template library based on: lead type, outreach tone (from user input or default), and country/language.

Drafts are saved in the app database and linked to: lead, session, country run, model metadata, draft version, template used.

### Stage 9: Approval Wait State

The send step is blocked. The draft enters a pending approval state visible in the UI. Leads are presented in confidence-score order.

### Stage 10: Human Review

The user can: approve the draft, request changes (with structured feedback), or reject the draft.

### Stage 11: Revision Loop

If changes are requested: reviewer feedback (structured + free-text) is stored, the drafting skill reruns with feedback, a new draft version is generated, the new version returns to pending approval.

### Stage 12: Final Send

If approved: send the email via `gws gmail +send` skill, log send result, update lead/outreach record, update session state.

## 13.4 Incremental Re-Run Behavior (NEW)

When a country is submitted that has been run before:

1. The system loads all previously discovered leads for that country from the app database.
2. Discovery agents receive the prior lead list as "already known" context.
3. The deduplication skill filters out re-discoveries during normalization.
4. Only net-new leads proceed to verification and drafting.
5. The session is linked to prior sessions for auditability.

The user can override this and force a full fresh run if desired.

---

# 14. Team and Agent Design

## 14.1 Orchestrator

Role: owns the workflow lifecycle, coordinates fan-out and fan-in, updates session state, triggers later stages, passes user context to downstream agents.

## 14.2 Discovery Team

Each discovery agent invokes the relevant **discovery skill** for its domain. Skills encapsulate the search strategy, source parsing, and candidate extraction logic so agents focus on coordination rather than re-deriving search patterns.

Suggested members:

### A. Miner Finder Agent

Focus: miners, mining companies, small-scale or alluvial discoverable operators.
Skill used: `discovery-miners` skill.

### B. Broker / Agent Finder Agent

Focus: brokers, agents, intermediaries, trading contacts.
Skill used: `discovery-brokers` skill.

### C. Exporter / Trader Finder Agent

Focus: exporters, trading companies, precious metals dealers.
Skill used: `discovery-exporters` skill.

### D. Directory / Association Agent

Focus: mining directories, chambers, associations, registries, local business databases.
Skill used: `discovery-directories` skill.

### E. Contact Extraction Agent

Focus: email, phone, WhatsApp when publicly discoverable, role / title, website.
Skill used: `contact-extraction` skill.

## 14.3 Verification Team

Each verifier invokes the relevant **verification skill**. Skills produce structured, scoreable outputs.

Suggested members:

### A. Entity Verifier

Checks whether company/person/entity appears real.
Skill used: `verify-entity` skill.

### B. Contact Verifier

Checks whether the contact information plausibly belongs to the entity.
Skill used: `verify-contact` skill.

### C. Source Quality Verifier

Checks whether the evidence is strong enough.
Skill used: `verify-source-quality` skill.

### D. Duplicate Resolver

Consolidates duplicate or near-duplicate entries.
Skill used: `dedup-resolver` skill.

## 14.4 Outreach Agent

Responsibilities: generate tailored draft email using the `draft-generation` skill, select appropriate template from the template library, incorporate reviewer feedback into revisions, maintain version history.

The template library should include at minimum:

* **Introduction / cold outreach** — first contact, establishing interest
* **Partnership inquiry** — exploring mutual business opportunities
* **Information request** — seeking specific data about operations or capacity
* **Follow-up** — for leads where prior contact exists (future phase)

Templates can be parameterized by language and tone.

## 14.5 Deterministic Service Layer (via `gws` CLI and Skills)

These are not "creative agents" and should be deterministic tools/services implemented as thin skill wrappers around `gws` CLI and database operations:

* **Sheet writer skill**: wraps `gws sheets spreadsheets.values append` / `gws sheets +append` to write lead rows
* **Email sender skill**: wraps `gws gmail +send` to send approved drafts
* **Database writer**: direct app DB persistence
* **Approval state updater**: direct app DB state transitions

The `gws` CLI returns structured JSON, making it straightforward for skills to parse responses and handle errors programmatically.

## 14.6 Skills Architecture (NEW)

### What is a Skill

A skill is a self-contained, versioned unit of agent behavior that encapsulates:

* a clear purpose and trigger condition
* input/output schema
* the logic or prompt template for execution
* tool dependencies (e.g., which `gws` commands it uses)
* error handling behavior

### Skill Categories

**Discovery skills**: one per lead type. Each encapsulates search strategy, source types, and extraction patterns for its category. Can be country-customized with knowledge overlays.

**Verification skills**: one per verification dimension. Each produces a structured score and rationale.

**Normalization skill**: handles field mapping, cleaning, format standardization. Single skill, versioned.

**GWS integration skills**: thin wrappers around `gws` CLI commands. Leverage the existing `gws-gmail`, `gws-sheets`, `gws-sheets-append` agent skills from the gws CLI repo where applicable.

**Draft generation skill**: combines template selection, personalization, and tone adjustment.

**Knowledge seeding skill**: loads and merges country-specific domain knowledge for discovery planning.

### Skill Lifecycle

Skills should be: versioned (so changes are auditable), testable in isolation (given mock inputs), extendable per-country (via knowledge overlays), and observable (invocation logged per session).

### Existing GWS Skills to Leverage

The `gws` CLI ships with 100+ agent skills including purpose-built skills for:

* `gws-gmail` — send, read, reply, forward, triage
* `gws-sheets` — read and write spreadsheets
* `gws-sheets-append` — append rows to a sheet
* `gws-sheets-read` — read values from a sheet

These should be used as the foundation for the system's GWS integration skills rather than building custom Google API wrappers.

## 14.7 Domain Knowledge Base (NEW)

A per-country knowledge store that agents consult before and during discovery. Contents may include:

* known mining directories and registries for the country
* regulatory bodies and licensing authorities
* common company naming patterns
* locale-specific search terms and language
* learnings from prior runs (which sources were productive, which were dead ends)
* country-specific compliance or risk notes

This knowledge base grows over time as the system runs more countries. It can be stored as Agno knowledge (vector-backed) or as structured config in the app database.

---

# 15. Async Execution Model

## 15.1 Requirement

All non-human stages should run asynchronously.

## 15.2 Interpretation

Async means: the country run does not block the UI thread, discovery tasks can run concurrently, verification tasks can run concurrently, multiple country workflows can run at the same time.

## 15.3 Human Gate Exception

The approval step is intentionally blocking from a business perspective. The workflow may pause or enter a waiting state until the reviewer acts. This is acceptable and required.

## 15.4 Operational Behavior

The UI should always show whether a run is: queued, seeding knowledge, running discovery, normalizing leads, running verification, writing leads, drafting email, waiting for approval, revising draft, sending email, completed, or failed.

## 15.5 Rate Limiting and Politeness Controls (NEW)

Discovery agents must respect rate limits and politeness constraints when accessing external sources:

* configurable delay between requests to the same domain
* maximum concurrent requests per source domain
* user-agent identification
* respect for robots.txt where applicable
* circuit-breaker behavior: if a source returns repeated errors, back off and mark it degraded rather than retrying aggressively

These controls should be part of the discovery skills so they are applied consistently across all agents.

---

# 16. UI Requirements

## 16.1 UI Goals

The UI is built with **TanStack Start** on **Bun** and should function as the operator workspace. It must allow users to: monitor all runs, inspect all generated leads (sorted by confidence), review email drafts, request changes with structured feedback, and approve and send.

All screens use TanStack Start's file-based routing. Data fetching uses server functions calling the Agno AgentOS API. Live status updates use TanStack Query polling. All UI components should be built using the **frontend-design skill** to ensure distinctive, production-grade interfaces that avoid generic aesthetics.

The UI design should follow an **operator-first / control-tower aesthetic** — clean data density, clear status indicators, confidence-based visual hierarchy, and fast keyboard-navigable workflows for approval batching.

## 16.2 Main Screens

### 16.2.1 Sessions List

Purpose: show all Agno sessions / country runs.

Required fields: session name or session ID, country, user-provided context summary, status, created time, updated time, number of leads found, number of verified leads, average confidence score, number of pending drafts, number of sent emails, error indicator if failed, token/cost estimate.

Actions: open session details, filter by status, search by country or session ID, re-run country (incremental or fresh).

### 16.2.2 Session Detail

Purpose: provide full visibility into a country run.

Sections: summary panel (including user-provided context), workflow timeline, current stage, lead counts by confidence tier, pending approvals, run errors / warnings, linked leads table, cost/token summary.

### 16.2.3 Leads List

Purpose: show all leads for a session.

Columns: Name, Role / Title, WhatsApp, Phone, Details, Email, Company Name, Website, Source, Confidence Score, verification state (app UI only), outreach state (app UI only).

Default sort: by confidence score descending.

Actions: view lead details, view linked sources, open draft email if one exists.

### 16.2.4 Lead Detail

Purpose: inspect a single lead deeply.

Must include: normalized lead fields, confidence score breakdown (entity / contact / source sub-scores), source evidence, extraction notes, verification notes, draft status, draft versions if any.

### 16.2.5 Pending Email Approvals Inbox

Purpose: central place to review unsent drafts.

Required fields: lead name, company name, country, subject line preview, draft version number, template used, confidence score, created at, awaiting review since.

Actions: open draft, approve, request changes, reject.

### 16.2.6 Draft Review Screen

Purpose: review and act on one draft.

Must show: lead summary, source summary, confidence score, template used, email subject, email body, previous versions, reviewer comments history.

Actions: approve and send, request changes (with structured feedback), reject.

### 16.2.7 Revision Screen / Inline Revision Flow

If the reviewer requests changes, the UI must capture:

**Structured feedback** (select one or more):

* Tone adjustment (too formal / too casual / wrong register)
* Missing information (specify what)
* Factual error (specify what)
* Too long / too short
* Wrong template / approach
* Personalization needed
* Other

**Free-text feedback**: additional instructions.

**Optional structured guidance** for future versions: specific phrases to include/exclude, alternative angles.

The system then regenerates a new version using the structured + free-text feedback and shows it again.

---

# 17. Approval Workflow Requirements

## 17.1 Approval Rule

No outreach email may be sent until explicitly approved by a user in the UI.

## 17.2 Approval States

Recommended states: `draft_generated`, `pending_review`, `changes_requested`, `draft_regenerating`, `draft_regenerated`, `approved`, `sending`, `sent`, `rejected`, `send_failed`.

## 17.3 Reviewer Actions

A reviewer can: approve, request changes (with structured feedback categories + free text), or reject.

Structured feedback categories ensure the revision skill receives actionable, parseable guidance rather than only free-text.

## 17.4 Approval Metadata

The system must store: reviewer ID, action taken, timestamp, structured feedback categories selected, free-text comments, draft version.

## 17.5 Revision Requirements

If changes are requested: original draft must be preserved, reviewer comments (structured + free-text) must be stored, a new draft version must be created, previous versions must remain visible.

## 17.6 Send Trigger

Send occurs only after: draft is approved, lead still exists and is eligible, no send lock or duplicate send condition exists.

---

# 18. Google Sheet Requirements

## 18.1 Sheet Purpose

The Google Sheet is a clean lead-facts surface, not the workflow database.

## 18.2 Access Method

Google Sheets are accessed via the **`gws` CLI** using the `gws-sheets-append` and `gws-sheets-read` agent skills.

Example write command:

```bash
gws sheets spreadsheets.values append \
  --params '{"spreadsheetId": "<ID>", "range": "Sheet1!A:I", "valueInputOption": "USER_ENTERED"}' \
  --json '{"values": [["Name", "Role", "WhatsApp", "Phone", "Details", "Email", "Company", "Website", "Source"]]}'
```

The sheet-writer skill wraps this command, handles errors, and logs the result.

## 18.3 Required Columns

The sheet should contain only these business-facing columns: Name, Role / Title, WhatsApp, Phone, Details, Email, Company Name, Website, Source.

## 18.4 Sheet Rules

1. Do not store session execution noise in the sheet.
2. Do not store approval comments in the sheet.
3. Do not store workflow debug logs in the sheet.
4. Do not store internal version history in the sheet.
5. Only store factual lead findings.
6. Before appending, the sheet-writer skill should check for duplicate rows by email/company to avoid re-inserting known leads.

## 18.5 Optional Future Columns

Possible later additions if needed: Country, Date Added, Verification Status, Outreach Status.

These are not required in the user's current preferred sheet schema.

---

# 19. Data Model Requirements

## 19.1 Principle

Use the application database as the operational source of truth.

## 19.2 Core Entities

### A. CountryJob

Represents a submitted country workflow.

Fields: id, country, created_by, created_at, updated_at, status, agno_session_id, agno_run_id, current_stage, summary_counts, error_message, **user_context** (JSON — stores all optional input fields: target_types, regions, language_preference, known_entities, outreach_tone, template_family, exclusions, notes), **prior_job_ids** (array — links to previous runs of same country), **total_token_count**, **estimated_cost**.

### B. WorkflowEvent

Represents important workflow-level events.

Fields: id, country_job_id, timestamp, event_type, stage, payload, **skill_invoked** (which skill was used, if any), **token_count** (tokens used in this event).

### C. Lead

Represents a normalized lead.

Fields: id, country_job_id, name, role_title, whatsapp, phone, details, email, company_name, website, source_text, source_urls, source_count, verification_status, **confidence_score** (0.0–1.0, composite), **confidence_breakdown** (JSON — sub-scores per verification dimension), **discovery_skill_used**, created_at, updated_at.

### D. LeadSource

Represents raw evidence linked to a lead.

Fields: id, lead_id, source_url, source_title, source_type, excerpt, collected_at.

### E. VerificationRecord

Represents verification results.

Fields: id, lead_id, status, confidence_score, **dimension** (entity / contact / source_quality / dedup), verifier_notes, contradictions_found, duplicate_of_lead_id, **skill_used**, created_at.

### F. EmailDraft

Represents one draft version.

Fields: id, lead_id, country_job_id, version_number, subject, body, status, model_name, **template_used**, **skill_used**, generated_at, created_by_system.

### G. DraftReviewAction

Represents user review actions.

Fields: id, email_draft_id, reviewer_id, action, **structured_feedback_categories** (array), comments, created_at.

### H. EmailSendLog

Represents send attempts and outcomes.

Fields: id, email_draft_id, lead_id, **send_method** (`gws_gmail`), provider_message_id, sent_at, send_status, failure_reason.

### I. SkillInvocationLog (NEW)

Represents a single skill invocation for observability.

Fields: id, country_job_id, skill_name, skill_version, agent_name, input_summary, output_summary, token_count, duration_ms, status, error_message, created_at.

### J. CountryKnowledge (NEW)

Represents domain knowledge per country.

Fields: id, country, knowledge_type (directory / registry / search_strategy / locale / learning), content (JSON), source, created_at, updated_at.

---

# 20. Functional Requirements

## 20.1 Country Submission

The system must allow a user to submit a country and optionally provide additional context (target types, regions, language preference, known entities, outreach tone, template family, exclusions, free-text notes) to start a new run.

## 20.2 Session Creation

The system must create and persist an Agno workflow session for each country run, including user-provided context.

## 20.3 Session Listing

The UI must display all sessions with filtering and sorting.

## 20.4 Async Discovery

The system must run discovery workers concurrently, each using the appropriate discovery skill.

## 20.5 Async Verification

The system must run verification workers concurrently, each using the appropriate verification skill and producing confidence sub-scores.

## 20.6 Lead Normalization

The system must normalize all candidate leads into one schema using the normalization skill before persistence.

## 20.7 Google Sheet Write

The system must write the lead findings to Google Sheets via `gws` CLI using only the defined sheet fields.

## 20.8 Draft Generation

The system must generate email drafts for outreach-eligible leads using the drafting skill and template library.

## 20.9 Draft Review UI

The system must show drafts in the UI before sending, ordered by lead confidence score.

## 20.10 Approval

The system must require explicit approval before sending.

## 20.11 Revision Loop

The system must allow structured reviewer feedback to create a regenerated draft version.

## 20.12 Final Send

The system must send only the approved version via `gws gmail +send`.

## 20.13 Audit Trail

The system must retain draft version history, approval actions, skill invocation logs, and send logs.

## 20.14 Error Visibility

The system must expose workflow failures, skill failures, and send failures in the UI.

## 20.15 Incremental Re-Run (NEW)

The system must support re-running a country with automatic deduplication against prior runs.

## 20.16 Skill Observability (NEW)

The system must log every skill invocation with inputs, outputs, token usage, and duration.

## 20.17 Test Coverage (NEW)

The system must maintain test coverage gates: ≥80% line coverage for frontend components, ≥85% for backend skills and models, 100% for Pydantic schemas and state machine transitions. All critical user flows must have Playwright E2E tests. All agents and teams must have Agno eval baselines.

## 20.18 Visual/UX Validation (NEW)

Every UI screen must be validated via Claude in Chrome before milestone delivery to verify design coherence, layout correctness, responsive behavior, interaction quality, and accessibility basics.

---

# 21. Non-Functional Requirements

## 21.1 Reliability

Runs must be restartable. Failures must be logged. Partial progress must not be lost.

## 21.2 Idempotency

Duplicate country submissions should be detectable. Duplicate lead insertions should be handled. Duplicate email sends must be prevented. Sheet writes should check for existing rows.

## 21.3 Performance

Discovery and verification should run concurrently. UI should remain responsive while workflows run. Rate limiting must not cause cascading timeouts.

## 21.4 Traceability

Every lead should retain source provenance. Every email should retain draft and approval history. Every skill invocation should be logged.

## 21.5 Security

Credentials must not be exposed in logs or UI. Provider secrets must be stored securely. `gws` CLI credentials must be encrypted at rest (handled by `gws` CLI's built-in AES-256-GCM encryption). Send actions must require authenticated users. All secrets (OpenRouter API keys, DB credentials, `gws` tokens) live in server-side environment variables — TanStack Start server functions ensure these never reach client bundles. AgentOS `authorization=True` enforces RBAC on backend endpoints.

## 21.6 Maintainability

Models should be swappable via configuration. Provider routing should be configurable. Workflows, teams, and skills should be modular. Skills should be independently versionable.

## 21.7 Observability

Session status must be visible. Workflow stage transitions must be visible. Errors and retries must be auditable. **Token usage and estimated cost per session must be tracked.** Skill invocation history must be queryable.

## 21.8 Testability

All layers of the system must be testable in isolation and in integration. The testing strategy encompasses unit tests, integration tests, end-to-end tests, visual/UX validation, and agent evaluation. Tests must run in CI and locally. No code should be merged without passing tests.

---

# 21A. Testing Strategy

Testing is a first-class requirement, not an afterthought. The system has three distinct testing surfaces — the TanStack Start frontend, the Agno Python backend, and the integrated system as a whole — each with its own toolchain, but all gated in CI.

## 21A.1 Frontend Testing (TanStack Start + Bun)

### Unit Tests — Vitest

**Tool:** Vitest (runs natively on Bun).

**Scope:** Individual components, utility functions, data transformations, and server function logic (handler functions in isolation).

**What to test:**

* **Components in isolation**: every screen-level and shared component — session list rendering, lead table sorting/filtering, approval inbox badge counts, draft review layout, structured feedback form state, country submission form validation
* **Server function handlers**: test the handler logic of `createServerFn` calls in isolation (mock the fetch to AgentOS API) — correct request shaping, error transformation, response parsing
* **Data transformers**: confidence score formatting, status badge mapping, date/time formatting, lead field normalization for display
* **Form validation**: country submission form (required `country`, optional fields schema), structured feedback form (at least one category selected), revision comment requirements
* **State management**: TanStack Query cache key strategies, optimistic update logic for approval actions, polling interval configuration

**Conventions:**

* Co-locate test files: `ComponentName.test.tsx` alongside `ComponentName.tsx`
* Use `@testing-library/react` for component tests with user-event simulation
* Mock AgentOS API responses with MSW (Mock Service Worker) or Vitest mocks
* Target: **≥80% line coverage** for components, **100% coverage** for server function handlers

**Example:**

```typescript
// src/components/ApprovalInbox.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ApprovalInbox } from './ApprovalInbox'

describe('ApprovalInbox', () => {
  it('renders pending drafts sorted by confidence score descending', () => {
    const drafts = [
      { id: '1', leadName: 'Acme Gold', confidence: 0.6 },
      { id: '2', leadName: 'Sahara Mining', confidence: 0.9 },
    ]
    render(<ApprovalInbox drafts={drafts} />)
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('Sahara Mining') // highest first
  })

  it('disables send button when no draft is approved', () => {
    render(<ApprovalInbox drafts={[]} />)
    expect(screen.queryByRole('button', { name: /send/i })).not.toBeInTheDocument()
  })
})
```

**Development reference:** Use **Context7** (`/websites/tanstack_start`) for testing patterns with server functions and TanStack Router test utilities.

### Integration Tests — Vitest + MSW

**Scope:** Full route-level rendering with mocked backend, testing the interaction between server functions, loaders, components, and navigation.

**What to test:**

* **Route loaders**: session list loader fetches and renders correctly, session detail loader handles missing sessions (404), lead list loader applies filters
* **Server function → UI flow**: submit country → loading state → redirect to session detail, approve draft → optimistic UI update → confirmation state
* **Auth middleware behavior**: unauthenticated request → redirect to login, expired session → re-auth prompt
* **Error boundaries**: AgentOS API down → error state rendered, malformed response → graceful degradation

### End-to-End Tests — Playwright

**Tool:** Playwright (cross-browser: Chromium, Firefox, WebKit).

**Scope:** Full user flows from browser to real (or test-stubbed) backend.

**What to test:**

* **Country submission flow**: navigate to `/country/new` → fill form (country + optional context) → submit → verify redirect to session detail → verify session appears in session list
* **Session monitoring flow**: navigate to sessions list → verify status indicators update (mock workflow progression) → click into session detail → verify lead counts, stage timeline
* **Lead review flow**: navigate to leads list → sort by confidence → click lead → verify detail view shows sources, verification breakdown, draft status
* **Approval flow (critical path)**: navigate to approvals inbox → open draft → verify lead summary + email body rendered → approve → verify status changes to "sending" → verify confirmation
* **Revision flow**: open draft → click "request changes" → select structured feedback categories → add free-text comment → submit → verify new version appears → verify version history shows both drafts
* **Rejection flow**: open draft → reject → verify status change → verify draft no longer in inbox
* **Error states**: simulate backend timeout → verify error message rendered, simulate 403 → verify auth redirect

**Configuration:**

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
    { name: 'webkit', use: { browserName: 'webkit' } },
  ],
  webServer: {
    command: 'bun run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
})
```

**Conventions:**

* E2E tests live in `frontend/e2e/` directory
* Use page object models for screen interactions
* Tests must be idempotent — seed test data before each test, clean up after
* Run in CI on every PR against Chromium; full cross-browser suite on merge to main

### Visual and UX Validation — Claude in Chrome

**Tool:** Claude in Chrome (browser agent) via Claude Code integration.

**Scope:** Human-quality visual and UX validation that automated tests cannot catch — layout correctness, design coherence, interaction feel, accessibility, and responsiveness.

**When to run:** After significant UI changes, before each phase milestone (§30), and as part of the design review process.

**What to validate:**

* **Design coherence**: does the UI follow the operator-first / control-tower aesthetic established by the frontend-design skill? Are colors, typography, and spacing consistent across screens?
* **Layout correctness**: do tables render properly with real-length data (long company names, multiple source URLs)? Do cards and panels align? Does the approval inbox scan well?
* **Responsive behavior**: does the session list remain usable at narrower viewports? Do tables scroll horizontally or collapse gracefully?
* **Interaction quality**: are loading states visible during long operations (workflow polling)? Do approval actions provide clear feedback? Is the structured feedback form intuitive?
* **Accessibility basics**: are focus states visible? Can the approval flow be navigated by keyboard? Are status badges distinguishable without color alone?
* **Cross-screen consistency**: navigate the full user journey (submit country → monitor session → review leads → approve draft → confirm send) and verify the experience feels cohesive
* **Edge case rendering**: how does the UI handle zero leads, zero pending drafts, a failed session, an extremely long country name, a lead with missing fields?

**Process:**

1. Developer builds or modifies a UI component/screen using the **frontend-design skill**
2. Claude Code builds the project and launches the local dev server (`bun run dev`)
3. Claude in Chrome opens the running app in a real Chrome browser
4. Claude navigates through the screens, interacts with elements, and visually inspects the output
5. Claude reports issues (layout breaks, visual regressions, UX friction, accessibility problems) back to the development context
6. Developer fixes issues and re-validates

**Integration with development workflow:**

```
Developer prompt to Claude Code:
"I just updated the approval inbox component. Can you open localhost:3000/approvals,
test the full approval flow with the seeded test data, check that the confidence
score badges render correctly, verify the structured feedback form works, and
check that the layout looks good on both desktop and narrower viewports?"
```

Claude in Chrome can also record browser sessions as GIFs for documentation and design review.

**Important constraints:** Claude in Chrome is for development-time validation, not CI. It requires a visible Chrome window and cannot run headless. It supplements but does not replace Playwright E2E tests.

## 21A.2 Backend Testing (Agno + Python)

### Unit Tests — pytest

**Tool:** pytest (run via `uv run pytest`).

**Scope:** Individual functions, Pydantic models, skill logic, database queries, and utility code.

**What to test:**

* **Pydantic models**: schema validation for all data entities — `NormalizedLead`, `EmailDraft`, `VerificationRecord`, `DraftReviewAction`, etc. Test required fields, optional fields, type coercion, invalid input rejection
* **Skill logic in isolation**: each skill's core logic tested with mock inputs — normalization skill (field mapping, phone format standardization, dedup logic), verification skills (score calculation, threshold behavior), draft generation skill (template selection, variable substitution)
* **Database queries**: lead CRUD, draft versioning, approval state transitions, dedup queries, sheet-write dedup check — test against a test Postgres instance
* **`gws` CLI wrapper skills**: mock subprocess calls to `gws`, test JSON response parsing, error handling for common failure modes (auth expired, rate limit, sheet not found)
* **Workflow step functions**: each `StepInput → StepOutput` function tested in isolation with mock dependencies
* **Configuration and routing**: model selection logic, OpenRouter routing, feature flags

**Conventions:**

* Test files in `backend/tests/` mirroring `src/` structure
* Use `pytest-asyncio` for async function tests
* Use `factory_boy` or fixtures for test data generation
* Test database: use a dedicated test Postgres database, reset between test runs
* Target: **≥85% line coverage** for skills, **100% coverage** for Pydantic models and state machine transitions

**Example:**

```python
# tests/skills/test_normalization.py
import pytest
from src.skills.normalization.normalize import normalize_lead
from src.models.lead import RawCandidate, NormalizedLead

def test_normalize_phone_formats():
    raw = RawCandidate(name="John", phone="+233-24-123-4567", company_name="Acme Gold")
    result = normalize_lead(raw)
    assert result.phone == "+233241234567"

def test_normalize_dedup_by_email():
    existing = [NormalizedLead(email="john@acme.com", name="John", company_name="Acme")]
    raw = RawCandidate(name="John Doe", email="john@acme.com", company_name="Acme Gold Ltd")
    result = normalize_lead(raw, existing_leads=existing)
    assert result.is_duplicate is True
    assert result.duplicate_of == existing[0].id

def test_normalize_rejects_missing_required_fields():
    raw = RawCandidate(name="", phone="", company_name="")
    with pytest.raises(ValueError, match="insufficient data"):
        normalize_lead(raw)
```

### Integration Tests — pytest + Test DB

**Scope:** Multi-component interactions — database writes, API route responses, workflow step chains.

**What to test:**

* **API routes**: POST `/workflows/run` with valid/invalid country input, GET `/sessions` with filters, POST `/approvals/{id}/approve`, POST `/approvals/{id}/request-changes` with structured feedback
* **Workflow step chains**: intake → knowledge seeding → discovery planning (mock discovery agents) → normalization → verification → persistence — verify state transitions and data flow
* **HITL flow**: trigger workflow → verify it pauses at confirmation step → call confirm → verify it resumes and completes send step
* **Database integrity**: lead creation → verification records linked → draft created → approval action stored → send log created — verify foreign keys and cascading
* **`gws` CLI integration** (with test doubles): mock `gws sheets` and `gws gmail` subprocess calls at the skill level, verify correct command construction and response handling

### Agent Evaluation — Agno Evals

**Tool:** Agno's built-in evaluation framework (`AccuracyEval`, `ReliabilityEval`).

**Scope:** Agent and team quality — are agents producing correct, structured outputs? Are they using the right tools?

**What to evaluate:**

* **Discovery agent accuracy**: given a known country with known gold mining companies, does the agent find them? Does the structured output match the `NormalizedLead` schema?
* **Verification agent reliability**: given a lead with known issues (fake company, invalid email), does the verifier flag it? Does it call the expected verification tools?
* **Outreach agent accuracy**: given a verified lead and a template, does the generated draft match the expected tone and include required personalization fields?
* **Team coordination reliability**: does the discovery team fan out correctly? Does the verification team consolidate results? Are tool calls made in the expected order?

**Configuration:**

```python
# tests/evals/test_discovery_accuracy.py
from agno.eval.accuracy import AccuracyEval
from src.agents.discovery.miner_finder import miner_finder_agent

evaluation = AccuracyEval(
    name="Miner Finder - Ghana",
    model=OpenRouter(id="moonshotai/kimi-k2.5"),
    agent=miner_finder_agent,
    input="Find gold mining companies in Ghana",
    expected_output="Should include at least one verifiable mining company with contact details",
    additional_guidelines="Output must conform to NormalizedLead schema. Must include company_name, source_url.",
    num_iterations=3,
)

result = evaluation.run(print_results=True)
assert result is not None and result.avg_score >= 7
```

**Conventions:**

* Agent evals are expensive (they call real models) — run on a schedule (nightly) or on-demand, not on every PR
* Use a fixed set of "golden" test cases per country with known-good expected outputs
* Track eval scores over time to detect model quality regressions after provider/model changes
* Store eval results in the database via Agno's eval persistence

## 21A.3 Full-Stack Integration Tests

**Scope:** End-to-end verification that the TanStack Start frontend correctly drives the Agno backend through complete workflows.

**What to test:**

* **Country submission → session creation**: frontend submits, backend creates workflow session, frontend polls and sees it appear
* **Workflow progression → UI updates**: mock backend workflow advances through stages, frontend polling picks up state changes and renders correctly
* **Approval → send**: frontend approves draft, backend receives confirmation, workflow resumes, send log created, frontend reflects final status

**Tool:** Playwright (frontend-driven) against a running test backend (`uv run src/main.py` with test config).

**Environment:** Dedicated test Postgres database, mocked `gws` CLI (subprocess mocks at skill level), real AgentOS but with test-mode OpenRouter calls (or mocked model responses).

## 21A.4 Testing Matrix Summary

| Layer | Tool | Runs In | Frequency | Coverage Target |
|-------|------|---------|-----------|-----------------|
| Frontend unit | Vitest + Bun | CI (every PR) | Every commit | ≥80% lines |
| Frontend integration | Vitest + MSW | CI (every PR) | Every commit | Key routes |
| Frontend E2E | Playwright | CI (every PR, Chromium) | Every PR + full cross-browser on merge | Critical paths |
| Frontend visual/UX | Claude in Chrome | Local dev | After UI changes, before milestones | All screens |
| Backend unit | pytest + uv | CI (every PR) | Every commit | ≥85% lines |
| Backend integration | pytest + test DB | CI (every PR) | Every commit | All API routes |
| Agent evals | Agno Evals | Scheduled | Nightly + on model changes | Golden test set |
| Full-stack | Playwright + test backend | CI (merge to main) | On merge | Critical flows |

## 21A.5 CI Pipeline

```
PR opened / updated:
  ├── Frontend:
  │   ├── bun install
  │   ├── bun run typecheck        (TypeScript strict)
  │   ├── bun run lint              (ESLint)
  │   ├── bun run test              (Vitest unit + integration)
  │   └── bunx playwright test --project=chromium  (E2E, Chromium only)
  │
  ├── Backend:
  │   ├── uv sync
  │   ├── uv run ruff check .       (linting)
  │   ├── uv run mypy src/          (type checking)
  │   └── uv run pytest             (unit + integration)
  │
  └── Gate: all must pass before merge

Merge to main:
  ├── Full cross-browser Playwright suite (Chromium + Firefox + WebKit)
  ├── Full-stack integration tests
  └── Trigger nightly agent eval if model config changed

Nightly:
  └── Agent evals (AccuracyEval, ReliabilityEval) on golden test set
```

## 21A.6 Test Data Management

* **Frontend test fixtures**: JSON fixture files with representative sessions, leads, drafts at various states — used by both Vitest and Playwright
* **Backend test fixtures**: factory functions generating valid `NormalizedLead`, `EmailDraft`, `VerificationRecord` instances with realistic data
* **Seed script**: a shared seed script that populates the test database with a complete "Ghana run" including leads at various verification states, drafts at various approval states, and send logs — used by Playwright E2E and full-stack integration tests
* **Golden eval dataset**: curated set of country + expected leads for agent evals, stored in `backend/tests/evals/golden/`

---

# 22. Model and Provider Strategy

## 22.1 Provider Choice

OpenRouter is the model gateway.

## 22.2 Initial Model Options

* Kimi K2.5
* GLM-5

## 22.3 Recommendation for v1

Use one primary model at first to reduce complexity.

Suggested initial default: Kimi K2.5 for discovery-heavy workloads.

Potential later split: Kimi K2.5 for discovery and extraction, GLM-5 for verification or rewrite passes if testing supports that choice.

## 22.4 Output Discipline

All structured extraction should use strict schema validation where possible. Use structured outputs for: normalized lead extraction, verification result schema, draft metadata schema, skill input/output schemas.

## 22.5 Tool Usage Strategy

Models should decide when to use research, persistence, and send tools, but the actual write/send behavior should be guarded by business rules. `gws` CLI interactions should always go through skills, never raw agent tool calls, to ensure consistent error handling and logging.

---

# 23. Integrations

## 23.1 Google Sheets (via `gws` CLI)

Purpose: factual lead output.

Access method: `gws` CLI with `gws-sheets-append` and `gws-sheets-read` skills.

Requirements: append or upsert lead rows, preserve exact field mapping, avoid operational clutter, check for duplicates before writing.

Authentication: `gws auth login` with OAuth credentials scoped to Sheets API. Credentials encrypted at rest by `gws` CLI.

## 23.2 Gmail (via `gws` CLI)

Purpose: send approved outreach emails.

Access method: `gws` CLI with `gws-gmail` skills (`+send` for sending, `+read` for delivery verification if needed).

Requirements: support subject/body send, return provider message ID from JSON response, allow send result logging.

Authentication: same `gws` OAuth flow, scoped to include Gmail API.

## 23.3 Future ClickUp

Out of scope for v1.

---

# 24. Session and State Management

## 24.1 Session Strategy

Each country run maps to one workflow session. User-provided context is stored as part of the session state.

## 24.2 Session Visibility

The UI must show the workflow sessions as a first-class object.

## 24.3 Session State

Workflow state should track at minimum: country, user context, current stage, lead counts (by confidence tier), pending drafts, approval wait count, send count, failure summary, total tokens used, skills invoked.

## 24.4 Resume Behavior

If a workflow pauses for approval, the system must be able to resume it after the reviewer acts.

---

# 25. Approval and Pause/Resume Strategy

## 25.1 Preferred Strategy

Use application-level review states plus Agno pause/resume capability where useful for protected actions.

## 25.2 Why

This keeps the UX under the product's control while still benefiting from Agno's approval primitives.

## 25.3 Operational Rule

The send step should be treated as a protected action.

---

# 26. Error Handling Requirements

## 26.1 Discovery Errors

If one discovery worker or skill fails: log the failure (including skill invocation log), allow the rest to continue where possible, mark session partially degraded if needed.

## 26.2 Verification Errors

If verification fails for a lead: mark lead as needs manual review or verification failed, do not send that lead to draft/send automatically.

## 26.3 Sheet Write Errors

If the `gws sheets` write fails: keep lead in app database, log retryable failure with `gws` CLI error output, show issue in UI.

## 26.4 Draft Generation Errors

If draft generation fails: log error (including skill and template info), show failure in session and lead record.

## 26.5 Send Errors

If `gws gmail +send` fails: keep draft status as send_failed, preserve failure reason from `gws` CLI JSON response, allow retry through controlled UI flow.

---

# 27. Security and Permissions

## 27.1 Authentication

Only authenticated internal users should access the UI.

## 27.2 Authorization

At minimum, the system should distinguish: viewer, reviewer, admin.

## 27.3 Secrets

Secrets must be stored securely for: OpenRouter API key, `gws` CLI OAuth credentials (encrypted at rest via `gws`), Postgres connection string, any JWT signing keys for AgentOS RBAC. All secrets are environment variables on the server side — TanStack Start server functions and Agno AgentOS both access them via `process.env` / `os.environ` respectively. Secrets must never appear in client-side JavaScript bundles, log output, or UI responses.

## 27.4 Auditability

All approvals, sends, and skill invocations must be auditable.

---

# 28. Metrics and Success Criteria

## 28.1 Core Metrics

* number of country runs initiated
* average leads found per country
* average verified leads per country
* average confidence score per country
* draft approval rate
* average revision cycles per draft
* email send success rate
* session failure rate
* average time from country submission to first pending draft

## 28.2 Quality Metrics

* lead completeness rate
* duplicate lead rate (within and across runs)
* source-backed lead rate
* reviewer satisfaction with draft quality
* structured feedback category distribution (reveals systemic draft issues)

## 28.3 Operational Metrics

* average workflow duration by stage
* approval wait time
* send latency after approval
* **token usage per session**
* **cost per lead discovered**
* **skill invocation success rate by skill type**

---

# 29. Acceptance Criteria

## 29.1 MVP Acceptance Criteria

The MVP is acceptable when:

1. A user can submit a country with optional context fields from the UI.
2. The system creates a workflow session and shows it in the sessions list.
3. Discovery and verification run asynchronously using composable skills.
4. Leads are normalized and stored with confidence scores.
5. The Google Sheet receives only the fields: Name, Role / Title, WhatsApp, Phone, Details, Email, Company Name, Website, Source — written via `gws` CLI.
6. Draft emails are generated for eligible leads using the template library.
7. Drafts are visible in a pending review UI, ordered by confidence score.
8. The user can approve or request changes with structured feedback.
9. Requested changes produce a new draft version.
10. Approved drafts can be sent via `gws gmail +send`.
11. Send status is reflected in the UI.
12. Session history, workflow status, and skill invocation logs remain visible throughout.
13. Re-running a country deduplicates against prior runs.
14. **Frontend unit tests pass with ≥80% line coverage (Vitest + Bun).**
15. **Backend unit tests pass with ≥85% line coverage (pytest + uv).**
16. **All critical user flows have passing Playwright E2E tests (country submission, session monitoring, lead review, approval, revision, send).**
17. **All agent teams have baseline Agno eval scores (AccuracyEval ≥7, ReliabilityEval passing).**
18. **All UI screens have been validated via Claude in Chrome for design coherence, layout correctness, and interaction quality.**
19. **CI pipeline gates all PRs on frontend + backend tests passing.**

---

# 30. Rollout Plan

## Phase 1: Core Workflow Prototype

Includes: `uv` project scaffold + Agno AgentOS backend, TanStack Start + Bun frontend scaffold with auth middleware, country input with context fields, async discovery with initial skills, async verification with initial skills, lead normalization with confidence scoring, Postgres setup (shared Agno + app tables), Agno session visibility in UI via TanStack Query polling, knowledge base scaffolding.

**Testing at Phase 1:** CI pipeline established (Vitest + pytest gated). Backend unit tests for all Pydantic models, skill logic, and workflow step functions. Frontend unit tests for session list and country submission components. Playwright E2E test for country submission → session appears flow. Claude in Chrome validation of sessions list and session detail screens. Initial Agno evals for discovery agents.

No real sending yet.

## Phase 2: Sheet Output + Drafting

Includes: `gws` CLI setup and auth, Google Sheets integration via `gws` CLI skills, draft generation with template library, pending review UI (TanStack Start approval inbox route), draft versioning, structured feedback capture.

**Testing at Phase 2:** Backend integration tests for `gws` CLI skill wrappers (mocked subprocess). Frontend unit tests for approval inbox, draft review, and structured feedback components. Playwright E2E tests for lead review and draft viewing flows. Claude in Chrome validation of leads list, lead detail, approval inbox, and draft review screens.

Still no live send or limited send.

## Phase 3: Approval + Send

Includes: approve/revise/reject loop with structured feedback, Agno HITL `requires_confirmation` for send gate, real email sending via `gws gmail +send`, send logs, failure handling.

**Testing at Phase 3:** Full-stack integration tests (Playwright against test backend). Playwright E2E tests for complete approval → send flow and revision loop. Backend integration tests for HITL confirm/reject → workflow resume. Claude in Chrome full journey validation (submit → monitor → review → approve → send). Agent evals for outreach agent draft quality.

## Phase 4: Hardening

Includes: retries, role-based access (AgentOS `authorization=True`), observability improvements (cost tracking, skill metrics), duplicate prevention improvements, better model routing, rate limiting tuning, incremental re-run support, TanStack Query optimistic updates for approval UX.

**Testing at Phase 4:** Cross-browser Playwright suite (Firefox + WebKit added). Edge case and error state E2E tests. Nightly agent eval pipeline. Claude in Chrome responsive and accessibility validation. Coverage gates enforced in CI.

## Phase 5: Future Extensions

Potential additions: ClickUp integration, reply tracking, compliance enrichment, per-country prompt configuration, multilingual outreach, knowledge base auto-enrichment from successful runs.

---

# 31. Risks and Mitigations

## Risk 1: Low-quality leads

Mitigation: verification stage with confidence scoring, source-count checks, manual review path, knowledge base to improve targeting over time.

## Risk 2: Duplicate records

Mitigation: duplicate resolver skill, normalization rules, unique matching heuristics, cross-session dedup in incremental mode.

## Risk 3: Poor outreach drafts

Mitigation: human approval loop, draft versioning, structured reviewer feedback, template library.

## Risk 4: Overloading Google Sheets with workflow noise

Mitigation: keep sheet facts-only, store operations in app DB, sheet-writer skill enforces clean column mapping.

## Risk 5: Stuck workflows

Mitigation: visible stage status, retry mechanisms, admin controls.

## Risk 6: Unapproved emails sending accidentally

Mitigation: approval-gated send path, send preconditions, audit trail, `gws gmail +send` wrapped in skill with pre-send checks.

## Risk 7: IP bans or source blocking during discovery (NEW)

Mitigation: rate limiting and politeness controls in discovery skills, circuit-breaker behavior, domain-level backoff.

## Risk 8: Uncontrolled token costs (NEW)

Mitigation: per-session token tracking, cost visibility in UI, configurable per-run token budget (future).

---

# 32. Open Questions

1. ~~What email provider should be used in v1?~~ **Resolved: Gmail via `gws` CLI.**
2. Should drafts be editable directly by the user in the UI, or only revised via feedback prompts?
3. Should rejected leads ever appear in the sheet?
4. What exact eligibility threshold (confidence score) determines whether a verified lead gets an outreach draft?
5. Should country runs be allowed to merge or compare against previous runs for the same country? **Partially resolved: incremental re-runs with dedup are supported. Full merge/comparison is a future extension.**
6. Should the UI expose raw source excerpts or only summarized evidence?
7. Should users be able to manually add or edit leads before drafting?
8. Should there be a manual "send later" state separate from approval?
9. (NEW) Should the knowledge base be editable by operators, or only auto-populated from runs?
10. (NEW) Should there be a confidence-score threshold below which leads are auto-rejected without human review?
11. (NEW) Should skills be hot-reloadable during a running workflow, or only changeable between runs?
12. (NEW) Should the TanStack Start frontend and Agno AgentOS backend be deployed as separate containers or a single monorepo with two entry points?
13. (NEW) Should real-time session status use TanStack Query polling or upgrade to WebSockets / SSE in v1?

---

# 33. Recommended MVP Decisions

To reduce complexity in v1, the recommended decisions are:

1. Use **one primary OpenRouter model** initially.
2. Use **Postgres** as the application database (shared with Agno internals).
3. Use **Agno workflows and AgentOS** as the orchestration backbone and backend runtime.
4. Use **TanStack Start on Bun** as the frontend framework and runtime.
5. Use **`uv`** for Python dependency management and environment reproducibility.
6. Treat **Google Sheets as output only**, not the operational database.
7. Keep **email sending fully approval-gated**.
8. Use **versioned drafts** rather than overwriting drafts.
9. Build a **simple internal admin UI first** using the frontend-design skill before optimizing UX.
10. Use **`gws` CLI** for all Google Workspace interactions (Sheets + Gmail).
11. Encode all repetitive agent behaviors as **composable skills** from day one.
12. Accept **optional user context** at submission but don't require any field beyond country.
13. Implement **confidence scoring** from first version to enable prioritized review.
14. Use **Context7** for all documentation lookups during development (TanStack Start, Agno, gws CLI).

---

# 34. Final Product Definition

This product is an **internal async lead discovery and outreach control system** for gold-market research.

It accepts a **country** as input — with optional research context — and uses **Agno workflows, teams, and composable skills** to:

* find leads,
* verify and score them,
* write clean findings to Google Sheets via `gws` CLI,
* create outreach drafts from a template library,
* and route every email through a human approval UI before sending via `gws` CLI.

The UI is not an optional add-on. It is a core part of the product because the approval and revision loop is central to safe operation.

The final architecture should therefore be treated as:

* **TanStack Start on Bun** for the operator-facing frontend (SSR, server functions, type-safe routing)
* **Agno AgentOS on uv-managed Python** for the backend (workflows, teams, agents, HITL, FastAPI)
* **Composable skills** for reusable agent behaviors
* **`gws` CLI** for Google Workspace integration (Gmail + Sheets)
* **Postgres** for all persistent data (Agno sessions + app operational tables)
* **OpenRouter** for model access
* **Frontend design skill** for UI quality during development
* **Context7** for documentation references during development

---

# 35. Appendix: Proposed Status Sets

## Country Job Status

* queued
* seeding_knowledge
* running
* waiting_for_approval
* partially_completed
* completed
* failed
* cancelled

## Lead Verification Status

* discovered
* normalized
* verified
* needs_review
* rejected

## Outreach Status

* not_started
* draft_generated
* pending_review
* changes_requested
* approved
* sending
* sent
* rejected
* send_failed

---

# 36. Appendix: Lead Sheet Mapping

## Internal-to-Sheet Field Mapping

* `lead.name` → Name
* `lead.role_title` → Role / Title
* `lead.whatsapp` → WhatsApp
* `lead.phone` → Phone
* `lead.details` → Details
* `lead.email` → Email
* `lead.company_name` → Company Name
* `lead.website` → Website
* `lead.source_text` or source summary → Source

---

# 37. Appendix: Skills Registry (NEW)

## Discovery Skills

| Skill ID | Purpose | Primary Sources |
|----------|---------|-----------------|
| `discovery-miners` | Find mining companies and operators | Company registries, mining directories, news |
| `discovery-brokers` | Find brokers and intermediaries | Trade directories, LinkedIn-style sources |
| `discovery-exporters` | Find exporters and traders | Export directories, customs data, trade associations |
| `discovery-directories` | Scan associations and registries | Government registries, chambers, industry bodies |
| `contact-extraction` | Extract contact details from entities | Company websites, directories, public records |

## Verification Skills

| Skill ID | Purpose | Output |
|----------|---------|--------|
| `verify-entity` | Check entity plausibility | Score 0–1 + rationale |
| `verify-contact` | Validate contact ownership | Score 0–1 + rationale |
| `verify-source-quality` | Assess evidence strength | Score 0–1 + rationale |
| `dedup-resolver` | Detect and merge duplicates | Duplicate flag + canonical ID |

## Integration Skills

| Skill ID | Purpose | Wraps |
|----------|---------|-------|
| `sheet-writer` | Append leads to Google Sheet | `gws sheets spreadsheets.values append` |
| `sheet-reader` | Read existing sheet data (for dedup) | `gws sheets spreadsheets.values get` |
| `email-sender` | Send approved outreach | `gws gmail +send` |
| `email-reader` | Check delivery status (future) | `gws gmail +read` |

## Workflow Skills

| Skill ID | Purpose |
|----------|---------|
| `normalization` | Standardize lead fields |
| `draft-generation` | Generate outreach email from template + lead |
| `knowledge-seeder` | Load country domain knowledge |

---

# 38. Appendix: Suggested Next Step After PRD Approval

After this PRD is approved, the next planning document should be a **Technical Design Specification** covering:

1. **TanStack Start frontend setup**: Bun project scaffold, `app.config.ts`, route tree, server function patterns, auth middleware, TanStack Query polling strategy
2. **Agno AgentOS backend setup**: `uv` project scaffold (`pyproject.toml`, `uv.lock`), AgentOS initialization, custom FastAPI route registration, CORS and auth config
3. database schema (including new entities: SkillInvocationLog, CountryKnowledge) — shared Postgres between Agno and app tables
4. Agno workflow definitions (Steps, HITL Conditions, Loops)
5. team definitions (discovery team, verification team)
6. skills registry and skill schemas (Python module structure)
7. structured output schemas (Pydantic models for leads, drafts, verification records)
8. API routes — AgentOS auto-generated + custom routes for approval actions, lead CRUD
9. UI screen map (TanStack Start file-based routes → components → server functions)
10. approval state machine (Agno `requires_confirmation` + app-level states)
11. `gws` CLI integration patterns and auth setup
12. retry and idempotency strategy
13. rate limiting configuration
14. deployment topology (Bun production server + Uvicorn/Gunicorn for AgentOS + Postgres)
15. **testing strategy implementation**: Vitest config, Playwright config, pytest structure, Agno eval golden dataset, Claude in Chrome validation checklist, CI pipeline definition
16. development workflow: `uv run` for backend, `bun dev` for frontend, Context7 for docs, frontend-design skill for UI, Claude in Chrome for visual validation
