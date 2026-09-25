<#
.SYNOPSIS
Downloads the 7 Core Intelligence Benchmark files for OIL / RITES Duliajan BQ Workmen Housing.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

if (-not (Test-Path $CoreDir)) {
    New-Item -ItemType Directory -Path $CoreDir -Force | Out-Null
}

$coreFiles = @(
    @{
        Filename = "NIT_9_pdf-2025-Aug-28-17-28-23.pdf"
        Url = "https://www.rites.com/Upload/Tender/NIT_9_pdf-2025-Aug-28-17-28-23.pdf"
        Category = "01_Tender_NIT_Contract\01_NIT_Conditions"
        Label = "1. NIT (full conditions)"
    },
    @{
        Filename = "Technical_Bid_pdf-2025-Aug-28-19-39-38.pdf"
        Url = "https://www.rites.com/Upload/Tender/Technical_Bid_pdf-2025-Aug-28-19-39-38.pdf"
        Category = "01_Tender_NIT_Contract\02_Technical_Bid_Volume"
        Label = "2. Technical Bid (full tender / specs volume)"
    },
    @{
        Filename = "DBR_pdf-2025-Aug-28-17-46-57.pdf"
        Url = "https://www.rites.com/Upload/Tender/DBR_pdf-2025-Aug-28-17-46-57.pdf"
        Category = "03_Specs_DBR_Finishes\Design_Basis_Report_DBR"
        Label = "3. Design Basis Report (DBR)"
    },
    @{
        Filename = "BoQ_1_pdf-2025-Aug-28-17-27-34.pdf"
        Url = "https://www.rites.com/Upload/Tender/BoQ_1_pdf-2025-Aug-28-17-27-34.pdf"
        Category = "02_Cost_BOQ_EPC\BoQ_Part_1"
        Label = "4. BOQ Part 1 (EPC Lump-sum Scope)"
    },
    @{
        Filename = "Tender_drawing_3_pdf-2025-Aug-28-17-39-16.pdf"
        Url = "https://www.rites.com/Upload/Tender/Tender_drawing_3_pdf-2025-Aug-28-17-39-16.pdf"
        Category = "05_Tender_Drawings\Vol_3_Structural_Housing_GuestHouse"
        Label = "5. Drawing 3 — Structural Housing & GH"
    },
    @{
        Filename = "Tender_drawing_4_pdf-2025-Aug-28-17-39-32.pdf"
        Url = "https://www.rites.com/Upload/Tender/Tender_drawing_4_pdf-2025-Aug-28-17-39-32.pdf"
        Category = "05_Tender_Drawings\Vol_4_Structural_CommunityCentre_Electrical_MEP"
        Label = "6. Drawing 4 — Structural & Electrical MEP"
    },
    @{
        Filename = "GT_report_pdf-2025-Aug-28-17-46-44.pdf"
        Url = "https://www.rites.com/Upload/Tender/GT_report_pdf-2025-Aug-28-17-46-44.pdf"
        Category = "04_Survey_Geotech\Geotechnical_Investigation"
        Label = "7. GT Report (310 pages geotechnical)"
    }
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "OIL / RITES DULIAJAN WORKMEN HOUSING - CORE DATASET DOWNLOADER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$success = 0
$idx = 1
$total = $coreFiles.Count

foreach ($item in $coreFiles) {
    Write-Host "[$idx/$total] Fetching: $($item.Label) ($($item.Filename))..." -ForegroundColor Yellow
    $coreTarget = Join-Path $CoreDir $item.Filename
    $catDir = Join-Path $BaseDir $item.Category
    $catTarget = Join-Path $catDir $item.Filename

    if (-not (Test-Path $catDir)) {
        New-Item -ItemType Directory -Path $catDir -Force | Out-Null
    }

    try {
        Invoke-WebRequest -Uri $item.Url -OutFile $coreTarget -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 45
        Copy-Item -Path $coreTarget -Destination $catTarget -Force
        $len = (Get-Item $coreTarget).Length
        Write-Host "    [OK] Downloaded $($len) bytes successfully!" -ForegroundColor Green
        $success++
    } catch {
        Write-Host "    [FAIL] Error downloading $($item.Filename): $_" -ForegroundColor Red
    }
    $idx++
}

Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Completed! $success / $total files saved to: $CoreDir" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

