# Qcells L1 Assistant — Chatbot POC

A support chatbot for Hanwha Qcells installer and admin users. The assistant answers
L1 (tier-1) questions using a simulated multi-agent RAG pipeline over a mock knowledge
graph, streams its reply over Server-Sent Events, hands off to a live L2 specialist
when it can't find a grounded answer, collects end-of-conversation ratings/feedback
(plus a reason on any thumbs-down), and surfaces everything — including a
knowledge-graph drill-down and an admin correction workflow — in an admin dashboard.

- **Frontend:** Next.js 14 (App Router) + TypeScript + React Context API + Tailwind CSS + Jest/RTL
- **Backend:** Python + FastAPI (auto-generated Swagger/OpenAPI docs)
- **Styling:** implements the "Qcells Gradient" design tokens (see `frontend/tailwind.config.ts` and `frontend/src/app/globals.css`)
- **Containerized:** Dockerfiles for both apps + a `docker-compose.yml` for local orchestration
- **Deployment target:** AWS Amplify Hosting (frontend) — see [Deploying to AWS Amplify](#deploying-to-aws-amplify)

## Project structure

```
Chatbot_POC/
├── backend/                   FastAPI service
│   ├── app/
│   │   ├── main.py            App entrypoint, CORS, router registration
│   │   ├── config.py          Environment-driven settings
│   │   ├── models.py          Pydantic request/response schemas
│   │   ├── auth.py            Mock bearer-token auth
│   │   ├── store.py           In-memory data store (seeded, linked demo conversations)
│   │   ├── utils.py           `new_id()` helper
│   │   ├── data/               Knowledge base content — see "Knowledge base" below
│   │   │   ├── solar_systems.json      Product/system specs (panels, battery, inverters, ...)
│   │   │   ├── case_tickets.json       Historical support case tickets
│   │   │   └── installer_queries.json  Installer FAQ / troubleshooting entries
│   │   ├── routers/           auth.py, chat.py, admin.py
│   │   └── services/
│   │       ├── knowledge_base.py   Loads app/data/*.json + admin corrections
│   │       ├── knowledge_graph.py  Curated + auto-generated topic subgraphs
│   │       ├── small_talk.py       Greeting/thanks/farewell detection (no handoff)
│   │       └── chat_pipeline.py    Router -> Retrieval(RAG) -> Response -> Grounding agents
│   ├── tests/                 Pytest API tests (incl. SSE stream + correction flow)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  Next.js app
│   ├── src/
│   │   ├── app/                Pages: login, onboarding, chat, history, help, admin/*
│   │   ├── components/
│   │   │   ├── ui/             Shared styled components (Button, Input, Card, ...)
│   │   │   ├── chat/           Composer, MessageBubble, ProcessTrace, HandoffScreen, ...
│   │   │   ├── layout/         Sidebar, ProfileCard, AdminTopbar
│   │   │   └── admin/          KpiCard, ActivityChart, FeedbackListItem, KnowledgeGraphView, ...
│   │   ├── context/            AuthContext, ChatContext (React Context API)
│   │   ├── lib/                api.ts (fetch client), types.ts, constants.ts
│   │   └── __tests__/          Jest + React Testing Library unit tests
│   ├── tailwind.config.ts      Design tokens mapped to Tailwind theme
│   ├── jest.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- (Optional) Docker Desktop, if you want to run everything containerized

## Run locally — option A: without Docker

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API base URL: `http://localhost:8000/api`
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- Raw OpenAPI spec: `http://localhost:8000/openapi.json`

### 2. Frontend (Next.js)

In a second terminal:

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

- App: `http://localhost:3000`
- `.env.local` sets `NEXT_PUBLIC_API_URL=http://localhost:8000/api` — update it if your backend runs elsewhere.

### 3. Log in

Demo accounts (seeded in `backend/app/store.py`):

| Role      | Email                                  | Password      |
|-----------|-----------------------------------------|---------------|
| Installer | jordan.reyes@installer.qcells.com       | installer123  |
| Installer | morgan.lee@installer.qcells.com         | installer123  |
| Admin     | casey.kim@qcells.com                    | admin123      |

Log in as an installer to try the chat + handoff + rating flow, or as the admin to
see the same chat plus the Admin section (Dashboard / Feedback / Documents tabs).
Seed data already links a few past conversations to feedback items, so the admin
Feedback page has real trace/knowledge-graph data to show immediately.

Try asking things like:
- "My inverter is showing an E02 error code" (Installer FAQ) → grounded answer,
  streamed over SSE, with citations and a **Trace** button showing the Router ->
  Retrieval(RAG) -> Response -> Grounding agent pipeline and the knowledge-graph subgraph it used
- "What's the usable capacity of the Q.HOME ESS battery?" (Solar System) → answers from the product datasheet
- "Two panels are showing near-zero output after a hailstorm" (Case Ticket) → answers
  by referencing the specific resolved case (Ticket #Q-10287), not just a generic FAQ
- "hi" → a normal conversational reply, not a handoff (see [`small_talk.py`](backend/app/services/small_talk.py))
- "Do you offer a referral bonus for new customers?" → genuinely out of scope → no KB match → automatic handoff to the Agent Handoff screen
- Thumbs-down any assistant reply to leave a short reason inline — it shows up
  immediately in Admin -> Feedback
- In Admin -> Feedback, open "View trace & knowledge graph" on any item, or "Add
  correction" on a negative one to teach the assistant the right answer (it's added
  as a new knowledge-base entry so the same query is grounded next time)
- Click **Mark as resolved** in the chat to trigger the end-of-conversation star rating
- Visit **History** (search bar included) to revisit any past conversation, or
  **Help** for the standalone contact-support page

## Run locally — option B: with Docker Compose

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend + Swagger: `http://localhost:8000/docs`

Stop with `docker compose down`.

## Running tests

**Frontend (Jest + React Testing Library):**

```bash
cd frontend
npm test
```

**Backend (Pytest):**

```bash
cd backend
.venv\Scripts\activate
pytest
```

## Application pages

| Page | Route | Notes |
|---|---|---|
| Login | `/login` | Work email/password or "Continue with Company SSO"; role is resolved server-side |
| Onboarding | `/onboarding` | First-run welcome screen, tailored copy per role (installer vs admin) |
| Chat (home) | `/chat` | Empty-state greeting + suggestion chips, SSE-streamed message thread with citations, quick replies, thumbs up/down (+ reason), a per-message **Trace** button, composer |
| History | `/history` | Search bar + every past conversation for the signed-in user, click to reopen (`/chat?conversationId=...`) |
| Help Center | `/help` | Standalone contact-support page (popular questions + the same contact cards as the handoff screen) |
| Agent Handoff | rendered inside `/chat` when a query can't be grounded | Banner + 2x2 contact cards (Installer Hotline, Emergency/Safety, Email, Warranty) |
| End-of-conversation rating | rendered inside `/chat` via "Mark as resolved" | 5-star rating, thumbs, optional comment |
| Admin — Dashboard | `/admin/dashboard` | KPI cards, grounding-rate/satisfaction rings, feedback breakdown, 7-day activity chart |
| Admin — Feedback | `/admin/feedback` | Filterable (All/Positive/Negative) feedback list; each item can show its trace + knowledge graph, and negative items can get a correction |
| Admin — Documents | `/admin/documents` | Knowledge-base source document list |

The Admin nav item is only shown to users with the `admin` role; installer accounts
are redirected away from `/admin/*`.

## Knowledge base

The knowledge base lives in `backend/app/data/` as three JSON content files, matching
the three categories the KB is scoped to cover. It's loaded once at startup by
[`app/services/knowledge_base.py`](backend/app/services/knowledge_base.py) into a
single searchable list (32 entries as shipped):

| File | Category | What it contains | Example entries |
|---|---|---|---|
| `solar_systems.json` | Solar System | Product/system specs for the Qcells lineup used in this POC | Q.PEAK / Q.TRON panel datasheets, Q.HOME ESS battery, Q.VOLT hybrid & string inverters, racking compatibility, Q.OMMAND monitoring platform, system sizing & net metering |
| `case_tickets.json` | Case Ticket | Historical, resolved installer support tickets — the answer is framed as "similar resolved case (Ticket #...)" | Recurring grid-fault shutdown, hail-damaged panel string, Wi-Fi/monitoring dropout, battery BMS firmware bug, failed rapid-shutdown inspection, rodent-damaged DC wiring, a burning-smell safety case, a denied warranty claim |
| `installer_queries.json` | Installer FAQ | Standard troubleshooting/how-to FAQ entries | Inverter fault codes, panel underperformance, monitoring login issues, warranty claims, firmware updates, installation sequence, rapid shutdown (NEC 690.12), battery clearances, permits/inspection, error code reference, grounding & bonding, L1->L2 escalation criteria |

Each entry has `keywords` (for the mock keyword-matching "RAG" lookup), a `topic` key,
a human-readable `title`, an `answer`, one or more `citations` (document + section),
and optional `quick_replies`. Admin corrections (via the Feedback page) are appended
to this same in-memory list at runtime as a fourth, ad-hoc category.

**Knowledge graph:** six "flagship" topics (inverter faults, panel output, monitoring,
warranty, firmware, installation) have a hand-curated subgraph in
[`knowledge_graph.py`](backend/app/services/knowledge_graph.py); every other entry —
all the solar-system products and case tickets — gets a subgraph auto-generated from
its own citations and keywords, so every answer has something real to show in the
admin **Trace** panel, not just the original six topics.

**Mock conversation history:** `store.py` seeds ~14 realistic conversations (built
with the same pipeline the live chat uses) across two installer accounts, spanning
all three KB categories plus one genuinely out-of-scope query that correctly falls
through to a handoff — so History, the admin Feedback list, and the Dashboard all
have real, varied data on first run instead of empty states. The **Documents** list
is derived directly from the KB's own citations (deduped, categorized by filename
pattern) rather than hand-maintained, so it can't drift out of sync with the KB.

