# Storylens

**AI works through a server-side provider gateway.** Production uses the OpenAI
API; local development can use Ollama. See [LOCAL_AI.md](LOCAL_AI.md) for the
offline development option. Provider credentials never enter the browser.


A working first vertical slice of the AI story-testing platform: a writer saves
a chapter, reviews structured story interpretations, freezes a verified state,
invites a specific beta reader, releases the chapter, and sees that reader's
annotations and interview responses in basic analytics.

**AI supports real beta readers. No reader reactions or analytics are fabricated.**

## Run the local sample

The prepared Windows workspace includes installed dependencies and a built frontend.
Run `./start-demo.ps1` from this folder and open http://127.0.0.1:8000.
Choose **Explore sample workspace**. This uses the explicitly isolated
`backend/storylens.db` database, even if another DATABASE_URL is present in
your shell.

1. Open **The Last Light**, then choose **Analyze saved chapter**.
2. In **Story Universe → Review list**, confirm, correct, or reject every entity.
   Click an entity to inspect its evidence, reader visibility, and character POV.
   Review the questions below the graph. Check the reader-safety acknowledgment,
   then choose **Verify & freeze chapter state**.
3. Open **Beta readers**. Invite `beta@storylens.test`.
4. Use **View as → Beta reader** in the sample banner. Accept the invitation.
5. Switch back to **Writer**, open **Story workspace → Beta release**, select Jamie,
   and release the chapter.
6. Switch to **Beta reader**. Open the released chapter, select a passage, and leave
   structured feedback. Finish reading and answer a question. Continue the interview
   to see a follow-up based on the answer, and open **Reader Memory**.
7. Switch to **Writer → Reader intelligence** to inspect the actual responses,
   tension, emotion matching, and simple prediction phrase matching.

Sample accounts and role switching exist **only when `DEMO_MODE=true`**. The app
refuses to start if demo mode and `APP_ENV=production` are combined. The sample
extraction applies only to the exact bundled manuscript; edited or original text
uses the installed local AI model (within pilot limits), or the manual review path. A demo workspace is shared local
test data, not a private deployment for real beta readers.

## Fresh installation

Requires Python 3.12+ and Node 22. Docker is optional for PostgreSQL.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
cd frontend
npm ci
npm run build
cd ..
./start-demo.ps1
```

For ordinary accounts instead of the sample, set `DEMO_MODE=false` and start
Uvicorn from `backend/`. Use signup for Writer, Beta Reader, or Reader accounts.
Invitations are delivered to the matching account's **in-app inbox**; there is no
outbound email service in this slice.

## PostgreSQL and production deployment

The application is Next.js/React plus FastAPI and SQLAlchemy. `compose.yaml` runs
the Python service with PostgreSQL 16 and pgvector. The Next.js static export is
served by FastAPI, so UI and API share an origin and an HttpOnly session cookie.
No API key or database credential is shipped to the browser.

```text
Browser → Next.js static UI → FastAPI API → PostgreSQL
                                 ├─ writer-only analysis → structured LLM output
                                 └─ reader-safe interview → bounded reader context
