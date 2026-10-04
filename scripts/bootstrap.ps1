# Bootstrap script for Windows
# Creates the virtual environment and installs all dependencies locally.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "=== Social Insights Bootstrap ===" -ForegroundColor Cyan

# Create venv if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    C:\Python312\python.exe -m venv .venv
}

$VenvPython = ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: venv python not found at $VenvPython" -ForegroundColor Red
    exit 1
}

$version = & $VenvPython --version
Write-Host "Using Python: $version"
$prefix = & $VenvPython -c "import sys; print(sys.prefix)"
Write-Host "sys.prefix: $prefix"

# Install dependencies
Write-Host "Installing runtime dependencies..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt

Write-Host "Installing dev dependencies..."
& $VenvPython -m pip install -r requirements-dev.txt

# Copy .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item .env.example .env
}

Write-Host ""
Write-Host "=== Bootstrap complete ===" -ForegroundColor Green
Write-Host "Activate the venv: .venv\Scripts\activate"
Write-Host "Run tests: .venv\Scripts\python.exe -m pytest"
Write-Host "Start server: .venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend"
