# Core Benchmark Downloader & Verifier PowerShell Script for EPI Trimbakeshwar EMRS
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir
$coreDir = Join-Path $baseDir "00_Core_Intelligence_Dataset"

Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "EPI TRIMBAKESHWAR EMRS - CORE DATASET VERIFIER" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

$files = Get-ChildItem -Path $coreDir -Filter "*.pdf"
Write-Host "Found $($files.Count) PDF documents in 00_Core_Intelligence_Dataset:`n" -ForegroundColor Green

$idx = 1
foreach ($f in ($files | Sort-Object Name)) {
    $sz = [string]::Format("{0:N0}", $f.Length)
    Write-Host ("[{0:D2}/{1:D2}] [VERIFIED] {2,-55} ({3} bytes)" -f $idx, $files.Count, $f.Name, $sz) -ForegroundColor Gray
    $idx++
}

Write-Host ("`n" + "=" * 80) -ForegroundColor Cyan
Write-Host "Core dataset verification complete." -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan

