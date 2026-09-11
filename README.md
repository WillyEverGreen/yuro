<p align="center">
  <img src="yuro.png" alt="Yuro mascot" width="240">
</p>

<h1 align="center">🦊 Yuro</h1>

<p align="center">
  <b>A local-first code context & evidence optimization engine for AI coding agents.</b>
</p>

<p align="center">
  <a href="https://github.com/WillyEverGreen/token-saver/actions"><img src="https://img.shields.io/badge/build-passing-brightgreen?style=flat-square" alt="Build"></a>
  <a href="validation/final/production_readiness_report.md"><img src="https://img.shields.io/badge/release-v1.0.0-blue?style=flat-square" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="License"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.8+-blue?style=flat-square" alt="Python"></a>
  <a href="validation/real_opensource/real_opensource_benchmark.json"><img src="https://img.shields.io/badge/task%20success-100%25-success?style=flat-square" alt="Validation"></a>
</p>

---

Yuro analyzes software repositories locally to find the minimum sufficient code context required for an LLM coding task. Instead of concatenating entire file trees into model prompt windows, Yuro performs AST parsing, symbol indexing, lexical BM25 ranking, and static call graph traversal to select, compress, and budget evidence before an API call is made.

The core objective is **maximum task performance per model-visible token**: spending cheap local CPU compute to eliminate redundant context without degrading task resolution.

---

## 🎯 Key Design Principles

* **Minimum Sufficient Context**: Extracts only the symbol definitions, signatures, and implementation subgraphs required for the task.
* **Deterministic Economics Gate**: Calculates exact net token savings (`Raw Context - Selected Evidence - Overhead`). Optimization is automatically bypassed if net savings are non-positive or if broad context is required.
* **AST Structural Equivalence**: Verifies that executable source AST remains identical (`executable_ast_before == executable_ast_after`). Prunes only non-executable material (comments, docstrings, formatting) and falls back to original source on syntactic ambiguity.
* **Local-First Execution**: Indexing, lexical retrieval, graph resolution, AST compression, and budgeting run locally on disk. Yuro requires no remote vector database or hosted retrieval pipeline.

---

## ⚙️ How Yuro Works

When a coding task is submitted, Yuro executes a local 5-stage pipeline:

1. **Structural Indexing**: Parses source files using Tree-Sitter ASTs to extract symbols, definitions, type signatures, imports, and exports into a local SQLite index.
2. **Hybrid Retrieval**: Combines BM25 term frequency scoring, natural language query expansion, static caller/callee graph traversal, and local semantic fallback to score candidate code units.
3. **Progressive Evidence Assembly**: Ranks candidates into progressive evidence depths:
   * **L0**: Module layout and file organization
   * **L1**: Interface signatures, docstrings, and symbol dependencies
   * **L2**: Target function implementations and callee bodies
4. **AST-Safe Compression**: Trims comments and non-executable syntax while verifying structural equivalence.
5. **Economics Gating**: Compares target context size against token budgets. If the selected evidence is sufficient and produces positive net token savings, Yuro emits the optimized payload; otherwise, it bypasses optimization and preserves the original context.

---

## 🏗️ Architecture Overview

* **Input Governor**: Controls context selection, AST compression, symbol ranking, and token budgeting before calling the LLM.
* **Output Governor (Caveman Mode)**: An optional middleware layer that constrains LLM output verbosity, trimming prose boilerplate while maintaining code diff accuracy.

---

## 📊 Real-World Validation

Evaluated across open-source production repositories using exact `tiktoken` accounting (`cl100k_base`):

| Repository | Language / Stack | Tasks | Task Success Rate | Whole-Workload Net Savings | p50 Local Latency |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Axios](https://github.com/axios/axios) | JavaScript / TypeScript | 5 | **100%** | **39.72%** | 77.08 ms |
| [Flask](https://github.com/pallets/flask) | Python | 5 | **100%** | **35.77%** | 241.85 ms |

> **10 tasks evaluated across independent open-source repositories: 100% sufficient-evidence task success.**

*Note: Savings depend on codebase density and task scope. Highly coupled, compact libraries (e.g. Axios, Flask) retain a higher proportion of core structural files (~35-40% savings) to preserve task sufficiency, whereas larger monorepos achieve 85-90%+ net reduction.*

---

## 🌐 Language Support Matrix

| Language | AST Symbol Parsing | Lexical Retrieval | Static Call Graph | Safe AST Compression |
| :--- | :---: | :---: | :---: | :---: |
| **Python** (`.py`) | ✅ | ✅ | ✅ | ✅ |
| **JavaScript** (`.js`, `.mjs`) | ✅ | ✅ | ✅ | ✅ |
| **TypeScript** (`.ts`) | ✅ | ✅ | ✅ | ✅ |
| **JSX** (`.jsx`) | ✅ | ✅ | ✅ | ✅ |
| **TSX** (`.tsx`) | ✅ | ✅ | ✅ | ✅ |

---

## 🛠️ Installation

```bash
git clone https://github.com/WillyEverGreen/token-saver.git
cd token-saver
pip install -e .
```

---

## 💻 Quickstart

```bash
# Automatically optimize code context for a prompt
token-save auto "Trace authentication middleware flow" .

# Inspect context decision routing and candidate evidence levels
token-save explain "Trace authentication middleware flow" .

# View local token accounting and budget diagnostics
token-save metrics --json
```

---

## 🔬 Testing & Verification

Yuro includes an 8-tier verification suite covering unit, integration, edge-case, property, and performance tests:

```bash
py -m unittest discover -s tests -t . -p "test_*.py"
```

* **Current Release Gate**: 35/35 tests passing cleanly.
* **Master Audit Report**: See [Production Readiness Report](validation/final/production_readiness_report.md).

---

## 📂 Project Structure

```text
src/
└── tokensaver/
    ├── core/           # Pipeline engine, admission gate, economics gate, tokenizer
    ├── indexing/       # Multi-language AST parsers (Python, TS, TSX, JS) & SQLite index
    ├── retrieval/      # Hybrid BM25, query expansion, symbol graph & semantic fallback
    ├── evidence/       # L0/L1/L2 evidence assembler & AST safe compressor
    └── output/         # Output token governor & formatting adapters
tests/                  # Unit, integration, property, regression, and performance tests
benchmarks/             # Benchmark runners and reproducibility scripts
validation/             # JSON audit artifacts and release gate logs
```

*Note: The underlying Python package name remains `tokensaver` for backwards compatibility; Yuro is the public project name.*

---

## 🔒 Security & Privacy

All repository scanning, AST parsing, symbol graph construction, lexical scoring, and token budgeting execute **100% locally on your machine**. Yuro does not use external vector databases, remote retrieval services, or telemetry tracking. Only the final selected evidence payload is passed to your configured LLM backend.

For security concerns, please refer to [SECURITY.md](SECURITY.md).

---

## 🗺️ Roadmap

- [ ] Additional language parsers (Go, Rust, C/C++)
- [ ] Direct IDE extensions (VS Code, JetBrains)
- [ ] Expanded multi-repository benchmark suites
- [ ] Incremental watcher performance enhancements

---

## 📄 License

Yuro is released under the [MIT License](LICENSE). Developed by [WillyEverGreen](https://github.com/WillyEverGreen). 🦊
