# Technical Plan — Qcells L1 Assistant

Implements [spec.md](spec.md) within the rules of [constitution.md](constitution.md).

## 1. Architecture
```
Browser (Next.js 14, TS, React Context, Tailwind)
   │  REST + SSE (bearer token)          │ GET /static/kb-images/*.png
   ▼                                     ▼
FastAPI (backend/app)  ── routers: auth, chat, admin ── StaticFiles(/static)
   │
   ├─ services/chat_pipeline.py   plan_for(): chitchat | handoff | kb | kb_ai | ai
   ├─ services/llm.py             optional OpenAI/Anthropic client (env-configured, never required)
   ├─ services/knowledge_base.py  JSON entries, follow-up routing, keyword search
   ├─ services/knowledge_graph.py mock subgraph per topic
   ├─ services/attachment_store.py in-memory, per-conversation
   ├─ services/pdf_export.py      fpdf2 transcript, tz-aware
   └─ store.py                    in-memory users/conversations/feedback
```

## 2. Stack and versions
- Frontend: Next.js 14.2, React, TypeScript, Tailwind, Jest + Testing Library.
- Backend: Python, FastAPI 0.115, Pydantic 2, Pillow (diagrams, image checks), fpdf2 (PDF), tzdata (timezones on Windows/slim Docker), pypdf / python-docx (attachment extraction).
- Delivery: Docker Compose (local), AWS Amplify (frontend).

## 3. Key design decisions
| Decision | Why |
|---|---|
| Timezone-aware UTC everywhere in the backend | Naive timestamps were read as local time by browsers. UTC + browser conversion gives "viewer's location" for free. |
| PDF built server-side, zone passed as `tz` | The PDF has no browser to localise for it; the client sends its IANA zone, UTC is the fallback. |
| Download via fetch → blob → anchor | The bearer token can't go on a plain link. `Content-Disposition` is CORS-exposed to read the filename. |
| Built-in Helvetica + Latin-1 sanitising | No font files to ship; non-Latin characters degrade to `?` instead of crashing. Revisit if non-Latin support is needed. |
| Curated `follow_ups` with a question→topic route table | Keyword search on free text was fragile: 32 of 78 earlier follow-ups dead-ended. Deterministic routing plus tests removes that class of bug. Same question text must always map to one topic (checked at import). |
| Field name stays `quick_replies` on `Message` | Avoids an API break; UI label became "Suggested follow-ups". |
| Original Pillow-drawn diagrams as PNG | No third-party licensing; reproducible from `scripts/generate_kb_images.py`; served statically and embedded in PDFs from disk. |
| History ordered by last activity (`updated_at`) | Matches "last chat first"; client sort toggle plus day grouping. |
| Planner (`plan_for`) decides the path once; the live trace and the reply both use it | Keeps SSE trace and final message consistent, and lets the trace show an AI step without calling the model. |
| Handoff only on an explicit human request, checked *before* retrieval | Keyword-substring retrieval is loose ("connect me to a specialist" matched a spec entry); intent must win. |
| Weak KB match (score ≤ 1, free-typed, model configured) → model rewords the entry | Vague queries got canned text; grounding the model on the entry keeps facts from the KB. |
| Model client via `httpx` REST, provider inferred from which key is set | No new dependency; works with OpenAI or Anthropic; `LLM_BASE_URL` allows compatible gateways. |
| Model call in `asyncio.to_thread` on the SSE path | The blocking network call must not stall the event loop. |
| Seed data uses `use_llm=False` and `handoff_reply` | Startup must be deterministic and offline. |
| Image download uses `fetch(cache: "reload")` + blob | `<img>` caches the PNG without CORS headers; a plain cross-origin fetch then fails. |
| Paused features commented out, tests skipped | Constitution §7. |
| Design tokens + `data-theme` | Constitution §6. |

## 4. Data contracts (changes in this iteration)
- `Message.images: [{url, alt, caption?}]`
- `ConversationSummary.updated_at`
- `GET /api/chat/conversations/{id}/export.pdf?tz=` → `application/pdf`, `Content-Disposition: attachment`
- KB JSON: `quick_replies` removed → `follow_ups: [{question, topic}]`, optional `images`
- `Message.is_ai_generated: bool` (frontend shows the AI label from it)
- Environment: `OPENAI_API_KEY` | `ANTHROPIC_API_KEY`, optional `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_TIMEOUT_SECONDS` (see `backend/.env.example`)

## 5. Frontend structure
- `lib/api.ts` (requests, SSE, `exportConversationPdf`, `assetUrl`), `lib/download.ts`, `lib/history.ts`, `lib/theme.ts`, `lib/types.ts`
- `components/chat/*` (MessageBubble, MessageActions, ExportPdfButton, ImageViewer, Composer, …), `components/layout/AppShell`, `components/ui/*`
- Pages: `/login`, `/onboarding`, `/chat`, `/history`, `/help`, `/admin/*`

## 6. Testing strategy
- Backend (pytest; `conftest.py` strips model keys so tests never hit a real API): planner and handoff rules, model request shapes (mocked `httpx`), fallbacks, key never logged, KB integrity, follow-up routing, images exist and are served, PDF export (auth, ownership, bad tz, non-Latin text, CORS header), history order, tz-aware timestamps, attachment latency.
- Frontend (Jest): components, history helpers, export button, image rendering, follow-up visibility, Trace absent.
- Gates: `pytest`, `jest`, `tsc --noEmit`, `next lint`, plus a manual browser pass (desktop and mobile).

## 7. Run and deploy
- Local: backend `uvicorn app.main:app --port 8000` (venv), frontend `npm run dev`; `.claude/launch.json` defines both.
- `NEXT_PUBLIC_API_URL` must point at the backend `/api`; image URLs derive from it.
- Do not run `next build` while the dev server is using `.next` (it fails on the trace file).

## 8. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Keyword search mismatches | Curated routing for follow-ups; add keywords/entries as gaps appear. |
| Diagram drift from source facts | Diagrams are generated from one script; update with the KB entry. |
| In-memory store loses data on restart | Accepted for POC; persistent store is a listed next step. |
| Mock auth | POC only; replace before any real exposure. |
| Model hallucination | Fixed safety-first system prompt, KB reference for weak matches, visible AI label, low temperature, capped length. |
| Conversation text sent to a third party | Only message text + last turns; documented in the constitution; provider is opt-in via env. |
| Extra latency / cost per free-typed message | 20 s cap, strong matches and follow-ups skip the model, fallback on failure. |

## 9. Future work
Real retrieval (vector store) instead of keyword matching, streaming model tokens to the UI, persistent DB, real auth, non-Latin PDF font, re-enable Trace/Documents/graph for the appropriate role.

## Revision log
| Date | Change |
|---|---|
| 2026-09-20 | Initial plan reflecting follow-ups, images, PDF export, history sort, tz handling. |
| 2026-09-21 | Added llm.py and planner design, handoff rules, image-viewer decisions, env contract. |
