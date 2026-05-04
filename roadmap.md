# Smart Parcel Tracker — Final Merged Roadmap

## Product direction

Smart Parcel Tracker is a self-hosted, privacy-aware tool that helps users find parcel-related Gmail messages, approve or reject suggestions, learn simple visible rules, extract tracking information, and track deliveries from a local dashboard.

The core idea is not “give an app full Gmail access and hope it behaves.” The app should run locally, use Gmail only as an input source, keep the token on the user’s machine, and make every automation rule inspectable and editable.

## Product principles

### 1. Self-hosted first

The default version should be self-hosted with Docker Compose. This avoids the biggest trust problem: a hosted app receiving sensitive parcel emails that may include full name, phone number, home address, ZIP code, pickup point, or order contents.

### 2. Existing Gmail account, no second mailbox required

Requiring users to create a new mailbox is too much friction. The app should connect to the existing Gmail account and work with a user-selected label.

Important limitation: Gmail OAuth cannot enforce “only this label” access. Label-only behavior is an app-level promise, not a Google-enforced permission boundary. Self-hosting makes this more acceptable because the token and processing stay local.

### 3. App-assisted labeling

The best product loop is:

```text
New email arrives
↓
App suggests: “maybe parcel?”
↓
User reviews a small card
↓
User chooses:
- Track this
- Ignore this
- Always add similar
- Never add similar
```

“Always” and “never” should create visible rules, not vague AI memory.

### 4. Rule-based first, LLM later

Rules decide which emails are worth looking at. Extractors decide what tracking data is inside. LLM fallback should be late, limited, structured, and only used after simpler methods fail.

### 5. Minimal raw email retention

Raw emails are sensitive. The app should avoid permanently storing raw email bodies by default.

Preferred behavior:

```text
Fetch email
↓
Parse body and links locally
↓
Extract candidate parcel data
↓
Store metadata, extracted values, evidence, and confidence
↓
Discard raw body unless retention is explicitly enabled
```

Optional raw retention modes:

```text
Never store raw body — default
Keep encrypted for 24 hours
Keep encrypted until reviewed
```

### 6. Database is the source of truth

Gmail labels are useful for visibility and sync state, but the local database should be the real source of truth.

## Recommended stack

The stack should be boring, practical, and easy to debug.

```text
API: FastAPI + Pydantic v2
Database: PostgreSQL 16
ORM: SQLAlchemy 2.0 async + Alembic
Jobs: ARQ
Broker/cache: Redis
Frontend: Next.js App Router or SvelteKit
Real-time updates: Server-Sent Events (SSE)
Gmail integration: google-api-python-client
Tracking provider: 17track API behind a thin wrapper
LLM fallback: Direct API call with structured output, no framework
Notifications: ntfy.sh first, Telegram later
Deployment: Docker Compose
Reverse proxy: Caddy
Auth: Single-user session cookies + bcrypt
```

Explicitly avoid for the first version:

```text
Kubernetes
Kafka
Celery
GraphQL
Microservices
Service mesh
Complex cloud-native deployment
Direct carrier API integrations for every carrier
Hosted SaaS mode
```

## Core data model

The exact schema can evolve, but these are the core concepts.

### Users and auth

For the first version, assume single-user self-hosted auth.

```text
users
sessions
```

### Gmail ingestion

```text
gmail_accounts
gmail_labels
gmail_messages
email_parse_attempts
raw_email_cache optional
```

`gmail_messages` should store metadata such as Gmail message ID, thread ID, sender, subject, received date, snippet, label IDs, and processing state.

`raw_email_cache` should be optional and short-lived. If it exists, store encrypted content and an expiration timestamp.

### Review and learning

```text
review_queue
filter_rules
rule_matches
user_decisions
```

Rules should be visible and editable.

Example rules:

```json
{
  "type": "sender_and_subject_keyword",
  "sender": "info@iherb.com",
  "subject_contains": ["shipped", "tracking"],
  "action": "candidate"
}
```

Supported early rule types:

```text
Sender equals
Sender contains
Subject contains keyword
Body/link contains tracking domain
Always suggest sender + keyword
Never suggest sender
Never suggest sender + keyword
```

### Parcels and extraction

```text
parcels
parcel_sources
extraction_results
tracking_events
```

`parcel_sources` links parcels back to source Gmail messages.

`extraction_results` should store what was extracted, how, and why.

Example:

```json
{
  "field": "tracking_number",
  "value": "JD0146...",
  "source": "tracking_url",
  "extractor_name": "dhl_url_param_extractor",
  "confidence": 0.93,
  "evidence": "Found inside DHL tracking link"
}
```

### Notifications and ops

```text
notification_rules
notification_events
job_runs
ops_health_checks
```

