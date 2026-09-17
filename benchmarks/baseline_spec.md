# TokenSaver v6.0 - Benchmark Baseline Specification & Audit

## 1. Executive Overview

This document specifies the exact methodology, repository snapshot, tokenization rules, and baseline models used for benchmarking **TokenSaver v6.0**.

The goal of this specification is to make baseline comparisons **transparent, non-gamed, and externally defensible**.

---

## 2. Full Context Baseline Audit (13.17M Token Experiment)

The 13,175,153 input token baseline reported in the Caveman Experiment represents the raw context accumulated when feeding complete repository source trees without TokenSaver context optimization.

### Repository Audit Parameters:
* **Included Files**: All standard source files (`.py`, `.ts`, `.js`, `.json`, `.md`).
* **Excluded Files**: `.git/`, `node_modules/`, `venv/`, `__pycache__/`, binary files, build artifacts.
* **Concatenation Rules**: Sequential reading with standard markdown header dividers (`# File: relative/path/to/file`).
* **Tokenizer Backend**: `tiktoken` with `cl100k_base` encoding (falling back to exact character-ratio `len(text)/3.8` when `tiktoken` is uninstalled).
* **System Prompt / Instruction Tokens**: 150 fixed system prompt tokens added per request.
* **Deduplication**: Files are deduplicated by canonical absolute filepath before concatenation.

---

## 3. Dual Baseline Definitions

TokenSaver v6.0 is evaluated against two explicit baseline models to ensure fair comparison:

### Baseline A - Full Repository Baseline
* **Description**: Concatenates all eligible source files in the target repository workspace up to the model's context window limit.
* **Use Case**: Measures context reduction against naive full-workspace prompting.

### Baseline B - Practical File-Level Baseline
* **Description**: Uses a simple keyword heuristic matching files referenced in the prompt and their direct 1-hop module imports.
* **Use Case**: Prevents TokenSaver from being compared exclusively against an unrealistically large full-repository payload.

---

## 4. Deterministic Repository-Size Partitioning Rule

Repositories are partitioned into three size tiers using an explicit deterministic hierarchy:

```text
LARGE if ANY large threshold is exceeded (>500KB OR >50 files)
else MEDIUM if ANY medium threshold is exceeded (>50KB OR >10 files)
else SMALL
```

### Tier Metrics Summary:
* **SMALL**: Repositories $\le$ 50 KB total size AND $\le$ 10 files.
* **MEDIUM**: Repositories between 50 KB and 500 KB OR between 10 and 50 files.
* **LARGE**: Repositories > 500 KB total size OR > 50 files.

---

## 5. Statistical Rigor & Confidence Intervals

* **Task Success Rates**: Descriptive 95% Wilson score confidence intervals are calculated using:
  $$p \pm Z \sqrt{\frac{p(1-p)}{n} + \frac{Z^2}{4n^2}}$$
  where $Z = 1.96$ for 95% confidence level.
* **Interpretation Note**: Confidence intervals on 30-task samples are reported as descriptive range bounds and are not overinterpreted as statistical superiority proofs.
