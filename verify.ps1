# YURO VERIFICATION SUITE
Write-Host "Running YURO Verification Suite..." -ForegroundColor Cyan

$checks = @(
    @{ Name = "token-tracker.js"; Path = "cmd\token-tracker.js" },
    @{ Name = "token-scan.cmd"; Path = "cmd\token-scan.cmd" },
    @{ Name = "token-audit.cmd"; Path = "cmd\token-audit.cmd" },
    @{ Name = "cbm.cmd"; Path = "cmd\cbm.cmd" },
    @{ Name = "rg-mini.cmd"; Path = "cmd\rg-mini.cmd" },
    @{ Name = "fd-mini.cmd"; Path = "cmd\fd-mini.cmd" },
    @{ Name = "auto-accept.cmd"; Path = "cmd\auto-accept.cmd" },
    @{ Name = "T0-T5 Protocol"; Path = "rules\T0-T5-protocol.md" },
    @{ Name = "TokenSaver Rule"; Path = "rules\token-saver.md" },
    @{ Name = "PC-Toolbox Skill"; Path = "skills\pc-toolbox\SKILL.md" }
)

$passed = 0
foreach ($c in $checks) {
    $p = Join-Path $PSScriptRoot $c.Path
    if (Test-Path $p) {
        Write-Host " [PASS] $($c.Name)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " [FAIL] $($c.Name) (missing at $p)" -ForegroundColor Red
    }
}

Write-Host "`nTesting token-tracker scan execution:" -ForegroundColor Yellow
try {
    & node "$PSScriptRoot\cmd\token-tracker.js" scan -n 1
    Write-Host " [PASS] token-tracker execution successful" -ForegroundColor Green
    $passed++
} catch {
    Write-Host " [FAIL] token-tracker failed: $_" -ForegroundColor Red
}

Write-Host "`nVerification Summary: $passed/$($checks.Count + 1) checks passed." -ForegroundColor Cyan
