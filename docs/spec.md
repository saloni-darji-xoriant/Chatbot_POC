# Specification — Qcells L1 Assistant (POC)

## 1. Purpose
Hanwha Qcells installers and support staff get fast, grounded first-line (L1) answers about solar systems, inverter faults, case history and installation guidance, with a clean escalation path to L2 humans. Admins review quality and teach the assistant through corrections.

## 2. Users
| Role | Needs |
|---|---|
| Installer | Ask a question, get a cited answer (with a diagram when it helps), follow next steps, export the chat, revisit history, escalate. |
| Admin | See KPIs and quality, review negative feedback, attach corrections, browse all conversations. |

## 3. Functional requirements

### 3.1 Authentication and onboarding
- FR-1 Email/password and mock company-SSO login; role-based routing (installer vs admin). Bearer-token auth (POC).
- FR-2 First-run onboarding screen.

### 3.2 Chat
- FR-3 Streaming responses over SSE: `user_message`, `trace`, `assistant_message`, `handoff`, `done`.
- FR-4 Simulated multi-agent pipeline (Router → Retrieval/RAG → Response → Grounding) with a live "thinking" indicator.
- FR-5 Small talk handled conversationally without handoff.
- FR-6 An explicit request for a person ("connect me to a live specialist", "talk to a human") → L2 handoff screen with contact cards; conversation status becomes `handoff`. Nothing else triggers it.
- FR-7 Answers carry citations and a knowledge-graph subgraph.
- FR-8 **Suggested follow-ups:** 2–4 curated questions per entry, shown under the latest assistant message only; each routes to its own target entry (never a repeat, never a handoff).
- FR-9 **Images:** troubleshooting/how-to answers include an original diagram with caption and alt text, served from `/static/kb-images/`.
- FR-10 Thumbs up/down per answer; thumbs-down accepts a reason and creates an admin-visible feedback item.
- FR-11 "Mark as resolved" with an end-of-conversation star rating.
- FR-12 **Export as PDF:** transcript with title block, timestamps, images, sources and page numbers; times in the viewer's timezone (`tz` query param; UTC fallback); only the owner can export.
- FR-13 Attachments (documents/images, session memory only, capped): attach control in the composer, pending chips, and chips on sent messages.
- FR-14 Per-message Trace option is currently commented out.

- FR-21 **Human-sounding replies for open-ended questions:** when no knowledge-base entry matches, the assistant replies conversationally (empathy, safe first checks, clarifying questions, offer of L2) instead of a handoff. With a language-model key the reply is model-written using recent conversation turns; without one, built-in guidance is used. The reply is labelled as AI-generated general guidance and offers follow-ups (error codes, diagnose low output, escalation, live specialist).
- FR-22 **Weak matches are reworded:** a single-keyword knowledge-base match (for example "my solar panel is not working") is rewritten conversationally by the model from the matched entry, keeping its citations, diagram and follow-ups and labelled "Written by AI from the sources below". Exact follow-up clicks and strong matches stay deterministic. If the model is unavailable the original knowledge-base answer is shown.
- FR-23 **Image viewer:** images in answers open full-screen on click, zoom (buttons, +/-/0 keys, Ctrl+wheel, double-click, up to 400%), download as a file, open in a new tab, and close with Esc or the Close button.

### 3.3 History
- FR-15 List the user's conversations, newest activity first by default (`updated_at` = last message time).
- FR-16 Sort by date and time (newest / oldest first), grouped by day (Today, Yesterday, date), plus text search.

### 3.4 Help
- FR-17 Help Center page with contact channels.

### 3.5 Admin
- FR-18 Dashboard: KPI cards, grounding and satisfaction rings, feedback breakdown, 7-day activity.
- FR-19 Feedback list with correction entry; a correction becomes a new KB entry (and graph node) so the same query is answered next time.
- FR-20 Documents tab and knowledge-graph button: implemented, currently commented out.

## 4. Knowledge base
- 39 entries in four categories: Solar System specs (8), Case Tickets (12), Installer FAQs (12), Reference Guides (7).
- Entry shape: `topic`, `title`, `category`, `keywords`, `answer`, `citations`, `follow_ups[{question, topic}]`, optional `images[{url, alt, caption}]`.
- Retrieval: exact follow-up-question routing first, then keyword-substring scoring (ties → load order).
- 11 diagrams cover 18 entries.

## 5. Non-functional requirements
- NFR-1 Timezone: backend UTC-aware; all displays in viewer's zone.
- NFR-2 Responsive from ~375px; mobile drawer under 900px.
- NFR-3 Theming through tokens; Qcells Gradient only.
- NFR-4 Attachment latency: extraction once at upload, bounded size (5 MB, 8 files, 20k chars); latency covered by tests.
- NFR-5 Accessibility: labelled controls, keyboard-usable.
- NFR-6 Deployable via Docker Compose; frontend Amplify-ready. Swagger at `/docs`.
- NFR-7 Security: no secrets in the repo; CORS restricted to configured origins; `Content-Disposition` exposed for downloads; model key only via environment; prompt-injection resistant system prompt (user text is data).
- NFR-8 A model timeout is capped (default 20 s) and never blocks the server's event loop.

## 5a. Out of scope (POC)
Vector search and a production-grade LLM integration (an optional model client exists), persistent database, real SSO/JWT, multi-tenant admin, live L2 chat.

## 6. Acceptance criteria (headline)
1. Asking "my inverter shows an error code" returns a cited answer with the power-cycle diagram and follow-ups.
2. Clicking any follow-up returns a different grounded answer.
3. An open-ended question with no match (for example "my rooftop setup is misbehaving") gets a conversational, labelled reply with clarifying questions - not the handoff screen. "Connect me to a live specialist" does trigger handoff; "hi" does not.
4. Export PDF downloads a file whose times match the viewer's timezone.
5. History lists newest first and re-sorts oldest first on demand.
6. No Trace control is visible on any message.
7. Clicking a response image opens it; zoom changes the percentage; Download saves a PNG.
8. The composer shows an attach button; an attached file appears as a chip and is used to answer.

## 7. Open questions
- Which real knowledge sources replace the sample data?
- Production auth provider and storage choice.
- Should Trace/Documents/graph return for admins only?
- Which provider and model for production, and is sending conversation text to a third party acceptable for real customer data?

## Revision log
| Date | Change |
|---|---|
| 2026-09-20 | Initial spec covering follow-ups, images, PDF export, history sort, timezone handling, Trace comment-out. |
| 2026-09-21 | Attachments UI re-enabled (FR-13); handoff only on explicit request (FR-6); added FR-21 AI replies, FR-22 weak-match rewording, FR-23 image viewer. |
