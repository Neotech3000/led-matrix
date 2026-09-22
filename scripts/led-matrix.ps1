# LED Matrix launcher for Windows PowerShell.
# Run from anywhere:  powershell -File scripts/led-matrix.ps1
Set-StrictMode -Version Latest
Set-Location (Split-Path -Parent $PSScriptRoot)
$extra = @("--gui", "--host", "127.0.0.1", "--port", "43173") + @args
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m matrix_deck @extra
    exit $LASTEXITCODE
}
& python -m matrix_deck @extra
exit $LASTEXITCODE
