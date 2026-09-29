# Free local AI pilot

Storylens now supports actual AI extraction and dynamic reader questions through
the installed Ollama `gemma3:4b` model. Users do not need an OpenAI account or API
key. The model runs on the host computer; the AI feature does not send manuscripts
to OpenAI or another remote model provider.

## Use it

Keep Ollama running, open Storylens, save your chapter, and choose **Analyze saved
chapter**. Save current edits before refreshing the interface. Local analysis can
take a few minutes. The original sample manuscript retains its clearly labeled
sample extraction; other chapters use the real local model.

- Maximum 8,000 characters per chapter. Longer chapters are rejected, never silently
  truncated. Split them into smaller chapters or use manual review.
- Maximum 5 successful AI requests per account per UTC day, shared between analysis
  and follow-ups. The pilot also permits 30 total requests per UTC day.
- One model request at a time. A busy request gets a retry message, not an unbounded queue.
- Model failures refund the persisted usage reservation. Usage survives API restarts.
- Compact analysis: asks for up to 3 important entities and 1 question. This is an initial
  overview, not an exhaustive inventory of a long manuscript.
- Exact evidence is validated against the manuscript. Unsupported items are omitted;
  if no verifiable entities/questions remain, analysis fails explicitly.
- All extracted entities and knowledge begin **writer-only** and **pending**. Review
  them, correct mistakes, and explicitly enable reader visibility before verification.
  The UI does not present the local adapter's placeholder confidence as a probability.
- Generated questions are reviewed by the writer before release. Later follow-ups
  receive only the released chapter, reader-safe entities, and that reader's bounded
  prior answers. Revocation is checked again after generation.

## Configuration

```text
AI_PROVIDER=ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma3:4b
```

`start-demo.ps1` selects the local provider and installed model. The live background
service was restarted with those settings while retaining `backend/storylens.db`.
Setting `AI_PROVIDER=openai` restores the optional original paid provider, which
requires an operator-supplied key. Users never supply provider credentials.

## Deployment boundary

This makes AI free of per-request API charges; it does not provide free public
hosting. The current site remains local. This computer and Ollama must stay on.
For a public pilot, host the model privately beside the API, disable sample accounts,
enable HTTPS and PostgreSQL, and keep the Ollama endpoint off the public internet.
The pilot's concurrency/usage admission control assumes **one API worker**. A
multi-worker deployment needs a distributed gate and atomic shared quota admission.

## Validation

- Live synthetic chapter extraction succeeded in approximately 71 seconds.
- Live reader follow-up succeeded in approximately 12 seconds.
- Thirteen automated tests cover, including evidence filtering, private defaults,
  schema compatibility, persisted quotas, failure refunds, concurrency, and the
  existing vertical-slice spoiler/access checks.
- Production frontend build passed. Real manuscripts still need writer review;
  a small model can miss details, duplicate entities, or misinterpret character beliefs.

Implementation follows [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

## Citation reliability fix

The model now cites numbered source passages instead of reproducing quotations.
The server resolves valid IDs to exact manuscript slices, preserving Unicode punctuation.
Invalid citations are omitted; missing entity or question citations fail the request.
A valid citation is not proof that the interpretation is correct: writer review remains required.
Local requests allow up to ten minutes on slower hardware.

The recovered 7,540-character chapter passed live extraction and exact-evidence validation: 3 entities, 1 question, approximately 120 seconds. See VALIDATION.md for the separate database recovery incident.

## Author Intent suggestions

Choose Fill with AI on Author Intent to draft all five fields from the saved chapter. It uses one shared free request. Suggestions are private, editable, clearable and undoable, and only Save intent persists them. Cleared numerical targets remain unset. Saving uses the existing revision check and requires fresh verification before release. A live local test on the recovered chapter returned all five fields successfully; 14 isolated backend tests and the frontend production build passed.