## Gmail labels managed by the app

The app can create and maintain labels like:

```text
ParcelTracker/Candidate
ParcelTracker/Confirmed
ParcelTracker/Needs Review
ParcelTracker/Ignored
```

Behavior:

```text
Candidate found → apply Candidate label
User clicks Track → apply Confirmed label
User clicks Ignore → apply Ignored label
Extraction fails → apply Needs Review label
```

These labels should mirror the local state, not replace the database.

## Final merged roadmap

The MVP is the end of Phase 5: the user can connect Gmail locally, review suggestions, create rules, extract tracking data, and see parcel cards in a dashboard. Carrier polling and notifications come after that.

## Phase 0 — Foundation

Goal: create a stable base that can run locally.

Build:

```text
Repository structure
FastAPI skeleton
/health endpoint
PostgreSQL in Docker Compose
Redis in Docker Compose
Alembic baseline
ARQ worker process
Pre-commit setup
Minimal CI
Basic settings/config handling
```

Deliverable:

```text
docker compose up starts the API, database, Redis, and worker successfully.
/health returns OK.
Alembic migrations run cleanly.
```

Do not add parcel logic yet.

## Phase 1 — Gmail ingestion, privacy-aware

Goal: connect Gmail and ingest messages from a selected label.

Build:

```text
Local OAuth2 flow
Gmail API client
Label selection
Scheduled ARQ job to poll selected Gmail label
Message metadata storage
Temporary body/link parsing
Optional encrypted raw email cache
```

Important privacy choice:

```text
Do not permanently store raw email bodies by default.
```

Store:

```text
Gmail message ID
Thread ID
Sender
Subject
Received date
Snippet
Labels
Processing state
Extracted links/text summary if needed
```

Deliverable:

```text
Emails from a selected Gmail label flow into Postgres and can be queried locally.
```

## Phase 2 — Detector + review queue + tiny review UI

Goal: detect likely parcel emails and let the user train the system.

Build:

```text
Heuristic detector
Keyword scoring
Known sender/domain scoring
Known tracking-domain scoring
Review queue
User decision endpoints
Minimal review UI
```

Initial keywords:

```text
tracking
shipment
shipped
delivery
package
parcel
order shipped
מספר מעקב
משלוח
החבילה
ההזמנה נשלחה
בדרך אליך
```

Initial domains:

```text
dhl.com
ups.com
fedex.com
israelpost.co.il
17track.net
parcelsapp.com
gcx.co.il
cheetah.co.il
```

Review card buttons:

```text
Track this
Ignore this
Always add similar
Never add similar
```

Deliverable:

```text
The app finds likely parcel emails and the user can approve, ignore, or create simple rules from the review screen.
```

## Phase 3 — App-assisted Gmail labeling and visible rules

Goal: make the learning behavior real and inspectable.

Build:

```text
filter_rules table
rule evaluation engine
rule match history
Gmail label creation
Gmail label updates based on state
Rules management UI
```

Rule actions:

```text
candidate
confirmed
ignored
needs_review
```

The app should suggest specific rules, not vague rules.

Example:

```text
Always suggest emails from info@iherb.com when the subject contains “shipped”.
```

Better than:

```text
Always suggest emails like this.
```

Deliverable:

```text
The app learns from user decisions by creating visible rules, applies Gmail labels, and reduces repeated manual review.
```

## Phase 4 — Tracking link and number extraction

Goal: extract useful tracking data from approved emails.

Build:

```text
HTML email parsing
Plain text parsing
Link extraction
Tracking domain detection
URL parameter extraction
Per-carrier regex extractors
Manual tracking number fallback
Extraction evidence storage
Confidence scoring
```

Extraction order:

```text
1. Links and buttons
2. URL domains and parameters
3. Body text near tracking keywords
4. Known carrier regex patterns
5. Manual user input
6. LLM fallback later, not yet
```

Initial carriers/providers:

```text
DHL
UPS
FedEx
USPS
Amazon Logistics
Israel Post
HFD
GCX
Cheetah
Yango Delivery if relevant
17track/parcelsapp tracking links
```

Deliverable:

```text
When the user approves an email, the app can extract a tracking link, tracking number, carrier, store/sender, confidence, and evidence. If extraction fails, the email goes to Needs Review with a manual entry option.
```

## Phase 5 — Parcel dashboard + deduplication

Goal: turn approved emails into useful parcel cards.

Build:

```text
Parcel list
Active/delivered tabs
Parcel detail page
Source email references
Extraction evidence display
Needs Review section
Manual merge
Automatic deduplication
SSE updates for local dashboard changes
```

Dashboard sections:

