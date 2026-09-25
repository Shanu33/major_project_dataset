<#
.SYNOPSIS
Downloader & Portal Mapper for NBCC GPRA Sarojini Nagar Benchmark Files in PowerShell.
#>

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir
$CoreDir = Join-Path $BaseDir "00_Core_Intelligence_Dataset"

if (-not (Test-Path $CoreDir)) {
    New-Item -ItemType Directory -Path $CoreDir -Force | Out-Null
}

$items = @(
    @{
        Filename = "Tendernotice_1_Pkg_III_Commercial_C.pdf"
        Url = "https://eprocure.gov.in/epublish/app?component=$DirectLink&page=FrontEndViewTender&service=direct&sp=S6lXrtT/fvpG4Tx8e8i2Dtw=="
        Label = "Package III Commercial C Master NIT"
    }
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "NBCC GPRA SAROJINI NAGAR - CORE DOWNLOADER & PORTAL MAPPER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

foreach ($it in $items) {
    Write-Host "Checking: $($it.Label)..." -ForegroundColor Yellow
    $target = Join-Path $CoreDir $it.Filename
    try {
        Invoke-WebRequest -Uri $it.Url -OutFile $target -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -TimeoutSec 40
        $sz = [math]::Round((Get-Item $target).Length / 1KB, 1)
        Write-Host "    [OK] Saved: $sz KB" -ForegroundColor Green
    } catch {
        Write-Host "    [NOTICE] Portal session requirement: $_" -ForegroundColor Yellow
        Write-Host "    Direct Link: $($it.Url)" -ForegroundColor White
    }
}

Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Access Complete Tender Packages at: https://nbcc.enivida.com / https://eprocure.gov.in" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

