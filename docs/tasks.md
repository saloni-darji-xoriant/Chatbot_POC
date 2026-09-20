# Tasks — Qcells L1 Assistant

Status: `[x]` done, `[ ]` open, `[~]` built but paused (commented out). Update this file in the same change as the work.

## Phase 1 — Foundation
- [x] Next.js + TS + Tailwind + Jest frontend; FastAPI backend with Swagger
- [x] Docker Compose; Amplify-ready config
- [x] Qcells Gradient design tokens
- [x] Mock bearer auth, login, SSO, onboarding

## Phase 2 — Chat core
- [x] SSE streaming chat and live process indicator
- [x] Simulated multi-agent RAG pipeline + mock knowledge graph
- [x] Small-talk handling
- [x] L2 handoff screen and Help page
- [x] Thumbs feedback with reason; end-of-conversation rating
- [x] History page with search

## Phase 3 — Knowledge base
- [x] Installer FAQs, case tickets, solar-system specs
- [x] Reference guides distilled from supplied PDFs (source PDFs not committed)
- [x] Admin corrections become KB entries

## Phase 4 — Admin
- [x] Dashboard, feedback review with corrections, conversations
- [~] Documents tab (commented out)
- [~] Admin knowledge-graph button (commented out)

## Phase 5 — Attachments
- [x] In-memory, session-scoped upload with text extraction and caps
- [x] Latency tests
- [~] Attachment UI in composer and message bubble (commented out)

## Phase 6 — Responsive and theming
- [x] Gradient-only theme via tokens (`data-theme`, `lib/theme.ts`)
- [x] Responsive AppShell, mobile drawer (900px breakpoint)

## Phase 7 — Follow-ups, images, export, history (2026-09-20)
- [x] Timezone-aware UTC across the backend
- [x] History ordered by last activity; `updated_at` in summaries
- [x] 11 original diagrams (`scripts/generate_kb_images.py`) and static serving
- [x] KB migrated to curated `follow_ups` and `images` (`scripts/apply_followups.py`)
- [x] Follow-up routing (`find_entry`) with dead-end tests
- [x] PDF export endpoint (fpdf2, tz-aware, images, sources, page numbers)
- [x] CORS exposes `Content-Disposition`
- [x] Frontend: images, "Suggested follow-ups" (latest message only), Export PDF button
- [x] Frontend: history sort control, day grouping, local-time display
- [~] Trace button/panel commented out; its test skipped
- [x] Backend and Jest tests; README section
- [x] Browser verification on desktop (chat, follow-up click, export request, history sort)

## Open / next
- [ ] Mobile-width browser pass for the new features (images, follow-ups, history controls)
- [ ] Confirm `next build` in a clean state (blocked while dev server holds `.next`)
- [ ] Decide production sources for the knowledge base and replace sample data
- [ ] Persistent store and real auth
- [ ] Non-Latin font for PDF export if required
- [ ] Decide whether Trace/Documents/graph return for admins

## Change log
| Date | Change |
|---|---|
| 2026-09-20 | Initial task list; Phase 7 recorded as done. |
