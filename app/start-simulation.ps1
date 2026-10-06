# Start the 3D replay lab on this machine. Read-only: no vehicle connection,
# no ECU command path, nothing written to disk but the usual review log.
#
#   powershell -ExecutionPolicy Bypass -File app\start-simulation.ps1
#
# Run it from the repository root, not from app\.
param(
    [int]$Port = 8000,
    [switch]$SkipVendor
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

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
# /agents computes an episode with stable-baselines3 and torch. Say so here
# when THIS python cannot: the page still lists every experiment, and its
# episode route answers 503. A native command's exit code never throws under
# $ErrorActionPreference 'Stop' in Windows PowerShell 5.1, so it is read here.
python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('stable_baselines3') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host '  Note: this python has no stable-baselines3, so /agents lists the'
    Write-Host '  experiments but cannot compute an episode (it answers 503). To'
    Write-Host '  compute one, start the server with an interpreter that has it:'
    Write-Host '      <that python> -m app.server --simulation'
}
Write-Host '  results tab    ->  ' -NoNewline
Write-Host "http://localhost:$Port/results"
Write-Host ''

python -m app.server --simulation --http-port $Port
