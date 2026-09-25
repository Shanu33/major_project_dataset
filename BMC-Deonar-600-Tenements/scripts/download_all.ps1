<#
.SYNOPSIS
    Bulk Downloader for BMC Deonar 600-Tenements Project.
.DESCRIPTION
    Reads file_manifest.json, checks file existence and downloads missing project files.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$ManifestPath = Join-Path $BaseDir "file_manifest.json"
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

if (-not (Test-Path $ManifestPath)) {
    Write-Host "Error: file_manifest.json not found at $ManifestPath" -ForegroundColor Red
    exit 1
}

$Manifest = Get-Content $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "BMC DEONAR 600-TENEMENTS - COMPLETE PACKAGE SYNCHRONIZER (POWERSHELL)" -ForegroundColor Cyan
Write-Host "Total Items: $($Manifest.Count)" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

$Present = 0
$Downloaded = 0
$Failed = 0

foreach ($item in $Manifest) {
    $fname = $item.filename
    $catRel = $item.category_path -replace "/", "\"
    $catDir = Join-Path $BaseDir $catRel
    New-Item -ItemType Directory -Force -Path $catDir | Out-Null
    $targetFile = Join-Path $catDir $fname

    if (Test-Path $targetFile) {
        $sz = (Get-Item $targetFile).Length
        if ($sz -gt 1000) {
            Write-Host "[PRESENT] $fname ($sz bytes)" -ForegroundColor Green
            $Present++
            continue
        }
    }

    Write-Host "[FETCH] Downloading $fname..." -ForegroundColor White
    try {
        Invoke-WebRequest -Uri $item.url -OutFile $targetFile -UserAgent "Mozilla/5.0" -TimeoutSec 60
        $sz = (Get-Item $targetFile).Length
        Write-Host "    [OK] Downloaded $fname ($sz bytes)" -ForegroundColor Green
        $Downloaded++
    } catch {
        Write-Host "    [FAIL] Error downloading $fname : $_" -ForegroundColor Red
        $Failed++
    }
}

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "Synchronization complete. Present: $Present | Downloaded: $Downloaded | Failed: $Failed" -ForegroundColor Cyan

