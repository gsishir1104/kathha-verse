# KathhaVerse
### AI-Powered Storytelling & Beta Reading Platform

KathhaVerse helps writers share chapters privately with beta readers, collect structured feedback, and explore AI-assisted story insights. Writers review AI interpretations before releasing chapters, while readers receive content and questions limited to their authorized chapter context.

**AI supports real beta readers and preserves the writer’s control over their story.**

## Live Website

**[Visit KathhaVerse](https://kathhaverse.org)**

Writers can create stories, review chapter analysis, and invite beta readers. Beta readers can create profiles, accept invitations, and provide structured feedback.

## Key Features

### Writer Workspace
- Create stories and write chapters with a rich-text manuscript editor.
- Track word counts and chapter verification status.
- Analyze characters, relationships, events, locations, clues, and other story elements.
- Confirm, correct, or reject AI interpretations before verifying chapter state.
- Explore interactive, chapter-specific Story Universe graphs.
- Discover beta readers by genre, feedback specialty, and availability.
- Invite selected readers and release verified chapters privately.

### Beta Reader Workspace
- Create a reading profile with interests, specialties, and availability.
- Manage invitations and access released chapters.
- Leave passage-specific annotations and structured feedback.
- Answer chapter-specific AI questions and follow-up questions.
- Preserve responses through Reader Memory.

### AI & Reader Intelligence
- Structured chapter analysis and continuity checks.
- Author-intent suggestions and reader insights.
- Chapter-bounded questions, recaps, and Story Companion interactions.
- Analytics comparing author intent with reader responses.
- Feedback organized by chapter revision and reader.

### Administration
- Account oversight and platform operations.
- AI request monitoring through operational metadata, including request status, model, timing, and token counts.

## Technology Stack

| Area | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript, CSS |
| Rich-text editing | Tiptap |
| Interactive graphs | React Flow |
| Interface icons | Lucide |
| Backend | Python, FastAPI, Uvicorn |
| Database | PostgreSQL; SQLite for local development |
| ORM & validation | SQLAlchemy, Pydantic |
| AI | OpenAI API; optional Ollama for local development |
| Testing | pytest, TypeScript type checking |
| Deployment | Render |
| Version control | Git, GitHub |

## Architecture

The Next.js frontend is exported as static assets and served by FastAPI. The interface and API share an origin, with server-managed session authentication.

```text
Next.js / React Interface
          |
      FastAPI API
          |
          +-- PostgreSQL
          |   Accounts, stories, chapter snapshots,
          |   invitations, feedback, and reader responses
          |
          +-- Server-Side AI Gateway
              OpenAI API / optional local Ollama
```

AI provider credentials remain on the server and are never included in browser code.

## Core Workflow

1. A writer creates a story and saves a chapter.
2. AI proposes structured story interpretations and reader questions.
3. The writer confirms, corrects, or rejects interpretations.
4. The writer verifies and freezes the chapter state.
5. An invited beta reader accepts the invitation.
6. The writer releases the verified chapter to that reader.
7. The reader submits annotations and interview responses.
8. The writer reviews feedback and reader-intelligence results.

## Access Control & Data Integrity

- Server-side role and ownership checks protect private resources.
- Passwords use scrypt hashing, and authentication uses opaque server sessions.
- Session cookies are HttpOnly, SameSite=Strict, and Secure in production.
- Verified snapshots preserve the manuscript and story state for a specific revision.
- Releases bind an authorized reader to an immutable chapter snapshot.
- Subsequent draft edits do not silently change an existing reader’s release.
- Reader-facing story data excludes writer-only and rejected interpretations.
- AI question context is restricted to the authorized chapter and eligible prior answers.
- Submitted answers remain immutable to preserve original reader responses.
- Revision checks help prevent accidental overwriting of concurrent manuscript edits.

## AI Implementation

AI features use a server-side provider gateway and Pydantic-validated structured outputs.

The application:
- Treats manuscripts and reader answers as untrusted input.
- Requests chapter-local evidence for story interpretations.
- Requires writer review before interpretations become verified story state.
- Surfaces provider failures instead of inventing analysis results.
- Sends hosted requests with `store=False`.
- Records operational metadata in the admin AI log, excluding manuscript text and prompts.

The `store=False` setting describes request configuration, rather than a blanket guarantee about provider retention.

See [Local AI Setup](LOCAL_AI.md) for the optional Ollama configuration.

## Testing

After installing the backend and frontend dependencies, run the following from the project root on Windows:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q

cd ../frontend
npm run typecheck
npm run build
```

The backend integration suite covers:
- Authentication, roles, and resource ownership.
- Invitation and chapter-release authorization.
- Mandatory writer verification.
- Invalid evidence and stale review states.
- Immutable snapshots and reader answers.
- Revoked reader access and private story knowledge.
- Cross-chapter Reader Memory boundaries.
- Restricted inputs to the reader-question generator.

## Deployment

KathhaVerse is deployed on **Render** and available at **[kathhaverse.org](https://kathhaverse.org)**.

The application uses PostgreSQL for deployment and supports SQLite for local development. AI credentials and database configuration are managed through server-side environment variables.

## Current Scope & Limitations

- KathhaVerse is an evolving MVP.
- AI interpretations can be incorrect and require writer review.
- Prediction matching uses exact phrases and requires writer interpretation; it is not semantic correctness scoring.
- Embedding generation and semantic retrieval are not active. Optional pgvector support is included in the database configuration, while the current reader-memory workflow uses SQL retrieval.
- AI calls are synchronous with timeouts; durable background processing is a future improvement.
- Public publishing and broader public-reader interactions remain outside the current private beta-reading workflow.
- Welcome email delivery requires a configured sender and SMTP credentials.

## Additional Documentation

- [Architecture](ARCHITECTURE.md)
- [Local AI Setup](LOCAL_AI.md)
- [Features and Recovery](FEATURES_AND_RECOVERY.md)
- [Writer and Beta Reader Features](WRITER_BETA_FEATURES.md)
- [Welcome Email Setup](WELCOME_EMAILS.md)

## Contributors

**Sishir Gottumukkala**  
Backend development, database design, AI integration, access controls, testing, and deployment.

**Akshaya Baitinti**  
Frontend development, responsive interfaces, reusable components, interactive story visualization, and API integration.
