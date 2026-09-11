# TokenSaver v5.0.0 PowerShell Uninstaller
Write-Host "==================================================" -ForegroundColor Yellow
Write-Host "Uninstalling TokenSaver v5.0.0 Local Engine..." -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Yellow

$cachePath = "C:\tools\.tokensaver-cache"
if (Test-Path $cachePath) {
    Remove-Item -Recurse -Force $cachePath
    Write-Host "[CLEANED] Removed $cachePath" -ForegroundColor Green
}

Write-Host "[NOTE] Source files and user repositories were NOT modified." -ForegroundColor Cyan
Write-Host "[COMPLETE] TokenSaver v5 uninstalled safely." -ForegroundColor Green
