@echo off
if exist "%~dp0..\scripts\replay_session.js" (
  node "%~dp0..\scripts\replay_session.js" %*
) else (
  node "C:\tools\replay_session.js" %*
)
