# TokenSaver v5 Architecture & Data Flow

```text
USER REQUEST
    │
    ▼
ADMISSION GATE (SKIP if general/simple)
    │
    ▼
POLICY ENGINE & REPOSITORY CAPABILITY ANALYZER
    │
    ▼
EVIDENCE PLANNER → HYBRID RETRIEVAL (Index & Graph)
    │
    ▼
RELEVANCE RANKER & TOKEN BUDGET MANAGER
    │
    ▼
3-LEVEL EVIDENCE ASSEMBLER → COVERAGE & FIDELITY CHECK
    │
    ▼
NET ECONOMICS GATE → FINAL MODEL-VISIBLE CONTEXT → LLM
```

## Local-First Isolation

The local SQLite database at `<workspace>\.tokensaver\index.db` is strictly isolated from LLM context payload. Downstream components query the database via local SQL calls and emit only compact, line-attributed symbol evidence units.
