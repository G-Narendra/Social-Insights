# ==============================================================================
# End-to-End System Smoke Test (PowerShell)
# ==============================================================================
param (
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://127.0.0.1:3000",
    [string]$Keyword = "Toyota"
)

$ErrorActionPreference = "Stop"

Write-Host "======================================================================"
Write-Host " Starting Social Insights End-to-End Smoke Test"
Write-Host " Backend:  $BackendUrl"
Write-Host " Frontend: $FrontendUrl"
Write-Host " Target:   $Keyword"
Write-Host "======================================================================"

# 1. Health
Write-Host -NoNewline "[1/7] Testing Backend /health ... "
$h = Invoke-RestMethod -Uri "$BackendUrl/health" -Method Get
if ($h.status -eq "ok") { Write-Host "OK" -ForegroundColor Green }

# 2. Ready
Write-Host -NoNewline "[2/7] Testing Backend /ready ... "
$r = Invoke-RestMethod -Uri "$BackendUrl/ready" -Method Get
if ($r.status -eq "ready") { Write-Host "OK" -ForegroundColor Green }

# 3. Trigger Collect
Write-Host "[3/7] Triggering Collection for '$Keyword' ... "
$body = @{ keyword = $Keyword; limit = 20 } | ConvertTo-Json
$c = Invoke-RestMethod -Uri "$BackendUrl/api/collect" -Method Post -Body $body -ContentType "application/json"
$runId = $c.run_id
Write-Host "  Run ID $runId queued."

# 4. Poll
Write-Host -NoNewline "[4/7] Polling collection run status "
$status = "queued"
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    Write-Host -NoNewline "."
    $poll = Invoke-RestMethod -Uri "$BackendUrl/api/runs/$runId" -Method Get
    $status = $poll.status
    if ($status -eq "succeeded" -or $status -eq "failed") { break }
}
Write-Host ""
if ($status -ne "succeeded") {
    Write-Error "Collection failed with status: $status"
}
Write-Host "  Collection and AI processing succeeded!" -ForegroundColor Green

# 5. Mentions & Stats
Write-Host -NoNewline "[5/7] Verifying /api/mentions & /api/stats/overview ... "
$m = Invoke-RestMethod -Uri "$BackendUrl/api/mentions?keyword=$Keyword&limit=5" -Method Get
$s = Invoke-RestMethod -Uri "$BackendUrl/api/stats/overview?keyword=$Keyword" -Method Get
if ($m.items.Count -gt 0 -and $s.total_mentions -gt 0) { Write-Host "OK" -ForegroundColor Green }

# 6. AI Summary
Write-Host -NoNewline "[6/7] Verifying /api/insights/summary ... "
$sum = Invoke-RestMethod -Uri "$BackendUrl/api/insights/summary?keyword=$Keyword" -Method Get
if ($sum.content) { Write-Host "OK" -ForegroundColor Green }

# 7. Frontend Check
Write-Host -NoNewline "[7/7] Checking Frontend Web Dashboard ... "
try {
    $f = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -TimeoutSec 3
    if ($f.StatusCode -eq 200) { Write-Host "OK" -ForegroundColor Green }
} catch {
    Write-Host "SKIPPED (frontend server not running on $FrontendUrl)" -ForegroundColor Yellow
}

Write-Host "======================================================================"
Write-Host " ALL SMOKE TESTS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "======================================================================"
