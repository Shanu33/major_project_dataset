<#
.SYNOPSIS
Bulk Downloader for Nalanda University Package 1C Tender Documents (~696 PDFs) in PowerShell.
Reads from file_manifest.json and downloads files into their respective folders.

.PARAMETER Category
Optional filter by category string (e.g. "01", "04_Architectural", "05_Structural").

.PARAMETER Overwrite
Force re-download of existing files.

.EXAMPLE
.\download_all.ps1
.\download_all.ps1 -Category "01_Tender"
#>

param(
    [string]$Category = "",
    [switch]$Overwrite = $false
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $BaseDir "file_manifest.json"
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

if (-not (Test-Path $ManifestPath)) {
    Write-Error "Manifest file not found: $ManifestPath"
    exit 1
}

$manifestJson = Get-Content -Path $ManifestPath -Raw | ConvertFrom-Json
if ($Category) {
    $manifestJson = $manifestJson | Where-Object { $_.category_path -like "*$Category*" }
}

$total = $manifestJson.Count
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "NALANDA UNIVERSITY PACKAGE 1C - POWERSHELL BULK DOWNLOADER" -ForegroundColor Cyan
Write-Host "Total files to process: $total" -ForegroundColor Cyan
if ($Category) { Write-Host "Filter: $Category" -ForegroundColor Yellow }
Write-Host "======================================================================" -ForegroundColor Cyan

$i = 1
$success = 0
$skipped = 0
$failed = 0

foreach ($item in $manifestJson) {
    $relPath = $item.category_path.Replace("/", "\")
    $targetDir = Join-Path $BaseDir $relPath
    $targetFile = Join-Path $targetDir $item.filename

    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    if (-not $Overwrite -and (Test-Path $targetFile) -and ((Get-Item $targetFile).Length -gt 1000)) {
        Write-Host "[$i/$total] [-] $($item.filename) (Already exists)" -ForegroundColor Gray
        $skipped++
    } else {
        try {
            Write-Host "[$i/$total] [>] Downloading $($item.filename)..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $item.url -OutFile $targetFile -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 45
            $sz = [math]::Round((Get-Item $targetFile).Length / 1KB, 1)
            Write-Host "    [OK] Saved: $sz KB" -ForegroundColor Green
            $success++

            if ($item.is_core) {
                if (-not (Test-Path $CoreDir)) { New-Item -ItemType Directory -Path $CoreDir -Force | Out-Null }
                Copy-Item -Path $targetFile -Destination (Join-Path $CoreDir $item.filename) -Force
            }
        } catch {
            Write-Host "    [FAIL] Could not download $($item.filename): $_" -ForegroundColor Red
            $failed++
        }
    }
    $i++
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Summary: Total: $total | Downloaded: $success | Skipped: $skipped | Failed: $failed" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

