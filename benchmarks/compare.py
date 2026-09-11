import sys
import os
import json
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tokensaver.core.engine import run_v6_pipeline
from tokensaver.core.tokenizer import get_default_token_counter

def run_benchmark_comparison(workspace_path: str = "."):
    counter = get_default_token_counter()
    workspace_path = os.path.abspath(workspace_path)

    sample_tasks = [
        "Fix run_index in tokensaver_v5_symbol_index.py",
        "Refactor budget allocation in tokensaver_v5_budget.py",
        "Explain task_classifier evaluation gate logic",
        "Audit security issues in payment queue worker"
    ]

    results = []
    print("==================================================")
    print("TOKENSAVER V6 BENCHMARK COMPARISON REPORT")
    print("==================================================")

    for idx, prompt in enumerate(sample_tasks, 1):
        t0 = time.time()
        res = run_v6_pipeline(prompt, workspace_path)
        lat_ms = round((time.time() - t0) * 1000, 2)

        raw = res.get("raw_context_tokens", 0)
        sel = res.get("selected_context_tokens", 0)
        net = res.get("net_saved_tokens", 0)
        pct = res.get("net_saved_percent", 0.0)

        record = {
            "task_id": f"BENCH-{idx:03d}",
            "prompt": prompt,
            "raw_tokens": raw,
            "selected_tokens": sel,
            "net_saved": net,
            "net_saved_percent": pct,
            "latency_ms": lat_ms,
            "bypassed": res.get("fallback", False) or res.get("skipped", False)
        }
        results.append(record)

        print(f"\nTask {idx}: \"{prompt}\"")
        print(f"  Raw: {raw:,} | Selected: {sel:,} | Net Saved: {net:,} ({pct}%) | Latency: {lat_ms}ms")

    print("\n--------------------------------------------------")
    avg_net = sum(r["net_saved"] for r in results) / len(results) if results else 0
    avg_pct = sum(r["net_saved_percent"] for r in results) / len(results) if results else 0
    avg_lat = sum(r["latency_ms"] for r in results) / len(results) if results else 0

    print(f"Average Net Savings:  {int(avg_net):,} tokens ({avg_pct:.1f}%)")
    print(f"Average Latency:      {avg_lat:.2f} ms")
    print("==================================================")

    return results

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    run_benchmark_comparison(target)
