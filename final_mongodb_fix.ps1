# Final MongoDB repair — uses config file to avoid path-with-spaces issue
$mongodExe  = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
$configFile = "C:\Program Files\MongoDB\Server\6.0\bin\mongod.cfg"
$logPath    = "C:\Program Files\MongoDB\Server\6.0\log\mongod.log"
$dataPath   = "C:\Program Files\MongoDB\Server\6.0\data"

Write-Host "=== Final MongoDB Repair (using --config) ===" -ForegroundColor Cyan

Stop-Service -Name "MongoDB" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Clear old log
if (Test-Path $logPath) { Remove-Item $logPath -Force -ErrorAction SilentlyContinue }

# Delete lock files one more time
@("$dataPath\mongod.lock", "$dataPath\WiredTiger.lock") | ForEach-Object {
    if (Test-Path $_) { Remove-Item $_ -Force -ErrorAction SilentlyContinue; Write-Host "Deleted: $(Split-Path $_ -Leaf)" }
}

Write-Host "`nRunning --repair with config (please wait 30-60s)..." -ForegroundColor Yellow

# Use & with proper quoting for paths with spaces
& $mongodExe --repair --config $configFile

Write-Host "`nRepair complete. Starting service..." -ForegroundColor Green
Start-Service -Name "MongoDB" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

$status = (Get-Service -Name "MongoDB").Status
Write-Host "MongoDB Status: $status" -ForegroundColor $(if($status -eq 'Running'){'Green'}else{'Red'})

if ($status -ne "Running") {
    Write-Host "`n--- New log tail ---" -ForegroundColor Yellow
    if (Test-Path $logPath) { Get-Content $logPath -Tail 15 }
}