No SOW file was present in this repo when this was built — the KB structure and
content were derived directly from "solar panel system + case tickets + installer
queries, realistic for Qcells" as scoped in the chat request. If you have an actual
SOW with a specific schema or content list, share it and the JSON files above can be
re-shaped to match exactly.

## Design tokens

The "Qcells Gradient" tokens (colors, typography, radii, shadows, component specs)
are implemented as:
- CSS custom properties in [`frontend/src/app/globals.css`](frontend/src/app/globals.css)
- A matching Tailwind theme in [`frontend/tailwind.config.ts`](frontend/tailwind.config.ts)

The brand gradient (`linear-gradient(120deg, #22C3A6, #1E6FEB)`) is reserved for the
assistant avatar, primary buttons, and the empty-state greeting text, per the token
spec — everywhere else uses solid surface/border/text colors.

## Backend API overview

All endpoints are namespaced under `/api` and documented live in Swagger (`/docs`).

- `POST /api/auth/login`, `POST /api/auth/sso`, `GET /api/auth/me`
- `POST /api/chat/conversations`, `GET /api/chat` (history), `GET /api/chat/conversations/{id}`
- `POST /api/chat/conversations/{id}/messages/stream` — **SSE** endpoint the chat UI
  uses: streams `user_message`, then a `trace` event per pipeline agent (Router,
  Retrieval/RAG, Response, Grounding) as each one runs, then the final
  `assistant_message` (with citations + its knowledge-graph subgraph), an optional
  `handoff` event, and a closing `done` event
