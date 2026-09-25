<#
.SYNOPSIS
Downloads the Core Benchmark Files for K-RIDE Railway Quarters & Belandur Road Station Infrastructure.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

if (-not (Test-Path $CoreDir)) {
    New-Item -ItemType Directory -Path $CoreDir -Force | Out-Null
}

$files = @(
    @{
        Filename = "Tender-Document-Belandur-Road-Baiyyappanahalli-Station-Building.pdf"
        Url = "https://kride.in/wp-content/uploads/2021/02/Tender-Document-Belandur-Road-Baiyyappanahalli-Station-Building.pdf"
        Category = "01_Tender_NIT_Bidding_Docs\01_Belandur_Road_Station_Tender_Volume"
        Label = "Belandur Road Station & Facilities Bid Volume (313 Pages)"
    },
    @{
        Filename = "HSRA-Staff-Quarters-Tender-Document.pdf"
        Url = "https://kride.in/wp-content/uploads/2021/03/HSRA-Staff-Quarters-Tender-Document.pdf"
        Category = "06_Related_Railway_Quarters_HSRA\01_Hosur_Staff_Quarters_Tender_Volume"
        Label = "Hosur Staff Quarters Type-II & Type-III Tender Volume"
    }
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "K-RIDE RAILWAY INFRASTRUCTURE - CORE BENCHMARK DOWNLOADER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

foreach ($item in $files) {
    Write-Host "Fetching: $($item.Label)..." -ForegroundColor Yellow
    $coreTarget = Join-Path $CoreDir $item.Filename
    $catDir = Join-Path $BaseDir $item.Category
    $catTarget = Join-Path $catDir $item.Filename

    if (-not (Test-Path $catDir)) {
        New-Item -ItemType Directory -Path $catDir -Force | Out-Null
    }

    try {
        Invoke-WebRequest -Uri $item.Url -OutFile $coreTarget -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 50
        Copy-Item -Path $coreTarget -Destination $catTarget -Force
        $sz = [math]::Round((Get-Item $coreTarget).Length / 1MB, 2)
        Write-Host "    [OK] Saved: $sz MB successfully!" -ForegroundColor Green
    } catch {
        Write-Host "    [FAIL] Error downloading $($item.Filename): $_" -ForegroundColor Red
    }
}

Write-Host "======================================================================" -ForegroundColor Cyan

