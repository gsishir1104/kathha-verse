$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    throw 'Install Python dependencies first. See README.md.'
}
if (-not (Test-Path -LiteralPath 'frontend/out/index.html')) {
    Push-Location -LiteralPath 'frontend'
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
}
$env:AI_PROVIDER = 'ollama'
$env:OLLAMA_MODEL = 'gemma3:4b'
$env:DEMO_MODE = 'true'
$env:APP_ENV = 'development'
$env:DATABASE_URL = 'sqlite:///./storylens.db'
$env:FRONTEND_DIST = '../frontend/out'
# Private Google download; never print credential values or load them in the frontend.
$oauthPath = Join-Path $PSScriptRoot 'google-oauth.json'
if (Test-Path -LiteralPath $oauthPath) {
    try { $oauth = (Get-Content -LiteralPath $oauthPath -Raw -Encoding UTF8 | ConvertFrom-Json).web }
    catch { throw 'The private Google credential file is not valid JSON.' }
    if (-not $oauth.client_id -or -not $oauth.client_secret -or
        $oauth.project_id -ne 'kathha-verse' -or
        'http://127.0.0.1:8000/api/auth/google/callback' -notin $oauth.redirect_uris) {
        throw 'The Google credential file must belong to Kathha Verse and include the local callback.'
    }
    $env:GOOGLE_CLIENT_ID = $oauth.client_id
    $env:GOOGLE_CLIENT_SECRET = $oauth.client_secret
    $env:PUBLIC_APP_URL = 'http://127.0.0.1:8000'
    $env:SUPPORT_EMAIL = 'kathhaverse.support@gmail.com'
}
# Local owner IDs are stored separately from source code.
$adminPath = Join-Path $PSScriptRoot 'admin-users.json'
if (Test-Path -LiteralPath $adminPath) {
    $env:ADMIN_USER_IDS = ((Get-Content -LiteralPath $adminPath -Raw | ConvertFrom-Json).user_ids -join ',')
}
Set-Location -LiteralPath 'backend'
& ../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
