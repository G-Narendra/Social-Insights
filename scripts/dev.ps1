# Social Insights — Local Development Orchestrator
# Automatically frees ports, launches backend & frontend with zero conflicts.

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Social Insights — Local Dev Server Launcher    " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$WorkspaceRoot = (Get-Item $PSScriptRoot).Parent.FullName
$VenvPython = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found at $VenvPython. Run scripts/bootstrap.ps1 first."
    exit 1
}

# Function to safely kill any process holding a specific port
function Clear-Port([int]$Port) {
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $pidToKill = $conn.OwningProcess
            if ($pidToKill -gt 0 -and $pidToKill -ne $PID) {
                Write-Host "Freeing occupied port $Port (Killing PID: $pidToKill)..." -ForegroundColor Yellow
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Milliseconds 500
    }
}

Write-Host "`n[1/3] Ensuring ports 8000 and 3000 are clean..." -ForegroundColor Gray
Clear-Port 8000
Clear-Port 3000

Write-Host "`n[2/3] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$BackendProc = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $WorkspaceRoot `
    -PassThru

# Wait for backend health check
$maxRetries = 15
$ready = $false
for ($i = 0; $i -lt $maxRetries; $i++) {
    Start-Sleep -Seconds 1
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($res.status -eq "ok") {
            $ready = $true
            break
        }
    } catch {}
}

if ($ready) {
    Write-Host "Backend is healthy and listening on http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "Backend is still initializing..." -ForegroundColor Yellow
}

Write-Host "`n[3/3] Launching Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
Set-Location (Join-Path $WorkspaceRoot "frontend")

try {
    Write-Host "`nDashboard ready! Opening http://localhost:3000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop both backend and frontend.`n" -ForegroundColor DarkGray
    npm run dev
} finally {
    Write-Host "`nShutting down backend process (PID: $($BackendProc.Id))..." -ForegroundColor Yellow
    Stop-Process -Id $BackendProc.Id -Force -ErrorAction SilentlyContinue
    Clear-Port 8000
    Clear-Port 3000
    Write-Host "Clean shutdown complete." -ForegroundColor Green
}
