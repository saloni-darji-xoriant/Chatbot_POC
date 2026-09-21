# Mockup Spec — Qcells L1 Assistant (all screens)

Give this file to a designer, a design tool, or an AI (for example: "Read `mockup-spec.md` and generate a clickable HTML mockup of every screen, desktop and mobile, in one file"). It describes the app as it is built today, so the mockups match the product. Where a feature is paused it says so.

## 0. How to use this spec

**Suggested prompt**

> Using `docs/mockup-spec.md`, produce high-fidelity mockups for every screen in section 4, at desktop (1280×800) and mobile (375×812). Include every state listed for each screen. Use only the design tokens in section 2, the components in section 3 and the sample content in section 5. Output one self-contained HTML file with a screen switcher, or one image per screen and state named with the screen ID (for example `S05-chat-conversation-desktop.png`).

**Deliverables checklist:** 19 screens/states groups (S01–S19), each at desktop and mobile; a components sheet; a tokens sheet.

## 1. Product in one paragraph
Hanwha Qcells L1 Assistant is a support chatbot for solar installers. They ask a question and get a cited answer, often with a diagram and suggested follow-ups. They can attach files, export the chat as PDF, revisit history, and reach a live specialist (L2). Admins review quality metrics and feedback and teach the assistant with corrections.

Roles: **Installer** (chat, history, help) and **Admin** (everything an installer has, plus the Admin area).

## 2. Design system: "Qcells Gradient" theme

### 2.1 Colour tokens
| Token | Value | Use |
|---|---|---|
| `--bg` / `--surface` | `#FFFFFF` | Page and card background |
| `--surface-2` | `#F5F8FC` | Subtle fills, user bubble, login/onboarding page background |
| `--text` | `#101B36` | Primary text |
| `--text-dim` | `#66708C` | Secondary text, hints |
| `--border` | `#E7EBF3` | 1px borders, dividers |
| `--accent` | `#1E6FEB` | Links, focus, active nav, primary actions |
| `--accent-ink` | `#FFFFFF` | Text on accent or gradient |
| `--accent-soft` | `#1E6FEB` at 7% | Active nav and selected fills |
| `--accent-2` | `#22C3A6` | Success, "grounded", positive |
| `--accent-2-soft` | `#22C3A6` at 10% | Success fills |
| `--danger` | `#D0413B` | Errors, thumbs-down, escalated |
| `--danger-soft` | `#D0413B` at 8% | Error fills |
| `--grad` | `linear-gradient(120deg, #22C3A6, #1E6FEB)` | Logo tile, primary buttons, welcome headline text, top bars |

### 2.2 Typography
| Role | Font | Notes |
|---|---|---|
| Display | Poppins (600) | Headings, page titles, KPI numbers |
| Body | Inter | Everything else |
| Mono | IBM Plex Mono | Filenames, timestamps, document names |

Sizes: xs 10.5, sm 11.5, base 12.5, md 13.5 (default body), lg 15, xl 18, 2xl 22, 3xl 24, 4xl 32 px. Heading letter-spacing -0.01em.

### 2.3 Shape, elevation, spacing
- Radius: small 8, medium 14, large 20, pill 999 px.
- Card shadow: `0 20px 44px -18px rgba(30,111,235,.18)`; composer float shadow `0 6px 20px -10px rgba(0,0,0,.15)`.
- Sidebar width 232 px. Chat column max width 620 px, centred. Page gutters 16 px on mobile, 24 px from 640 px up.
- Breakpoint: below **900 px** the sidebar becomes a slide-in drawer opened from a top-bar hamburger.

### 2.4 Tone
Clean, light, professional; lots of white; gradient used sparingly for brand moments (logo, primary button, welcome headline, top accent line). Friendly, plain-language copy.

## 3. Shared components (draw once, reuse)

