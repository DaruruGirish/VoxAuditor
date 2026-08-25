# =============================================================================
# start_services.ps1 — Vox Auditor Microservices Launcher
# Starts all 5 services in separate PowerShell windows using the shared venv.
# Run from the havells/ root directory.
# =============================================================================
param()

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe  = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$SharedDir  = Join-Path $ScriptDir "shared"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Vox Auditor — Microservices Launcher" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# ── Validate venv ─────────────────────────────────────────────────────────────
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python venv not found at: $PythonExe" -ForegroundColor Red
    Write-Host "Please run: cd backend && python -m venv .venv && .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# ── Shared directory setup ────────────────────────────────────────────────────
if (-not (Test-Path $SharedDir)) {
    New-Item -ItemType Directory -Path $SharedDir | Out-Null
    Write-Host "[Setup] Created shared/ directory" -ForegroundColor Yellow
}

$ReviewsSrc = Join-Path $ScriptDir "backend\reviews.json"
$ReviewsDst = Join-Path $SharedDir "reviews.json"
if (-not (Test-Path $ReviewsDst)) {
    if (Test-Path $ReviewsSrc) {
        Copy-Item $ReviewsSrc $ReviewsDst
        Write-Host "[Setup] Copied reviews.json → shared/" -ForegroundColor Yellow
    } else {
        Write-Host "WARNING: reviews.json not found in backend/. Vector index will fail." -ForegroundColor Yellow
    }
}

# ── Kill anything already on our ports ───────────────────────────────────────
$ports = 8000, 8001, 8002, 8003, 8004
foreach ($port in $ports) {
    $procId = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
    if ($procId) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "[Cleanup] Killed existing process on port $port" -ForegroundColor DarkYellow
    }
}
Start-Sleep -Milliseconds 500

# ── Service definitions ───────────────────────────────────────────────────────
$services = @(
    [ordered]@{ Name="review-store";  Dir="services\review_store";  Port=8001 },
    [ordered]@{ Name="vector-search"; Dir="services\vector_search"; Port=8002 },
    [ordered]@{ Name="analytics";     Dir="services\analytics";     Port=8003 },
    [ordered]@{ Name="qa-agent";      Dir="services\qa_agent";      Port=8004 },
    [ordered]@{ Name="gateway";       Dir="services\gateway";       Port=8000 }
)

# ── Launch each service in a new window ──────────────────────────────────────
foreach ($svc in $services) {
    $svcDir = Join-Path $ScriptDir $svc.Dir
    $title  = "Vox [$($svc.Name)] :$($svc.Port)"
    $cmd    = "& '$PythonExe' main.py"

    Write-Host "[Start] $($svc.Name) on port $($svc.Port)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList `
        "-NoExit",
        "-Command",
        "`$host.UI.RawUI.WindowTitle = '$title'; cd '$svcDir'; $cmd"
    Start-Sleep -Milliseconds 800   # stagger starts
}

# ── Wait for startup (vector-search needs time to load embeddings) ────────────
Write-Host ""
Write-Host "Waiting 20s for services to fully start (embedding model loads on first run)..." -ForegroundColor Cyan
for ($i = 20; $i -gt 0; $i--) {
    Write-Host -NoNewline "`r  $i seconds remaining...  "
    Start-Sleep -Seconds 1
}
Write-Host ""

# ── Health checks ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Health Checks ===" -ForegroundColor Cyan
$allOk = $true
foreach ($svc in $services) {
    $url = "http://localhost:$($svc.Port)/health"
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        $body = $resp.Content | ConvertFrom-Json
        $status = if ($body.status -eq "ok") { "✅ OK" } else { "⚠️  $($body.status)" }
        Write-Host "  $status   $($svc.Name) ($url)" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ FAIL  $($svc.Name) ($url)" -ForegroundColor Red
        $allOk = $false
    }
}

# ── Gateway fan-out status ────────────────────────────────────────────────────
Write-Host ""
if ($allOk) {
    Write-Host "All services healthy!" -ForegroundColor Green
} else {
    Write-Host "Some services failed to start. Check the individual service windows." -ForegroundColor Red
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Frontend : http://localhost:5173" -ForegroundColor White
Write-Host "  Gateway  : http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs : http://localhost:8000/docs" -ForegroundColor White
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to close this launcher (services keep running in their windows)." -ForegroundColor DarkGray
