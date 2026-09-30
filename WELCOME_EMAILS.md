# Kathha Verse email setup

The public brand is Kathha Verse. The proposed Gmail addresses below are not created or verified yet. Confirm ownership before enabling mail.

# Kathha Verse welcome emails

New registrations queue one welcome message in the same transaction as the account. Signing in, switching sample accounts, and duplicate registration attempts do not queue another welcome. Existing accounts are not backfilled.

Messages use the display name **Kathha Verse**, the configured sender address, and the subject **Welcome to Kathha Verse**. Both HTML and plain-text versions include role-specific guidance and an Open Kathha Verse link. They contain no passwords, manuscripts or private feedback. A welcome email does not verify ownership of an email address.

## Enable real delivery

1. Obtain a sender address on a domain you control, such as `hello@your-domain`. The example is not a registered Kathha Verse address.
2. Configure that domain with your email provider and complete its sender/domain verification requirements.
3. Set the server variables in `.env.example`: `MAIL_FROM_ADDRESS`, `PUBLIC_APP_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`, `SMTP_USERNAME`, and `SMTP_PASSWORD`.
4. Use `starttls` with port 587 or `ssl` with port 465, according to your provider. Cleartext SMTP is not supported.
5. Set `MAIL_ENABLED=true` and restart the application. Pending welcomes from registrations made since this feature was installed will then be sent. Review the queue before enabling delivery if those registrations were only for testing.

Docker Compose reads these variables from the root `.env`. For direct Python execution, supply them in the server process environment; the application does not automatically load `.env`. Keep credentials out of frontend code and source control.

## Delivery behavior

The database outbox survives restarts. A background worker processes it without holding up registration. Failed sends with an explicit SMTP rejection retry up to five times with backoff. The `sent` state means the provider accepted the message, not that it reached the inbox. Bounce tracking is not implemented.

Interrupted sends or lost connections have uncertain outcomes. They become `uncertain` for operator review rather than automatically risking duplicate welcomes. Check provider logs before resetting those records to `pending`. Failed configuration leaves pending records queued and logs only an error class; passwords and recipient/message content are not logged.

Sending is disabled by default. Tests use a temporary database and mock delivery; no real email has been sent as part of implementation. Real inbox delivery must be tested after a sender and provider are configured.

## Selected setup: Gmail for the pilot

No Gmail accounts have been created or verified yet. Desired addresses, subject to availability:
- kathhaverse.hello@gmail.com for automated welcome messages
- kathhaverse.support@gmail.com for replies and customer support

Complete both account signups yourself where Google requests personal details, passwords, verification, or acceptance of terms. Enable two-step verification on the welcome account and create an app password if Google makes that option available. Do not share the app password in chat or commit it to source control.

Configure private server environment values:
- SMTP_HOST=smtp.gmail.com
- SMTP_PORT=587
- SMTP_SECURITY=starttls
- SMTP_USERNAME and MAIL_FROM_ADDRESS: the confirmed welcome Gmail address
- SMTP_PASSWORD: the welcome account's app password, not its regular password
- SUPPORT_EMAIL: the confirmed support Gmail address (sets Reply-To)
- PUBLIC_APP_URL: the actual website URL, not localhost when sending to other people
- MAIL_ENABLED=true only once setup is complete, then restart the server

Replies arrive in the support inbox. This is not a helpdesk or automatic support responder. Gmail has sending limits and may restrict delivery, so it is intended only for a small pilot. For Resend, use `smtp.resend.com`, username `resend`, and a domain-restricted sending API key as `SMTP_PASSWORD`. Kathha Verse recognizes those credentials and uses Resend's HTTPS API so hosted platforms do not depend on outbound SMTP ports.

## Google sign-in

In Google Cloud, create/select a project, configure the Google Auth Platform branding/audience and a Web application OAuth client. Request only openid, email, profile. Add test users while the app is in testing. Before public launch, complete Google's applicable publishing requirements.

Configure GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, PUBLIC_APP_URL privately on the server. The exact authorized redirect URI is PUBLIC_APP_URL + /api/auth/google/callback. For this local app it is http://127.0.0.1:8000/api/auth/google/callback. Use HTTPS for a public site. Gmail SMTP credentials and Google OAuth credentials are different; neither is entered by Kathha Verse users.

Restart the backend after configuration. The frontend checks /api/auth/google/status and enables Continue with Google only when configuration is present. Presence of configuration is not proof the Google Cloud settings are correct: complete a real sign-in before launch.

New Google users choose a role and receive one queued welcome. Returning users keep their existing role. Accounts are identified by Google's stable subject, not by a changeable email. Existing password accounts are not silently merged: those users must keep signing in with their existing password. A dedicated authenticated account-linking flow is not implemented yet.

Google login uses browser-bound, ten-minute, single-use state and PKCE. Identity is fetched from Google's HTTPS userinfo endpoint using the server-exchanged access token; tokens are not stored. Database migration 007_google_login.sql adds identity and temporary flow tables (local startup also creates missing tables).

Official setup: https://developers.google.com/identity/protocols/oauth2/web-server
App passwords: https://support.google.com/mail/answer/185833
