<div align="center">

<img src="yuro.png" alt="Yuro mascot" width="240" style="margin-bottom: 15px;" />

# Yuro

**The Context Engine for AI Coding Agents.**  
*Understand large codebases with 80%+ less context.*

[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v2.0.0%20Unified-blue.svg)](pyproject.toml)
[![Context Reduction](https://img.shields.io/badge/Context%20Reduction--95%25%20Empirical-success.svg)](#-empirical-benchmarks-proven-on-production-codebases)
[![Integrations](https://img.shields.io/badge/Integrations-Claude%20%7C%20Gemini%20%7C%20Cursor%20%7C%20Codex%20%7C%20MCP-purple.svg)](#-agent-integrations)
[![Architecture](https://img.shields.io/badge/Architecture-T0--T5%20Routing-cyan.svg)](#-the-t0-t5-unified-routing-protocol)

---

</div>

## ⚡ The 10-Second Pitch

Modern AI coding agents (Claude Code, Gemini CLI, Cursor, Antigravity) are brilliant at reasoning, but **notoriously wasteful with context**. When an agent investigates an unfamiliar codebase, it blindly greps, crawls directory trees, and dumps 10 full source files into prompt context—blowing **15,000 to 40,000 tokens** on questions that can be answered in **under 350 tokens**.

Because LLM context accumulates turn-over-turn, early token bloat compounds on every subsequent turn, rapidly triggering model amnesia, bloated API bills, and context compaction.

**YURO is the "don't be stupid with context" layer underneath your agent.**

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

## 🏛️ What YURO Actually Is

YURO is not an AI model or a standalone chat app. **Claude, Gemini, and GPT remain the brain.**

YURO is the **agent-side context optimization engine** that equips the model with bounded, purpose-built tools:

```text
                           ┌──────────────────────────────┐
                           │      AI CODING AGENT         │
                           │   Claude / Gemini / GPT      │
                           └──────────────┬───────────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
        ┌──────────────────────┐                      ┌──────────────────────┐
        │      YURO LAYER      │                      │    EXTERNAL TIERS    │
        │ (Context & Tooling)  │                      │   GitHub / Web /     │
        │                      │                      │   Telegram Drive     │
        └──────────┬───────────┘                      └──────────┬───────────┘
                   │                                             │
                   ▼                                             ▼
        [Minimum Sufficient Code]                     [Persistent Docs/Files]
        AST Graphs, Bounded Grep                      PDFs, Knowledge Base
```

### The Core Triad
1. **Code Graph Intelligence (`cbm`)**: AST-indexed SQLite call graphs and dependency mapping in **<350 tokens**.
2. **Bounded High-Speed Search (`rg-mini`, `fd-mini`)**: Enforced 20-line boundaries that prevent catastrophic terminal context dumps.
3. **Ground-Truth Token Auditor (`token-audit`, `token-scan`)**: Real-time forensic parser reading untruncated engine transcripts to track exact characters, tokens, and context leaks.
4. **AST Context Compression (`token-save` / Yuro Core)**: Structural AST pruning for Python error logs and tracebacks.

---

## 📊 Empirical Benchmarks: Proven on Production Codebases

YURO has been rigorously tested across both massive open-source libraries and production application codebases:

### Benchmark 1: `expressjs/express` (64,000+ GitHub Stars)
*Target: Node.js standard web framework (996 AST nodes, 1,647 edges)*

| Scenario | Task | No-Stack Baseline | YURO Optimized | Context Reduction | Speed Delta |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **1. Architecture & Deps** | Discover module layout & exports | 1,372 tok (1,043ms) | **221 tok** (2,117ms) | **-84%** | 2x slower |
| **2. Router Call Graph** | Trace `app.handle` request pipeline | 4,043 tok (1,175ms) | **160 tok** (2,558ms) | **-96%** | 2x slower |
| **3. Implementation Lookup**| Extract `res.json` source body | 6,871 tok (324ms) | **194 tok** (2,283ms) | **-97%** | 7x slower |
| **4. String Search** | Find `X-Powered-By` header refs | 161 tok (500ms) | **33 tok** (87ms) | **-80%** | **6x faster** |
| **CUMULATIVE WORKLOAD** | **4 Agent Exploration Queries** | **12,447 tokens** | **608 tokens** | **-95%** | **~11,839 tokens saved** |

### Benchmark 2: `Techtruction` (Production React SPA)
*Target: React 18, React Router v6, Context API (25 files, 183 nodes, 297 edges)*

| Scenario | Task | No-Stack Baseline | YURO Optimized | Context Reduction |
| :--- | :--- | :--- | :--- | :---: |
| **1. App Architecture** | Component hierarchy & dependencies | 1,615 tok (941ms) | **329 tok** (2,429ms) | **-80%** |
| **2. Call Graph Tracing** | Trace `useAuth` callers & context | 2,284 tok (941ms) | **212 tok** (2,148ms) | **-91%** |
| **3. Exact Implementation** | Extract `Login` form submit logic | 1,621 tok (253ms) | **163 tok** (2,195ms) | **-90%** |
| **4. Config Key Search** | Find `process.env` references | 72 tok (355ms) | **21 tok** (75ms) | **-71%** |
| **CUMULATIVE WORKLOAD** | **4 Agent Exploration Queries** | **5,592 tokens** | **725 tokens** | **-87%** |

> **The Brutal Tradeoff**: A ~1.5 second local graph traversal eliminates **87% to 95% of context bloat**. Across a 30-turn session, this prevents **~150,000 to ~350,000 token-turns** from compounding and re-billing.

### 🔬 Real-World Context Savings Variance
* **Compact, Tightly Coupled Libraries** (e.g. Axios, Flask): Achieve **~35–40% net reduction** because a higher proportion of core structural interface files must be retained to preserve 100% task sufficiency.
* **Component-Driven Applications & Monorepos** (e.g. Express, React apps, full-stack microservices): Achieve **85–95%+ net reduction** because YURO pinpoints exact call subgraphs, completely eliminating massive multi-hundred-line file dumps.

---

## 🔌 Agent Integrations

Install YURO once. Your coding agent gains a codebase brain:

| Agent / Environment | Integration Mode | Setup |
| :--- | :--- | :--- |
| **Claude Code** | Global CLI tools (`cbm`, `rg-mini`, `token-audit`) | Native PATH integration |
| **Gemini CLI / Codex** | System rules & execution wrappers | Auto-configured via `install.ps1` / `install.sh` |
| **Cursor / VS Code** | Terminal & subagent execution | Added to workspace shell environment |
| **Antigravity IDE** | Rules, Skills, and MCP sidecars | Native `%USERPROFILE%\.gemini\config\` sync |
| **Model Context Protocol (MCP)** | Lazy MCP server (`codebase-memory`) | Included in `mcp/mcp_config.global.json` |

---

## 🎯 The T0–T5 Unified Routing Protocol

Apply the **FIRST** matching tier. Never invoke multiple exploration tools in sequence.

| Tier | Name | When to Use | Approved Command | Token Budget |
| :--- | :--- | :--- | :--- | :--- |
| **T0** | **Direct Answer** | Casual chat, concepts, general Q&A | *Zero tools* | 0 |
| **T1** | **Direct File Edit** | File path or line numbers are already known | `view_file(StartLine, EndLine)` + `replace_file_content` | <150 tok |
| **T2** | **Graph Intelligence** | Architecture, symbol lookup, call hierarchies | `cbm arch`, `cbm search`, `cbm trace`, `cbm snippet` | 100–350 tok |
| **T3** | **Capped Text Search**| Literal strings, regex, config keys, filenames | `rg-mini`, `fd-mini`, `es-mini` (max 20 lines) | <80 tok |
| **T4** | **Python Traceback** | Python project + explicit error log + >20 files | `token-save auto "<prompt>" "<dir>"` | 300–600 tok |
| **T5** | **Full Repo Audit** | Whole-repo architectural audit in one shot | `npx repomix --compress` | Whole-repo |

### 🔒 Invariant Rules
- ❌ **NEVER** run `cbm` or `grep` when the target file/line is already known. Use `view_file` direct (T1).
- ❌ **NEVER** call `view_file` without `StartLine` and `EndLine` (max 60 lines).
- ❌ **NEVER** dump raw `Get-ChildItem -Recurse` or uncapped `grep` output into context.
- ❌ **NEVER** load MCP schemas eagerly; invoke the compiled CLI wrapper `cbm` directly.

---

## 🚀 Quick Start & Installation

### Windows (One-Click Setup)
Run in PowerShell:
```powershell
git clone https://github.com/WillyEverGreen/YURO.git
cd YURO
.\install.ps1
```

*What `install.ps1` does automatically:*
1. Copies all CLI tools and binaries to `C:\tools\`.
2. Auto-downloads and verifies `codebase-memory-mcp.exe` v0.11.0 if not already present.
3. Appends `C:\tools` to User Environment `PATH`.
4. Synchronizes global rules to `%USERPROFILE%\.gemini\config\rules\`.
5. Synchronizes modular skills to `%USERPROFILE%\.gemini\config\skills\`.
6. Configures global `mcp_config.json`.
7. Runs the 10-point verification suite.

### Linux / macOS
```bash
git clone https://github.com/WillyEverGreen/YURO.git
cd YURO
chmod +x install.sh
./install.sh
```

---

## ⌨️ Command Cheatsheet

```cmd
# -------------------------------------------------------------
# 1. TOKEN AUDITING & TELEMETRY
# -------------------------------------------------------------
token-audit                    # Audit active session context payload
token-scan                     # Scan across all historical chat sessions
token-scan -n 5                # Scan last 5 sessions
token-tracker audit --all      # Global lifetime portfolio audit
token-scan --csv > tokens.csv  # Export metrics to CSV for Excel
token-tracker live             # Real-time live session monitor

# -------------------------------------------------------------
# 2. CODEBASE MEMORY (GRAPH QUERIES)
# -------------------------------------------------------------
cbm index <path>               # Index codebase AST into SQLite graph
cbm arch <project>             # Instant architecture map (<350 tokens)
cbm search <project> <symbol>  # Fast symbol location (<200 tokens)
cbm trace <project> <function> # Call hierarchy traversal (<200 tokens)
cbm snippet <project> <symbol> # Qualified function source lines (<180 tokens)

# -------------------------------------------------------------
# 3. HIGH-SPEED BOUNDED SEARCH
# -------------------------------------------------------------
rg-mini "<query>" [path]       # Capped ripgrep (max 20 lines)
fd-mini "<pattern>" [path]     # Capped file finder (max 20 results)
es-mini "<pattern>"            # Instant Everything IPC search

# -------------------------------------------------------------
# 4. SYSTEM & IDE MAINTENANCE
# -------------------------------------------------------------
agy-brain                      # Inspect IDE memory state
agy-clean                      # Purge IDE crash dumps and temporary logs
agy-check                      # Verify IDE environment permissions & tools
/boost                         # Free workstation standby RAM
/clean                         # Clean temporary directories & cache
/status                        # Workstation diagnostic telemetry
```

---

## 📂 Project Structure

```text
YURO/
├── yuro.png                      # Official Fox Mascot & Logo
├── cmd/                          # Production CLI tools & wrappers (33 tools)
│   ├── token-tracker.js          # Ground-truth transcript parser & auditor
│   ├── token-audit.cmd           # Session audit command
│   ├── token-scan.cmd            # Multi-session scanner command
│   ├── cbm.cmd                   # Codebase Memory CLI runner
│   ├── cbm-mini.cmd              # High-level graph overview
│   ├── rg-mini.cmd               # Capped ripgrep wrapper
│   ├── fd-mini.cmd               # Capped file search wrapper
│   ├── es-mini.cmd               # Everything IPC search wrapper
│   ├── sg-mini.cmd               # ast-grep structural search
│   ├── token-save.cmd            # Python AST pruner
│   ├── session_logger.cmd        # Session performance tracker
│   ├── antigravity-brain.cmd     # IDE memory analyzer
│   ├── antigravity-clean.cmd     # IDE crash/temp cleaner
│   ├── antigravity-check.cmd     # IDE diagnostic checker
│   ├── agent_benchmark.cmd       # Agent benchmark runner
│   ├── long_session_benchmark.cmd# Long-session simulator
│   ├── code-sig.cmd              # Code signature extractor
│   ├── repo_indexer.cmd          # AST indexer
│   ├── playwright-cli.cmd        # Browser automation runner
│   └── md-mermaid.cmd            # Mermaid diagram compiler
├── bin/                          # Platform binaries (rg.exe, fd.exe, ast-grep.exe, etc.)
├── rules/                        # Antigravity IDE global rules
│   ├── T0-T5-protocol.md         # Master decision protocol
│   ├── token-saver.md            # T4 Python traceback context rule
│   ├── pc-commands.md            # Slash command shortcuts
│   └── agent-browser-default.md  # Tier 1 browser automation policy
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
├── verify.ps1                    # Verification & sanity test suite
├── package.json                  # NPM scripts & metadata (v2.0.0)
├── pyproject.toml                # Python package metadata (v2.0.0)
└── LICENSE                       # MIT License
```

---

<div align="center">
<b>YURO</b> • Engineered for Maximum Cognitive Density and Zero Token Waste. 🦊
</div>