| ID | Component | Description |
|---|---|---|
| C1 | **Logo tile** | Rounded square, gradient fill, white bold "Q" (38 px on login, 12 px radius 14 on onboarding, 26 px avatar in chat). |
| C2 | **Button** | Variants: solid (accent), gradient (brand gradient), outline, ghost. Full-width option. Disabled at 40% opacity. Radius 14. |
| C3 | **Text input** | Optional label above, 1px border, radius 14, focus border accent. Error text below in danger colour. |
| C4 | **Card** | White, 1px border, radius 20, card shadow. |
| C5 | **Badge** | Small pill: positive (green tint), negative (red tint), neutral (grey). |
| C6 | **Chip** | Pill. Variants: *suggestion* (empty-state prompts), *quick reply / follow-up* (accent outline, blue text), *citation* (mono document name, grey fill, doc icon). |
| C7 | **Message bubble, user** | Right-aligned, `--surface-2` fill, max width 420, radius 14. May have attachment chips above it. |
| C8 | **Message, assistant** | Left; 26 px gradient "Q" avatar; plain text (no bubble) up to the 620 px column. Below the text, in order: optional AI note, image cards, citation chips, "Suggested follow-ups" group, action row. |
| C9 | **AI note** | Small italic dim line: "AI-generated general guidance - not from the Qcells knowledge base. Please verify before acting." or "Written by AI from the sources below." |
| C10 | **Image card** | Diagram thumbnail (16:9, max 560 px wide, border, radius 14). Footer bar: caption on the left (truncated), **Enlarge** and **Download** text links in accent on the right. Cursor: zoom-in. |
| C11 | **Follow-up group** | Tiny uppercase label "SUGGESTED FOLLOW-UPS" above a wrapped row of quick-reply chips. Shown only under the latest assistant message. |
| C12 | **Action row** | 26 px icon buttons: thumbs up (green tint when active), thumbs down (red tint when active). No Trace button (paused). |
| C13 | **Thumbs-down reason** | Inline input "What was wrong? (optional)" plus a small Save button, appears under the action row. |
| C14 | **Composer** | Floating pill: paperclip button, text input "Ask a question...", circular gradient send button. Above it, when files are pending: attachment chips (icon, filename, size, ×), an "Attaching..." spinner chip, or a red error text. |
| C15 | **Attachment chip** | Rounded rectangle chip: document or image icon, filename, size (e.g. `66B`, `12KB`), × to remove (composer only). |
| C16 | **Live process trace** | While the assistant is working: a small card listing four agent steps (Router, Retrieval/RAG, Response, Grounding), each with a pending dot, spinner (active) or check (done). |
| C17 | **Error banner** | Red-tint strip with message and icon. |
| C18 | **Sidebar** | See S05 layout: logo + title, gradient "+ New question" button, nav (AI Support, History, Help, Admin for admins), "RECENT" list of five conversation titles (truncated), profile card at the bottom (avatar initial, name, region, chevron), "Log out" link. Active nav item: `--accent-soft` fill, accent text. |
| C19 | **Profile card** | Rounded card, initial avatar (gradient), name bold, region dim. |
| C20 | **Image viewer overlay** | Full-screen dark overlay (85% black). Top toolbar: caption on the left; on the right **−**, zoom percentage (mono), **+**, **Fit**, **Download**, **New tab**, **Close** as white-on-translucent buttons. Centre: the diagram on white, fit to screen, scrollable when zoomed. |
| C21 | **KPI card** | Card with a 34 px tinted icon square, big Poppins number, dim label. |
| C22 | **Progress ring** | Circular ring with the percentage in the centre and a label below; green ring for grounding, blue for satisfaction. |
| C23 | **Star rating** | Five outlined stars, filled gradient/gold when chosen, hover preview. |
| C24 | **Bar and activity chart** | Feedback breakdown: a two-segment horizontal bar (green positive, red negative) with counts. Activity: 7 vertical bars, weekday labels, values on top. |
| C25 | **Sort select** | Native select styled with 1px border, radius 14: "Sort by date: Newest first / Oldest first". |
| C26 | **Day heading** | Uppercase 11.5 px semibold dim label ("TODAY", "YESTERDAY", "FRI, SEP 18, 2026"). |
| C27 | **Top accent line** | 4 px gradient strip across the top of exported PDFs (also useful on marketing-style headers). |

## 4. Screens

Each screen lists: route, who sees it, purpose, layout, content, states, mobile behaviour. Draw desktop and mobile for all.

