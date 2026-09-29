# Current update

Real local AI extraction and reader follow-up have now passed live tests. The
automated suite now has 10 passing tests. See [LOCAL_AI.md](LOCAL_AI.md).
The historical record below describes the original pre-local-AI build.

# Validation record

## Passed

- Production Next.js static build and TypeScript checks.
- Six integration tests against an isolated SQLite test database, covering the
  working vertical slice and spoofed/unauthorized access paths.
- Browser walkthrough: sample sign-in → sample extraction → per-entity decisions
  → explicit safety verification → beta invitation → acceptance → writer release
  → reader shelf → exact-text inline annotation → completed reading → locked answer
  → Reader Memory → dynamic follow-up → writer analytics.
- The browser test submitted visibly labeled `UI test` responses, not real reader
  research. Its analytics showed one respondent, 80% tension against a 65% target,
  70% prediction confidence, and a matching prediction phrase, as expected.
- Responsive inspection at 390 × 844 CSS pixels: no horizontal document overflow.
- Verified that the local HTTP entrypoint returns 200 and the API initializes.

## Not verified here

- Live OpenAI requests: no API key supplied. The real adapter is implemented; the
  workflow test used the explicitly labeled deterministic sample extractor.
- PostgreSQL/pgvector or Docker execution: no Docker runtime or provisioned database
  available. The schema was compiled for the PostgreSQL dialect, and Compose,
  initial SQL, and the container build definition are included.
- Public hosting, HTTPS, external invitation delivery, load testing, and semantic
  spoiler evaluation with real manuscripts.

Two third-party deprecation warnings are emitted by the installed FastAPI/Starlette
test client. They do not fail the tests; no application test failures remain.


## Recovery incident during local-AI regression testing

The old test import order loaded the live database engine before the test database
variable was assigned. Fixture cleanup removed the live tables. The database was
copied before further recovery work. The complete 7,540-character active chapter
was recovered to `../Chronos-Chapter-one-recovered.txt` and its length and checksum
matched the still-open browser editor. Account and other records are not restored.
Tests now select a unique temporary database in conftest before collection and
assert its path before any fixture cleanup. Earlier passing tests must not be
interpreted as evidence of data preservation.
