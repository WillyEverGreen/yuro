@echo off
setlocal

set "CMD=%~1"

if "%CMD%"=="" goto help
if /i "%CMD%"=="help" goto help
if /i "%CMD%"=="index" goto do_index
if /i "%CMD%"=="search" goto do_search
if /i "%CMD%"=="trace" goto do_trace
if /i "%CMD%"=="query" goto do_query
if /i "%CMD%"=="list" goto do_list
if /i "%CMD%"=="stats" goto do_stats
if /i "%CMD%"=="arch" goto do_arch
if /i "%CMD%"=="outline" goto do_outline
if /i "%CMD%"=="snippet" goto do_snippet
if /i "%CMD%"=="ui" goto do_ui

:: Fallback: pass through to cli directly
C:\tools\codebase-memory-mcp.exe cli --quiet %* <nul
exit /b %ERRORLEVEL%

:help
echo Usage: cbm [index^|search^|trace^|arch^|outline^|snippet^|query^|list^|stats^|ui] [args...]
echo   cbm index [repo_path]             Index repository into graph (fast mode)
echo   cbm search [project] [pattern]    Search symbols by regex pattern
echo   cbm trace [project] [function]    Trace call hierarchy both directions
echo   cbm arch [project]                Get architectural overview
echo   cbm outline [project] [file]      Get all symbols in a file
echo   cbm snippet [project] [qname]     Get source lines for a qualified symbol name
echo   cbm query [project] [cypher]      Run raw Cypher graph query
echo   cbm list                          List all indexed projects
echo   cbm stats [project]               Get index status and coverage
echo   cbm ui                            Launch visual graph at http://localhost:9749
echo.
echo When to use what:
echo   Architecture/symbols  -^> cbm arch / cbm search / cbm trace  (T2)
echo   Literal string search -^> rg-mini (NOT cbm)                  (T3)
echo   Python traceback      -^> token-save auto (NOT cbm)          (T4)
echo   File path known       -^> view_file direct (NOT cbm)         (T1)
exit /b 0

:do_index
set "REPO=%~2"
if "%REPO%"=="" set "REPO=."
C:\tools\codebase-memory-mcp.exe cli --quiet index_repository --repo-path "%REPO%" --mode fast <nul
exit /b %ERRORLEVEL%

:do_search
set "PROJ=%~2"
set "PAT=%~3"
C:\tools\codebase-memory-mcp.exe cli --quiet search_graph --project "%PROJ%" --name-pattern "%PAT%" --max-output-tokens 800 <nul
exit /b %ERRORLEVEL%

:do_trace
set "PROJ=%~2"
set "FN=%~3"
C:\tools\codebase-memory-mcp.exe cli --quiet trace_path --project "%PROJ%" --function-name "%FN%" --max-output-tokens 800 <nul
exit /b %ERRORLEVEL%

:do_arch
set "PROJ=%~2"
C:\tools\codebase-memory-mcp.exe cli --quiet get_architecture --project "%PROJ%" <nul
exit /b %ERRORLEVEL%

:do_outline
set "PROJ=%~2"
set "FPATH=%~3"
C:\tools\codebase-memory-mcp.exe cli --quiet get_file_outline --project "%PROJ%" --file-path "%FPATH%" <nul
exit /b %ERRORLEVEL%

:do_snippet
set "PROJ=%~2"
set "QN=%~3"
C:\tools\codebase-memory-mcp.exe cli --quiet get_code_snippet --project "%PROJ%" --qualified-name "%QN%" --max-output-tokens 800 <nul
exit /b %ERRORLEVEL%

:do_query
set "PROJ=%~2"
set "CYPHER=%~3"
C:\tools\codebase-memory-mcp.exe cli --quiet query_graph --project "%PROJ%" --query "%CYPHER%" --max-output-tokens 800 <nul
exit /b %ERRORLEVEL%

:do_list
C:\tools\codebase-memory-mcp.exe cli --quiet list_projects <nul
exit /b %ERRORLEVEL%

:do_stats
set "PROJ=%~2"
C:\tools\codebase-memory-mcp.exe cli --quiet index_status --project "%PROJ%" <nul
exit /b %ERRORLEVEL%

:do_ui
C:\tools\codebase-memory-mcp.exe --ui=true --port=9749
exit /b %ERRORLEVEL%