### S01 Login: `/login`
- **Who:** anyone signed out. **Purpose:** authenticate.
- **Layout:** centred 360 px card on a `--surface-2` page. Logo tile (C1, 38 px) and title "Qcells L1 Assistant", subtitle "Sign in to get help with L1 support queries". Fields: Work email (`you@qcells.com`), Password. Full-width solid button "Continue". Divider "or". Outline button with shield icon "Continue with Company SSO". Footer text "Trouble signing in? Contact your site administrator." Below it a small grey box listing demo accounts (installer and admin).
- **States:** default; submitting (button "Signing in...", disabled); error (red line "Invalid email or password" under the fields); SSO with empty email (email field focused).
- **Mobile:** card fills width with 16 px margins.

### S02 Onboarding: `/onboarding`
- **Who:** first sign-in only. **Purpose:** explain what the user can do.
- **Layout:** centred 560 px column. 48 px logo tile, headline "Welcome, **Jordan**" (first name in gradient text), subtitle "Here's what the Qcells L1 Assistant can do for you as an installer." Three large cards, each with a green check circle, bold title and dim description:
  1. Ask L1 support questions
  2. See exactly where answers come from
  3. Get escalated when needed
  Then a full-width gradient button "Get started".
- **Variant:** admin capabilities ("Everything installers get", "Monitor quality in real time", "Manage feedback & documents"), subtitle "as an admin".

### S03 App shell (desktop): applies to S04 to S12
- Left fixed sidebar (C18, 232 px), right content area that scrolls. Chat pages keep the composer pinned at the bottom.

### S03b App shell (mobile): applies to S04 to S12
- Top bar (56 px): hamburger left, logo and "Qcells L1 Assistant" centre. The sidebar is a drawer sliding in from the left over a dark scrim; tapping the scrim or a nav item closes it. Draw both closed and open.

### S04 Chat: empty state: `/chat`
- **Layout:** centred column. Headline (gradient text, 32 px Poppins) "Hi Jordan, how can I help?". Paragraph: "Ask about inverter faults, panel output, warranty claims, firmware, or installation steps — I'll answer from the Qcells knowledge base. You can also attach a site photo or document for me to reference." Three suggestion chips (C6): "My inverter is showing an error code", "What's the capacity of the Q.HOME ESS battery?", "Two panels are showing near-zero output after a hailstorm". Composer (C14) pinned at the bottom.
- **States:** default; composer with a pending attachment chip; composer with an upload error ("File exceeds the 5MB limit").

### S05 Chat: conversation with answer, image and follow-ups: `/chat`
- **Layout:** column at the top-right has an outline button **Export PDF** (download icon). Then the conversation:
  - User bubble: "My inverter is showing an error code".
  - Assistant message (C8): answer paragraph, image card (C10, "Power-cycle procedure timeline"), two citation chips (`QVOLT-Inverter-Manual.pdf`, `Inverter-Troubleshooting.md`), follow-ups group (C11) with three chips: "What does each inverter error code mean?", "When should I escalate an inverter fault to L2?", "How do I push a firmware update to the inverter?", action row (thumbs).
  - Above the composer, right-aligned link "Mark as resolved".
- **States:** thumbs-up active; thumbs-down active with reason input (C13); export button in "Preparing PDF..." state; export error text "Couldn't export the chat. Please try again."

### S06 Chat: streaming / thinking: `/chat`
- User bubble, then the live process trace card (C16) with the first two steps done, the third active, the fourth pending. Composer disabled (60% opacity).

### S07 Chat: AI-written general guidance: `/chat`
- User: "my rooftop setup is misbehaving again today". Assistant message with the AI note (C9, "AI-generated general guidance - not from the Qcells knowledge base. Please verify before acting."), a warm reply with three numbered clarifying questions and a safety paragraph, no citations, follow-ups: "What do the inverter error codes mean?", "How do I diagnose low panel output?", "How do I escalate this to L2?", "Connect me to a live specialist".
- **Variant:** reworded knowledge-base answer with the note "Written by AI from the sources below.", citations, image and follow-ups.

### S08 Chat: image viewer: overlay on `/chat`
- Overlay (C20) over a dimmed chat. Draw: fit (100%), zoomed (200% with scrolling and a partly visible image), and the mobile version where the toolbar wraps onto two rows.

