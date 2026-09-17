---
name: pc-toolbox
description: >-
  Workstation CLI & diagnostics suite consolidated across C:\tools (global PATH).
  Handles /toolbox, /boost, /clean, /status, /diagnose, /security, /find, /rg, /fd, /ast,
  /stats, /startup, /unlock, /benchmark, Playwright, repomix, and antigravity-auto-submit.
---

# Local System Agent & Diagnostic Architecture (`pc-toolbox`)

Authoritative reference and operational rules for the local developer tool stack consolidated in **`C:\tools\`** (global PATH).

> [!IMPORTANT]
> **UNIFIED T0-T5 PROTOCOL DIRECTIVE:**
> - **T0 (Direct Answer):** 0 tools. Casual chat, concepts, pure Q&A.
> - **T1 (Direct File Edit):** 0 exploration tools. Use view_file(StartLine, EndLine) + replace_file_content ONLY.
> - **T2 (Graph-First Intelligence):** Architecture, symbol links, call graphs (cbm arch, cbm search, cbm trace, cbm snippet).
> - **T3 (Capped Text Search):** String/regex search (rg-mini, fd-mini, es-mini capped at 20 lines / <80 tokens).
> - **T4 (Python Traceback Context):** token-save auto ONLY when Python + explicit traceback/error + >20 source files.
> - **T5 (Full Repo Audit):** npx repomix --compress for whole-repo audits only.
>
> **CRITICAL SLICING DIRECTIVE:** Never call view_file without StartLine and EndLine (max 60 lines). Never dump full files into context.

---

## 1. Operating Rules & Safety Tiers

### Closed-Loop Verification Protocol
```text
Diagnose (telemetry) → Identify (target PID/query) → Safety Gate → Execute → Verify Delta → Keep/Revert
```

### Capability-Based Safety Tiers
- **Tier 1 (Read / Inspect / Measure):** `rg`, `es`, `fd`, `sg`, `tokei`, `jq`, `repomix`, `fastfetch`, `autorunsc`; `hyperfine` *only when benchmarked commands are read-only/safe* → Execute immediately.
- **Tier 2 (Safe Local Modification):** Project-local `uv` environments/packages, `7z` extraction/archiving, safe temp/cache purges, local file edits → Execute with logged metrics.
- **Tier 3 (Destructive / External / System-wide):** Registry edits, service configuration, system-wide `--system` installs, remote deletion, form submission, sending messages, financial transactions, public network exposure → HALT and require explicit user approval.

### 1.1 Capability-First Fallback & Token Optimization Policy
Select tools based on required capability, current execution context, and token efficiency:
1. **Cheapest Local Determinism:** Prefer direct CLI/API operations over browser automation when equivalent.
2. **Token Minimization (Pre-filtering):** Always filter large JSON payloads via `jq` and source code via `rg` / `sg` at the source. Never dump multi-MB raw text into model context.
3. **Graph-First Code Intelligence & Architecture:** Query `cbm arch`, `cbm search`, or `cbm trace` before opening or grepping source files to resolve relationships in <50 tokens.
4. **Repository Context Packing:** Use `repomix --compress` (Tree-sitter AST compression) to pack repository context efficiently, reducing input tokens by ~70%.
5. **Concise Communication ("Caveman Mode"):** When performing long token-heavy agentic tasks, strip non-essential conversational filler and respond with high-density, action-focused output.
6. **File Discovery:** Try `es.exe` if Everything IPC is available; fall back automatically to `fd` if IPC is unavailable. Never crawl with slow `Get-ChildItem -Recurse`.
7. **Code & Syntax Search:** Use `cbm` for symbol links/call hierarchies, `rg` for literal text/regex; route to `sg` (`ast-grep`) when structural syntax/code shapes are required.
8. **Python Tooling:** Prefer `uv` for Python environments and package management (`uv venv` / `uv run`).

### 1.2 Mandatory Low-Token Tool Directives & Hard Limits
Whenever executing tools, enforce the following output boundaries to prevent context inflation:
- **Search Output Truncation:** Limit file/text search results using `-n 15` or `-n 20` or call mini wrappers (`fd-mini`, `rg-mini`, `es-mini`).
- **Targeted Line Slice Viewing:** Never view full multi-hundred line files. Always specify `StartLine` and `EndLine` parameters when reading files.
- **Compact Diagnostics:** Always pass `-Compact` switch to `toolbox.cmd` commands (`toolbox Status -Compact`, `toolbox Security -Compact`, `toolbox Startup -Compact`).
- **Strict Package List Scope:** Always use `npm list -g --depth=0` or `pip list --format=freeze` to prevent massive recursive dependency tree output.
- **JSON Payload Slicing:** Mandatory piping of CLI JSON output through `jq` (e.g., `tokei . --output json | jq '.languages'`).
- **Concise Diff Edits:** Use `replace_file_content` with concise target snippets rather than rewriting complete source files.

---

## 2. Command & Tool Reference (Categorized)

All primary binaries reside in **`C:\tools\`** (global PATH):

### 🖥️ System Health & OS Diagnostics
| Command / Trigger | Execution Syntax | Domain & Capabilities |
| :--- | :--- | :--- |
| **`/status`** | `cmd.exe /c "toolbox.cmd Status -Compact"` | Drive space (C:, D:), RAM %, power plan (Low-token mode) |
| **`/info`** | `fastfetch --logo none` / `toolbox Info` | Hardware/OS info stripped of ASCII art (65 tokens) |
| **`/diagnose`** | `tasklist /FO CSV` / PS working set counters | Root-cause analysis of CPU/RAM consumers |
| **`/security`** | `cmd.exe /c "toolbox.cmd Security"` | Windows Defender shield & firewall profiles |
| **`/startup`** | `cmd.exe /c "toolbox.cmd Startup -Compact"` | Audits startup apps with top-15 line filter |
| **`/unlock <path>`** | `cmd.exe /c "toolbox.cmd Unlock \"<path>\""` | Identifies locking PIDs via Restart Manager |
| **`/clean`** | `cmd.exe /c "toolbox.cmd Clean"` | BleachBit safe clean + user temp & pip/npm cache purge |
| **`antigravity-check`** | `antigravity-check` / `agy-check` | 3-tier deletion audit scan (🟢 Safe / 🟡 Review / 🔴 Do Not Delete) |
| **`antigravity-clean`** | `antigravity-clean` / `agy-clean` | Purges safe scratch scripts, browser WebP recordings, and package caches |
| **`/boost`** | `cmd.exe /c "toolbox.cmd BoostRAM"` | *Emergency only:* NT Working Set trim + MemReduct |

### 🔍 Codebase & Search Tools
| Command / Trigger | Execution Syntax | Domain & Capabilities |
| :--- | :--- | :--- |
| **`/find <query>`** | `es-mini <query>` | Fast indexed file lookup capped to 15 results |
| **`/fd <pat> [dir]`** | `fd-mini "<pat>" [dir]` | Fast directory traversal capped to 20 results (-98.7% tokens) |
| **`/rg <pat> [dir]`** | `rg-mini "<pat>" [dir]` | Recursive code search capped to 20 matches |
| **`/ast <pat> [lang]`**| `sg run -p "<pat>" --lang <lang> [dir]` | Structural AST code syntax search (ast-grep) |
| **`/cbm <cmd> [args]`**| `cbm [index\|search\|trace\|query\|list]` | Structural code knowledge graph (Tree-sitter + SQLite) |
| **`/stats [dir]`** | `tokei [dir] --output json \| jq '.languages'` | Language composition, lines of code, blanks, comments |
| **`/benchmark "<c1>" "<c2>"`** | `hyperfine "<c1>" "<c2>"` | Statistical execution benchmark (mean, min, max, stddev) |

### ⚡ Token Saver & Context Optimizers
| Tool / Technique | Execution Syntax | Domain & Capabilities |
| :--- | :--- | :--- |
| **Repomix** | `npx repomix --compress` | Packs repos into single compressed AST file (~70% token savings) |
| **Caveman Mode** | High-density concise prompt mode | Strips conversational fluff to minimize output tokens by 50%+ |
| **JSON Slicing** | `... \| jq '<filter>'` | High-performance CLI JSON parsing and filtering |
| **Archives** | `7z x <archive> -o<dir>` / `7z a <arc> <files>` | High-ratio 7-Zip compression & decompression |
| **Python Tooling** | `uv run ...` / `uv pip install ...` | Fast Python environment & package management |

### 🤖 Web Automation & Background Services
| Command / Trigger | Execution Syntax / Path | Domain & Capabilities |
| :--- | :--- | :--- |
| **Playwright** | `py -c "from playwright.sync_api import sync_playwright..."` | Headless Chrome batch extraction & browser automation |
| **Auto-Submit Daemon** | `C:\Users\advdi\tools\antigravity-auto-submit` | Local IDE modal auto-approval & rule daemon |

---

## 3. Diagnostic & Operational Protocols

### Failure & Recovery Protocol
```text
After every execution:
  ├─ SUCCESS            → Keep result → Continue workflow
  ├─ FAILURE            → Diagnose context/environment → Route to next safe fallback → Retry at most 2 times
  └─ PERSISTENT FAILURE → Stop execution → Preserve state → Report exact root-cause and safe next action
