# MongoDB Repair Script — Recovers corrupted WiredTiger storage engine
# Does NOT delete your data/collections
# Must run as Administrator

$mongodExe  = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
$configFile = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.cfg"
$dataPath   = "C:\Program Files\MongoDB\Server\6.0\data"
$logPath    = "C:\Program Files\MongoDB\Server\6.0\log\mongod.log"
$lockFile   = "$dataPath\mongod.lock"

Write-Host "=== MongoDB WiredTiger Repair ===" -ForegroundColor Cyan
Write-Host "Your data files (.wt) will NOT be deleted" -ForegroundColor Green

# Ensure service is stopped
Stop-Service -Name "MongoDB" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Delete lock file (safe)
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "Lock file deleted." -ForegroundColor Green
}

# Delete old log so we can read fresh output
if (Test-Path $logPath) {
    Remove-Item $logPath -Force
}

Write-Host "`nRunning: mongod --repair ..." -ForegroundColor Yellow
Write-Host "(This may take 1-3 minutes. Please wait...)" -ForegroundColor Yellow

# Run repair — this recovers WiredTiger without data loss
$proc = Start-Process -FilePath $mongodExe `
    -ArgumentList "--repair", "--config", $configFile `
    -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$dataPath\repair_output.txt" -RedirectStandardError "$dataPath\repair_error.txt"

Write-Host "`nRepair process exit code: $($proc.ExitCode)" -ForegroundColor Cyan

# Show repair output
if (Test-Path "$dataPath\repair_output.txt") {
    Write-Host "`n--- Repair Output ---"
    Get-Content "$dataPath\repair_output.txt" | Select-Object -Last 20
}

if ($proc.ExitCode -eq 0) {
    Write-Host "`nRepair SUCCESS. Starting MongoDB service..." -ForegroundColor Green
    Start-Service -Name "MongoDB" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    $svc = Get-Service -Name "MongoDB"
    Write-Host "MongoDB Service Status: $($svc.Status)" -ForegroundColor Green
} else {
    Write-Host "`nRepair may have issues. Check log:" -ForegroundColor Red
    if (Test-Path $logPath) { Get-Content $logPath -Tail 15 }
}
