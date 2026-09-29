# Integrated product screens

These screens extend the existing Kathha Verse application and use persisted application data.

- Story Universe: React Flow graph controls, character POV inspector, chapter selection, writer corrections, and a server-filtered beta preview of verified snapshots.
- Manuscript editor: Tiptap connected to the existing plain-text autosave and revision model. Formatting beyond manuscript text is intentionally not stored.
- Question Studio: editable questions, approval/rejection, ordering, checkpoint timing, and frequency persisted in the snapshot. Final writer verification remains mandatory. Existing snapshots retain their prior verification behavior.
- Releases: existing author-selected beta access and verification gate remain in force. Public publication is a separate explicit writer action; no existing draft is automatically published.
- Intelligence Lab: snapshot/revision filters and charts backed by human answers and observations. Predictability remains exact phrase matching; it is not an automatic assessment of whether a theory is correct. Different beta groups are not a controlled experiment.
- Public reading: authenticated discovery, genre/search filters, genre-based recommendations, library from saved chapters, focus mode, reading typography/themes, bookmarks, progress, completed-chapter maps and evidence-checked local-AI recaps. Optional private theories, chapter discussions, and side-by-side reveal comparisons. Later saved reading progress locks earlier theories. Public chapter discussions are user-authored and can contain user-posted spoilers; they are not automatically semantically moderated.
- Safety Center: permission failures, story-state validation failures, invitation-action failures, and failed local AI jobs; severity/status updates and audited investigation notes. Evidence excludes manuscript and private-feedback contents.
- Writer overview: review backlog, accepted beta readers, completed reads, and recent inline feedback.

Limits: email invitation delivery is not configured; invitation-action errors are distinct from email delivery tracking. AI recaps are labeled interpretations, and evidence checks do not guarantee semantic correctness. Existing confirmed beta graph entities remain visible per the established beta-release contract; private character knowledge is filtered. Public publishing is local until deployment. Staff access remains deployment-configured. Granular semantic question-safety review remains the writer's responsibility in addition to server-side evidence and checkpoint validation.

Validation: 60-test backend suite passed during integration; focused product and studio checks passed after subsequent changes. Frontend production build and browser checks cover the editor, graph/POV inspector, question studio, discovery and reading controls. UI validation used an isolated sample database, not the user's manuscripts. Dependency audit reported zero vulnerabilities after the compatible PostCSS override.

Guest account-access support: login page includes a no-sign-in request form. Guests save a request ID and private access code to read/reply; only the code hash is stored. Requests appear in staff Cases, marked unverified, and never establish account ownership. Email confirmations are not sent. Startup creates the separate guest_support_cases table; existing account tickets are unchanged. Existing public-request throttling applies.

Writer-beta messaging uses accepted invitations as private story-scoped conversations. Server denies unrelated users, staff and revoked/pending connections. Messages persist; newest 100 load initially with older-message paging. Presence expires after 65 seconds, heartbeats every 25 seconds while visible; message polling every 5 seconds. Directory uses real listed profiles and ratings; favorites are browser-local per story. No invented project counts, feedback samples or turnaround commitments. AI ideation chat remains a separate future feature.

Beta discovery now uses a literary ink-and-gold design with a bundled original SVG reading-room illustration, real directory totals, themed cards, profile section tabs and an invitation confirmation dialog. Invitations continue to use the existing server endpoint; no chapter is released by the design change.

Site-wide literary refresh: shared midnight/gold tokens, serif headings, warm light theme, dashboard hero and working quick links, updated editor/reader/universe/analytics/profile surfaces, matching sign-in artwork. New visitors default to dark; saved theme and public reading preferences remain respected. Author cover artwork takes priority over the decorative fallback. This visual update does not introduce a community feed or fabricated metrics.

Four supplied screenshot images are bundled under frontend/public/artwork and used as decorative backgrounds on welcome, dashboard, discovery, invitations, reader headers, profile-card covers and fallback book jackets. CSS overlays preserve text contrast; custom author covers retain priority.

## Story Companion and support (September 2026)
- Writer-only bottom-left companion/support drawer, with story and focus-chapter selectors.
- Private per-story discussion history; recent four exchanges are provided to the model. The newest 50 exchanges are shown in the UI.
- Bounded lexical retrieval: up to six 1,200-character draft excerpts plus up to 6,000 characters of confirmed entities from current-revision verified snapshots. This is not exhaustive whole-book continuity analysis.
- References use server-supplied source IDs; invalid IDs reject the response and refund the request. AI prose remains an interpretation, not verified canon.
- Shared local-AI limits remain five requests per user/day and thirty platform-wide/day, resetting at midnight UTC; single API worker required by the existing inference gate.
- Support adds urgency, optional private PNG/JPEG screenshots up to 2 MB, scoped staff assignment and metadata-only durable email notifications. Existing ticket replies and in-app notices remain available with email disabled.
- SMTP uses the existing MAIL_ENABLED / SMTP_* / MAIL_FROM_ADDRESS / PUBLIC_APP_URL configuration. Local mail is not configured; no real email delivery has been claimed or tested. Once enabled, queued notifications are processed by the mail worker. Ambiguous delivery is marked uncertain instead of automatically duplicated.
- Email links require sign-in and the existing case permission checks. Companion history is never attached to tickets or made available in staff endpoints.

## Longer chapter analysis
Local AI accepts chapters up to 40,000 characters (comfortably covering typical 3,000-word chapters). Standard analysis automatically covers contiguous sections of up to 6,000 characters and merges cited results; detailed analysis retains its 2,200-character sections. All passes remain within one daily analysis allowance. Ancillary chapter AI uses an adaptive model context window. Automated tests cover a 3,000-word input, exact section coverage including the ending, and the size-limit rejection. Long real-model runs are slower on CPU; no claim of a full-length live performance benchmark.
`nChapter AI now enforces an explicit 4,000-word limit, alongside the 40,000-character safety limit. Tests cover complete 4,000-word processing and rejection at 4,001 words.