### S09 Chat: message with attachment: `/chat`
- User bubble with an attachment chip above it (`site-notes.txt`, `66B`). Assistant reply that quotes the file: "From your attached file "site-notes.txt": ..." with a citation chip "Your attachment: site-notes.txt".

### S10 Handoff to a specialist: `/chat` (status handoff)
- Replaces the conversation view. Card layout: icon, title "Connecting you to a specialist", subtitle "This conversation has been escalated from L1 to L2 support." Green-tint notice "You're being connected to a live specialist. Average wait time is 3-5 minutes." (queue position 2). Heading "Contact support" with four contact cards: Installer Hotline `1-800-555-0142` (phone), Emergency / Safety `1-800-555-0199` (alert triangle, red tint), Email Support `installer-support@qcells.com` (mail), Warranty Claims `warranty@qcells.com` (shield). Link "Back to chat".

### S11 End-of-conversation rating: `/chat`
- Card in the conversation column: "How did we do?", "Rate this conversation before you go.", five stars, thumbs up/down toggle, textarea "Anything we should improve?", buttons Submit (gradient) and Dismiss (ghost). Second state: "Thanks for the feedback!" and "It helps us improve the assistant for every installer."

### S12 History: `/history`
- **Layout:** title "History", subtitle "Every conversation you've had with the assistant." Row with a search input "Search conversations..." and the sort select (C25). Then day groups: heading (C26) and stacked cards. Each card: bold title, status badge (In progress neutral, Resolved green, Escalated red), one-line preview in dim text, mono timestamp with zone (`Sep 20, 2026, 11:26 AM GMT+5:30`).
- **States:** default newest first (TODAY, YESTERDAY, dated groups); oldest first; loading ("Loading history..."); empty ("You haven't started a conversation yet."); no search results ("No conversations match your search.").
- **Mobile:** search and sort stack vertically.

### S13 Help Center: `/help`
- Title "Help Center" and short subtitle. Section "Popular questions" with suggestion chips (click opens chat). Section "Contact support" with the four contact cards from S10. Footer line in dim text.

### S14 Admin: Dashboard: `/admin/dashboard` (admin only)
- Admin top tabs (Dashboard active, Feedback) with a refresh icon button on the right. Row of four KPI cards (Conversations 42, Total messages 186, Unique users 27, Messages today 5). Two progress rings (Grounding rate 92.3%, Satisfaction 84%). Card "Feedback breakdown" with the two-segment bar. Card "Last 7 days" with the activity chart.
- **States:** loading ("Loading dashboard..."). **Mobile:** KPIs 2×2, cards stacked.

### S15 Admin: Feedback list: `/admin/feedback`
- Filter tabs or chips (All, Negative, Positive). List of feedback cards: quoted user query, optional comment, sentiment badge, stars, user name and mono timestamp. Negative items have a **Add correction** button.
- **States:** empty ("No feedback in this category yet."); loading.

### S16 Admin: Feedback item, correction form: `/admin/feedback` (expanded)
- Expanded card with a "Correct answer" textarea ("What should the assistant have said?"), an optional source filename input, and buttons Save correction (gradient, disabled until text is entered) and Cancel. After saving, a green-tint block "Correction applied" showing the text and filename in mono.

### S17 Admin: Documents: `/admin/documents` *(paused: tab hidden in the UI)*
- Draw as an optional appendix labelled "Paused". Table or list of source documents: filename (mono), category, type badge (PDF/MD), updated date, delete icon; button "Add document".

### S18 Export PDF: the downloaded file
- A4 portrait. 4 px gradient strip across the top edge. Title (conversation title, 18 pt bold navy). Meta lines: "Exported by Jordan Reyes on 20 Sep 2026, 11:26 AM IST", "Conversation status: active | Messages: 4", "Started: ... | Times shown in Asia/Kolkata". Blue rule. Then each message: sender name (bold, blue for the user, navy for the assistant), timestamp (small grey), body text, full-width diagram with an italic "Figure: ..." caption, "Sources" list (small grey). Thin divider between messages. Footer: "Hanwha Qcells L1 Assistant - chat transcript" left, "Page 1 of 2" right. Draw two pages.

### S19 Error and empty states (one sheet)
- Chat error banner: "Could not reach the assistant. Check your connection and try again."
- 404-style "Conversation not found".
- Session-expired redirect to login.
- Offline/loading skeletons for history, dashboard and feedback.

