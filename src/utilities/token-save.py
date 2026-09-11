import sys
import os
import json
import time
import subprocess
import argparse
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR) # d:\Fullstack project\tokensaver\src
WORKSPACE_ROOT = os.path.dirname(REPO_ROOT) # d:\Fullstack project\tokensaver

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from tokensaver.core.engine import run_v6_pipeline
from tokensaver.output.caveman import CavemanGovernor
from tokensaver.core.tokenizer import get_default_token_counter
from tokensaver.retrieval.ranker import rank_evidence_units

CACHE_DIR = os.path.expanduser("~/.tokensaver-cache")
LAST_METRICS_FILE = os.path.join(CACHE_DIR, "last_metrics.json")
METRICS_HISTORY_FILE = os.path.join(CACHE_DIR, "metrics_history.jsonl")

def get_tool_script(filename):
    local_path = os.path.join(SCRIPT_DIR, filename)
    if os.path.exists(local_path):
        return local_path
    return os.path.join(os.path.expanduser("~"), filename)

def save_metrics(metrics_data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(LAST_METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)
        with open(METRICS_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics_data) + "\n")
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to save metrics: {e}\n")

def load_metrics():
    if os.path.exists(LAST_METRICS_FILE):
        try:
            with open(LAST_METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": "6.0",
        "task": "unknown",
        "confidence": "UNKNOWN",
        "raw_context_tokens": 0,
        "selected_context_tokens": 0,
        "net_saved_tokens": 0,
        "net_saved_percent": 0.0,
        "tokenizer_backend": "heuristic",
        "token_count_mode": "estimated"
    }

def run_auto_pipeline(task_prompt: str, workspace_path: str, mode: str = "adaptive"):
    start_time = time.time()
    governor = CavemanGovernor(mode=mode)
    
    # Pre-evaluate gate for task mode & caveman policy
    try:
        import task_classifier
    except ImportError:
        from utilities import task_classifier
    task_res = task_classifier.evaluate_gate(task_prompt)
    task_mode = task_res.get("mode", "targeted")
    confidence = task_res.get("confidence", "HIGH")
    
    caveman_enabled, caveman_reason = governor.should_enable(task_mode, confidence, task_prompt)
    
    # Run v6 Core Pipeline
    res = run_v6_pipeline(task_prompt, workspace_path, caveman_active=caveman_enabled)

    if res.get("skipped"):
        skipped_metrics = {
            "version": "6.0",
            "task": res.get("task_class", "simple"),
            "confidence": res.get("confidence", "HIGH"),
            "mode": "skipped",
            "caveman_enabled": False,
            "caveman_instruction_tokens": 0,
            "raw_tokens": 0,
            "selected_tokens": 0,
            "overhead_tokens": 0,
            "gross_savings": 0,
            "net_savings": 0,
            "net_savings_percent": 0.0,
            "fidelity": "VERIFIED",
            "result": "SKIPPED",
            "reason": res.get("reason", "skipped"),
            "raw_context_tokens": 0,
            "selected_context_tokens": 0,
            "net_saved_tokens": 0,
            "net_saved_percent": 0.0
        }
        save_metrics(skipped_metrics)
        print("// --- [TokenSaver Auto Engine v6.0 - Skipped] ---")
        print(f"// Task Mode: {res.get('task_class')} ({res.get('confidence')}) | Action: SKIP ({res.get('reason')})")
        print("// NET SAVINGS: 0")
        return

    caveman_enabled, caveman_reason = governor.should_enable(
        res.get("task_class", "targeted"),
        res.get("confidence", "HIGH"),
        task_prompt
    )

    full_metrics = {
        "version": "6.0",
        "task": res.get("task_class", "targeted"),
        "confidence": res.get("confidence", "HIGH"),
        "fallback": res.get("fallback", False),
        "raw_context_tokens": res.get("raw_context_tokens", 0),
        "selected_context_tokens": res.get("selected_context_tokens", 0),
        "gross_saved_tokens": res.get("gross_saved_tokens", 0),
        "overhead_tokens": res.get("overhead_tokens", 0),
        "net_saved_tokens": res.get("net_saved_tokens", 0),
        "net_saved_percent": res.get("net_saved_percent", 0.0),
        "coverage_score": res.get("coverage_score", 1.0),
        "tokenizer_backend": res.get("tokenizer_backend", "tiktoken"),
        "token_count_mode": res.get("token_count_mode", "exact"),
        "output_governor": {
            "caveman_enabled": caveman_enabled,
            "caveman_reason": caveman_reason,
            "directive": governor.get_directive() if caveman_enabled else ""
        },
        "elapsed_ms": round((time.time() - start_time) * 1000, 1),
        # Legacy compatibility aliases for legacy test suite
        "raw_tokens": res.get("raw_context_tokens", 0),
        "selected_tokens": res.get("selected_context_tokens", 0),
        "gross_savings": res.get("gross_saved_tokens", 0),
        "net_savings": res.get("net_saved_tokens", 0),
        "net_savings_percent": res.get("net_saved_percent", 0.0),
        "caveman_enabled": caveman_enabled,
        "caveman_instruction_tokens": 35 if caveman_enabled else 0,
        "result": "NET_POSITIVE" if res.get("net_saved_tokens", 0) > 0 else "NET_ZERO",
        "fidelity": "VERIFIED" if not res.get("fallback") else "FALLBACK"
    }
    save_metrics(full_metrics)

    print(res.get("banner", "// --- [TokenSaver Auto Engine v6.0 - Active] ---"))
    print(f"// Raw: {res.get('raw_context_tokens'):,} | Selected: {res.get('selected_context_tokens'):,} | Net: {res.get('net_saved_tokens'):,} ({res.get('net_saved_percent')}%) [{res.get('token_count_mode').upper()}]")
    if caveman_enabled:
        print(governor.get_directive())
    print(res.get("payload", ""))

