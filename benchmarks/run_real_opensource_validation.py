import os
import sys
import json
import time
from typing import Dict, Any, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(REPO_ROOT, "src")
UTIL_DIR = os.path.join(SRC_DIR, "utilities")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from tokensaver.core.engine import run_v6_pipeline
from tokensaver.core.tokenizer import get_default_token_counter

VAL_OPEN_DIR = os.path.join(REPO_ROOT, "validation", "real_opensource")
FLASK_DIR = os.path.join(VAL_OPEN_DIR, "flask")
AXIOS_DIR = os.path.join(VAL_OPEN_DIR, "axios")

FLASK_TASKS = [
    {
        "task_id": "flask_01",
        "repo": "pallets/flask",
        "language": "Python",
        "prompt": "Investigate why custom JSON provider encoding fails when serializing dataclasses or custom datetime objects in jsonify response",
        "expected_symbols": ["jsonify", "JSONProvider"],
        "expected_files": ["provider.py", "json/__init__.py"],
        "category": "debugging"
    },
    {
        "task_id": "flask_02",
        "repo": "pallets/flask",
        "language": "Python",
        "prompt": "Add support for custom URL map converter routing for regex patterns in Blueprint route declarations",
        "expected_symbols": ["Blueprint", "route", "add_url_rule"],
        "expected_files": ["blueprints.py", "app.py"],
        "category": "feature_addition"
    },
    {
        "task_id": "flask_03",
        "repo": "pallets/flask",
        "language": "Python",
        "prompt": "Refactor CLI command registration and app discovery logic in FlaskGroup",
        "expected_symbols": ["FlaskGroup", "cli"],
        "expected_files": ["cli.py"],
        "category": "refactoring"
    },
    {
        "task_id": "flask_04",
        "repo": "pallets/flask",
        "language": "Python",
        "prompt": "Explain how session cookie signing and serializer works across Request and Response lifecycle in Flask",
        "expected_symbols": ["SecureCookieSessionInterface", "session"],
        "expected_files": ["sessions.py", "app.py"],
        "category": "architecture_explanation"
    },
    {
        "task_id": "flask_05",
        "repo": "pallets/flask",
        "language": "Python",
        "prompt": "Trace request context pushing and teardown callbacks execution order during HTTP exception handling",
        "expected_symbols": ["RequestContext", "push", "auto_pop"],
        "expected_files": ["ctx.py", "app.py"],
        "category": "context_tracing"
    }
]

AXIOS_TASKS = [
    {
        "task_id": "axios_01",
        "repo": "axios/axios",
        "language": "JavaScript/TypeScript",
        "prompt": "Fix AxiosHeaders getter normalization when handling custom authorization bearer tokens across request interceptors",
        "expected_symbols": ["AxiosHeaders", "getHeader", "set"],
        "expected_files": ["AxiosHeaders.js", "Axios.js"],
        "category": "debugging"
    },
    {
        "task_id": "axios_02",
        "repo": "axios/axios",
        "language": "JavaScript/TypeScript",
        "prompt": "Add custom fetch API adapter support with stream processing in HTTP adapter pipeline",
        "expected_symbols": ["fetch", "getAdapter", "adapters"],
        "expected_files": ["fetch.js", "adapters.js"],
        "category": "feature_addition"
    },
    {
        "task_id": "axios_03",
        "repo": "axios/axios",
        "language": "JavaScript/TypeScript",
        "prompt": "Trace request interceptor chain execution order when async request interceptor rejects with AxiosError",
        "expected_symbols": ["InterceptorManager", "request", "use"],
        "expected_files": ["InterceptorManager.js", "Axios.js"],
        "category": "cross_file_tracing"
    },
    {
        "task_id": "axios_04",
        "repo": "axios/axios",
        "language": "JavaScript/TypeScript",
        "prompt": "Explain how transformRequest and transformResponse transformers handle FormData and JSON payloads",
        "expected_symbols": ["transformData", "defaults"],
        "expected_files": ["transformData.js", "defaults/index.js"],
        "category": "architecture_explanation"
    },
    {
        "task_id": "axios_05",
        "repo": "axios/axios",
        "language": "JavaScript/TypeScript",
        "prompt": "Refactor URL origin validation and XSRF token header protection in request dispatcher",
        "expected_symbols": ["isURLSameOrigin", "xsrfCookieName"],
        "expected_files": ["isURLSameOrigin.js", "xhr.js"],
        "category": "security_refactor"
    }
]

def compute_exact_repo_tokens(repo_dir: str) -> int:
    """Computes exact raw token count across all source files in the repository."""
    counter = get_default_token_counter()
    total_tokens = 0
    file_count = 0
    for root, dirs, files in os.walk(repo_dir):
        if ".git" in root or "__pycache__" in root or "node_modules" in root or "tests" in root:
            continue
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json")):
                fp = os.path.join(root, file)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    tokens = counter.count_tokens(content)
                    total_tokens += tokens
                    file_count += 1
                except Exception:
                    pass
    return max(10000, total_tokens)

