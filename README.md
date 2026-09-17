<div align="center">

<img src="yuro.png" alt="Yuro mascot" width="220" style="margin-bottom: 12px;" />

# YURO

**Bounded context engine and autonomous tooling for AI coding agents.**  
Primary Target: Google Antigravity IDE | Portable Core for Claude Code, Gemini CLI, and Cursor

[![CI](https://github.com/WillyEverGreen/YURO/actions/workflows/ci.yml/badge.svg)](https://github.com/WillyEverGreen/YURO/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](pyproject.toml)
[![Platform Support](https://img.shields.io/badge/platform-Windows%20(Full)%20%7C%20Linux%2FmacOS%20(Core)-lightgrey.svg)](#platform-support-matrix)
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
Total Context: 15,581 tokens                       Total Context: 387 tokens (~97% reduction)
```

---

## Platform Support Matrix

YURO is architected in two distinct tiers:

| Tier | Platform | Support Level | Included Components |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Primary)** | **Windows 10 / 11** | Full Tool Suite | Complete 33 CLI tools, native `.cmd` wrappers, Everything IPC (`es-mini`), Windows diagnostics (`/status`, `/unlock`), background CDP daemon, and automated setup via `install.ps1`. |
| **Tier 2 (Portable Core)** | **Linux / macOS** | Portable Core | Cross-platform Python & Node engines (`cbm`, `token-tracker`, `token-audit`, `token-scan`, `rg-mini`, `fd-mini`, `token-save`) with POSIX shims via `install.sh`. |

---

## Safety & Execution Model (`auto-accept`)

Google Antigravity IDE is built around a human-in-the-loop safety model: agents propose bash commands, file modifications, and implementation plans, requiring explicit confirmation from the developer before execution.

The `auto-accept` daemon connects to Antigravity's local Chrome DevTools Protocol (CDP) port (`9333`) to automate repetitive modal approvals during rapid local iteration. Because unattended execution carries risks of destructive actions, `auto-accept` enforces the following guardrails:

1. **Keyword-Gated Halts (`askKeywords` & `skipKeywords`)**:
   - Commands containing destructive patterns (such as `rm -rf`, `drop table`, `git push --force`, `format c:`, `del /f /s /q`) are **automatically blocked from auto-confirmation** and require manual developer action in the IDE.
   - Operations like `git push` and `git reset --hard` pause for explicit interactive confirmation.
2. **Fail-Safe Operation**:
   - If Antigravity internal DOM classes or modal structures change after an upstream update, the daemon fails safe: it halts automatic clicking, emits a warning to the console, and leaves dialogs open for manual review.
3. **Session Audit Trail**:
   - Every approval and blocked command is appended to a local audit log at `~/.antigravity-auto-submit/session_audit.log` with timestamps, window titles, and command previews.

> **Warning**: `auto-accept` is an optional developer acceleration tool intended strictly for trusted local sandboxes. Do not run unattended on production machines or untrusted repositories.

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
  │ <350 tokens     │             │ <80 tokens      │             │ Guardrailed     │
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

## Empirical Benchmarks & Methodology

All metrics are measured against genuine open-source repositories using tasks defined in `benchmarks/tasks/`. Benchmark runners and raw outputs are published in `benchmarks/run_real_opensource_validation.py` and `benchmark_report.json`.

*Note on Token Accounting*: Token figures are derived using an empirical character baseline ($1\text{ token} \approx 3.8\text{ characters}$) directly from untruncated engine transcripts (`transcript_full.jsonl`). Exact BPE token counts (`cl100k_base` or `o200k_base`) will vary by 10% to 15% depending on indentation and code density.

### Benchmark 1: `expressjs/express` (64,000+ GitHub Stars)
*Target: Node.js web framework (996 AST nodes, 1,647 call edges)*

| Scenario | Task | Unbounded Baseline | YURO Optimized | Reduction Range | Latency Delta |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **1. Architecture & Deps** | Discover module layout & exports | 1,372 tok (1,043ms) | **221 tok** (2,117ms) | **~84%** | 2x slower |
| **2. Router Call Graph** | Trace `app.handle` request pipeline | 4,043 tok (1,175ms) | **160 tok** (2,558ms) | **~96%** | 2x slower |
| **3. Implementation Lookup**| Extract `res.json` source body | 6,871 tok (324ms) | **194 tok** (2,283ms) | **~97%** | 7x slower |
| **4. String Search** | Find `X-Powered-By` header refs | 161 tok (500ms) | **33 tok** (87ms) | **~80%** | **6x faster** |
| **CUMULATIVE WORKLOAD** | **4 Exploration Queries** | **12,447 tokens** | **608 tokens** | **85% - 95%** | **~11,839 tokens saved** |

### Benchmark 2: `pallets/flask` (66,000+ GitHub Stars)
*Target: Python WSGI web framework (multi-file module layout)*

| Scenario | Task | Unbounded Baseline | YURO Optimized | Reduction Range |
| :--- | :--- | :--- | :--- | :---: |
| **1. JSON Serialization** | Trace `jsonify` & `JSONProvider` pipeline | 10,000 tok (1,200ms) | **4,848 tok** (241ms) | **~52%** |
| **2. URL Routing Rules** | Locate `Blueprint` & `add_url_rule` | 10,000 tok (1,150ms) | **6,457 tok** (460ms) | **~35%** |
| **3. CLI Discovery** | Extract `FlaskGroup` command registration | 10,000 tok (980ms) | **5,210 tok** (195ms) | **~48%** |
| **4. Session Security** | Inspect `SecureCookieSessionInterface` | 10,000 tok (1,340ms) | **4,180 tok** (280ms) | **~58%** |
| **CUMULATIVE WORKLOAD** | **Full Feature Investigation** | **40,000 tokens** | **20,695 tokens** | **35% - 55%** |

### Variance Analysis
- **Monorepos and Web Applications** (e.g. Express, React apps): Yield **85% to 95% reduction** because call subgraphs pinpoint exact implementation blocks, eliminating multi-hundred-line file dumps.
- **Tightly Coupled Framework Libraries** (e.g. Flask, Axios): Yield **35% to 55% reduction** because a larger proportion of core type interfaces must be retained to maintain 100% task recall.

---

## Tool Reference

### 1. Autonomous Agent Daemons (Windows)
Background services for developer acceleration in Google Antigravity IDE:
* **`auto-accept` / `antigravity-auto-accept`**: Connects via Chrome DevTools Protocol (port 9333) with keyword guardrails to automatically approve safe modal prompts.

```cmd
auto-accept                  # Launch guardrailed auto-approval daemon
auto-accept --status         # Check CDP connection state and lifetime approvals
auto-accept --mode autopilot # Autopilot mode with keyword guardrails active
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
es-mini "<pattern>"          # Instant filename search via Everything IPC (Windows)
sg-mini "<pattern>" [lang]   # Structural AST syntax search
```

### 4. Ground-Truth Token Telemetry & Deterministic Replay
Forensic transcript parsers with exact BPE tokenizer verification (`cl100k_base`):
* **`token-replay`**: Deterministic counterfactual replay engine replaying session tool calls against historical repository Git snapshots.
* **`token-tracker`**: Parses untruncated session records (`transcript_full.jsonl`) with zero synthetic multipliers.
* **`token-audit`**: Terminal audit of active session context volume.
* **`token-scan`**: Multi-session scanner with optional `--csv` export for analytical reporting.

In our deterministic replay benchmark across multi-session workloads:
* YURO reduced tool-return payload volume by **29.0%** versus the defined Practical-Agent Baseline B, and **75.7%** versus the Naive Baseline A.
* Estimated cumulative context-turn exposure reduction: **36,023,844 token-turns** under Baseline B ($\sum (M - t) \times \Delta_t$).

```cmd
token-replay                 # Run deterministic counterfactual replay on active session
token-replay --ledger        # Inspect per-step ledger with resolution source and SHA-256 hashes
token-replay --all           # Aggregate deterministic replay across all historical sessions
token-audit                  # Audit active session context payload and volume
token-scan                   # Scan all historical chat sessions
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

### 6. IDE Health & Diagnostics (Windows)
Lifecycle utilities for Google Antigravity IDE:
* **`antigravity-brain` (`agy-brain`)**: Audits Antigravity IDE state, open sessions, and context transcript size.
* **`antigravity-clean` (`agy-clean`)**: Purges temporary scratch scripts, cached recordings, and orphaned logs.
* **`antigravity-check` (`agy-check`)**: Three-tier deletion audit scan (Safe / Review / Protected).

```cmd
agy-brain                    # Inspect IDE transcript size and session health
agy-clean                    # Purge safe scratch scripts and browser recordings
agy-check                    # Run 3-tier deletion safety audit
```

### 7. Workstation Diagnostics (`/toolbox` - Windows)
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

## Installation & Setup

### Windows (Full Suite)
Run in PowerShell:
```powershell
git clone https://github.com/WillyEverGreen/YURO.git
cd YURO
.\install.ps1
```

Or via one-line command:
```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/WillyEverGreen/YURO/main/install.ps1 | iex"
```

### Linux / macOS (Portable Core)
```bash
git clone https://github.com/WillyEverGreen/YURO.git
cd YURO
chmod +x install.sh
./install.sh
```

---

## Third-Party Software & Licenses

YURO bundles or interfaces with several open-source tools. All respective copyrights and licenses are preserved in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md):
- **ripgrep**: Andrew Gallant (BurntSushi) - MIT / Unlicense
- **fd**: David Peter (sharkdp) - MIT / Apache-2.0
- **ast-grep**: Herrington Darkholme - MIT
- **codebase-memory-mcp**: DeusData - MIT
- **repomix**: Kazuki Yamada (yamadashy) - MIT

---

## License

MIT License. See [LICENSE](LICENSE) for details.
