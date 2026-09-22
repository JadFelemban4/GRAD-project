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

python -m app.server --simulation --http-port $Port
