# Technical Plan — Qcells L1 Assistant

Implements [spec.md](spec.md) within the rules of [constitution.md](constitution.md).

## 1. Architecture
```
Browser (Next.js 14, TS, React Context, Tailwind)
   │  REST + SSE (bearer token)          │ GET /static/kb-images/*.png
   ▼                                     ▼
FastAPI (backend/app)  ── routers: auth, chat, admin ── StaticFiles(/static)
   │
   ├─ services/chat_pipeline.py   Router → Retrieval → (Document) → Response → Grounding
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
| Paused features commented out, tests skipped | Constitution §7. |
| Design tokens + `data-theme` | Constitution §6. |

## 4. Data contracts (changes in this iteration)
- `Message.images: [{url, alt, caption?}]`
- `ConversationSummary.updated_at`
- `GET /api/chat/conversations/{id}/export.pdf?tz=` → `application/pdf`, `Content-Disposition: attachment`
- KB JSON: `quick_replies` removed → `follow_ups: [{question, topic}]`, optional `images`

## 5. Frontend structure
- `lib/api.ts` (requests, SSE, `exportConversationPdf`, `assetUrl`), `lib/download.ts`, `lib/history.ts`, `lib/theme.ts`, `lib/types.ts`
- `components/chat/*` (MessageBubble, MessageActions, ExportPdfButton, Composer, …), `components/layout/AppShell`, `components/ui/*`
- Pages: `/login`, `/onboarding`, `/chat`, `/history`, `/help`, `/admin/*`

## 6. Testing strategy
- Backend (pytest): KB integrity, follow-up routing, images exist and are served, PDF export (auth, ownership, bad tz, non-Latin text, CORS header), history order, tz-aware timestamps, attachment latency.
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

## 9. Future work
Real retrieval (vector store + LLM), persistent DB, real auth, non-Latin PDF font, re-enable Trace/Attachments/Documents/graph for the appropriate role.

## Revision log
| Date | Change |
|---|---|
| 2026-09-20 | Initial plan reflecting follow-ups, images, PDF export, history sort, tz handling. |
