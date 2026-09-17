# UNIFIED TOOL DECISION PROTOCOL (T0-T5)

Apply the FIRST matching tier. Never invoke multiple exploration tools for the same task.

## The 6 Tiers:

### T0 - Direct Answer (0 Tools)
- **When**: Pure Q&A, conceptual explanations, brainstorming, general conversation.
- **Action**: Answer directly with zero tool calls.

### T1 - Direct File Edit (0 Exploration Tools)
- **When**: Target file path or line numbers are already known from the prompt.
- **Action**: Use `view_file(StartLine, EndLine)` + `replace_file_content` ONLY.
- **Rule**: NEVER search, grep, or query the graph when target file is known.

### T2 - Graph-First Code Intelligence (`cbm`)
- **When**: Multi-file architecture, symbol definitions, call hierarchies ("who calls X", "what imports Y", "where is AuthContext used").
- **Action**:
  - `cbm arch <project>` (~320 tokens)
  - `cbm search <project> <symbol>` (~150 tokens)
  - `cbm trace <project> <function>` (~120 tokens)
  - `cbm snippet <project> <qn>` (~80 tokens)
- **Rule**: Auto-index first with `cbm index <workspace>`. DO NOT grep across files; DO NOT read raw source files into context.

### T3 - Capped Text / File Search (`rg-mini` / `fd-mini`)
- **When**: Finding literal strings, regex patterns, environment variables, config keys, or file paths.
- **Action**: `rg-mini "<pattern>" [path]` or `fd-mini "<pattern>" [path]`.
- **Rule**: Hard-capped at 20 lines (<80 tokens). NEVER run uncapped grep or directory listing.

### T4 - Python Traceback Context (`token-save auto`)
- **When**: ONLY when ALL THREE conditions are met:
  1. Project is primarily Python.
  2. Prompt contains an explicit error traceback, log, or specific filename.
  3. Project has >20 source files.
- **Action**: `token-save auto "<prompt>" "<workspace>"`.
- **Rule**: If fidelity fails, discard and fall back to T2/T3. NEVER run on JS/TS/general tasks.

### T5 - Full Repo Context Pack (`repomix`)
- **When**: Whole-repo architectural reviews requiring the entire codebase in one prompt.
- **Action**: `npx repomix --compress`.
- **Rule**: Strictly reserved for whole-repo audit requests.

---

## Hard Prohibitions & Invariants:
1. **CRITICAL SLICING INVARIANT**: All file reads MUST specify `StartLine` and `EndLine` (max 60 lines). Never view whole files.
2. **NO TOOL CHAINING**: Never run multiple exploration tools in sequence for the same query.
3. **NO JSON SCHEMA BLOAT**: Keep MCP tools Lazy; run CLI wrappers directly to avoid prompt schema overhead.
