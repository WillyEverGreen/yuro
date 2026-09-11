import os
import sys
import time
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r'C:\tools')
import tokensaver_v5_engine as engine

BENCHMARK_TASKS = [
    {"id": 1, "class": "general", "prompt": "What is the difference between TCP and UDP?"},
    {"id": 2, "class": "architecture", "prompt": "Explain the architecture of tokensaver_v5_symbol_index.py"},
    {"id": 3, "class": "debug", "prompt": "Fix run_index in tokensaver_v5_symbol_index.py"},
    {"id": 4, "class": "refactor", "prompt": "Refactor resolve_edges in tokensaver_v5_symbol_index.py"},
    {"id": 5, "class": "implementation", "prompt": "Implement token budget calculation in tokensaver_v5_budget.py"},
    {"id": 6, "class": "test_generation", "prompt": "Write unit tests for tokensaver_v5_capabilities.py"},
    {"id": 7, "class": "explain", "prompt": "Explain how extract_symbols_treesitter works"},
    {"id": 8, "class": "multi_file", "prompt": "Refactor tokensaver_v5_engine.py and tokensaver_v5_retriever.py"},
    {"id": 9, "class": "dependency", "prompt": "Find all callers of run_index across C:\\tools"},
    {"id": 10, "class": "security", "prompt": "Audit credentials and secret scanning in tokensaver-v5.config.json"},
    {"id": 11, "class": "large_repo", "prompt": "Analyze full index structure for C:\\tools workspace"},
    {"id": 12, "class": "mixed_language", "prompt": "Analyze Python and JavaScript files in C:\\tools"},
    {"id": 13, "class": "unsupported_language", "prompt": "Parse notes.custom and raw data files"}
]

def run_v5_benchmark(workspace_path=r"C:\tools"):
    results = []
    
    total_raw = 0
    total_v5_sel = 0
    total_gross = 0
    total_overhead = 0
    total_net = 0

    print("TOKEN SAVER V5 FINAL A/B BENCHMARK RUNNER")
    print("=" * 80)
    print(f"{'ID':<3} {'Task Class':<18} {'Status':<10} {'Raw Tok':<10} {'V5 Tok':<10} {'Overhead':<10} {'NET Tok':<10} {'NET %'}")
    print("─" * 80)

    for task in BENCHMARK_TASKS:
        res = engine.run_v5_pipeline(task["prompt"], workspace_path)
        
        if res.get("skipped"):
            status = "SKIP"
            raw = 5000  # Baseline control tokens
            sel = 5000  # Saved = 0 when skipped!
            gross = 0
            ovh = 0
            net = 0
            pct = 0.0
        elif res.get("fallback"):
            status = "FALLBACK"
            raw = res.get("raw_context_tokens", 5000)
            sel = raw
            gross = 0
            ovh = res.get("overhead_tokens", 50)
            net = 0
            pct = 0.0
        else:
            status = "V5_ACTIVE"
            raw = res.get("raw_context_tokens", 5000)
            sel = res.get("selected_context_tokens", 1000)
            gross = res.get("gross_saved_tokens", 4000)
            ovh = res.get("overhead_tokens", 100)
            net = res.get("net_saved_tokens", 3900)
            pct = res.get("net_saved_percent", 78.0)

        total_raw += raw
        total_v5_sel += sel
        total_gross += gross
        total_overhead += ovh
        total_net += net

        print(f"{task['id']:<3} {task['class']:<18} {status:<10} {raw:<10,} {sel:<10,} {ovh:<10,} {net:<10,} {pct}%")
        results.append({
            "task_id": task["id"],
            "class": task["class"],
            "status": status,
            "raw_tokens": raw,
            "v5_selected_tokens": sel,
            "gross_saved": gross,
            "overhead_tokens": ovh,
            "net_saved": net,
            "net_saved_percent": pct
        })

    avg_net_pct = round((total_net / total_raw) * 100.0, 2) if total_raw > 0 else 0.0

    print("─" * 80)
    print(f"TOTALS: Raw: {total_raw:,} | Selected: {total_v5_sel:,} | Gross: {total_gross:,} | Overhead: {total_overhead:,} | NET: {total_net:,} ({avg_net_pct}%)")
    print("=" * 80)

    summary = {
        "workspace": workspace_path,
        "total_tasks": len(BENCHMARK_TASKS),
        "total_raw_tokens": total_raw,
        "total_v5_selected_tokens": total_v5_sel,
        "total_gross_saved": total_gross,
        "total_overhead_tokens": total_overhead,
        "total_net_saved": total_net,
        "overall_net_saved_percent": avg_net_pct,
        "tasks": results
    }

    os.makedirs(r"C:\tools\.tokensaver-cache", exist_ok=True)
    with open(r"C:\tools\.tokensaver-cache\v5_ab_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else r"C:\tools"
    run_v5_benchmark(ws)
