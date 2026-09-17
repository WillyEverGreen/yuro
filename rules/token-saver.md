# Unified Context Routing & Tool Protocol (T0-T5)

Apply the FIRST matching tier. Never invoke multiple exploration tools for the same task.

## Tier Decision Protocol:

1. **T0 - Direct Answer (0 tools):**
   - Pure Q&A, general knowledge, conceptual explanations, brainstorming.
   - DO NOT invoke any tools or context engines.

2. **T1 - Direct File Edit (0 exploration tools):**
   - Target file path or line number is known from prompt or context.
   - Use view_file(StartLine, EndLine) + replace_file_content ONLY.
   - DO NOT run searches or graph queries.

3. **T2 - Graph-First Code Intelligence (cbm):**
   - Multi-file architecture, symbol definitions, call hierarchies ("who calls X", "what imports Y").
   - Use: cbm arch / cbm search / cbm trace / cbm snippet (~150-320 tokens).
   - DO NOT grep across files; DO NOT read raw source files into context.

4. **T3 - Capped Text / File Search (rg-mini / fd-mini):**
   - Finding literal text, string constants, config keys, or file paths.
   - Use: rg-mini / fd-mini (hard-capped at 20 results, <80 tokens).

5. **T4 - Python Traceback Context (token-save auto ONLY):**
   - ONLY valid when ALL THREE conditions are met:
     a) Project is primarily Python.
     b) Prompt contains an explicit error traceback, log, or specific filename.
     c) Project has >20 source files.
   - NEVER run token-save auto on JavaScript, TypeScript, or general exploration tasks.

6. **T5 - Full Repo Context Pack (repomix):**
   - Whole-repo architectural reviews only. Use: npx repomix --compress.

## Mandatory Slicing Rule:
- All file reads: ALWAYS specify StartLine and EndLine (maximum 60-80 lines per read).
- NEVER read entire large files or un-sliced markdown/pdf documents.
