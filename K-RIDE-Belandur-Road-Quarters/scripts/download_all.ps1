<#
.SYNOPSIS
Bulk Downloader for K-RIDE Railway Quarters & Station Infrastructure in PowerShell.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir

$files = @(
    @{
        Filename = "Tender-Document-Belandur-Road-Baiyyappanahalli-Station-Building.pdf"
        Url = "https://kride.in/wp-content/uploads/2021/02/Tender-Document-Belandur-Road-Baiyyappanahalli-Station-Building.pdf"
        Path = "01_Tender_NIT_Bidding_Docs\01_Belandur_Road_Station_Tender_Volume"
    },
    @{
        Filename = "HSRA-Staff-Quarters-Tender-Document.pdf"
        Url = "https://kride.in/wp-content/uploads/2021/03/HSRA-Staff-Quarters-Tender-Document.pdf"
        Path = "06_Related_Railway_Quarters_HSRA\01_Hosur_Staff_Quarters_Tender_Volume"
    }
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "K-RIDE RAILWAY INFRASTRUCTURE - BULK DOWNLOADER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

foreach ($f in $files) {
    $targetDir = Join-Path $BaseDir $f.Path
    $targetFile = Join-Path $targetDir $f.Filename

    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    if (Test-Path $targetFile) {
        Write-Host "[SKIP] $($f.Filename) already exists." -ForegroundColor Gray
    } else {
        Write-Host "[FETCH] Downloading $($f.Filename)..." -ForegroundColor Yellow
        try {
            Invoke-WebRequest -Uri $f.Url -OutFile $targetFile -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 50
            Write-Host "    [OK] Saved successfully." -ForegroundColor Green
        } catch {
            Write-Host "    [FAIL] Error downloading $($f.Filename): $_" -ForegroundColor Red
        }
    }
}

Write-Host "======================================================================" -ForegroundColor Cyan

