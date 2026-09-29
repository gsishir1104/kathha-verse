# Operations implementation status

Implemented in this increment:
- Owner/support/moderator/technical server-configured staff roles and endpoint permission checks.
- Participant-owned support, access, report, appeal, copyright and privacy-request cases; replies, status changes, assignment API and view auditing. Staff cannot inspect cases outside their scope.
- Metadata-only story/chapter/snapshot inventory.
- Release permission diagnosis; reasoned invitation revocation which disables associated releases.
- Searchable, paginated combined admin/operations/security event history.
- HTTP denial/error event capture without request bodies, query strings or credentials.
- Local model-call status, elapsed time and reported token counts; reasoned local AI pause/resume.
- Database and local AI checks; recent local backup metadata.

Limits: these workflows do not complete the entire requested specification. Privacy cases are requests, not automatic exports/deletion. Copyright/report cases do not implement public-content publishing or takedowns. There is no exceptional manuscript-access grant, account recovery email flow, durable AI queue, automated retry, cost budget, scheduled retention, full signup/invitation lifecycle timestamping, or public analytics. Staff-role assignment remains deployment configuration. Audit storage is not cryptographically tamper-proof. Crash-interrupted model calls can remain marked running. Technical controls currently cover local Ollama calls only.

No new staff accounts have been granted access. Set STAFF_SUPPORT_IDS, STAFF_MODERATOR_IDS or STAFF_TECHNICAL_IDS to existing approved user IDs in the deployment environment; the owner remains ADMIN_USER_IDS. Do not configure the same user with multiple roles.
