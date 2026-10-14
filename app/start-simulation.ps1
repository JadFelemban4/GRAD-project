# Start the 3D replay lab on this machine. Read-only: no vehicle connection,
# no ECU command path, nothing written to disk but the usual review log.
#
#   powershell -ExecutionPolicy Bypass -File app\start-simulation.ps1
#   powershell -ExecutionPolicy Bypass -File app\start-simulation.ps1 -Python C:\Python312\python.exe
param(
    [ValidateRange(1, 65535)][int]$Port = 8000,
    [switch]$SkipVendor,
    [string]$Python
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Fail before probing Python or starting the server if localhost cannot bind
# the requested port. The listener is released before uvicorn starts.
$listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $Port)
try {
    $listener.Start()
}
catch {
    throw "Local port $Port is unavailable on 127.0.0.1: $($_.Exception.Message)"
}
finally {
    if ($listener -and $listener.Server.IsBound) { $listener.Stop() }
}

if (-not (Test-Path 'app\static\vendor\three\three.module.js')) {
    if ($SkipVendor) {
        throw 'Three.js is not vendored and -SkipVendor was passed. Run: cd app; npm install; npm run vendor'
    }
    Write-Host 'Three.js is not vendored yet. Copying it from node_modules...'
    if (-not (Test-Path 'app\node_modules\three')) {
        Push-Location app
        npm install
        $code = $LASTEXITCODE
        Pop-Location
        if ($code -ne 0) { throw "npm install failed (exit $code). The lab cannot render without Three.js." }
    }
    Push-Location app
    npm run vendor
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { throw "npm run vendor failed (exit $code)." }
    # Serving a page whose renderer is missing looks like a broken app, not a
    # failed install, so stop here rather than starting the server.
    if (-not (Test-Path 'app\static\vendor\three\three.module.js')) {
        throw 'Three.js still is not in app\static\vendor\three. Not starting the server.'
    }
}

Write-Host ''
Write-Host '  3D replay lab  ->  ' -NoNewline
Write-Host "http://localhost:$Port/simulation"
Write-Host '  Local recordings only. No vehicle connection.'
Write-Host ''
Write-Host '  The first drive you pick is computed before it can play: the lab'
Write-Host '  runs the project plant and thermal model over every sample at the'
Write-Host '  original timestamps. About 75 samples a second, so a short drive'
Write-Host '  takes seconds and the 2-hour Taif drive takes several minutes.'
Write-Host '  Picking a different drive cancels the one being computed.'
Write-Host ''
Write-Host '  agent replay   ->  ' -NoNewline
Write-Host "http://localhost:$Port/agents"
Write-Host '  results tab    ->  ' -NoNewline
Write-Host "http://localhost:$Port/results"
Write-Host ''

$candidates = @()
if ($Python) {
    if (Test-Path -LiteralPath $Python -PathType Leaf) {
        $candidates += [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Python).Path)
    }
    else {
        $command = Get-Command $Python -ErrorAction SilentlyContinue
        if ($command -and $command.Source) { $candidates += [System.IO.Path]::GetFullPath($command.Source) }
        else { throw "The selected Python interpreter was not found: $Python" }
    }
}
else {
    $repoPython = Join-Path $root '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $repoPython -PathType Leaf) {
        $candidates += [System.IO.Path]::GetFullPath($repoPython)
    }
    $availablePython = Get-Command python -ErrorAction SilentlyContinue
    if ($availablePython -and $availablePython.Source) {
        $availablePath = [System.IO.Path]::GetFullPath($availablePython.Source)
        if ($candidates -notcontains $availablePath) { $candidates += $availablePath }
    }
    if ($candidates.Count -eq 0) { throw 'No Python interpreter was found. Install Python or pass -Python <path>.' }
}

$selectedPython = $null
$probeErrors = @()
foreach ($candidate in $candidates) {
    $probeOutput = & $candidate -c "import fastapi, uvicorn, numpy, gymnasium; import sys; print(sys.executable)" 2>&1
    $probeCode = $LASTEXITCODE
    if ($probeCode -eq 0) {
        $selectedPython = $candidate
        break
    }
    $details = ($probeOutput | Out-String).Trim()
    $probeErrors += "$candidate (exit $probeCode): $details"
    if ($Python) { break }
}
if (-not $selectedPython) {
    $why = $probeErrors -join [Environment]::NewLine
    throw "No selected Python interpreter can import FastAPI, uvicorn, NumPy, and Gymnasium. Pass a valid -Python path.`n$why"
}

Write-Host "  Python interpreter -> $selectedPython"

# Optional model inference is separate from the app's required imports. Never
# install these large packages automatically; catalog browsing still works.
$capabilityOutput = & $selectedPython -c "import importlib.util, json; print(json.dumps({'stable_baselines3': importlib.util.find_spec('stable_baselines3') is not None, 'torch': importlib.util.find_spec('torch') is not None}))" 2>&1
$capabilityCode = $LASTEXITCODE
$capability = $null
if ($capabilityCode -eq 0) {
    try { $capability = ($capabilityOutput | Select-Object -Last 1 | ConvertFrom-Json) } catch { $capability = $null }
}
if (-not $capability -or -not $capability.stable_baselines3 -or -not $capability.torch) {
    $missing = @()
    if (-not $capability -or -not $capability.stable_baselines3) { $missing += 'stable-baselines3' }
    if (-not $capability -or -not $capability.torch) { $missing += 'torch' }
    Write-Host "  Note: this Python lacks $($missing -join ' and '). The /agents catalog is available, but model inference may be unavailable."
}

& $selectedPython -m app.server --simulation --http-port $Port
$serverExit = $LASTEXITCODE
exit $serverExit
