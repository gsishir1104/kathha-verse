# Private beta workflow additions

## Where to find them

- **Appearance**, bottom-right: Light, Dark, or System. Saved in this browser for every role, including sign-in. Other devices keep their own choice.
- **Manuscript → Detailed chapter analysis**: sequential local-model passes over every section, then merge matching entity names/types and remap connections. Uses one daily request. The 8,000-character limit still applies. Large chapters take several minutes. All interpretations remain pending writer review. Different aliases may need manual merging; section-local analysis can miss long-range relationships.
- **Story Universe → Feedback on the graph**: beta readers select a node, or choose its existing outgoing connection, and submit categorized comments. Comments remain private to that reader and the owning writer and are pinned to the frozen snapshot. A newly released version rejects stale submissions.
- **Story Universe → What changed?**: compares confirmed entities by normalized name and type against the nearest earlier chapter. Readers can compare only their active released chapters, never later chapters or writer drafts. Not present means absent from that snapshot, not dead or removed from the fictional world.
- **Reader intelligence → Feedback to work through**: graph and inline comments grouped by category, filtered by New, Reviewed, or Addressed. Category counts are explicit grouping, not semantic AI agreement.
- **Manuscript → Saved versions & recovery**: every saved edit preserves the previous draft, including intent. Preview and restore an earlier version as a new draft. Existing releases are immutable. History begins when this feature was installed; old unsaved text cannot be recreated.

## Automatic local database backups

SQLite backups use the transaction-consistent SQLite backup API and are integrity-checked. They are made at service startup, before schema creation, and before a modifying API request when the previous backup is at least five minutes old. No idle timer is required. They live in `backend/backups/`. These copies include accounts, drafts, releases, and feedback; they are not served over HTTP or included in the source archive. Existing backups are retained. Copies on the same disk do not protect against loss of the computer; copy them to personal external storage if needed.

For whole-database recovery, stop the service. From backend, run:

```powershell
..\.venv\Scripts\python.exe recover_backup.py backups/<chosen-backup>.sqlite3 recovered-storylens.db
```

The utility validates the backup and writes a NEW database, refusing any existing output. Set DATABASE_URL to that recovered file before restarting. Keep the old database. Whole-database recovery restores the backup's point in time; use chapter history for individual draft recovery. PostgreSQL hosting and its operational backup setup remain outside the current local pilot.

## Validation

Automated tests use a unique temporary database selected before any application import. An autouse guard rejects a non-test engine before fixture cleanup. Coverage includes restore conflicts, released-content immutability, graph target validation, feedback ownership and status updates, no future-chapter comparisons, SQLite backup integrity, and detailed-analysis source coverage/link remapping. The frontend production build passed. Browser checks verified dark graph readability, selecting a node as comment target, and Chapter 2 comparison with Chapter 1. No test comments were posted into the user's real story.

Final validation: 23 tests passed. Live detailed extraction of the recovered 7,540-character chapter produced 11 entities and 2 questions in 279 seconds, with every retained evidence passage matching the source. Whole-database recovery into a separate file passed integrity checking and retained accounts and chapters. No live records were overwritten.
