param([switch]$Stop)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectPath 'backend'
$statePath = Join-Path $backendPath '.screener-worker.json'
$workerProcess = $null
if (Test-Path -LiteralPath $statePath) {
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    $candidate = Get-Process -Id $state.process_id -ErrorAction SilentlyContinue
    if ($candidate -and $candidate.StartTime.ToUniversalTime().ToString('o') -eq $state.started_at) {
        $workerProcess = $candidate
    }
}
if ($Stop) {
    if ($workerProcess) {
        # A Windows venv redirector can spawn a second Python process. Stop only
        # children carrying this worker module, then its verified parent process.
        $workerChildren = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($workerProcess.Id)" | Where-Object { $_.CommandLine -like '*app.workers.stock_sync_worker*' }
        foreach ($child in $workerChildren) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
        Stop-Process -Id $workerProcess.Id -ErrorAction SilentlyContinue
        Write-Output 'Screener worker stopped.'
    }
    else { Write-Output 'No matching screener-results worker is running.' }
    exit 0
}
if ($workerProcess) { Write-Output "Screener worker already running: $($workerProcess.Id)"; exit 0 }
$pythonPath = Join-Path $backendPath 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = Join-Path $backendPath '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create the backend Python virtual environment first.' }
$env:DEBUG = 'false'
$env:PYTHONDONTWRITEBYTECODE = '1'
$started = Start-Process -FilePath $pythonPath -ArgumentList @('-B', '-m', 'app.workers.stock_sync_worker') -WorkingDirectory $backendPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $backendPath '.screener-worker.stdout.log') -RedirectStandardError (Join-Path $backendPath '.screener-worker.stderr.log') -PassThru
@{ process_id = $started.Id; started_at = $started.StartTime.ToUniversalTime().ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
Write-Output "Screener worker started: $($started.Id). Exchange-wide financial refresh enabled; progress is saved after each listing."

