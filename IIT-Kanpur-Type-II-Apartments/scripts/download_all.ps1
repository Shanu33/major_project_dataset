<#
.SYNOPSIS
Repository Downloader & Google Drive Guide for IIT Kanpur Type-II Apartments.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir

$url = "https://iitk.ac.in/iwd/file/2025/44-Composite-D3-2024-25/Tenderdocument44D3.pdf"
$fname = "Tenderdocument44D3.pdf"
$target = Join-Path $BaseDir "01_Tender_NIT_Eligibility\01_Master_Tender_Document\$fname"
$core = Join-Path $BaseDir "00_Core_Intelligence_Dataset\$fname"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "IIT KANPUR TYPE-II APARTMENTS - BULK DOWNLOADER & DRIVE MAPPER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if (Test-Path $target) {
    Write-Host "[SKIP] $fname already exists." -ForegroundColor Gray
} else {
    Write-Host "[FETCH] Downloading $fname from IITK official site..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $url -OutFile $target -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 60
        Copy-Item -Path $target -Destination $core -Force
        Write-Host "[OK] Master Tender Document Downloaded Successfully." -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] Error downloading: $_" -ForegroundColor Red
    }
}

Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "GOOGLE DRIVE DRAWINGS ACCESS:" -ForegroundColor Yellow
Write-Host "URL: https://drive.google.com/drive/folders/1-3XgCAKZ4VkDADDHG_qNN9pnY-TEA3lS?usp=sharing" -ForegroundColor White
Write-Host "Download and place extracted drawing files into:" -ForegroundColor Yellow
Write-Host "  -> $(Join-Path $BaseDir '05_Drawings')" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

