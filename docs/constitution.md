# Constitution — Qcells L1 Assistant

The non-negotiable principles for this project. Specs, plans and tasks must comply with them; change this file only deliberately, and record the change in the log at the bottom.

## 1. Grounded or handed off
- The assistant answers only from the knowledge base (or a file the user attached). It never guesses.
- No grounded match for a real support question → hand off to L2 with contact details. Greetings, thanks and farewells are conversational and never trigger a handoff.
- Every grounded answer carries citations.

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

## 4a. Data handling
- Attachments live only in process memory, are never written to the project folder, and vanish on restart. Size and count are capped.
- POC storage (users, conversations, feedback) is in-memory by design; anything beyond a demo needs a real store and real auth first.

## 5. Time follows the viewer
- The backend emits timezone-aware UTC. Every displayed time (UI and PDF) is in the viewer's own timezone; the PDF states the zone used, with UTC as fallback.

## 6. Theme is tokens, not hard-coded
- All styling flows from design tokens (`data-theme`, `lib/theme.ts`, Tailwind). Only the Qcells Gradient theme ships, but adding a theme must not require touching components.

## 7. Comment out, don't delete
- Features paused for later (attachment UI, Documents admin tab, admin knowledge-graph button, message Trace) are commented out with an explanatory note and their tests `it.skip`-ed, so they can return without rewriting.

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
