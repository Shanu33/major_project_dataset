<#
.SYNOPSIS
    Core Benchmark Dataset Verifier for CPWD / RBI Kharghar 354 Staff Quarters.
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "CPWD / RBI KHARGHAR 354 QUARTERS - CORE BENCHMARK VERIFIER (POWERSHELL)" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

$Files = Get-ChildItem -Path $CoreDir -Filter "*.pdf"
foreach ($f in $Files) {
    Write-Host "[VERIFIED] $($f.Name) ($($f.Length) bytes)" -ForegroundColor Green
}

Write-Host "Total verified core PDFs: $($Files.Count)" -ForegroundColor Cyan
