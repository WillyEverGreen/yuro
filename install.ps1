# YURO ONE-CLICK INSTALLER (WINDOWS)
# Consolidates all tools into C:\tools, configures PATH, synchronizes rules & skills, and downloads required binaries.

param (
    [string]$ToolsDir = "C:\tools",
    [switch]$SkipDownload
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "             YURO TOOLCHAIN INSTALLER (WINDOWS)             " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Ensure Target Tools Directory Exists
if (-not (Test-Path $ToolsDir)) {
    Write-Host "[1/6] Creating directory: $ToolsDir..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $ToolsDir -Force | Out-Null
} else {
    Write-Host "[1/6] Tools directory exists: $ToolsDir" -ForegroundColor Green
}

# 2. Copy CLI Tools & Wrappers to C:\tools
Write-Host "[2/6] Copying CLI wrappers and auditor tools to $ToolsDir..." -ForegroundColor Yellow
$cmdDir = Join-Path $PSScriptRoot "cmd"
$binDir = Join-Path $PSScriptRoot "bin"

if (Test-Path $cmdDir) {
    Copy-Item -Path "$cmdDir\*" -Destination $ToolsDir -Force -Recurse
}
if (Test-Path $binDir) {
    Copy-Item -Path "$binDir\*" -Destination $ToolsDir -Force -Recurse
}
Write-Host "      Copied CLI tools and binaries successfully." -ForegroundColor Green

# 3. Download codebase-memory-mcp binary if not present
$cbmExe = Join-Path $ToolsDir "codebase-memory-mcp.exe"
if (-not (Test-Path $cbmExe) -and -not $SkipDownload) {
    Write-Host "[3/6] codebase-memory-mcp.exe not found. Downloading release v0.11.0..." -ForegroundColor Yellow
    $zipUrl = "https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-windows-amd64.zip"
    $tempZip = Join-Path $env:TEMP "codebase-memory-mcp-windows-amd64.zip"
    $tempExtract = Join-Path $env:TEMP "cbm_extract"

    Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip
    Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
    $extractedExe = Get-ChildItem -Path $tempExtract -Filter "codebase-memory-mcp.exe" -Recurse | Select-Object -First 1
    if ($extractedExe) {
        Copy-Item -Path $extractedExe.FullName -Destination $cbmExe -Force
        Write-Host "      Downloaded and installed codebase-memory-mcp.exe successfully." -ForegroundColor Green
    }
    Remove-Item $tempZip, $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "[3/6] codebase-memory-mcp.exe is present." -ForegroundColor Green
}

# 4. Configure User PATH
Write-Host "[4/6] Checking User Environment PATH for $ToolsDir..." -ForegroundColor Yellow
$userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($userPath -notlike "*$ToolsDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$ToolsDir;$userPath", [EnvironmentVariableTarget]::User)
    $env:Path = "$ToolsDir;$env:Path"
    Write-Host "      Added $ToolsDir to User PATH." -ForegroundColor Green
} else {
    Write-Host "      $ToolsDir is already in User PATH." -ForegroundColor Green
}

# 5. Synchronize Rules & Skills to ~/.gemini/config
Write-Host "[5/6] Synchronizing rules, skills, and MCP configs to ~/.gemini/config..." -ForegroundColor Yellow
$geminiConfig = Join-Path $env:USERPROFILE ".gemini\config"
$rulesTarget = Join-Path $geminiConfig "rules"
$skillsTarget = Join-Path $geminiConfig "skills"

New-Item -ItemType Directory -Path $rulesTarget, $skillsTarget -Force | Out-Null

$rulesSrc = Join-Path $PSScriptRoot "rules"
if (Test-Path $rulesSrc) {
    Copy-Item -Path "$rulesSrc\*" -Destination $rulesTarget -Force
    Write-Host "      Synchronized $( (Get-ChildItem $rulesSrc).Count ) rules." -ForegroundColor Green
}

$skillsSrc = Join-Path $PSScriptRoot "skills"
if (Test-Path $skillsSrc) {
    Copy-Item -Path "$skillsSrc\*" -Destination $skillsTarget -Force -Recurse
    Write-Host "      Synchronized $( (Get-ChildItem $skillsSrc).Count ) skills." -ForegroundColor Green
}

# MCP Config setup
$mcpTarget = Join-Path $geminiConfig "mcp_config.json"
$mcpSrc = Join-Path $PSScriptRoot "mcp\mcp_config.global.json"
if (-not (Test-Path $mcpTarget) -and (Test-Path $mcpSrc)) {
    Copy-Item -Path $mcpSrc -Destination $mcpTarget -Force
    Write-Host "      Initialized $mcpTarget." -ForegroundColor Green
}

# 6. Verification
Write-Host "[6/6] Verifying toolchain execution..." -ForegroundColor Yellow
try {
    $scanOutput = & node "$ToolsDir\token-tracker.js" scan -n 1
    Write-Host "      token-tracker: OK" -ForegroundColor Green
} catch {
    Write-Warning "token-tracker verification failed: $_"
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "              YURO SETUP COMPLETED SUCCESSFULLY!            " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Available Global Commands:" -ForegroundColor White
Write-Host "  - token-scan       : Scan token usage across all chat sessions" -ForegroundColor Cyan
Write-Host "  - token-audit      : Deep audit of active conversation tokens" -ForegroundColor Cyan
Write-Host "  - cbm arch <proj>  : Instant architecture map (<350 tokens)" -ForegroundColor Cyan
Write-Host "  - cbm trace <fn>   : Call hierarchy traversal (<200 tokens)" -ForegroundColor Cyan
Write-Host "  - rg-mini <query>  : Capped ripgrep search (<80 tokens)" -ForegroundColor Cyan
Write-Host "  - fd-mini <query>  : Capped filename search (<80 tokens)" -ForegroundColor Cyan
