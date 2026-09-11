# TokenSaver v5.0.0 PowerShell Installer
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Installing TokenSaver v5.0.0 (Local Engine)..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

try {
    $pythonVersion = & py --version
    Write-Host "[PASS] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Python is required but not found in PATH!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "C:\tools")) {
    New-Item -ItemType Directory -Path "C:\tools" -Force | Out-Null
}

if (-not (Test-Path "C:\tools\.tokensaver-cache")) {
    New-Item -ItemType Directory -Path "C:\tools\.tokensaver-cache" -Force | Out-Null
}

$scriptDir = Split-Path -Parent $PSScriptRoot

Write-Host "Syncing files to C:\tools..." -ForegroundColor Yellow
Copy-Item "$scriptDir\src\tokensaver_v5\*.py" "C:\tools" -Force
Copy-Item "$scriptDir\src\utilities\*.py" "C:\tools" -Force
Copy-Item "$scriptDir\config\*.json" "C:\tools" -Force
Copy-Item "$scriptDir\cmd\*.cmd" "C:\tools" -Force
if (Test-Path "$scriptDir\bin\*.exe") { Copy-Item "$scriptDir\bin\*.exe" "C:\tools" -Force }
if (Test-Path "$scriptDir\bin\*.dll") { Copy-Item "$scriptDir\bin\*.dll" "C:\tools" -Force }

if (Test-Path "C:\tools\tokensaver-v5.cmd") {
    Write-Host "[PASS] TokenSaver v5 CLI script verified at C:\tools\tokensaver-v5.cmd" -ForegroundColor Green
} else {
    Set-Content -Path "C:\tools\tokensaver-v5.cmd" -Value "@echo off`npy C:\tools\tokensaver_v5_symbol_index.py %*"
    Write-Host "[PASS] Created C:\tools\tokensaver-v5.cmd" -ForegroundColor Green
}

Write-Host "`nRunning TokenSaver Doctor..." -ForegroundColor Yellow
& C:\tools\tokensaver-v5.cmd doctor

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "TokenSaver v5.0.0 Installation Complete!" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
