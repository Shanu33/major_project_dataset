<#
.SYNOPSIS
    Full Repository Synchronizer for CPWD / RBI Kharghar 354 Staff Quarters.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $BaseDir "file_manifest.json"

if (-not (Test-Path $ManifestPath)) {
    Write-Host "Manifest file not found: $ManifestPath" -ForegroundColor Red
    exit 1
}

$Manifest = Get-Content $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "CPWD / RBI KHARGHAR - REPOSITORY INTEGRITY CHECK (POWERSHELL)" -ForegroundColor Cyan
Write-Host "Total Items in Manifest: $($Manifest.Count)" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

foreach ($it in $Manifest) {
    $p = Join-Path $BaseDir ($it.category -replace "/", "")
    $f = Join-Path $p $it.filename
    if (Test-Path $f) {
        $sz = (Get-Item $f).Length
        Write-Host "[PRESENT] $($it.filename) ($sz bytes)" -ForegroundColor Green
    } else {
        Write-Host "[PENDING] $($it.filename)" -ForegroundColor Yellow
    }
}