```

### Memory Diagnostic Protocol (No Blind Flushing)
1. **Available RAM:** Total - In-Use. If available RAM is sufficient for active apps, memory is healthy.
2. **Standby Cache:** Standby contains cached file pages freed automatically on demand by Windows; it is not a leak.
3. **Working Sets:** Identify top consumer PIDs (`Get-Process | Sort WorkingSet64 -Descending`).
4. **Targeted Action:** If legitimate apps account for memory, report metrics; do NOT flush. Trigger `/boost` ONLY if commit charge approaches 95% and disk swapping occurs.

### Codebase Reconnaissance Protocol (T0–T5 Decision Tree)

```text
User Code Request
  │
  ├─ T0: Pure Q&A / concept / brainstorm, no file reference
  │      → Direct answer. ZERO tools.
  │
  ├─ T1: File path or line already known / provided
  │      → view_file(StartLine, EndLine) + replace_file_content ONLY.
  │         No search. No graph. No exploration.
  │
  ├─ T2: Architecture / symbol / call hierarchy / "who calls X" / "what imports Y"
  │      → cbm arch <project>                  (overview, ~320 tokens)
  │      → cbm search <project> <pattern>      (symbol lookup, ~150 tokens)
  │      → cbm trace <project> <function>      (call graph, ~120 tokens)
  │      → cbm outline <project> <file>        (file symbols, ~50 tokens)
  │      → cbm snippet <project> <qn>          (source lines by name, ~80 tokens)
  │      Auto-index: cbm index <workspace>  on first touch if not indexed.
  │      NOT: rg across files, NOT: token-save auto, NOT: read raw files first.
  │
  ├─ T3: Literal string / filename search with no graph context needed
  │      → rg-mini "<pattern>" [path]           (text search, <80 tokens)
  │      → fd-mini "<pattern>" [path]           (file find, <80 tokens)
  │      → es-mini <query>                      (Everything indexed, 15 results)
  │      NOT: cbm (overkill), NOT: Get-ChildItem -Recurse (uncapped, slow)
  │
  ├─ T4: Python project + explicit traceback/error/filename + >20 files
  │      → token-save auto "<prompt>" "<workspace>"
  │      IF fidelity=FIDELITY_FAILED: discard output, fall back to T2/T3.
  │      NOT: use for JS/TS/general tasks (direct_import scorer breaks on these).
  │
  └─ T5: Full-repo architectural audit requiring entire context in one shot
         → npx repomix --compress
         NOT: for localized tasks. Only for whole-repo audit requests.
