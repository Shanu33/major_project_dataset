<#
.SYNOPSIS
    Downloads core benchmark documentation for BMC Deonar 600-Tenements Turnkey Project.
.DESCRIPTION
    Fetches the 253-page Master Tender PDF, Building 04 Architectural Drawing Pack,
    Podium Levels Infrastructure Drawings, and Draft MOU format from official MCGM portals.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

New-Item -ItemType Directory -Force -Path $CoreDir | Out-Null

$Files = @(
    @{
        Filename = "ETH_7000022191_020922.pdf"
        Url = "https://www.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_020922.pdf"
        Category = "01_Tender_NIT_Eligibility\01_Main_Bid_Document"
        Label = "Master Bid Document (253 Pages Complete)"
    },
    @{
        Filename = "ETH_7000022191_DRAWING-4.pdf"
        Url = "https://portal.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_DRAWING-4.pdf"
        Category = "04_Architectural_Drawings_Building_04\01_Full_Drawing_Set_PDF"
        Label = "Building 04 Complete Architectural Drawings (8 Sheets)"
    },
    @{
        Filename = "ETH_7000022191_DRAWING-8.pdf"
        Url = "https://portal.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_DRAWING-8.pdf"
        Category = "05_Podium_Site_Infrastructure_Drawings\01_Full_Podium_Drawing_PDF"
        Label = "Podium Levels P1-P3 & Site Master Plan Drawings (8 Sheets)"
    },
    @{
        Filename = "ETH_7000022191_11_130922.pdf"
        Url = "https://r3app.mcgm.gov.in/irj/go/km/docs/documents/Tenders/ETH/ETH_7000022191_11_130922.pdf"
        Category = "02_Project_Scope_BUA_Payment\04_Draft_MOU_Format"
        Label = "Official Joint Venture Draft MOU Format"
    }
)

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "BMC DEONAR 600-TENEMENTS - CORE BENCHMARK DOWNLOADER (POWERSHELL)" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

foreach ($item in $Files) {
    $targetCore = Join-Path $CoreDir $item.Filename
    $catFolder = Join-Path $BaseDir $item.Category
    New-Item -ItemType Directory -Force -Path $catFolder | Out-Null
    $targetCat = Join-Path $catFolder $item.Filename

    if (Test-Path $targetCore) {
        $len = (Get-Item $targetCore).Length
        if ($len -gt 50000) {
            Write-Host "[SKIP] $($item.Filename) already exists ($len bytes)." -ForegroundColor Yellow
            continue
        }
    }

    Write-Host "[FETCH] Downloading $($item.Label)..." -ForegroundColor White
    try {
        Invoke-WebRequest -Uri $item.Url -OutFile $targetCore -UserAgent "Mozilla/5.0" -TimeoutSec 60
        Copy-Item -Path $targetCore -Destination $targetCat -Force
        $downloadedLen = (Get-Item $targetCore).Length
        Write-Host "    [OK] Downloaded successfully ($downloadedLen bytes)!" -ForegroundColor Green
    } catch {
        Write-Host "    [FAIL] Error downloading $($item.Filename): $_" -ForegroundColor Red
    }
}

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "Core dataset download process finished." -ForegroundColor Cyan

