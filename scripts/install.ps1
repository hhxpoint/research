# hhxpoint/research installer for Windows.
# Usage: .\scripts\install.ps1 [--mode minimal|writing|full] [--only a,b] [--dsh-home PATH] [--dry-run]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$cli = Join-Path $repo 'tools\dsh_skills.py'
if (-not (Test-Path $cli)) {
    Write-Error "dsh_skills.py not found under $repo"
    exit 2
}

$hasMode = $false
foreach ($a in $Args) {
    if ($a -eq '--mode' -or $a -like '--mode=*') { $hasMode = $true }
}
if (-not $hasMode) { $Args = @('--mode', 'full') + $Args }

& python $cli install @Args
exit $LASTEXITCODE
