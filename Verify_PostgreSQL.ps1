$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Install and start Docker Desktop first, or follow the manual PostgreSQL steps in README.md.'
}

docker compose up -d --wait db
if ($LASTEXITCODE -ne 0) { throw 'Database startup failed. Make sure Docker Desktop is running and port 5432 is free.' }

Set-Location (Join-Path $PSScriptRoot 'backend')
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
}
$projectPython = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $projectPython -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $projectPython verify_postgres.py
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL verification failed. Check the error and backend/.env database settings.' }
