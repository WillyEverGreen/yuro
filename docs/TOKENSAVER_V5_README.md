# TokenSaver v5.0.0 — Production-Ready Adaptive Evidence Engine

TokenSaver v5 is a local-first, symbol-aware evidence engine for AI coding assistants. It turns raw repository code into minimum sufficient model-visible evidence while guaranteeing positive NET token savings.

## Quick Start Commands

```cmd
tokensaver-v5 doctor
tokensaver-v5 version
tokensaver-v5 index C:\tools
tokensaver-v5 graph C:\tools
tokensaver-v5 retrieve C:\tools "Fix run_index in tokensaver_v5_symbol_index.py"
tokensaver-v5 metrics --json
tokensaver-v5 benchmark C:\tools
```

## Features

- **Tree-sitter Symbol Indexing**: Incremental parsing with sub-20ms file update performance.
- **Local Relationship Graph**: Directional dependency tracking (`IMPORTS`, `CALLS`, `INHERITS_FROM`, `DEFINES`).
- **Strict Local Isolation**: SQLite database (`index.db`) stays 100% local on disk; raw graph structures are never serialized into LLM prompts.
- **Deterministic Token Economics**: Guaranteed positive net savings gate (Net = Gross - Overhead).
