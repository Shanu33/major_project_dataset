<#
.SYNOPSIS
    Repository Synchronizer for KMRL Muttom Staff Quarters.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $BaseDir "file_manifest.json"

if (-not (Test-Path $ManifestPath)) {
    Write-Host "Manifest not found!" -ForegroundColor Red
    exit 1
}

$Manifest = Get-Content $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "KMRL MUTTOM STAFF QUARTERS - REPOSITORY INTEGRITY (POWERSHELL)" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

foreach ($it in $Manifest) {
    $target = Join-Path $BaseDir (Join-Path ($it.category -replace "/", "") $it.filename)
    if (Test-Path $target) {
        $sz = (Get-Item $target).Length
        Write-Host "[PRESENT] $($it.filename) ($sz bytes)" -ForegroundColor Green
    } else {
        Write-Host "[PENDING] $($it.filename)" -ForegroundColor Yellow
    }
}