- `POST /api/chat/conversations/{id}/messages` — synchronous (non-streaming) variant of the same pipeline
- `POST /api/chat/conversations/{id}/handoff` — contact-card info for the handoff screen
- `GET /api/chat/help-contacts` — the same contact list, for the standalone Help Center page
- `POST /api/chat/messages/{id}/vote` — thumbs up/down (+ optional reason) on an assistant
  message; a thumbs-down immediately records an admin-visible feedback item
- `POST /api/chat/conversations/{id}/rating` — end-of-conversation star/thumbs/comment
- `GET /api/admin/dashboard`, `GET /api/admin/feedback`, `GET /api/admin/documents`,
  `GET /api/admin/conversations`, `GET /api/admin/conversations/{id}` (admin role required)
- `POST /api/admin/feedback/{id}/correction` — attaches a correction to a negative
  feedback item; it's turned into a new knowledge-base entry (and knowledge-graph
  node) so the same query is answered directly next time instead of handing off

Auth is a simplified bearer-token scheme (`token_<user_id>`) and data is stored
in-memory per process — both are intentional POC simplifications; see the
"Known simplifications" section below before using this beyond a demo.

## Deploying to AWS Amplify

This app is structured so the frontend can go straight onto **Amplify Hosting**:

1. Push this repo to a Git provider Amplify can connect to (GitHub, GitLab, Bitbucket, or CodeCommit).
2. In the Amplify console, create a new app from your repo and set the app root to `frontend/` (monorepo setting).
3. Amplify will detect `frontend/amplify.yml`; it already runs `npm ci` + `npm run build` and publishes the `.next` build for Next.js SSR hosting.
4. Add an environment variable on the Amplify app: `NEXT_PUBLIC_API_URL` pointing at your deployed backend's `/api` base URL.

The **backend is a standalone container** (see `backend/Dockerfile`) and isn't hosted
by Amplify Hosting itself — deploy it to a container runtime such as AWS App Runner,
ECS/Fargate, or Amplify's own container/compute support, then point the frontend's
`NEXT_PUBLIC_API_URL` at it. Make sure `CORS_ORIGINS` on the backend includes your
Amplify domain.

## Known simplifications (by design, for a POC)

- **Auth** is a mock bearer token, not JWT/OAuth — replace before production.
- **Data store** is in-memory and resets on backend restart — swap `app/store.py` for a real database.
- **Multi-agent RAG pipeline** (`app/services/chat_pipeline.py`) is a simulated 4-step
  pipeline (Router -> Retrieval/RAG -> Response -> Grounding) over **keyword** matching,
  not real LLM-backed agents or vector search — it exists to make the orchestration
  and its trace/telemetry real and inspectable, not to demonstrate model quality.
- **Knowledge graph** (`app/services/knowledge_graph.py`) hand-curates six "flagship"
  topic subgraphs and auto-generates the rest from each entry's own citations/keywords
  — a real deployment would back this with a graph database (e.g. Neo4j / Amazon
  Neptune) populated by an ingestion pipeline, not build it at lookup time.
- **Knowledge base content** (`app/data/*.json`) — the solar-system specs are
  plausible/representative numbers based on Qcells' real product lines and naming
  (Q.PEAK, Q.TRON, Q.HOME ESS, Q.VOLT), not verified current datasheets; the case
  tickets are illustrative fictional examples, not real historical Qcells support
  records. No SOW document was available when this was authored — see the
  "Knowledge base" section above for how content was scoped.
- **Admin corrections** append a new in-memory KB entry/graph node at runtime; they
  don't persist across a backend restart and don't do any real document parsing —
  registering a "document" just adds its filename as metadata.
- **Handoff to L2** returns mock contact info/queue position; there's no live agent transport (e.g. websockets to a real agent).
