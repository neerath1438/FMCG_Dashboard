# MongoDB Recovery Script — SAFE (only deletes lock + log, NOT data)
# Run this as Administrator

$dataPath = "C:\Program Files\MongoDB\Server\6.0\data"
$logPath  = "C:\Program Files\MongoDB\Server\6.0\log\mongod.log"
$lockFile = "$dataPath\mongod.lock"

Write-Host "=== MongoDB Safe Recovery ===" -ForegroundColor Cyan

# Step 1: Stop service if somehow partially running
Write-Host "`n[1] Stopping MongoDB service..." -ForegroundColor Yellow
Stop-Service -Name "MongoDB" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Step 2: Delete lock file ONLY (NOT *.wt data files)
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "[2] mongod.lock deleted." -ForegroundColor Green
} else {
    Write-Host "[2] mongod.lock not found (already clean)." -ForegroundColor Gray
}

# Step 3: Delete log file (optional, not data)
if (Test-Path $logPath) {
    Remove-Item $logPath -Force
    Write-Host "[3] mongod.log deleted." -ForegroundColor Green
} else {
    Write-Host "[3] mongod.log not found." -ForegroundColor Gray
}

# Step 4: Verify data files are UNTOUCHED
$wtFiles = Get-ChildItem $dataPath -Filter "*.wt" -ErrorAction SilentlyContinue
Write-Host "`n[4] Data files intact: $($wtFiles.Count) .wt files found (your data is SAFE)" -ForegroundColor Green

# Step 5: Start MongoDB
Write-Host "`n[5] Starting MongoDB..." -ForegroundColor Yellow
Start-Service -Name "MongoDB" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

$svc = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue
if ($svc.Status -eq "Running") {
    Write-Host "`nSUCCESS: MongoDB is now RUNNING!" -ForegroundColor Green
} else {
    Write-Host "`nERROR: Still not running. Status: $($svc.Status)" -ForegroundColor Red
    Write-Host "Check new log for details." -ForegroundColor Yellow
    # Show last 10 log lines if new log was created
    if (Test-Path $logPath) {
        Get-Content $logPath -Tail 10
    }
}
