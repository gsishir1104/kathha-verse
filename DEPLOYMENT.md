# Publish Kathha Verse

The repository includes a Render Blueprint in `render.yaml`. It creates the
Docker web application and a PostgreSQL database, enables production security,
and asks for the OpenAI key without saving that key in Git.

## Accounts required

1. Create an OpenAI API account, enable API billing, and create a project API
   key. A ChatGPT subscription does not automatically provide API billing.
2. Create a Render account and connect the GitHub repository containing this
   project.

## Deploy

1. Push this project to a private GitHub repository.
2. In Render, choose **New → Blueprint** and select that repository.
3. Render reads `render.yaml`. When prompted for `OPENAI_API_KEY`, paste the
   project API key into Render's secret field. Never add it to this repository.
4. Create the Blueprint and wait for both `kathha-verse-db` and
   `kathha-verse` to become available.
5. Open `https://<your-render-host>/api/health`. Confirm that it reports
   `"ai_connected": true`, `"ai_provider": "openai"`, and
   `"database": "postgresql"`.
6. Open the main URL, create a writer account, save a short test chapter, and
   run **Analyze full chapter**. Confirm the resulting Story Universe before
   inviting readers.

Render and OpenAI can change their available plans and prices. Review the price
shown by each service before creating resources. AI requests are limited by
`AI_DAILY_LIMIT` and `AI_SHARED_DAILY_LIMIT`; adjust them in the Render service
environment when needed.
