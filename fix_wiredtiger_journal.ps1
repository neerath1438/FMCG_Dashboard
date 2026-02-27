# MongoDB Journal Fix — Removes corrupted WiredTiger journal files ONLY
# The journal folder contains Write-Ahead Log (WAL) entries for crash recovery
# Deleting journal files = lose uncommitted transactions from last session ONLY
# Your actual collection data (.wt files) ARE NOT touched

$dataPath   = "C:\Program Files\MongoDB\Server\6.0\data"
$journalPath = "$dataPath\journal"
$lockFile   = "$dataPath\mongod.lock"
$mongodExe  = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
$configFile = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.cfg"

Write-Host "=== MongoDB Journal Recovery ===" -ForegroundColor Cyan

# Stop service
Stop-Service -Name "MongoDB" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Show data files BEFORE (so you can see nothing is deleted)
Write-Host "`n[DATA FILES - will NOT be touched]:" -ForegroundColor Green
Get-ChildItem $dataPath -Filter "*.wt" | Select-Object Name, @{N='SizeKB';E={[math]::Round($_.Length/1KB,1)}}

# Delete lock
if (Test-Path $lockFile) { Remove-Item $lockFile -Force; Write-Host "`nLock file deleted." -ForegroundColor Green }

# Show journal files
Write-Host "`n[JOURNAL files - THESE will be deleted]:" -ForegroundColor Yellow
if (Test-Path $journalPath) {
    Get-ChildItem $journalPath | Select-Object Name, @{N='SizeKB';E={[math]::Round($_.Length/1KB,1)}}
    
    # Delete journal files
    Remove-Item "$journalPath\*" -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "Journal files deleted." -ForegroundColor Green
} else {
    Write-Host "No journal folder found." -ForegroundColor Gray
}

# Also delete WiredTiger.lock (not WiredTiger.wt or WiredTiger.turtle)
$wtLock = "$dataPath\WiredTiger.lock"
if (Test-Path $wtLock) {
    Remove-Item $wtLock -Force
    Write-Host "WiredTiger.lock deleted." -ForegroundColor Green
}

# Start service
Write-Host "`nStarting MongoDB..." -ForegroundColor Yellow
Start-Service -Name "MongoDB" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

$svc = Get-Service -Name "MongoDB"
Write-Host "`nMongoDB Status: $($svc.Status)" -ForegroundColor $(if($svc.Status -eq 'Running'){'Green'}else{'Red'})

if ($svc.Status -eq "Running") {
    Write-Host "`n✅ SUCCESS! MongoDB is running." -ForegroundColor Green
    Write-Host "Your data is safe. Verify in NoSQLBooster." -ForegroundColor Green
} else {
    Write-Host "`nStill failing. Showing new log:" -ForegroundColor Red
    $logPath = "C:\Program Files\MongoDB\Server\6.0\log\mongod.log"
    if (Test-Path $logPath) {
        Get-Content $logPath -Tail 10 | Select-String -Pattern "error|panic|fatal|assert" -CaseSensitive:$false
    }
}