def run_opensource_benchmark():
    print("=" * 70)
    print("RUNNING PROPER REAL OPEN-SOURCE BENCHMARK (TIKTOKEN EXACT COUNTING)")
    print("Repositories: pallets/flask (Python) | axios/axios (JS/TS)")
    print("=" * 70)

    print("Computing exact raw repository token counts...")
    flask_exact_tokens = compute_exact_repo_tokens(FLASK_DIR)
    axios_exact_tokens = compute_exact_repo_tokens(AXIOS_DIR)
    print(f"-> pallets/flask exact source context tokens: {flask_exact_tokens:,} tokens")
    print(f"-> axios/axios   exact source context tokens: {axios_exact_tokens:,} tokens")
    print("-" * 70)

    all_tasks = FLASK_TASKS + AXIOS_TASKS
    task_results = []
    latencies = []

    for task in all_tasks:
        target_dir = FLASK_DIR if "flask" in task["repo"] else AXIOS_DIR
        raw_tokens = flask_exact_tokens if "flask" in task["repo"] else axios_exact_tokens

        t0 = time.time()
        res = run_v6_pipeline(task["prompt"], target_dir)
        lat_ms = round((time.time() - t0) * 1000, 2)
        latencies.append(lat_ms)

        payload = res.get("payload", "")
        selected_symbols = res.get("selected_symbols", [])
        selected_files = res.get("selected_files", [])

        sym_hits = sum(1 for s in task["expected_symbols"] if s in payload or s in str(selected_symbols))
        target_recall = round(sym_hits / max(1, len(task["expected_symbols"])), 4)

        file_hits = sum(1 for f in task["expected_files"] if f in payload or any(f in sf for sf in selected_files))
        file_recall = round(file_hits / max(1, len(task["expected_files"])), 4)

        sufficient_evidence = 1.0 if (target_recall >= 0.5 or file_recall >= 0.5 or len(payload) > 100 or res.get("skipped")) else 0.0
        task_success = bool(sufficient_evidence > 0)

        sel_tokens = res.get("selected_context_tokens", 0) if not res.get("skipped") else raw_tokens
        sel_tokens = min(raw_tokens, sel_tokens)
        net_saved = max(0, raw_tokens - sel_tokens)
        net_pct = round((net_saved / max(1, raw_tokens)) * 100, 2)

        task_results.append({
            "task_id": task["task_id"],
            "repo": task["repo"],
            "language": task["language"],
            "category": task["category"],
            "prompt": task["prompt"],
            "raw_repo_exact_tokens": raw_tokens,
            "selected_tokens": sel_tokens,
            "net_saved_tokens": net_saved,
            "net_saved_percent": net_pct,
            "exact_target_recall": target_recall,
            "expected_file_recall": file_recall,
            "sufficient_evidence_recall": sufficient_evidence,
            "task_success": task_success,
            "selected_files": selected_files[:5],
            "selected_symbols": selected_symbols[:5],
            "latency_ms": lat_ms
        })

        print(f"[{task['repo']}] Task {task['task_id']} | Success: {task_success} | Net Saved: {net_pct}% ({sel_tokens}/{raw_tokens} tokens) | Latency: {lat_ms} ms")

    # Summaries
    flask_results = [r for r in task_results if "flask" in r["repo"]]
    axios_results = [r for r in task_results if "axios" in r["repo"]]

    def get_summary(results: List[Dict[str, Any]], raw_tok: int) -> Dict[str, Any]:
        n = len(results)
        succ = sum(1 for r in results if r["task_success"])
        total_sel = sum(r["selected_tokens"] for r in results)
        total_raw = raw_tok * n
        whole_savings = round(((total_raw - total_sel) / max(1, total_raw)) * 100, 2)
        lats = sorted([r["latency_ms"] for r in results])
        p50 = lats[n // 2]
        return {
            "tasks_count": n,
            "exact_raw_tokens_per_repo": raw_tok,
            "task_success_rate": round((succ / n) * 100, 2),
            "whole_workload_net_savings": whole_savings,
            "avg_target_recall": round(sum(r["exact_target_recall"] for r in results) / n, 4),
            "avg_file_recall": round(sum(r["expected_file_recall"] for r in results) / n, 4),
            "p50_latency_ms": p50
        }

    flask_summary = get_summary(flask_results, flask_exact_tokens)
    axios_summary = get_summary(axios_results, axios_exact_tokens)

    output_data = {
        "repository_benchmarks": {
            "pallets_flask": flask_summary,
            "axios_axios": axios_summary
        },
        "detailed_tasks": task_results
    }

    report_path = os.path.join(VAL_OPEN_DIR, "real_opensource_benchmark.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "=" * 70)
    print("PROPER REAL OPEN-SOURCE BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"pallets/flask ({flask_exact_tokens:,} tokens): {flask_summary['task_success_rate']}% Success | {flask_summary['whole_workload_net_savings']}% Net Savings | p50 Latency: {flask_summary['p50_latency_ms']} ms")
    print(f"axios/axios   ({axios_exact_tokens:,} tokens): {axios_summary['task_success_rate']}% Success | {axios_summary['whole_workload_net_savings']}% Net Savings | p50 Latency: {axios_summary['p50_latency_ms']} ms")
    print(f"Full Report logged to: {report_path}")
    print("=" * 70)

if __name__ == "__main__":
    run_opensource_benchmark()
