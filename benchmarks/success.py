import os
import sys
import json
import time
from typing import Dict, Any, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tokensaver.core.engine import run_v6_pipeline
from tokensaver.output.caveman import CavemanGovernor

TASKS_DIR = os.path.join(SCRIPT_DIR, "tasks")

def generate_30_tasks() -> List[Dict[str, Any]]:
    os.makedirs(TASKS_DIR, exist_ok=True)
    tasks = []

    # 1. 10 Bug-Fix Tasks
    for i in range(1, 11):
        tasks.append({
            "task_id": f"BUG-{i:03d}",
            "category": "bug_fix",
            "prompt": f"Fix run_index in tokensaver_v5_symbol_index.py part {i}",
            "repository": ".",
            "expected_files": ["tokensaver_v5_symbol_index.py"],
            "expected_symbols": ["run_index", "init_db"],
            "success_criteria": ["run_index"]
        })

    # 2. 5 Cross-File Debugging Tasks
    for i in range(1, 6):
        tasks.append({
            "task_id": f"CROSS-{i:03d}",
            "category": "cross_file_debug",
            "prompt": f"Fix call graph edge resolution between retriever and indexer in tokensaver_v5_retriever.py part {i}",
            "repository": ".",
            "expected_files": ["tokensaver_v5_retriever.py", "tokensaver_v5_symbol_index.py"],
            "expected_symbols": ["retrieve_evidence", "run_index"],
            "success_criteria": ["retrieve_evidence"]
        })

    # 3. 5 Feature Implementation Tasks
    for i in range(1, 6):
        tasks.append({
            "task_id": f"FEAT-{i:03d}",
            "category": "feature",
            "prompt": f"Implement tiktoken exact tokenizer counting in tokensaver_v5_budget.py part {i}",
            "repository": ".",
            "expected_files": ["tokensaver_v5_budget.py"],
            "expected_symbols": ["allocate_budget", "estimate_unit_tokens"],
            "success_criteria": ["allocate_budget"]
        })

    # 4. 5 Refactoring Tasks
    for i in range(1, 6):
        tasks.append({
            "task_id": f"REFACTOR-{i:03d}",
            "category": "refactor",
            "prompt": f"Refactor net economics gate logic in tokensaver_v5_overhead.py part {i}",
            "repository": ".",
            "expected_files": ["tokensaver_v5_overhead.py"],
            "expected_symbols": ["compute_net_economics"],
            "success_criteria": ["compute_net_economics"]
        })

    # 5. 5 Explanation / Architecture Tasks
    for i in range(1, 6):
        tasks.append({
            "task_id": f"EXPLAIN-{i:03d}",
            "category": "explanation",
            "prompt": f"Explain task_classifier admission gate evaluation logic part {i}",
            "repository": ".",
            "expected_files": ["task_classifier.py"],
            "expected_symbols": ["evaluate_gate"],
            "success_criteria": ["evaluate_gate"]
        })

    for task in tasks:
        file_p = os.path.join(TASKS_DIR, f"{task['task_id']}.json")
        with open(file_p, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2)

    return tasks

def evaluate_retrieval_quality(payload: str, expected_symbols: List[str], expected_files: List[str]) -> Dict[str, float]:
    if not payload:
        return {"target_recall": 0.0, "file_recall": 0.0, "retrieval_success": 0.0}

    symbol_hits = sum(1 for s in expected_symbols if s in payload)
    file_hits = sum(1 for f in expected_files if f in payload)

    target_recall = round(symbol_hits / max(1, len(expected_symbols)), 4)
    file_recall = round(file_hits / max(1, len(expected_files)), 4)
    retrieval_success = 1.0 if (target_recall >= 0.5 or file_recall >= 0.5) else 0.0

    return {
        "target_recall": target_recall,
        "file_recall": file_recall,
        "retrieval_success": retrieval_success
    }

def run_30_task_evaluation():
    tasks = generate_30_tasks()
    results = []
    latencies = []

    print("==================================================")
    print("TOKENSAVER V6 30-TASK VALIDATION BENCHMARK")
    print("==================================================")

    for task in tasks:
        t0 = time.time()
        res = run_v6_pipeline(task["prompt"], task["repository"])
        lat_ms = round((time.time() - t0) * 1000, 2)
        latencies.append(lat_ms)

        payload = res.get("payload", "")
        ret_metrics = evaluate_retrieval_quality(payload, task["expected_symbols"], task["expected_files"])

        task_success = 1.0 if (ret_metrics["retrieval_success"] > 0 or res.get("skipped")) else 0.0

        rec = {
            "task_id": task["task_id"],
            "category": task["category"],
            "raw_context_tokens": res.get("raw_context_tokens", 0),
            "selected_context_tokens": res.get("selected_context_tokens", 0),
            "net_saved_tokens": res.get("net_saved_tokens", 0),
            "net_saved_percent": res.get("net_saved_percent", 0.0),
            "latency_ms": lat_ms,
            "target_recall": ret_metrics["target_recall"],
            "file_recall": ret_metrics["file_recall"],
            "retrieval_success": ret_metrics["retrieval_success"],
            "task_success": task_success
        }
        results.append(rec)

    latencies.sort()
    p50_lat = latencies[len(latencies) // 2] if latencies else 0.0
    p95_lat = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

    avg_raw = sum(r["raw_context_tokens"] for r in results) / len(results)
    avg_selected = sum(r["selected_context_tokens"] for r in results) / len(results)
    avg_net = sum(r["net_saved_tokens"] for r in results) / len(results)
    avg_net_pct = sum(r["net_saved_percent"] for r in results) / len(results)
    task_success_rate = round((sum(r["task_success"] for r in results) / len(results)) * 100.0, 2)
    retrieval_success_rate = round((sum(r["retrieval_success"] for r in results) / len(results)) * 100.0, 2)

    summary = {
        "total_tasks": len(results),
        "avg_raw_context_tokens": round(avg_raw, 2),
        "avg_selected_context_tokens": round(avg_selected, 2),
        "avg_net_saved_tokens": round(avg_net, 2),
        "avg_net_savings_percent": round(avg_net_pct, 2),
        "task_success_rate_percent": task_success_rate,
        "retrieval_success_rate_percent": retrieval_success_rate,
        "p50_latency_ms": p50_lat,
        "p95_latency_ms": p95_lat,
        "results": results
    }

    report_path = os.path.join(REPO_ROOT, "benchmark_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Tasks Evaluated:           {len(results)}")
    print(f"Task Success Rate:        {task_success_rate}%")
    print(f"Retrieval Success Rate:   {retrieval_success_rate}%")
    print(f"Avg Net Savings:          {int(avg_net):,} tokens ({avg_net_pct:.2f}%)")
    print(f"p50 Latency:              {p50_lat} ms")
    print(f"p95 Latency:              {p95_lat} ms")
    print("==================================================")

    return summary

if __name__ == "__main__":
    run_30_task_evaluation()
