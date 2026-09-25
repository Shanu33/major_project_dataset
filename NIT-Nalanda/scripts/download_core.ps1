<#
.SYNOPSIS
Downloads the 7 Core Intelligence Dataset benchmark files for Nalanda University Package 1C.
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
        Filename = "finalnit25-03-17.pdf"
        Url = "https://nalandauniv.edu.in/wp-content/uploads/2019/07/finalnit25-03-17.pdf"
        Category = "01_Tender_NIT_PreBid\02_NIT_Conditions"
        Label = "1. NIT (full conditions)"
    },
    @{
        Filename = "05.-boq-schedule-b-combined.pdf"
        Url = "https://nalandauniv.edu.in/wp-content/uploads/2019/07/05.-boq-schedule-b-combined.pdf"
        Category = "02_Cost_BOQ_Makes\02_BOQ_Schedules\Combined_BOQ"
        Label = "2. Combined BOQ (best single BOQ)"
    },
    @{
        Filename = "nalanda-residential-specifications-part-i-civil-works.pdf"
        Url = "https://nalandauniv.edu.in/wp-content/uploads/2019/07/nalanda-residential-specifications-part-i-civil-works.pdf"
        Category = "03_Technical_Specifications_Reports\Specifications\Part_I_Civil_Works"
        Label = "3. Specs Part I — Civil"
    },
    @{
        Filename = "nalanda-residential-specifications-part-ii-services.pdf"
        Url = "https://nalandauniv.edu.in/wp-content/uploads/2019/07/nalanda-residential-specifications-part-ii-services.pdf"
        Category = "03_Technical_Specifications_Reports\Specifications\Part_II_Services"
        Label = "4. Specs Part II — Services"
    },
    @{
        Filename = "02.-ecpt.pdf"
        Url = "https://nalandauniv.edu.in/wp-content/uploads/2019/07/02.-ecpt.pdf"
        Category = "02_Cost_BOQ_Makes\01_Estimated_Cost_ECPT"
        Label = "5. Estimated cost (ECPT)"
    },
    @{
        Filename = "a.2.1-type-1b-ground-floor-plan.pdf"
        Url = "https://nalandauniv.edu.in/wp-content/uploads/2019/07/a.2.1-type-1b-ground-floor-plan.pdf"
        Category = "04_Architectural_Drawings\01_Faculty_Apartments\Type_1B"
        Label = "6. Type 1B GF plan"
    },
    @{
        Filename = "1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf"
        Url = "https://nalandauniv.edu.in/wp-content/uploads/2019/07/1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf"
        Category = "05_Structural_Drawings\01_Faculty_Housing_Apartments\Type_1B"
        Label = "7. Type 1B pile layout"
    }
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "NALANDA UNIVERSITY PACKAGE 1C - CORE BENCHMARK DATASET DOWNLOADER" -ForegroundColor Cyan
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
        Invoke-WebRequest -Uri $item.Url -OutFile $coreTarget -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 30
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

