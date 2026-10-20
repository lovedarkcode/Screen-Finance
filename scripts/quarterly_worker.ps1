param([switch]$Stop)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectPath 'backend'
$statePath = Join-Path $backendPath '.quarterly-worker.json'
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
        $workerChildren = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($workerProcess.Id)" | Where-Object { $_.CommandLine -like '*app.workers.quarterly_results_worker*' }
        foreach ($child in $workerChildren) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
        Stop-Process -Id $workerProcess.Id -ErrorAction SilentlyContinue
        Write-Output 'Quarterly-results worker stopped.'
    }
    else { Write-Output 'No matching quarterly-results worker is running.' }
    exit 0
}
if ($workerProcess) { Write-Output "Quarterly-results worker already running: $($workerProcess.Id)"; exit 0 }
$pythonPath = Join-Path $backendPath 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = Join-Path $backendPath '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create the backend Python virtual environment first.' }
$env:DEBUG = 'false'
$env:PYTHONDONTWRITEBYTECODE = '1'
$started = Start-Process -FilePath $pythonPath -ArgumentList @('-B', '-m', 'app.workers.quarterly_results_worker', '--bootstrap') -WorkingDirectory $backendPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $backendPath '.quarterly-worker.stdout.log') -RedirectStandardError (Join-Path $backendPath '.quarterly-worker.stderr.log') -PassThru
@{ process_id = $started.Id; started_at = $started.StartTime.ToUniversalTime().ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
Write-Output "Quarterly-results worker started: $($started.Id). Yahoo discovery batches enabled; then polls every 15 minutes."

