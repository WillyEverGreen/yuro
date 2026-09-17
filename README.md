<div align="center">

<img src="yuro.png" alt="Yuro mascot" width="240" style="margin-bottom: 15px;" />

# YURO

**The Autonomous Context & Tooling Engine for AI Coding Agents.**  
*Primary Focus: Google Antigravity IDE • Universal CLI Support for Claude Code, Gemini CLI & Cursor*

[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v2.0.0%20Unified-blue.svg)](pyproject.toml)
[![Primary IDE](https://img.shields.io/badge/Primary%20IDE-Google%20Antigravity-4285F4.svg)](#-flagship-target-google-antigravity-ide)
[![Context Reduction](https://img.shields.io/badge/Context%20Reduction--95%25%20Empirical-success.svg)](#-empirical-benchmarks-on-open-source-codebases)
[![Architecture](https://img.shields.io/badge/Architecture-T0--T5%20Routing-cyan.svg)](#-the-t0-t5-unified-routing-protocol)

---

</div>

## Overview

Modern AI coding agents are exceptional at reasoning, but fundamentally inefficient at context management. When investigating unfamiliar codebases, agents routinely run unrestricted greps, crawl directory trees, and dump dozens of full source files into context—spending **15,000 to 40,000 tokens** on inquiries that require **under 350 tokens** of targeted evidence.

Because LLM context accumulates turn-over-turn, unconstrained file dumping causes prompt bloat to compound exponentially, triggering:
- **Model Amnesia**: Critical instructions pushed outside the active attention window.
- **Context Compaction**: Loss of granular nuances and past implementation history.
- **Inflated Costs & Latency**: Large payloads driving up token bills and response wait times.

**YURO is the bounded context and autonomous execution layer.** It provides AST-indexed code graphs, strictly bounded search wrappers, ground-truth token telemetry, and autonomous approval daemons that preserve model intelligence while eliminating token waste.

```text
                  WITHOUT YURO                                         WITH YURO
        (Blind Exploration & File Dumps)                   (Bounded Graph & Context Engine)

Agent:                                             Agent:
  grep "app.handle"...          -> 380 tokens        cbm trace handle          -> 160 tokens
  read lib/application.js       -> 4,120 tokens                                   (exact call hierarchy)
  read lib/router/index.js      -> 4,210 tokens      cbm snippet json          -> 194 tokens
  read lib/response.js (1,150L) -> 6,871 tokens                                   (res.json body only)
                                                     rg-mini "X-Powered-By"    -> 33 tokens
                                                                                  (capped header match)
─────────────────────────────────────────────      ─────────────────────────────────────────────
TOTAL DUMPED: 15,581 tokens 💥                     TOTAL DUMPED: 387 tokens 🚀 (-97.5% reduction)
```

---

## 🎯 Flagship Target: Google Antigravity IDE

While YURO delivers universal CLI tools compatible with Claude Code, Gemini CLI, Cursor, and Codex, **its primary design and flagship target is Google Antigravity IDE**.

YURO integrates natively with Antigravity's architectural layers:

1. **Autonomous Approval Daemon (`auto-accept`)**: Direct Chrome DevTools Protocol (CDP) daemon that monitors Antigravity's internal WebView to auto-approve tool execution, bash commands, and plan dialogs without stealing physical mouse or keyboard focus.
2. **Ground-Truth Transcript Telemetry (`token-tracker` / `antigravity-brain`)**: Directly parses Antigravity's untruncated session records (`transcript_full.jsonl`) to measure exact character volumes, token consumption, and tool payloads without synthetic multipliers.
3. **Global Rule Injection**: Automatically deploys the deterministic `T0-T5` protocol into `%USERPROFILE%\.gemini\config\rules\` so the agent autonomously chooses the correct tool tier.
4. **Modular Agent Skills**: Seamlessly delivers workstation diagnostic skills (`pc-toolbox`), multi-tier scrapers (`auto-scraper`), and concise token governors (`caveman-mode`) to `%USERPROFILE%\.gemini\config\skills\`.
5. **Model Context Protocol (MCP)**: Bundles native `codebase-memory` MCP server configurations for lazy graph-backed symbol discovery.

---

## Architecture

YURO sits directly between the AI agent and the underlying filesystem, replacing unbounded shell tools with deterministic, bounded primitives:

```text
                      ┌─────────────────────────────────────────┐
                      │             AI CODING AGENT             │
                      │  ★ Google Antigravity IDE (Flagship)   │
                      │    Claude Code / Gemini / Cursor        │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │               YURO ENGINE               │
                      │    T0–T5 Deterministic Routing Protocol │
                      └─────┬──────────────┬──────────────┬─────┘
                            │              │              │
           ┌────────────────┘              │              └────────────────┐
           ▼                               ▼                               ▼
  ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
  │ CODE GRAPH (cbm)│             │ BOUNDED SEARCH  │             │ AUTONOMOUS OPS  │
  │ Tree-sitter AST │             │ rg-mini/fd-mini │             │ auto-accept CDP │
  │ SQLite Cache    │             │ Max 20 Lines    │             │ Zero-Blocking   │
  │ <350 tokens     │             │ <80 tokens      │             │ 100% Unattended │
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

## 📊 Empirical Benchmarks on Open-Source Codebases

All metrics are measured against genuine, public open-source repositories using exact character token counting ($1\text{ token} \approx 3.8\text{ chars}$) from raw agent transcripts:

### Benchmark 1: `expressjs/express` (64,000+ GitHub Stars)
*Target: Standard Node.js Web Framework (996 AST nodes, 1,647 call edges)*

| Scenario | Task | Unbounded Baseline | YURO Optimized | Context Reduction | Speed Delta |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **1. Architecture & Deps** | Discover module layout & exports | 1,372 tok (1,043ms) | **221 tok** (2,117ms) | **-84%** | 2x slower |
| **2. Router Call Graph** | Trace `app.handle` request pipeline | 4,043 tok (1,175ms) | **160 tok** (2,558ms) | **-96%** | 2x slower |
| **3. Implementation Lookup**| Extract `res.json` source body | 6,871 tok (324ms) | **194 tok** (2,283ms) | **-97%** | 7x slower |
| **4. String Search** | Find `X-Powered-By` header refs | 161 tok (500ms) | **33 tok** (87ms) | **-80%** | **6x faster** |
| **CUMULATIVE WORKLOAD** | **4 Exploration Queries** | **12,447 tokens** | **608 tokens** | **-95.1%** | **~11,839 tokens saved** |

### Benchmark 2: `pallets/flask` (66,000+ GitHub Stars)
*Target: Python WSGI Web Framework (Multi-file module architecture)*

| Scenario | Task | Unbounded Baseline | YURO Optimized | Context Reduction |
| :--- | :--- | :--- | :--- | :---: |
| **1. JSON Serialization** | Trace `jsonify` & `JSONProvider` pipeline | 10,000 tok (1,200ms) | **4,848 tok** (241ms) | **-51.5%** |
| **2. URL Routing Rules** | Locate `Blueprint` & `add_url_rule` | 10,000 tok (1,150ms) | **6,457 tok** (460ms) | **-35.4%** |
| **3. CLI Discovery** | Extract `FlaskGroup` command registration | 10,000 tok (980ms) | **5,210 tok** (195ms) | **-47.9%** |
| **4. Session Security** | Inspect `SecureCookieSessionInterface` | 10,000 tok (1,340ms) | **4,180 tok** (280ms) | **-58.2%** |
| **CUMULATIVE WORKLOAD** | **Full Feature Investigation** | **40,000 tokens** | **20,695 tokens** | **-48.3%** |

> **Variance Analysis**:
> - **Monorepos & Web Applications** (e.g. Express): Achieve **85% to 95%+ net reduction** because subgraphs pinpoint exact call hierarchies, eliminating massive file dumps.
> - **Tightly Coupled Framework Libraries** (e.g. Flask, Axios): Achieve **35% to 55% net reduction** because higher proportions of core interface types must be retained to maintain 100% task recall.

---

## 🛠️ The Complete Tool Suite

YURO consolidates every tool required for high-efficiency agentic development into `C:\tools` (added to User `PATH`):

### 1. Autonomous Agent Daemons
Lightweight CDP background daemons designed for unattended agent operation in Google Antigravity IDE:
* **`auto-accept` / `antigravity-auto-accept`**: Connects via Chrome DevTools Protocol (`port 9333`) to automatically approve confirmation dialogs (bash commands, file writes, plan approvals) without stealing mouse or keyboard focus.

```cmd
auto-accept                  # Launch autonomous modal approval daemon
auto-accept --status         # Check CDP connection state and lifetime approvals
auto-accept --mode autopilot # Aggressive autopilot approval mode
```

### 2. Codebase Graph Intelligence (`cbm`)
Tree-sitter AST and SQLite graph intelligence for navigating large codebases in <350 tokens:
* **`cbm` / `cbm-mini`**: Instant symbol lookup, call hierarchy tracing, and architectural summaries.
* **`codebase-memory-mcp`**: Native compiled binary backend serving the Model Context Protocol (MCP) interface.

```cmd
cbm index <path>             # Index repository AST into SQLite graph
cbm arch <project>           # High-level architecture & module layout (<350 tokens)
cbm search <project> <sym>   # Exact symbol definition lookup (<200 tokens)
cbm trace <project> <func>   # Complete call hierarchy & callers (<200 tokens)
cbm snippet <project> <sym>  # Extract qualified function source lines (<180 tokens)
cbm outline <project> <file> # File-level symbol outline (<60 tokens)
```

### 3. Bounded High-Speed Search
Strictly capped CLI search wrappers that eliminate runaway terminal output:
* **`rg-mini`**: Ripgrep wrapper bounded to **20 output lines** (<80 tokens).
* **`fd-mini`**: Directory finder capped at **20 results**.
* **`es-mini`**: Voidtools Everything IPC search for instant Windows indexing (15 results).
* **`sg-mini`**: Structural AST pattern matching powered by `ast-grep`.

```cmd
rg-mini "<query>" [path]     # Bounded code search (max 20 lines)
fd-mini "<pattern>" [path]   # Bounded file search (max 20 results)
es-mini "<pattern>"          # Instant filename search via Everything IPC
sg-mini "<pattern>" [lang]   # Structural AST syntax search
```

### 4. Ground-Truth Token Telemetry
Forensic transcript parsers with exact BPE character counting ($1\text{ tok} \approx 3.8\text{ chars}$):
* **`token-tracker`**: Parses untruncated session records (`transcript_full.jsonl`) with zero synthetic multipliers.
* **`token-audit`**: Instant terminal audit of the active session's context volume.
* **`token-scan`**: Multi-session scanner with optional `--csv` export for analytical reporting.

```cmd
token-audit                  # Audit active session context payload & volume
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
token-save auto "<prompt>" "<dir>" # Prune Python traceback & error context
structural-prune <file>            # Strip non-semantic comments & docstrings
code-sig <file>                    # Extract symbol definitions without bodies
npx repomix --compress             # Pack entire repository with AST compression
```

### 6. IDE Health & Memory Management
Dedicated lifecycle utilities for Google Antigravity IDE:
* **`antigravity-brain` (`agy-brain`)**: Audits Antigravity IDE state, open sessions, and context transcript size.
* **`antigravity-clean` (`agy-clean`)**: Purges temporary scratch scripts, cached recordings, and orphaned logs.
* **`antigravity-check` (`agy-check`)**: Three-tier deletion audit scan (🟢 Safe / 🟡 Review / 🔴 Protected).

```cmd
agy-brain                    # Inspect IDE transcript size & session health
agy-clean                    # Purge safe scratch scripts and browser recordings
agy-check                    # Run 3-tier deletion safety audit
```

### 7. Workstation Diagnostics (`/toolbox`)
System-level diagnostic and optimization suite for high-performance agent workflows:
* **`/status`**: Quick workstation health check (RAM %, drive space, power plan) in compact mode.
* **`/info`**: Clean hardware and OS summary via `fastfetch` without bloated ASCII art.
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
cmd.exe /c "toolbox Clean"           # Purge temp files & cache
cmd.exe /c "toolbox BoostRAM"        # Emergency working set memory trim
```

### 8. Automation & Specialized Skills
* **`auto-scraper`**: Multi-tier web extraction engine (Direct HTTP -> agent-browser CLI -> Playwright -> CDP subagent).
* **`playwright-cli`**: Headless browser automation runner.
* **`md-mermaid`**: Local command-line compiler for Mermaid diagrams.
* **`caveman-mode`**: High-density communication governor that reduces LLM output token consumption by 50%+.

---

## 🎯 The T0–T5 Unified Routing Protocol

Agents operating with YURO adhere to a deterministic tool hierarchy. Apply the **FIRST** matching tier:

| Tier | Protocol Level | Trigger Condition | Approved Action | Token Budget |
| :--- | :--- | :--- | :--- | :--- |
| **T0** | **Direct Answer** | Casual chat, concepts, general Q&A | *Zero tools* | 0 |
| **T1** | **Direct File Edit** | File path or line numbers already known | `view_file(StartLine, EndLine)` + `replace_file_content` | <150 tok |
| **T2** | **Graph Intelligence** | Architecture, symbol lookup, call hierarchies | `cbm arch`, `cbm search`, `cbm trace`, `cbm snippet` | 100–350 tok |
| **T3** | **Capped Text Search** | Literal strings, regex, config keys, filenames | `rg-mini`, `fd-mini`, `es-mini` (max 20 lines) | <80 tok |
| **T4** | **Python Traceback** | Python project + explicit error log + >20 files | `token-save auto "<prompt>" "<dir>"` | 300–600 tok |
| **T5** | **Full Repo Audit** | Whole-repo architectural audit in one shot | `npx repomix --compress` | Whole-repo |

### 🔒 Operational Rules
- ❌ **NEVER** run `cbm` or `grep` when the target file and line are already known. Use `view_file` directly (T1).
- ❌ **NEVER** view full files without `StartLine` and `EndLine` parameters (max 60 lines per read).
- ❌ **NEVER** run uncapped `Get-ChildItem -Recurse` or raw `grep` commands.
- ❌ **NEVER** load MCP schemas eagerly; invoke the compiled `cbm` CLI directly.

---

## 🚀 Installation & Setup

### Windows (One-Click Setup)
Run in PowerShell:
```powershell
git clone https://github.com/WillyEverGreen/YURO.git
cd YURO
.\install.ps1
```

*What `install.ps1` automates:*
1. Deploys all 33 CLI tools, wrappers, and background daemons into `C:\tools\`.
2. Automatically downloads and installs `codebase-memory-mcp.exe` v0.11.0 if not already present.
3. Appends `C:\tools` to User Environment `PATH`.
4. Synchronizes global rules to `%USERPROFILE%\.gemini\config\rules\`.
5. Synchronizes modular skills to `%USERPROFILE%\.gemini\config\skills\`.
6. Configures global `mcp_config.json` for Antigravity IDE and MCP clients.
7. Executes the 11-point automated verification suite.

### Linux / macOS
```bash
git clone https://github.com/WillyEverGreen/YURO.git
cd YURO
chmod +x install.sh
./install.sh
```

---

## 🔌 Agent Integrations

| Agent / Environment | Integration Mode | Configuration |
| :--- | :--- | :--- |
| **Google Antigravity IDE** *(Flagship)* | Native CDP Daemon (`auto-accept`), Rules & Skills Sync | Automatically configured via `install.ps1` |
| **Claude Code** | Global CLI tools (`cbm`, `rg-mini`, `token-audit`) | Native User `PATH` integration |
| **Gemini CLI / Codex** | System rules & execution wrappers | Linked through `%USERPROFILE%\.gemini\config\` |
| **Cursor / VS Code** | Shell tools & terminal subagents | Included in workspace shell environment |
| **Model Context Protocol (MCP)** | Lazy MCP server (`codebase-memory`) | Pre-configured in `mcp/mcp_config.global.json` |

---

## 📂 Repository Layout

```text
YURO/
├── yuro.png                      # Official Fox Mascot & Identity
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

<div align="center">
<b>YURO</b> • Engineered for Maximum Cognitive Density and Zero Context Waste. 🦊
</div>
