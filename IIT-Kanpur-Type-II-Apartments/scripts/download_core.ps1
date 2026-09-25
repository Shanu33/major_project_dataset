<#
.SYNOPSIS
Downloads the Core Benchmark Files for IIT Kanpur Type-II Apartments.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

if (-not (Test-Path $CoreDir)) {
    New-Item -ItemType Directory -Path $CoreDir -Force | Out-Null
}

$url = "https://iitk.ac.in/iwd/file/2025/44-Composite-D3-2024-25/Tenderdocument44D3.pdf"
$fname = "Tenderdocument44D3.pdf"
$coreTarget = Join-Path $CoreDir $fname
$catDir = Join-Path $BaseDir "01_Tender_NIT_Eligibility\01_Master_Tender_Document"
$catTarget = Join-Path $catDir $fname

if (-not (Test-Path $catDir)) {
    New-Item -ItemType Directory -Path $catDir -Force | Out-Null
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "IIT KANPUR TYPE-II APARTMENTS - CORE BENCHMARK DOWNLOADER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Downloading Master Tender Document (190 Pages)..." -ForegroundColor Yellow

try {
    Invoke-WebRequest -Uri $url -OutFile $coreTarget -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 50
    Copy-Item -Path $coreTarget -Destination $catTarget -Force
    $sz = [math]::Round((Get-Item $coreTarget).Length / 1MB, 2)
    Write-Host "    [OK] Saved: $sz MB successfully!" -ForegroundColor Green
} catch {
    Write-Host "    [FAIL] Error downloading tender document: $_" -ForegroundColor Red
}

Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Google Drive Drawings Link: https://drive.google.com/drive/folders/1-3XgCAKZ4VkDADDHG_qNN9pnY-TEA3lS?usp=sharing" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