```

**Hard "use this NOT that" boundaries:**
- Architecture overview → `cbm arch`, NOT `repomix` or multi-file grep
- Symbol/call trace → `cbm trace`, NOT `rg` loop + file reads
- Python traceback → `token-save auto`, NOT `cbm` (no Python AST call graph)
- Single-file edit → `view_file` direct, NOT any exploration tool
- Literal string → `rg-mini`, NOT `cbm` (cbm doesn't index string literals)

### Web Automation & Playwright Protocol
1. **Local Playwright Installations:**
   - **Python Module:** `C:\Users\advdi\AppData\Local\Programs\Python\Python312\Lib\site-packages\playwright`
   - **Node.js Module:** `C:\Users\advdi\AppData\Roaming\npm\node_modules\playwright`
   - **Browser Binaries Cache:** `C:\Users\advdi\AppData\Local\ms-playwright\` (`chromium-1228`, `chromium_headless_shell-1228`, `ffmpeg-1011`)
2. **Headless by Default:** Launch with `headless=True` unless visually debugging.
3. **Browser Binary & Memory:** Use `channel="chrome"` to avoid downloading secondary browser binaries when appropriate.
4. **Context Isolation:** Always automate inside isolated Playwright browser contexts to protect personal user sessions.
5. **Lifecycle & Selective Cleanup:** Close browsers in `finally` blocks. On abnormal exit, terminate only orphaned processes spawned by that specific run.
6. **CDP Security Gate:** Any debugging/CDP endpoints must remain strictly bound to `127.0.0.1` (localhost).
7. **Auto-Submit Boundary:** Auto-submit automation is strictly scoped to local IDE confirmation modals. Never automatically submit external web forms, financial transactions, or third-party web portals.
