param(
    [int]$Port = 8000,
    [switch]$NoReload
)

$pythonPath = Join-Path $PSScriptRoot ".venv312\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Error "Python 3.12 environment not found at $pythonPath"
    exit 1
}

$reloadArgs = @()
if (-not $NoReload) {
    $reloadArgs += "--reload"
}

$args = @(
    "-m", "uvicorn",
    "--app-dir", $PSScriptRoot,
    "main:app",
    "--host", "127.0.0.1",
    "--port", $Port
) + $reloadArgs

& $pythonPath @args