```text
Needs Review
Active
Waiting for Pickup
Delivered
Ignored / Archived
```

Parcel card example:

```text
iHerb
DHL • JD0146••••92
Status: Tracking extracted
Source: Gmail email from May 4
Confidence: 93%
```

Deduplication rules:

```text
Same tracking number → same parcel
Same tracking URL → same parcel
Same store + order number → probably same parcel
Same sender + close date + similar subject → possible duplicate, ask user
```

Deliverable:

```text
The app feels like real software: suggested emails become parcel records, duplicates are merged, uncertain items are reviewable, and the dashboard is usable.
```

This is the first real MVP.

## Phase 6 — Tracking polling

Goal: update parcel status after extraction.

Build:

```text
17track API wrapper
Tracking registration if required
Retry and backoff
ARQ scheduled polling job
tracking_events table
Status derivation from latest event
Adaptive polling
```

Important rule:

```text
Do not make current_status the source of truth.
Append tracking events and derive current status from the latest relevant event.
```

Adaptive polling examples:

```text
Delivered parcels → never poll
Stuck parcels → poll less often
Out for delivery → poll more often
Recently added parcels → poll normally
```

Deliverable:

```text
The backend can fetch live tracking updates, append events, and update the dashboard status.
```

## Phase 7 — Notifications

Goal: notify users only when it matters.

Build:

```text
ntfy.sh integration
Telegram bot integration later
notification_rules table
Notification event hooks
Notification history
```

Notification triggers:

```text
Status changed
Out for delivery
Delivered
Exception / failed delivery
Waiting for pickup
```

Default behavior should be conservative. Too many notifications will train the user to ignore the app.

Deliverable:

```text
The user gets useful delivery notifications without spam.
```

## Phase 8 — LLM fallback for messy emails

Goal: handle emails where heuristics say “parcel” but regex extraction fails.

Build:

```text
Redaction step before LLM call
Structured LLM extraction function
Daily call cap
Cost guardrails
Cache by Gmail message ID
Low-confidence review flow
```

Structured output only:

```json
{
  "carrier": "DHL",
  "tracking_number": "JD0146...",
  "tracking_url": "https://...",
  "confidence": 0.82
}
```

Rules:

```text
No LangChain
No autonomous agent flow
No unbounded backlog processing
Never pay twice for the same email
Low confidence goes back to user review
```

Deliverable:

```text
Messy but likely parcel emails can be pre-filled for review instead of requiring the user to start from scratch.
```

## Phase 9 — Hardening and portfolio polish

Goal: make it reliable, presentable, and safe to demo.

Build:

```text
Single-user auth
Caddy reverse proxy
HTTPS
Nightly pg_dump backup
Structured logging with structlog
Ops page
Job health checks
Error rate tracking
Last successful Gmail poll
Last successful carrier poll
Data export
Data deletion
Demo mode with fake emails
README
Architecture diagram
Screenshots
Short demo GIF/video
Tests for rules and extractors
Privacy section
```

Ops page should show:

```text
Last Gmail poll
Last carrier poll
Worker status
Queue depth
Recent job errors
17track API failures
LLM usage if enabled
```

Deliverable:

```text
The project is reliable enough for personal use and polished enough to show as a portfolio project.
```

## What not to build early

Avoid these until the core product works:

```text
Hosted SaaS
Mobile app
Full carrier coverage
Direct SMTP/MX receiving
Complex multi-user auth
Payments
Browser extension
Gmail add-on
Full cloud deployment
AI agent workflow
```

## Suggested MVP definition

The MVP is complete when:

```text
The app runs locally with Docker Compose.
It connects to Gmail.
It reads from a selected label.
It suggests parcel candidates.
The user can approve, ignore, always add similar, or never add similar.
The app creates visible rules.
The app applies Gmail labels.
The app extracts tracking links/numbers from approved emails.
The app creates parcel records.
The dashboard shows active, delivered, and needs-review parcels.
Duplicates are handled reasonably.
Raw email bodies are not permanently stored by default.
```

Carrier polling, notifications, and LLM fallback are valuable, but they are not required for the first MVP.

## Portfolio positioning

A good one-sentence description:

```text
A self-hosted, privacy-aware Gmail assistant that learns user-approved parcel-detection rules, extracts tracking data with explainable confidence, and turns shipping emails into a local delivery dashboard.
```

What this project demonstrates:

```text
Backend architecture
Gmail API integration
OAuth handling
Async background jobs
PostgreSQL schema design
Email parsing
Rule engine design
Data extraction
Deduplication
Privacy-aware engineering
Frontend dashboard work
Real-time updates with SSE
Dockerized deployment
Testing and operational thinking
```

The privacy angle is not an afterthought. It is part of the product’s technical design.
