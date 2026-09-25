# Full Package Synchronizer & Manifest Verifier in PowerShell for EPI Trimbakeshwar EMRS
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir
$manifestPath = Join-Path $baseDir "file_manifest.json"

Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "EPI TRIMBAKESHWAR EMRS - FULL PACKAGE SYNCHRONIZER" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

if (-not (Test-Path $manifestPath)) {
    Write-Error "Manifest file not found at: $manifestPath"
    exit 1
}

$raw = Get-Content -Path $manifestPath -Raw -Encoding UTF8
$manifest = $raw | ConvertFrom-Json

Write-Host "Total cataloged manifest items: $($manifest.Count)`n" -ForegroundColor Green

$present = 0
$idx = 1

foreach ($item in $manifest) {
    $subPath = $item.category.Replace("/", [System.IO.Path]::DirectorySeparatorChar)
    $fullPath = Join-Path (Join-Path $baseDir $subPath) $item.filename
    
    if ((Test-Path $fullPath) -and ((Get-Item $fullPath).Length -gt 200)) {
        $sz = [string]::Format("{0:N0}", (Get-Item $fullPath).Length)
        Write-Host ("[{0:D2}/{1:D2}] [PRESENT]  {2,-40} / {3,-45} ({4} bytes)" -f $idx, $manifest.Count, $item.category, $item.filename, $sz) -ForegroundColor Gray
        $present++
    } else {
        Write-Host ("[{0:D2}/{1:D2}] [MISSING]  {2,-40} / {3,-45}" -f $idx, $manifest.Count, $item.category, $item.filename) -ForegroundColor Red
    }
    $idx++
}

Write-Host ("`n" + "=" * 80) -ForegroundColor Cyan
Write-Host "SUMMARY: Verified $present / $($manifest.Count) records present." -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan

