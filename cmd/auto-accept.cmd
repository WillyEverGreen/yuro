@echo off
if exist "%~dp0..\daemon\auto-accept\auto-accept.js" (
  node "%~dp0..\daemon\auto-accept\auto-accept.js" %*
) else if exist "%~dp0daemon\auto-accept\auto-accept.js" (
  node "%~dp0daemon\auto-accept\auto-accept.js" %*
) else if exist "%USERPROFILE%\tools\antigravity-auto-submit\auto-accept.js" (
  node "%USERPROFILE%\tools\antigravity-auto-submit\auto-accept.js" %*
) else (
  node "%~dp0auto-accept.js" %*
)
