# Constitution — Qcells L1 Assistant

The non-negotiable principles for this project. Specs, plans and tasks must comply with them; change this file only deliberately, and record the change in the log at the bottom.

## 1. Grounded first, honest always
- Specific facts (specs, codes, procedures, warranty) come only from the knowledge base or a file the user attached, and carry citations.
- When nothing matches, the assistant still helps: it gives clearly labelled **general guidance** (written by a language model when a key is configured, otherwise built-in guidance) with safe first checks, clarifying questions and an offer of L2. It never invents product specs, part numbers, prices, warranty terms or error-code meanings.
- AI-written text is always labelled ("AI-generated general guidance..." or "Written by AI from the sources below"), and counts as *not grounded* in admin metrics unless it rewords a knowledge-base answer.
- The L2 handoff screen appears only when the user explicitly asks for a person. Greetings, thanks and farewells are conversational and never trigger a handoff.

## 2. Every suggestion leads somewhere
- Suggested follow-ups must route to a different, real answer: never a repeat of the same answer, never an accidental handoff. Tests enforce this.
- Follow-ups exist to get the installer to a resolution faster (next diagnostic step, the reference, or escalation).

## 3. Safety first
- Safety-critical topics (burning smell, arc fault, electrical hazards) point to escalation and emergency contacts, not self-service fixes.
- Installer-inaccessible settings are never presented as installer actions.

## 4. Original content, no leaked credentials
- Diagrams and knowledge-base text are original works; source PDFs supplied by the team are summarised in our own words and are **not** committed to the repo.
- Region-specific figures that contradict the US-oriented content are left out.
- Secrets, tokens and passwords are never committed, printed or requested. Browser-stored credentials are never extracted.

## 4a. Data handling and language-model use
- The model API key lives only in `backend/.env` (git-ignored) or the host's environment. It is never committed, logged, returned to the browser or pasted into chat.
- Only the user's message text and the last few turns are sent to the model provider - never names, emails or attachment contents. Seed data and tests never call a model.
- The model call must degrade gracefully: no key, timeout or error falls back to built-in guidance or the knowledge-base answer, never to an error screen.

- Attachments live only in process memory, are never written to the project folder, and vanish on restart. Size and count are capped.
- POC storage (users, conversations, feedback) is in-memory by design; anything beyond a demo needs a real store and real auth first.

## 5. Time follows the viewer
- The backend emits timezone-aware UTC. Every displayed time (UI and PDF) is in the viewer's own timezone; the PDF states the zone used, with UTC as fallback.

## 6. Theme is tokens, not hard-coded
- All styling flows from design tokens (`data-theme`, `lib/theme.ts`, Tailwind). Only the Qcells Gradient theme ships, but adding a theme must not require touching components.

## 7. Comment out, don't delete
- Features paused for later (Documents admin tab, admin knowledge-graph button, message Trace) are commented out with an explanatory note and their tests `it.skip`-ed, so they can return without rewriting.

## 8. Responsive and accessible
- Works from phone width up (mobile drawer below 900px). Interactive elements have accessible names; state is not conveyed by colour alone.

## 9. Quality gates
- A change is done only when: backend `pytest`, frontend `jest`, `tsc --noEmit` and `next lint` pass, and any visible change has been checked in the browser.
- New behaviour ships with tests. Bug fixes ship with a regression test.

## 10. Keep the docs alive
- `constitution.md`, `spec.md`, `plan.md` and `tasks.md` in `docs/` are updated in the same change as the behaviour they describe. `tasks.md` is the running record of what is done.

## Change log
| Date | Change |
|---|---|
| 2026-09-20 | Initial constitution. |
| 2026-09-21 | §1 rewritten: open-ended questions get labelled AI guidance instead of an automatic handoff; §4a adds language-model rules. |
