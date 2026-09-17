<div align="center">

<img src="yuro.png" alt="Yuro mascot" width="240" style="margin-bottom: 15px;" />

# Yuro

**A Local-First Code Intelligence, Graph Engine & Zero-Waste Context Architecture for AI Coding Agents**

[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)
[![Release: v2.0.0](https://img.shields.io/badge/Release-v2.0.0%20Unified-blue.svg)](pyproject.toml)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](pyproject.toml)
[![Node: 18+](https://img.shields.io/badge/Node-18%2B-green.svg)](package.json)
[![Context Reduction](https://img.shields.io/badge/Context%20Reduction--87%25%20Empirical-success.svg)](#-empirical-benchmark-yuro-vs-no-stack-baseline)
[![Protocol](https://img.shields.io/badge/Protocol-T0--T5%20Tiered-purple.svg)](#-the-t0-t5-unified-protocol)

---

</div>

## 🧠 What YURO Actually Is (and Isn't)

**YURO is not an AI model or a standalone chatbot.** Claude, Gemini, and GPT remain the brain. 

YURO is the **agent-side context optimization and evidence harness** underneath them—informally known as the **"don't be stupid with context" layer**.

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

Without YURO, an autonomous agent searching for a function or tracking an authentication flow will blindly run recursive directory scans, uncapped greps, and dump 10 entire files into prompt context—blowing **15,000 to 40,000 tokens** on questions that can be answered in **under 350 tokens**.

Because LLM conversation context accumulates turn-over-turn, early token bloat compounds on every subsequent prompt, triggering model amnesia, high API costs, and context compaction.

**YURO equips your agent with bounded, purpose-built tools:**
1. **Local Code Graph Intelligence (`cbm`)**: AST-indexed SQLite call graphs and dependency maps that answer architectural questions in under 350 tokens.
2. **Hard-Capped Mini Wrappers (`rg-mini`, `fd-mini`)**: Enforced 20-line boundaries that prevent catastrophic terminal context dumps.
3. **Ground-Truth Token Auditor (`token-audit`, `token-scan`)**: Real-time forensic parser reading untruncated engine transcripts to track exact characters, tokens, and context leaks.
4. **AST Context Compression (`token-save` / Yuro Core)**: Safe AST-level pruning for Python error logs and tracebacks.
5. **Tiered Tool Routing (T0–T5)**: Strict decision protocol that prevents exploration tool chaining and unnecessary searches.
6. **Workstation & Diagnostic Automation (`pc-toolbox`)**: RAM boosting, temporary cache purges, and background process telemetry.

---

## 🏛️ How Everything Works Together: The Unified Ecosystem

Every tool in Yuro has a precise role within the cognitive workflow. No tool steps on another:

```text
                                 ┌──────────────────────────────┐
                                 │     User Request / Task      │
                                 └──────────────┬───────────────┘
                                                │
                                    [T0-T5 Decision Gate]
                                                │
          ┌─────────────────┬───────────────────┼───────────────────┬─────────────────┐
          ▼                 ▼                   ▼                   ▼                 ▼
        [T0]              [T1]                [T2]                [T3]              [T4]
     Direct Q&A        Target Known        Architecture        Search & Find      Python Bug
      (0 tools)        (File Slicing)       (Graph AST)        (Capped Search)    (AST Prune)
          │                 │                   │                   │                 │
    Pure Answer      view_file(L1-L60)     cbm arch/trace       rg-mini / fd-mini  token-save
                     replace_content       snippet (<350t)       (<20 lines, <80t)    auto
          │                 │                   │                   │                 │
          └─────────────────┴───────────────────┼───────────────────┴─────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │  System Maintenance & Telemetry │
                               │  - agy-brain (memory health)    │
                               │  - agy-clean (purge crash logs) │
                               │  - pc-toolbox (RAM / disk)      │
                               │  - auto-scraper (web browser)   │
                               └────────────────┬────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │    Ground-Truth Token Auditor   │
                               │    token-audit / token-scan     │
                               │  (Inspects untruncated logs,    │
                               │   measures exact ROI & leaks)   │
                               └─────────────────────────────────┘
```

---

## 📊 Empirical Benchmark: Yuro vs. No-Stack Baseline

Tested head-to-head on the production `Techtruction` React codebase across 4 common developer queries:

```text
══════════════════════════════════════════════════════════════════════════════════════════
          BRUTAL EMPIRICAL BENCHMARK: OPTIMIZED STACK vs NO-STACK BASELINE
══════════════════════════════════════════════════════════════════════════════════════════
 Target Repo:      Techtruction (React 18, React Router, Context API, 25 files)
 Evaluation Mode:  Ground-Truth Payload Characters & Estimated Tokens (3.8 ch/tok)
──────────────────────────────────────────────────────────────────────────────────────────
 Scenario                  No-Stack Payload        YURO Payload          Context Reduction
 ────────────────────────────────────────────────────────────────────────────────────────
 1. Architecture & Deps    1,615 tok (941ms)       329 tok (2429ms)            -80%
 2. Call Graph & Tracing   2,284 tok (941ms)       212 tok (2148ms)            -91%
 3. Literal String Search  72 tok (355ms)          21 tok (75ms)               -71% (5x faster)
 4. Function Source Lookup 1,621 tok (253ms)       163 tok (2195ms)            -90%
──────────────────────────────────────────────────────────────────────────────────────────
 CUMULATIVE TOTALS:        5,592 tokens            725 tokens                  -87%
══════════════════════════════════════════════════════════════════════════════════════════
```

> **The Tradeoff**: A ~1.5 second local graph traversal eliminates **87% of context bloat**. Across a 30-turn session, this prevents **~146,000 token-turns** from compounding and re-billing.

### 🔬 Real-World Context Savings Variance
Savings naturally depend on codebase architecture and task coupling:
* **Compact, Highly Coupled Libraries** (e.g. Axios, Flask): Achieve **~35–40% net reduction** because a higher proportion of core structural interface files must be retained to maintain 100% task sufficiency.
* **Component-Driven Applications & Monorepos** (e.g. React/Next.js apps, full-stack microservices): Achieve **80–90%+ net reduction** because YURO pinpoints exact call subgraphs, completely eliminating massive multi-hundred-line file dumps.

---

## 🗂️ Complete Tool Catalog

Yuro organizes all 33 integrated utilities into 7 coordinated domains:

### 1. Token Tracking & Context Auditing Engine
* **`token-audit`**: Forensic single-session auditor. Parses untruncated logs (`transcript_full.jsonl`) to report exact characters, estimated tokens, prompt-vs-output ratio, tool overhead, and alerts on heavy context dumps (>500 tokens).
* **`token-scan`**: Multi-session scanner. Aggregates all conversations across history with step counts, total characters, token volumes, and extracted session intents.
* **`token-tracker live`**: Real-time ticker. Watches active chat sessions live and updates token expenditure as tools run.

### 2. Code Graph & Architecture Intelligence
* **`cbm`**: High-speed CLI wrapper for Codebase Memory. Traverses AST-indexed SQLite graphs in `--quiet` mode.
  - `cbm arch <project>`: Instant architecture summary (nodes, edges, packages, frameworks) in **<350 tokens**.
  - `cbm search <project> <query>`: Qualified symbol lookup in **<200 tokens**.
  - `cbm trace <project> <function>`: Call graph hierarchy ("who calls X and what does X call") in **<200 tokens**.
  - `cbm snippet <project> <symbol>`: Extracts target function source lines by qualified name in **<180 tokens**.
* **`cbm-mini`**: Formatted high-level project summary wrapper.
* **`code-sig`**: Fast AST function/class signature extractor.
* **`repo_indexer`**: Automatic repository AST indexer and graph cache generator.

### 3. Bounded High-Speed Search Wrappers
* **`rg-mini`**: Ripgrep wrapper hard-capped at 20 lines (`--max-count 20`). Ensures text searches consume **<80 tokens**.
* **`fd-mini`**: Find wrapper hard-capped at 20 results (`--max-results 20`).
* **`es-mini`**: Windows Everything IPC fast-path search. Resolves filenames in **<10ms**.
* **`sg-mini`**: Ast-grep wrapper for structural code syntax queries.

### 4. Context Compression & Relevance Ranking
* **`token-save`**: AST-based relevance engine and code pruner for Python error logs and tracebacks (T4).
* **`tokensaver` Python Core**: Multi-language AST parsing (Python, TS, TSX, JS), BM25 scoring, and structural equivalence gating.
* **`session_logger`**: Tracks cumulative token compression metrics, fidelity scores, and session latency.

### 5. Antigravity IDE Memory & Health Suite
* **`antigravity-brain` (`agy-brain`)**: Inspects IDE memory state, artifact storage, and active conversation indices.
* **`antigravity-clean` (`agy-clean`)**: Purges IDE crash dumps, orphaned memory locks, and temporary scratch bloat.
* **`antigravity-check` (`agy-check`)**: Verifies IDE environment variables, permissions, and tool health.

### 6. Long-Session & Agent Benchmarking
* **`agent_benchmark`**: Automated agent accuracy and token efficiency benchmarking suite.
* **`long_session_benchmark`**: Simulates multi-turn long-running sessions to test context degradation and token accumulation.

### 7. Workstation Diagnostics & Browser Automation
* **`pc-toolbox`**: Workstation maintenance commands (`/boost` RAM, `/clean` temp files, `/status`, `/diagnose`, `/unlock`).
* **`auto-scraper`**: Multi-tier autonomous web extraction (Tier 1: Direct HTTP → Tier 2: Agent Browser → Tier 3: Playwright).
* **`playwright-cli`**: Headless browser automation test runner.
* **`md-mermaid`**: Mermaid diagram CLI compiler and renderer (`mmdc`).

---

## 🎯 The T0–T5 Unified Protocol

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
├── package.json                  # NPM scripts & metadata
├── pyproject.toml                # Python package metadata (v2.0.0)
└── LICENSE                       # MIT License
```

---

<div align="center">
<b>YURO</b> • Engineered for Maximum Cognitive Density and Zero Token Waste. 🦊
</div>