## 5. Sample content (use verbatim)

**Users:** Jordan Reyes (installer, Southwest Region); Morgan Lee (installer, Northeast Region); Casey Kim (admin, HQ - Irvine, CA).

**Recent conversations (sidebar and history):**
1. My inverter is showing an error code, In progress, today 11:26 AM
2. What's the difference between the Q.PEAK and Q.TRON panels?, Resolved, today 9:24 AM
3. My panels stopped producing after the storm, Resolved, yesterday 11:24 AM
4. Where do I file a warranty claim?, Resolved, Fri Sep 18
5. Firmware update stuck at 40%, Resolved, Thu Sep 17
6. I smell something burning near the inverter, Escalated, Tue Sep 15

**Answer text (S05):** "Most Q.VOLT inverter fault codes clear after a full power cycle: switch off the AC disconnect, wait 60 seconds, then switch off the DC disconnect for another 60 seconds before restoring both (AC first, then DC). If the same code returns within 10 minutes, treat it as hardware-related — log the exact code, the inverter serial number, and a timestamp, then escalate to L2 rather than repeating the cycle."

**AI general guidance (S07):** "I'm sorry you're running into this - let's narrow it down together. A few quick things that will help me point you the right way: 1. What is the inverter display or the monitoring app showing right now — any error code, or a red/orange light? 2. When did it start, and did anything change just before (a storm, a power cut, a router or firmware update)? 3. Is the whole system affected, or only some panels or strings? While you check, please stay safe: don't open the DC junction box, touch wiring or work on the roof. If you notice a burning smell, smoke, sparks or crackling, switch off the AC disconnect if it's safe to do so and call the emergency line straight away."

**Diagrams available for the image cards** (1200×675, navy/blue/teal palette, titled, captioned "Qcells L1 Assistant | illustrative diagram"): power-cycle procedure, inverter error codes, rapid shutdown layout, installation sequence, battery clearances, escalation flow, grounding and bonding, panel troubleshooting flow, monitoring connectivity, shading clearance, PV system components. Files: `backend/app/static/kb-images/*.png`. Use them as image assets in mockups.

**Dashboard numbers:** Conversations 42, Total messages 186, Unique users 27, Messages today 5; Grounding 92.3%, Satisfaction 84%; feedback 21 positive / 4 negative; last 7 days: Mon 12, Tue 18, Wed 9, Thu 22, Fri 30, Sat 14, Sun 8.

**Feedback samples:** "Where do I find the Q.HOME serial number?" (negative, comment "Missed the label location", 2 stars, Morgan Lee); "What torque spec should I use for racking bolts?" (positive, 4 stars).

## 6. Interaction notes (for clickable mockups)
- Suggestion chips and follow-up chips send that text as a new message.
- Clicking an image, or **Enlarge**, opens S08; Esc or **Close** returns. **Download** saves a PNG. Zoom range 100% to 400%.
- **Export PDF** downloads a PDF (S18); the button shows "Preparing PDF..." meanwhile.
- The paperclip opens a file picker; chosen files appear as chips above the composer.
- Typing "Connect me to a live specialist" leads to S10. Nothing else leads there.
- "Mark as resolved" leads to S11.
- Thumbs-down reveals the reason input (C13).
- History cards open the conversation in S05. The sort select re-orders the list instantly.
- Admin nav item appears only for admins.

## 7. Accessibility and responsive rules to reflect
- Every icon-only control has a text label in the design notes (aria-label): Thumbs up, Thumbs down, Attach a file, Send message, Export chat as PDF, Zoom in, Zoom out, Reset zoom, Download image, Close image viewer.
- Colour is never the only signal (badges have text; thumbs have pressed states).
- Minimum touch target 36 px on mobile; the viewer toolbar wraps rather than shrinking.
- Contrast: body text on white at least 4.5:1 (navy `#101B36`; dim text `#66708C` for secondary only).

## 8. Out of scope for mockups
Trace panel per message (paused), knowledge-graph view (paused), Documents tab (paused, appendix only), dark mode (only the Gradient light theme ships; other themes swap tokens later).

## Revision log
| Date | Change |
|---|---|
| 2026-09-21 | Initial mockup spec covering S01 to S19. |
