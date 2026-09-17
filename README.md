<div align="center">

<img src="yuro.png" alt="Yuro mascot" width="220" style="margin-bottom: 12px;" />

# YURO

**Bounded context engine and autonomous tooling for AI coding agents.**  
Flagship Target: Google Antigravity IDE | Universal CLI for Claude Code, Gemini CLI, and Cursor

[![CI](https://github.com/WillyEverGreen/YURO/actions/workflows/ci.yml/badge.svg)](https://github.com/WillyEverGreen/YURO/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](pyproject.toml)
[![Primary IDE](https://img.shields.io/badge/target-Google%20Antigravity-4285F4.svg)](#flagship-target-google-antigravity-ide)
[![Stars](https://img.shields.io/github/stars/WillyEverGreen/YURO?style=social)](https://github.com/WillyEverGreen/YURO)

---

</div>

## Overview

AI coding agents waste context during repository exploration. When investigating an unfamiliar codebase, agents typically run unrestricted searches, traverse full directories, and dump multiple source files into context. A single inquiry can consume 15,000 to 40,000 tokens when only 350 tokens of targeted evidence are actually needed.

Because conversational context accumulates turn over turn, early token bloat compounds on every subsequent step:
- **Attention degradation**: Key system instructions and past constraints get diluted.
- **Context compaction**: Session summaries drop nuanced implementation details.
- **Cost and latency inflation**: Large payloads slow model responses and drive up API bills.

YURO provides bounded tooling and AST graph intelligence for coding agents. Instead of loading whole files into model context, YURO indexes repositories into an SQLite graph and runs bounded search primitives, returning the exact evidence required for the task.

```text
                  UNBOUNDED BASELINE                                   WITH YURO
           (Full File Dumps & Uncapped Grep)               (AST Code Graph & Bounded Search)

Agent:                                             Agent:
  grep "app.handle"...          -> 380 tokens        cbm trace handle          -> 160 tokens
  read lib/application.js       -> 4,120 tokens                                   (call hierarchy)
  read lib/router/index.js      -> 4,210 tokens      cbm snippet json          -> 194 tokens
  read lib/response.js (1,150L) -> 6,871 tokens                                   (res.json body only)
                                                     rg-mini "X-Powered-By"    -> 33 tokens
                                                                                  (capped header match)
─────────────────────────────────────────────      ─────────────────────────────────────────────
Total Context: 15,581 tokens                       Total Context: 387 tokens (-97.5% reduction)
```

---

## Quick Start

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/WillyEverGreen/YURO/main/install.ps1 | iex"
```

Or clone and install locally:
```powershell
git clone https://github.com/WillyEverGreen/YURO.git
cd YURO
.\install.ps1
```

### Linux / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/WillyEverGreen/YURO/main/install.sh | bash
```

---

## Flagship Target: Google Antigravity IDE

While YURO provides universal CLI binaries compatible with Claude Code, Gemini CLI, Cursor, and Codex, **its primary design target is Google Antigravity IDE**.

YURO integrates with Antigravity across five key touchpoints:

1. **Autonomous Approval Daemon (`auto-accept`)**: Direct Chrome DevTools Protocol (CDP) daemon connecting to Antigravity on port `9333`. Automatically approves tool execution, terminal commands, and implementation plan modals without taking focus from mouse or keyboard.
2. **Ground-Truth Transcript Telemetry (`token-tracker` / `antigravity-brain`)**: Directly reads Antigravity untruncated session transcripts (`transcript_full.jsonl`). Computes exact character volumes, token usage, and per-tool payload metrics with zero synthetic multipliers.
3. **Global Rule Synchronization**: Deploys the deterministic T0-T5 routing protocol to `%USERPROFILE%\.gemini\config\rules\` so the model autonomously selects the most token-efficient tool.
4. **Modular Agent Skills**: Installs system diagnostic skills (`pc-toolbox`), web scrapers (`auto-scraper`), and concise output governors (`caveman-mode`) to `%USERPROFILE%\.gemini\config\skills\`.
5. **Model Context Protocol (MCP)**: Bundles native `codebase-memory` MCP configuration for on-demand graph queries.

---

## Architecture

YURO sits between the agent runtime and the filesystem, intercepting unstructured queries and routing them through bounded primitives:

```text
                      ┌─────────────────────────────────────────┐
                      │             AI CODING AGENT             │
                      │    Google Antigravity IDE (Flagship)    │
                      │      Claude Code / Gemini / Cursor      │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │               YURO ENGINE               │
                      │       T0-T5 Decision Protocol           │
                      └─────┬──────────────┬──────────────┬─────┘
                            │              │              │
           ┌────────────────┘              │              └────────────────┐
           ▼                               ▼                               ▼
  ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
  │ CODE GRAPH (cbm)│             │ BOUNDED SEARCH  │             │ AUTONOMOUS OPS  │
  │ Tree-sitter AST │             │ rg-mini/fd-mini │             │ auto-accept CDP │
  │ SQLite Cache    │             │ Max 20 Lines    │             │ Port 9333       │
  │ <350 tokens     │             │ <80 tokens      │             │ Background      │
  └─────────────────┘             └─────────────────┘             └─────────────────┘
           │                               │                               │
           └────────────────┬──────────────┴───────────────┬───────────────┘
                            ▼                               ▼
                  ┌───────────────────┐           ┌───────────────────┐
                  │  TOKEN AUDITING   │           │ CONTEXT PRUNING   │
                  │  token-tracker    │           │ token-save / AST  │
                  │  transcript_full  │           │ structural-prune  │
                  └───────────────────┘           └───────────────────┘
```

---

## Empirical Benchmarks

All metrics are measured against public open-source repositories using exact character token accounting (1 token ≈ 3.8 characters) from raw agent transcripts:

### Benchmark 1: `expressjs/express` (64,000+ GitHub Stars)
*Target: Node.js web framework (996 AST nodes, 1,647 call edges)*

| Scenario | Task | Unbounded Baseline | YURO Optimized | Context Reduction | Latency Delta |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **1. Architecture & Deps** | Discover module layout & exports | 1,372 tok (1,043ms) | **221 tok** (2,117ms) | **-84%** | 2x slower |
| **2. Router Call Graph** | Trace `app.handle` request pipeline | 4,043 tok (1,175ms) | **160 tok** (2,558ms) | **-96%** | 2x slower |
| **3. Implementation Lookup**| Extract `res.json` source body | 6,871 tok (324ms) | **194 tok** (2,283ms) | **-97%** | 7x slower |
| **4. String Search** | Find `X-Powered-By` header refs | 161 tok (500ms) | **33 tok** (87ms) | **-80%** | **6x faster** |
| **CUMULATIVE WORKLOAD** | **4 Exploration Queries** | **12,447 tokens** | **608 tokens** | **-95.1%** | **~11,839 tokens saved** |

### Benchmark 2: `pallets/flask` (66,000+ GitHub Stars)
*Target: Python WSGI web framework (multi-file module layout)*

| Scenario | Task | Unbounded Baseline | YURO Optimized | Context Reduction |
| :--- | :--- | :--- | :--- | :---: |
| **1. JSON Serialization** | Trace `jsonify` & `JSONProvider` pipeline | 10,000 tok (1,200ms) | **4,848 tok** (241ms) | **-51.5%** |
| **2. URL Routing Rules** | Locate `Blueprint` & `add_url_rule` | 10,000 tok (1,150ms) | **6,457 tok** (460ms) | **-35.4%** |
| **3. CLI Discovery** | Extract `FlaskGroup` command registration | 10,000 tok (980ms) | **5,210 tok** (195ms) | **-47.9%** |
| **4. Session Security** | Inspect `SecureCookieSessionInterface` | 10,000 tok (1,340ms) | **4,180 tok** (280ms) | **-58.2%** |
| **CUMULATIVE WORKLOAD** | **Full Feature Investigation** | **40,000 tokens** | **20,695 tokens** | **-48.3%** |

### Variance Analysis
- **Monorepos and Web Applications** (e.g. Express, React apps): Yield **85% to 95%+ reduction** because call subgraphs pinpoint exact implementation blocks, eliminating multi-hundred-line file dumps.
- **Tightly Coupled Framework Libraries** (e.g. Flask, Axios): Yield **35% to 55% reduction** because a larger proportion of core type interfaces must be retained to maintain 100% task recall.

---

## Tool Reference

All production tools are installed to `C:\tools` (automatically configured in User `PATH`):

### 1. Autonomous Agent Daemons
Background services for unattended agent operation:
* **`auto-accept` / `antigravity-auto-accept`**: Connects via Chrome DevTools Protocol (port 9333) to automatically approve modal prompts (bash commands, file writes, plan approvals).

```cmd
auto-accept                  # Launch autonomous modal approval daemon
auto-accept --status         # Check CDP connection state and lifetime approvals
auto-accept --mode autopilot # Aggressive autopilot approval mode
```

### 2. Codebase Graph Intelligence (`cbm`)
Tree-sitter AST and SQLite graph intelligence for navigating codebases in <350 tokens:
* **`cbm` / `cbm-mini`**: Instant symbol lookup, call hierarchy tracing, and architectural summaries.
* **`codebase-memory-mcp`**: Native compiled binary backend serving the Model Context Protocol (MCP) interface.

```cmd
cbm index <path>             # Index repository AST into SQLite graph
cbm arch <project>           # High-level architecture and module layout (<350 tokens)
cbm search <project> <sym>   # Exact symbol definition lookup (<200 tokens)
cbm trace <project> <func>   # Complete call hierarchy and callers (<200 tokens)
cbm snippet <project> <sym>  # Extract qualified function source lines (<180 tokens)
cbm outline <project> <file> # File-level symbol outline (<60 tokens)
```

### 3. Bounded High-Speed Search
Strictly capped CLI search wrappers that eliminate runaway terminal output:
* **`rg-mini`**: Ripgrep wrapper bounded to 20 output lines (<80 tokens).
* **`fd-mini`**: Directory finder capped at 20 results.
* **`es-mini`**: Voidtools Everything IPC search for instant Windows indexing (15 results).
* **`sg-mini`**: Structural AST pattern matching powered by `ast-grep`.

```cmd
rg-mini "<query>" [path]     # Bounded code search (max 20 lines)
fd-mini "<pattern>" [path]   # Bounded file search (max 20 results)
es-mini "<pattern>"          # Instant filename search via Everything IPC
sg-mini "<pattern>" [lang]   # Structural AST syntax search
```

### 4. Ground-Truth Token Telemetry
Forensic transcript parsers with exact BPE character counting (1 token ≈ 3.8 characters):
* **`token-tracker`**: Parses untruncated session records (`transcript_full.jsonl`) with zero synthetic multipliers.
* **`token-audit`**: Instant terminal audit of the active session context volume.
* **`token-scan`**: Multi-session scanner with optional `--csv` export for analytical reporting.

```cmd
token-audit                  # Audit active session context payload and volume
token-scan                   # Scan all historical chat sessions
token-scan -n 5              # Scan the last 5 sessions
token-tracker audit --all    # Global cumulative tool cost breakdown
token-scan --csv > data.csv  # Export metrics to CSV for analysis
```

### 5. Context Pruning & Compression
Evidence extraction engines that discard irrelevant code while preserving syntactic invariants:
* **`token-save` / `tokensaver-v5`**: AST context compression engine for Python tracebacks and error logs.
* **`structural-prune`**: AST-level comment and docstring optimizer preserving executable invariants.
* **`code-sig`**: Class and function signature extractor.
* **`repomix --compress`**: Whole-repository Tree-sitter AST compression for full audits.

```cmd
token-save auto "<prompt>" "<dir>" # Prune Python traceback and error context
structural-prune <file>            # Strip non-semantic comments and docstrings
code-sig <file>                    # Extract symbol definitions without bodies
npx repomix --compress             # Pack entire repository with AST compression
```

### 6. IDE Health & Memory Management
Lifecycle utilities for Google Antigravity IDE:
* **`antigravity-brain` (`agy-brain`)**: Audits Antigravity IDE state, open sessions, and context transcript size.
* **`antigravity-clean` (`agy-clean`)**: Purges temporary scratch scripts, cached recordings, and orphaned logs.
* **`antigravity-check` (`agy-check`)**: Three-tier deletion audit scan (Safe / Review / Protected).

```cmd
agy-brain                    # Inspect IDE transcript size and session health
agy-clean                    # Purge safe scratch scripts and browser recordings
agy-check                    # Run 3-tier deletion safety audit
```

### 7. Workstation Diagnostics (`/toolbox`)
System-level diagnostic and optimization suite for high-performance agent workflows:
* **`/status`**: Quick workstation health check (RAM %, drive space, power plan) in compact mode.
* **`/info`**: Clean hardware and OS summary via `fastfetch` without ASCII art.
* **`/diagnose`**: Identifies top CPU and RAM consumers.
* **`/security`**: Inspects Windows Defender shield status and active firewall profiles.
* **`/startup`**: Audits top startup applications.
* **`/unlock <path>`**: Detects and unlocks file-locking process IDs via Windows Restart Manager.
* **`/clean`**: Runs safe system temp, pip, and npm cache purges.
* **`/boost`**: Trims working set memory when system commit charge approaches limits.

```cmd
cmd.exe /c "toolbox Status -Compact" # Workstation telemetry (<70 tokens)
cmd.exe /c "toolbox Diagnose"        # Analyze top resource consumers
cmd.exe /c "toolbox Unlock <path>"   # Release locked files
cmd.exe /c "toolbox Clean"           # Purge temp files and cache
cmd.exe /c "toolbox BoostRAM"        # Emergency working set memory trim
```

### 8. Automation & Specialized Skills
* **`auto-scraper`**: Multi-tier web extraction engine (Direct HTTP -> agent-browser CLI -> Playwright -> CDP subagent).
* **`playwright-cli`**: Headless browser automation runner.
* **`md-mermaid`**: Local command-line compiler for Mermaid diagrams.
* **`caveman-mode`**: High-density communication governor that reduces LLM output token consumption by 50%+.

---

## T0-T5 Routing Protocol

Agents operating with YURO adhere to a deterministic tool hierarchy. Apply the **FIRST** matching tier:

| Tier | Protocol Level | Trigger Condition | Approved Action | Token Budget |
| :--- | :--- | :--- | :--- | :--- |
| **T0** | **Direct Answer** | Casual chat, concepts, general Q&A | *Zero tools* | 0 |
| **T1** | **Direct File Edit** | File path or line numbers already known | `view_file(StartLine, EndLine)` + `replace_file_content` | <150 tok |
| **T2** | **Graph Intelligence** | Architecture, symbol lookup, call hierarchies | `cbm arch`, `cbm search`, `cbm trace`, `cbm snippet` | 100-350 tok |
| **T3** | **Capped Text Search** | Literal strings, regex, config keys, filenames | `rg-mini`, `fd-mini`, `es-mini` (max 20 lines) | <80 tok |
| **T4** | **Python Traceback** | Python project + explicit error log + >20 files | `token-save auto "<prompt>" "<dir>"` | 300-600 tok |
| **T5** | **Full Repo Audit** | Whole-repo architectural audit in one shot | `npx repomix --compress` | Whole-repo |

### Invariant Rules
- Do not run `cbm` or `grep` when the target file and line are already known. Use `view_file` directly (T1).
- Do not view full files without `StartLine` and `EndLine` parameters (max 60 lines per read).
- Do not run uncapped `Get-ChildItem -Recurse` or raw `grep` commands.
- Do not load MCP schemas eagerly; invoke the compiled `cbm` CLI directly.

---

## Agent Integrations

| Agent / Environment | Integration Mode | Configuration |
| :--- | :--- | :--- |
| **Google Antigravity IDE** *(Flagship)* | Native CDP Daemon (`auto-accept`), Rules & Skills Sync | Automatically configured via `install.ps1` |
| **Claude Code** | Global CLI tools (`cbm`, `rg-mini`, `token-audit`) | Native User `PATH` integration |
| **Gemini CLI / Codex** | System rules & execution wrappers | Linked through `%USERPROFILE%\.gemini\config\` |
| **Cursor / VS Code** | Shell tools & terminal subagents | Included in workspace shell environment |
| **Model Context Protocol (MCP)** | Lazy MCP server (`codebase-memory`) | Pre-configured in `mcp/mcp_config.global.json` |

---

## Repository Layout

```text
YURO/
├── yuro.png                      # Official Mascot & Identity
├── cmd/                          # Production CLI tools & wrappers (33 tools)
│   ├── auto-accept.cmd           # Antigravity IDE modal auto-approval daemon
│   ├── antigravity-auto-accept.cmd
│   ├── token-tracker.js          # Ground-truth transcript parser & auditor
│   ├── token-audit.cmd           # Instant session audit command
│   ├── token-scan.cmd            # Multi-session scanner command
│   ├── cbm.cmd                   # Codebase Memory graph runner
│   ├── cbm-mini.cmd              # Graph overview & status
│   ├── rg-mini.cmd               # Bounded ripgrep wrapper (max 20 lines)
│   ├── fd-mini.cmd               # Bounded file search wrapper
│   ├── es-mini.cmd               # Everything IPC search wrapper
│   ├── sg-mini.cmd               # ast-grep structural search wrapper
│   ├── token-save.cmd            # Python AST pruner
│   ├── antigravity-brain.cmd     # IDE memory & transcript analyzer
│   ├── antigravity-clean.cmd     # IDE crash/temp cleaner
│   ├── antigravity-check.cmd     # IDE 3-tier deletion checker
│   ├── code-sig.cmd              # Code signature extractor
│   ├── structural-prune.cmd      # AST docstring & comment trimmer
│   ├── playwright-cli.cmd        # Headless browser runner
│   └── md-mermaid.cmd            # Mermaid diagram compiler
├── daemon/                       # Background services
│   └── auto-accept/              # Antigravity CDP auto-approval daemon source
├── bin/                          # Standalone binaries (rg.exe, fd.exe, ast-grep.exe)
├── rules/                        # Global agent rules
│   ├── T0-T5-protocol.md         # Master decision protocol
│   ├── token-saver.md            # Python traceback context rule
│   ├── pc-commands.md            # Slash command shortcuts
│   └── agent-browser-default.md  # Browser automation policy
├── skills/                       # Modular Antigravity skills
│   ├── pc-toolbox/               # Workstation CLI & diagnostics
│   ├── auto-scraper/             # Multi-tier web extraction engine
│   └── caveman-mode/             # High-density agent output protocol
├── mcp/                          # Model Context Protocol configurations
│   ├── mcp_config.global.json    # Global MCP template
│   ├── mcp_config.ide.json       # IDE remote plugins template
│   └── setup-guide.md            # Cross-platform MCP deployment guide
├── src/                          # TokenSaver core Python package
│   └── tokensaver/               # AST parsing, BM25 retrieval, evidence assembly
├── install.ps1                   # One-click Windows PowerShell installer
├── install.sh                    # One-click Linux/macOS Bash installer
├── verify.ps1                    # Verification & sanity test suite (11/11 tests)
├── package.json                  # NPM scripts & metadata (v2.0.0)
├── pyproject.toml                # Python package metadata (v2.0.0)
└── LICENSE                       # MIT License
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
