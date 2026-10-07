$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    Write-Error 'The project Python environment is missing. See README.md in Explanatory Simulation for setup.'
}
$env:PYTHONDONTWRITEBYTECODE = '1'
& $taskPython (Join-Path $PSScriptRoot 'launch.py') @args
exit $LASTEXITCODE