```

1. Copy `.env.example` to `.env`. Set a strong URL-safe `POSTGRES_PASSWORD`.
2. Set `AI_PROVIDER=openai`, add your server-side `OPENAI_API_KEY`, and choose a
   structured-output model in `OPENAI_MODEL`. Never use a `NEXT_PUBLIC_` variable
   for this key. Set `AI_DAILY_LIMIT` and `AI_SHARED_DAILY_LIMIT` to control usage.
3. Run `docker compose up --build` and open http://127.0.0.1:8000.
4. For public access, run this container on a Python/container-capable host behind
   HTTPS. Set `APP_ENV=production`, `DEMO_MODE=false`, and `FRONTEND_ORIGINS` to the
   exact HTTPS origin. Use a managed PostgreSQL instance or durable volume and backups.
   The same-origin layout is intentional; do not deploy the UI and cookie API to
   unrelated domains without adapting the authentication design.

The built-in Sites host cannot execute this Python backend. No online deployment
has been made and no database/cloud resources have been purchased. The local
runtime uses persistent SQLite for development; PostgreSQL is the deployment
configuration, not a database that was silently provisioned.

Every AI feature uses the same production gateway: chapter and Story Universe
analysis, author-intent suggestions, beta-reader MCQs, continuity checks, reader
insights, spoiler-safe recaps, and the private Story Companion. Hosted requests
use schema-validated responses, are not stored by the model request, and record
only operational metadata (status, model, timing, and token counts) in the admin
AI log. Manuscript text and prompts are not written to that log.

## Data and access invariants

- `Chapter` is mutable, with optimistic revision checks. A save invalidates the
  current review state. Nothing silently overwrites concurrent manuscript edits.
- `Snapshot` stores the exact manuscript, title, author intent, and structured
  universe for one revision. Verified snapshots are immutable.
- Verification requires decisions for all entities, valid exact evidence, valid
  graph references, and explicit author confirmation of reader safety/questions.
- `Release` binds a chapter, an accepted invited reader, and an immutable snapshot.
  New draft edits never change a beta reader's old release. A new revision is tested
  with fresh readers in this MVP; replacing existing readers' releases is disabled.
- Every private read, feedback, question, answer, and memory operation rechecks
  reader identity, active release, and accepted invitation on the server.
- Reader projection excludes writer-only/rejected entities, unsafe knowledge, and
  edges to excluded entities. It does not return author intent or the full snapshot.
- Dynamic questions receive the safe projection, that released manuscript, and
  only this reader's authorized answers at or before the current chapter. Later
  answers are excluded even when the reader has access to later chapters.
- Annotations store code-point offsets and exact quotes against the released text.
- Submitted answers are immutable, preserving predictions even before a reveal.
  This is intentionally stricter than allowing edits until a reveal.
- Analytics aggregate by immutable snapshot/version and unique respondent. Prediction
  correctness is a visibly labeled **exact phrase match** that needs writer review,
  not inferred truth. Small sample counts are always displayed.
- Auth uses scrypt password hashes and hashed opaque server sessions; cookies are
  HttpOnly, SameSite=Strict, and Secure in production. Role and ownership checks are
  server-side. Origin checks and no-store API responses protect private state.

## AI behavior

The real adapter uses `OpenAI.responses.parse` with strict Pydantic output types.
It treats manuscripts and reader answers as untrusted data, requests chapter-local
evidence, stores no API-side response (`store=False`), and surfaces service failures.
It does not fall back to invented extraction for user manuscripts.

For direct local execution, set `OPENAI_API_KEY` in the shell before starting the
app (for example `$env:OPENAI_API_KEY = 'your-key'` in your own terminal). Do not
paste the key into chat or frontend code. The `.env` file is consumed by Docker
Compose; the local demo script deliberately does not read unrelated environment files.

Writer review is essential: an exact supporting quote does not prove that an AI
interpretation is correct. Character feelings remain labeled interpretations.
The reader question generator never receives later chapters or author-only canon,
but model wording still needs real evaluation before a wider launch.

References used for implementation:
- [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Next.js static exports](https://nextjs.org/docs/app/guides/static-exports)

## Verification

```powershell
cd backend
../.venv/Scripts/python.exe -m pytest -q
cd ../frontend
npm run typecheck
npm run build
```

The integration suite covers the whole vertical slice, anonymous access, role and
owner checks, uninvited readers, explicit writer review, invalid evidence, stale
reviews, immutable releases and answers, revoked access, private knowledge,
cross-chapter Reader Memory, and safe question-generator inputs.

## Current boundaries / next increments

This is an MVP implementation, not a production-hardened service. Live local LLM calls have been verified; PostgreSQL execution and Docker deployment
still need verification in the target environment. No Docker runtime is available here.

- AI calls are synchronous with timeouts. Add a durable analysis-job queue and
  shared rate limits before scaling. Current auth throttling is process-local.
- Local schema initialization uses SQLAlchemy `create_all`. The checked-in initial
  PostgreSQL schema is for deployment review; add versioned migrations for changes.
- pgvector extension and an optional memory-vector index are included. Embedding
  generation and semantic retrieval are not active; this slice uses exact SQL
  retrieval with reader/chapter boundaries.
- Graphs preserve chapter-local snapshots. The history view compares any available chapters and can display the latest approved entry per matching name/type through a selected chapter. It does not infer missing changes or resolve aliases across chapters automatically. Labeled connections are edited in the entity form.
- Beta profiles, private genre/specialty discovery and manuscript import are implemented. Email verification, password reset, outbound invitation emails, moderation and public publishing are not implemented. Public Readers see no drafts. Their optional interactive-reading
  preference is persisted, but theories/discussions/reveal comparison await publishing.
- Intent analytics cover emotion/tension plus structured trust, suspicion, clue, confusion and prediction targets. Chapter/version comparisons, prediction history and cited AI explanations are available. Prediction matching remains phrase-based and requires writer interpretation; it is not semantic correctness scoring or a controlled experiment.

See `ARCHITECTURE.md` for the schema and workflow map.

## Private workflow additions

See [Features and recovery](FEATURES_AND_RECOVERY.md) for dark/system appearance, detailed chapter analysis, graph comments and comparisons, feedback review statuses, saved draft recovery, and local database backups.

## Writer and Beta Reader studio

See [Writer and Beta Reader features](WRITER_BETA_FEATURES.md) for the current private-workflow additions, locations, validation and remaining limitations. Public Reader features remain deferred.

## Welcome emails

New registrations queue a role-specific Storylens welcome email. Sending remains disabled until a sender address and SMTP credentials are configured. See [Welcome email setup](WELCOME_EMAILS.md).
