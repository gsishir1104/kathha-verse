# Writer and Beta Reader features

Implemented in the private local pilot. Normal Reader/public publishing features are deferred.

## Writer workspace

- Manuscript autosave after a typing pause, revision history and conflict detection. Manual Save remains available. Switching chapters is disabled while changes are unsaved.
- Story settings: title, description, genre, tags, content information, uploaded cover, private workflow stage, book/daily word goals and recent writing activity. The final private stage is “ready to publish”; it does not publish anything.
- TXT, Markdown and DOCX import with chapter preview. Confirmed imports append draft chapters rather than replacing existing manuscripts. Limits: 4 MB upload, 100 detected chapters, 120,000 characters per chapter.
- Expanded Story Universe: mysteries, open/resolved threads, character status, goals/conflicts, story time, timeline ordering, directed labeled connections and relationship strength.
- Character knowledge can reference a subject or secret. Writers can mark a belief false. That truth assessment is withheld from beta readers; evidence and reader visibility remain separately reviewable.
- Merge duplicate entities within an unverified chapter review. The retained summary stays; knowledge and connections combine and require review again.
- AI can suggest richer story-state details with exact source citations. New suggestions create a pending review, including when the source snapshot was verified.
- AI can suggest questions from verified reader-safe facts and suggest reading checkpoints from approved clue/reveal passages. The writer edits and verifies the new review before releasing it.
- AI-assisted continuity review across approved chapter states. Concerns cite the compared passages and remain interpretations, not automatic corrections.
- Chapter graph comparisons, searchable character/secret/thread history and timeline views. “Known universe” carries the latest approved entry per matching entity name/type through the selected chapter, with its original chapter identified. Matching does not infer changes, reconcile aliases or replace the saved snapshots.
- Expanded private author intent: trust, suspicion, clue, confusion, prediction and mystery-difficulty targets; proposed reveal chapter; scene-specific reaction notes. AI can suggest targets and a cited scene, and the writer can edit/remove them.

## Beta Reader workspace

- Optional discoverable profile with biography, preferred genres, feedback specialties and availability. Writers can search listed profiles and invite a selected person. The directory does not expose email addresses or reading responses.
- Bookmarks at selected passages and partial reading progress; completed reading remains a separate action.
- Structured observations for beliefs, predictions, trust, suspicion, clues, confusion, emotions and mystery difficulty, with strength, confidence, reasoning and optional exact chapter evidence.
- Observation history is append-only and joins the reader’s chapter-bounded memory used for follow-up interviews. Other readers’ answers and author intent do not enter that context.
- Overall chapter feedback and overall/final manuscript feedback on released material.
- Ongoing interviews can add further questions after earlier follow-ups are answered, up to five follow-ups per release and subject to free AI limits.
- For a writer-approved reading checkpoint, the server withholds later manuscript text, later questions and the chapter graph until the checkpoint is answered. Direct attempts to answer a locked question, bookmark later text or complete the chapter are blocked.
- All confirmed entities remain visible to the selected beta reader after the chapter checkpoints, while private knowledge/goals/conflicts and future chapters remain unavailable.

## Writer intelligence

- Structured intent-versus-experience comparisons use the latest matching observation per reader and frozen chapter version. Unanswered metrics remain unmeasured.
- Chapter/version response groups support revision comparisons with fresh beta readers. Existing readers keep their original frozen release and answers.
- Prediction/suspicion history shows matching percentages, confidence, changes between measured chapters, each reader’s earliest matching observation, and final observations before an intended reveal chapter.
- Matching uses a phrase in the latest observation of that type with strength at least 50. It is not proof that a theory is correct. Pre-reveal here means chapter order, and chapter groups may contain different people.
- Reader explanations and cited passages are available beside increases in suspicion. They suggest possible reasons; they do not prove a clue caused a change.
- AI can group and explain real reader observations with validated references to those observations. Writers can inspect the original human responses.
- Writers can rate a contributing beta reader’s helpfulness. Listed profiles show the average and number of writer ratings.

## Validation and boundaries

- 35 automated backend checks passed against isolated temporary databases, covering the original vertical slice and new import, profile, privacy, merge, checkpoint, memory and AI citation paths.
- Production frontend build and type checking passed.
- Browser checks passed for autosave, story settings, author targets, advanced entity editing, profile opt-in, released graphs, observations, overall feedback and Reader Memory in dark mode, using a separate database and browser context.
- A live request to the free local model produced a valid intent draft with two targets and one cited scene reaction.
- The live database passed its integrity check and retained its five accounts, two stories, three chapters and two releases. A verified backup was made before additive schema initialization.
- PostgreSQL DDL for the new tables is in `database/005_writer_beta_studio.sql`; runtime checks used the local SQLite pilot. PostgreSQL deployment has not been exercised here.

## Practical limits

The local AI still supports chapters up to 8,000 characters, five requests per account per day and 30 shared requests per day. Detailed analysis and multi-checkpoint suggestions may take several minutes. Continuity review is bounded to 40 confirmed entries and a bounded input size. Evidence citations establish where an interpretation came from; they do not establish that the interpretation is correct.

Graph history matches entity names and types. Semantic entity resolution, semantic prediction scoring, durable background analysis jobs, and production-scale hosting remain further work. The current workflow uses explicit analysis actions rather than automatically sending every autosaved change to AI.
