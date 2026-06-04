$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv")) {
    Write-Host "Missing .venv. Run .\scripts\setup.ps1 first."
    exit 1
}

$env:PYTHONPATH = (Get-Location).Path
& ".\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

