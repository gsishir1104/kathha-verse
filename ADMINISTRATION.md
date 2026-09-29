# Administration

Sign in with a designated owner account and choose **Administration** in the sidebar.

Features: paginated account search, display-name and role editing, suspension/reactivation, sign-out on all devices, site totals, welcome-email queue totals, configured provider status, and the latest 100 administrator changes (actor, time, target, reason, before/after values).

Set ADMIN_USER_IDS to a comma-separated list of existing account IDs. No account is an administrator by default, and signup cannot grant administrator rights. Local start-demo.ps1 optionally loads user_ids from the ignored admin-users.json file. Docker passes ADMIN_USER_IDS from its environment. Startup creates the two additive tables; database/008_administration.sql is also supplied for managed migrations.

Suspension preserves data and blocks existing sessions and new password/Google sessions. Saving an account change revokes all its sessions. Writers with existing stories cannot be changed to another role, and administrator roles/suspension cannot be changed from this panel. Email identifiers and credentials cannot be edited here. No permanent account deletion or manuscript browsing is included.

Email/provider configuration indicators are not live availability checks. Welcome email delivery still requires sender setup. The activity list covers administrator actions, not all reader/writer activity.

User activity: the Accounts table shows the last successful authenticated request time. Activity opens a paginated per-account history of successful mutations and sign-ins, unexpired session count, and last sign-in. Request bodies, query strings, credentials, and manuscript text are never captured. This tracks actions, not before/after content differences. Tracking begins on deployment; first-seen is the beginning of tracking, not registration date. Existing accounts show unknown values until observed. Read-only requests update presence without adding history entries. Last active does not imply online presence.

Notifications: select Notify next to accounts, compose a title/message, then confirm sending. Up to 100 selected accounts per send; selections persist across account searches. Users have a paginated Notifications inbox with unread counts and mark-read controls. The inbox refreshes every 30 seconds while the page is visible. Notifications are in-app only; no email is sent. Recipient ownership is enforced server-side and sends are audited.
Relationships: search writer, beta reader, or story. Unique invited and accepted counterpart counts avoid double-counting multiple stories. Expand each story invitation for current accessible chapter completion, saved progress, answer counts, and inline feedback counts. Inactive releases remain labeled. Completion refers only to currently accessible releases, not an entire manuscript. Counts are based on current stored invitations, not a historical selection ledger.

Account detail dashboards: click an account name or Open account. The directory is hidden while inspecting one account. Overview shows timestamps, sessions and invitation totals; writer progress lists stories, word counts, revisions and chapter states; beta-reader/writer tabs scope pairings to the selected account and show chapter progress bars. Notifications can target the selected account directly. Back to All accounts restores the directory search/page. Counts do not imply a manuscript is finished.
