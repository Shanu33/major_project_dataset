<#
.SYNOPSIS
Repository Directory & Portal Synchronizer for NBCC GPRA Sarojini Nagar in PowerShell.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $BaseDir "file_manifest.json"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "NBCC GPRA SAROJINI NAGAR - REPOSITORY MAPPER & DIRECTORY" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if (Test-Path $ManifestPath) {
    $manifest = Get-Content -Path $ManifestPath -Raw | ConvertFrom-Json
    Write-Host "Total cataloged files & package modules: $($manifest.Count)" -ForegroundColor Green
    $i = 1
    foreach ($m in $manifest) {
        Write-Host "[$i] $($m.category_path) -> $($m.filename)" -ForegroundColor Yellow
        $i++
    }
}

Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Portals: CPPP (https://eprocure.gov.in) | NBCC e-Nivida (https://nbcc.enivida.com)" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

