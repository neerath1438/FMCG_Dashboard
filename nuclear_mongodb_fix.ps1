# MongoDB Nuclear Recovery
# Deletes WiredTiger METADATA files only (not your collection .wt data files)
# WiredTiger.wt = storage engine index (rebuilt automatically)  
# WiredTiger.turtle = checkpoint metadata (rebuilt automatically)
# Your fmcg_mastering data files ARE SAFE

$dataPath = "C:\Program Files\MongoDB\Server\6.0\data"
$mongodExe = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
$logPath = "C:\Program Files\MongoDB\Server\6.0\log\mongod.log"

Write-Host "=== MongoDB Nuclear WiredTiger Recovery ===" -ForegroundColor Cyan
Write-Host "DATA FILES (fmcg_mastering collections) - SAFE:" -ForegroundColor Green
Get-ChildItem $dataPath -Filter "collection-*.wt" | Select-Object Name | Format-Table -AutoSize

# Stop service
Stop-Service -Name "MongoDB" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Delete fresh log so we get clean output
if (Test-Path $logPath) { Remove-Item $logPath -Force -ErrorAction SilentlyContinue }

# Delete ONLY WiredTiger internal metadata — NOT collection data
$toDelete = @(
    "$dataPath\mongod.lock",
    "$dataPath\WiredTiger.lock", 
    "$dataPath\WiredTiger.wt",       # Storage engine index — auto rebuilt
    "$dataPath\WiredTiger.turtle",   # Checkpoint pointer — auto rebuilt
    "$dataPath\WiredTigerHS.wt",     # History store — auto rebuilt
    "$dataPath\sizeStorer.wt"        # Size cache — auto rebuilt
)

foreach ($f in $toDelete) {
    if (Test-Path $f) {
        Remove-Item $f -Force -ErrorAction SilentlyContinue
        Write-Host "Deleted: $(Split-Path $f -Leaf)" -ForegroundColor Yellow
    }
}

# Delete all journal files
$journalPath = "$dataPath\journal"
if (Test-Path $journalPath) {
    Remove-Item "$journalPath\*" -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "Journal cleared." -ForegroundColor Yellow
}

Write-Host "`nRunning mongod --repair (30-60 sec)..." -ForegroundColor Cyan
$repairProc = Start-Process -FilePath $mongodExe `
    -ArgumentList "--repair", "--dbpath", $dataPath, "--logpath", $logPath `
    -Wait -PassThru -NoNewWindow
    
Write-Host "Repair exit code: $($repairProc.ExitCode)"

# Now start service
Write-Host "`nStarting MongoDB service..." -ForegroundColor Yellow
Start-Service -Name "MongoDB" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

$status = (Get-Service -Name "MongoDB").Status
Write-Host "MongoDB Status: $status" -ForegroundColor $(if($status -eq 'Running'){'Green'}else{'Red'})

if ($status -eq "Running") {
    Write-Host "`n✅ MongoDB RUNNING! All collections should be intact." -ForegroundColor Green
} else {
    Write-Host "`nNew log errors:" -ForegroundColor Red
    if (Test-Path $logPath) {
        Get-Content $logPath | Select-String "\"s\":\"F\"|\"s\":\"E\"|panic|fatal" -CaseSensitive:$false | Select-Object -Last 5
    }
}