def run_explain(task_prompt: str, workspace_path: str):
    import task_classifier
    import tokensaver_v5_evidence_planner as planner
    import tokensaver_v5_retriever as retriever

    task_res = task_classifier.evaluate_gate(task_prompt)
    print("==================================================")
    print("TOKEN SAVER V6 EXPLAINABILITY REPORT")
    print("==================================================")
    print(f"Prompt:     \"{task_prompt}\"")
    print(f"Admission:  {task_res.get('action')} ({task_res.get('reason')})")
    print(f"Task Mode:  {task_res.get('mode')} ({task_res.get('confidence')})")
    print("--------------------------------------------------")

    if task_res.get("action") == "SKIP":
        print("Pipeline bypassed by Admission Gate.")
        return

    plan = planner.create_evidence_plan(task_res.get("mode"), task_prompt)
    retrieved = retriever.retrieve_evidence(workspace_path, plan)
    ranked = rank_evidence_units(retrieved, plan)

    print(f"Retrieved Candidates: {len(retrieved)}")
    print("Top Ranked Symbols with Signal Breakdown:")
    for idx, u in enumerate(ranked[:5]):
        sig = u.get("signals", {})
        print(f"  {idx+1}. [{u.get('unit_type')}] {u.get('symbol_name')} ({u.get('relative_path')}) -> Score: {u.get('score')}")
        print(f"     Signals: target={sig.get('target_match')} bm25={sig.get('bm25')} graph={sig.get('graph_proximity')} centrality={sig.get('centrality')}")
    print("==================================================")

def main():
    parser = argparse.ArgumentParser(description="TokenSaver v6.0 Production CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auto_p = subparsers.add_parser("auto", help="Automatic workflow entry point")
    auto_p.add_argument("prompt", help="User task prompt")
    auto_p.add_argument("workspace", help="Target workspace path")
    auto_p.add_argument("--mode", choices=["normal", "caveman", "adaptive"], default="adaptive")

    explain_p = subparsers.add_parser("explain", help="Detailed explainability inspection")
    explain_p.add_argument("prompt", help="User task prompt")
    explain_p.add_argument("workspace", help="Target workspace path")

    metrics_p = subparsers.add_parser("metrics", help="Show token saver metrics")
    metrics_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    if args.command == "auto":
        run_auto_pipeline(args.prompt, args.workspace, mode=args.mode)
    elif args.command == "explain":
        run_explain(args.prompt, args.workspace)
    elif args.command == "metrics":
        m = load_metrics()
        if args.json:
            print(json.dumps(m, indent=2))
        else:
            print(f"Task: {m.get('task')} | Mode: {m.get('token_count_mode')} | Net Saved: {m.get('net_saved_tokens')} ({m.get('net_saved_percent')}%)")

if __name__ == "__main__":
    main()
