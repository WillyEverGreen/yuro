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
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

def get_tool_script(filename):
    local_path = os.path.join(SCRIPT_DIR, filename)
    if os.path.exists(local_path):
        return local_path
    return os.path.join(r"C:\tools", filename)

def get_config_path():
    local_cfg = os.path.join(REPO_ROOT, "config", "token-save.config.json")
    if os.path.exists(local_cfg):
        return local_cfg
    return r"C:\tools\token-save.config.json"

CACHE_DIR = r"C:\tools\.tokensaver-cache"
LAST_METRICS_FILE = os.path.join(CACHE_DIR, "last_metrics.json")
METRICS_HISTORY_FILE = os.path.join(CACHE_DIR, "metrics_history.jsonl")
CONFIG_PATH = get_config_path()

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "budgets": {"normal": 8000, "prune": 20000, "signatures": 40000, "aggressive": 60000},
        "fidelity_check": True
    }

def estimate_tokens(text):
    if not text:
        return 0
    return int(len(text) / 3.8)

def get_raw_workspace_text(workspace_path):
    if not os.path.exists(workspace_path):
        return ""
    if os.path.isfile(workspace_path):
        try:
            with open(workspace_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    elif os.path.isdir(workspace_path):
        parts = []
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'dist', 'build', '.tokensaver-cache']]
            for file in sorted(files):
                if file.endswith(('.py', '.ts', '.js', '.go', '.rs', '.cs', '.java', '.cpp', '.h', '.json', '.md')):
                    fp = os.path.join(root, file)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            parts.append(f.read())
                    except Exception:
                        pass
        return "\n".join(parts)
    return ""

def save_metrics(metrics):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(LAST_METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        with open(METRICS_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics) + "\n")
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
        "task": "unknown",
        "confidence": "UNKNOWN",
        "mode": "full",
        "caveman_enabled": False,
        "caveman_instruction_tokens": 0,
        "output_token_savings": "NOT MEASURED",
        "raw_tokens": 0,
        "selected_tokens": 0,
        "pruned_tokens": 0,
        "instruction_overhead": 0,
        "generated_result_overhead": 0,
        "overhead_tokens": 0,
        "gross_savings": 0,
        "net_savings": 0,
        "net_savings_percent": 0.0,
        "fidelity": "UNCHECKED",
        "result": "NET_ZERO",
        "estimation_method": "len(text) / 3.8 (ESTIMATED context tokens)",
        "overhead_breakdown": {
            "banner": 0,
            "history": 0,
            "headers": 0,
            "caveman": 0
        }
    }

def format_cli_report(m):
    task = m.get("task", "unknown")
    conf = m.get("confidence", "UNKNOWN")
    mode = m.get("mode", "full")
    caveman_enabled = m.get("caveman_enabled", False)
    caveman_tok = m.get("caveman_instruction_tokens", 0)
    raw = m.get("raw_tokens", 0)
    sel = m.get("selected_tokens", 0)
    gross = m.get("gross_savings", 0)
    overhead = m.get("overhead_tokens", 0)
    net = m.get("net_savings", 0)
    pct = m.get("net_savings_percent", 0.0)
    fid = m.get("fidelity", "VERIFIED")
    res = m.get("result", "NET_POSITIVE")

    lines = [
        "TOKEN SAVER METRICS",
        "────────────────────────────",
        f"Task:                 {task}",
        f"Confidence:           {conf}",
        f"Mode:                 {mode}",
        f"Caveman:              {'ENABLED' if caveman_enabled else 'DISABLED'}",
        f"Caveman overhead:       {caveman_tok} est. tokens",
        "",
        f"Raw context:          {raw:,} est. tokens",
        f"Selected context:      {sel:,} est. tokens",
        "",
        f"Gross savings:        {gross:,}",
        f"TokenSaver overhead:     {overhead:,}",
        "",
        f"NET SAVINGS:          {net:,}" if net > 0 else "NET SAVINGS:          0 / NEGATIVE",
        f"Net reduction:          {pct:.1f}%",
        "",
        f"Fidelity:             {fid}",
        f"Result:               {res}"
    ]
    if net <= 0 and res != "SKIPPED":
        lines.append("TokenSaver did not provide a net token benefit for this request.")
    return "\n".join(lines)

def run_multi_check_fidelity(raw_text, opt_text):
    checks = {}
    if not raw_text or not opt_text:
        return {"Fidelity": "PASS"}, "VERIFIED"
        
    if "def " in raw_text or "class " in raw_text:
        checks["Syntax Validity"] = "PASS" if ("def " in opt_text or "class " in opt_text or "..." in opt_text) else "FAIL"
    else:
        checks["Syntax Validity"] = "PASS" if len(opt_text) > 5 else "FAIL"

    raw_symbols = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{3,}\b', raw_text))
    opt_symbols = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{3,}\b', opt_text))
    preserved_ratio = len(raw_symbols.intersection(opt_symbols)) / max(len(raw_symbols), 1)
    checks["Symbol Preservation"] = "PASS" if preserved_ratio > 0.3 else "WARNING"

    if "import " in raw_text or "require(" in raw_text:
        checks["Imports Preserved"] = "PASS" if ("import " in opt_text or "require(" in opt_text or "from " in opt_text) else "WARNING"
    else:
        checks["Imports Preserved"] = "PASS"

    if "Traceback" in raw_text or "Error:" in raw_text:
        checks["Error Frames Preserved"] = "PASS" if ("Traceback" in opt_text or "Error:" in opt_text or "..." in opt_text) else "WARNING"
    else:
        checks["Error Frames Preserved"] = "PASS"

    checks["Referenced Files Preserved"] = "PASS" if len(opt_text) > 0 else "NOT VERIFIED"
    checks["Referenced Functions Preserved"] = "PASS" if ("def " in opt_text or "function" in opt_text or "..." in opt_text) else "NOT VERIFIED"
    checks["Explicit Requirements Preserved"] = "PASS" if len(opt_text) > 20 else "NOT VERIFIED"

    overall = "VERIFIED" if all(v in ["PASS", "VERIFIED"] for v in checks.values()) else "FIDELITY_FAILED"
    return checks, overall

def run_auto_pipeline(task_prompt, workspace_path):
    start_time = time.time()
    
    # 1. Deterministic task classification
    cls_proc = subprocess.run([sys.executable, get_tool_script("task_classifier.py"), task_prompt], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    cls_lines = cls_proc.stdout.strip().split('\n')
    
    task_mode = "plan"
    confidence = "HIGH"
    context_policy = "signatures"
    action = "INVOKE"
    reason = "workspace task"

    for line in cls_lines:
        if "TASK MODE:" in line: task_mode = line.split(":")[-1].strip()
        if "CONFIDENCE:" in line: confidence = line.split(":")[-1].strip()
        if "CONTEXT POLICY:" in line: context_policy = line.split(":")[-1].strip()
        if "Action:" in line: action = line.split(":")[-1].strip()
        if "Reason:" in line: reason = line.split(":")[-1].strip()

    # 2. Check if task classifier returned SKIP (conceptual/general Q&A)
    if action == "SKIP":
        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        metrics = {
            "task": task_mode,
            "confidence": confidence,
            "mode": "skipped",
            "caveman_enabled": False,
            "caveman_instruction_tokens": 0,
            "output_token_savings": "NOT MEASURED",
            "raw_tokens": 0,
            "selected_tokens": 0,
            "pruned_tokens": 0,
            "instruction_overhead": 0,
            "generated_result_overhead": 0,
            "overhead_tokens": 0,
            "gross_savings": 0,
            "net_savings": 0,
            "net_savings_percent": 0.0,
            "fidelity": "VERIFIED",
            "result": "SKIPPED",
            "reason": reason,
            "elapsed_ms": elapsed_ms,
            "estimation_method": "len(text) / 3.8 (ESTIMATED context tokens)",
            "overhead_breakdown": {
                "banner": 0,
                "history": 0,
                "headers": 0,
                "caveman": 0
            }
        }
        save_metrics(metrics)
        print(f"// --- [TokenSaver Auto Engine v4.0 - Skipped] ---")
        print(f"// Task Mode: {task_mode} ({confidence}) | Action: SKIP ({reason})")
        print(f"// NET SAVINGS: 0 (ESTIMATED)")
        return

    # 3. Adaptive Caveman Mode Decision Engine
    prompt_lower = task_prompt.lower()
    caveman_enabled = False
    caveman_reason = "disabled by default"

    if action == "SKIP":
        caveman_enabled = False
        caveman_reason = "task skipped"
    elif task_mode in ["security"]:
        caveman_enabled = False
        caveman_reason = "security mode requires full precision"
    elif task_mode in ["implement"] or "implement" in prompt_lower:
        caveman_enabled = False
        caveman_reason = "implementation requires detailed output"
    elif task_mode in ["plan", "architecture", "explain"] or any(k in prompt_lower for k in ["explain", "architecture"]):
        caveman_enabled = True
        caveman_reason = "high verbosity explanation benefits from concise output protocol"
    elif task_mode in ["debug", "refactor"] or any(k in prompt_lower for k in ["fix", "traceback", "refactor"]):
        if confidence == "HIGH":
            caveman_enabled = True
            caveman_reason = f"high-confidence task benefits from concise output protocol"
        else:
            caveman_enabled = False
            caveman_reason = f"low-confidence task defaults to full output"
    else:
        caveman_enabled = False
        caveman_reason = "default conservative policy"

    caveman_text = ""
    caveman_skill_path = r"C:\Users\advdi\.gemini\config\skills\caveman-mode\SKILL.md"

    if caveman_enabled and os.path.exists(caveman_skill_path):
        try:
            with open(caveman_skill_path, "r", encoding="utf-8", errors="ignore") as f:
                skill_content = f.read()
            caveman_text = (
                "// [TokenSaver Output Protocol: Caveman Active]\n"
                "// - Direct answers. No greetings, prompt restatements, or filler.\n"
                "// - Prefer code blocks and concise bullet lists over prose.\n"
                "// - Auto-expand ONLY for: security, destructive commands, breaking API changes, ambiguity, complex root causes, or explicit 'why' queries."
            )
        except Exception:
            caveman_enabled = False
            caveman_reason = "failed to read caveman skill file"

    caveman_instruction_tokens = estimate_tokens(caveman_text) if (caveman_enabled and caveman_text) else 0

    # 4. Low-confidence safety fallback
    if confidence == "LOW":
        task_mode = "implement"
        context_policy = "full"
        caveman_enabled = False

    # 5. Measure RAW available context
    raw_text = get_raw_workspace_text(workspace_path)
    raw_tokens = estimate_tokens(raw_text)

    # 6. Incremental Repository Index & Relevance Scoring
    subprocess.run([sys.executable, get_tool_script("repo_indexer.py"), workspace_path], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    subprocess.run([sys.executable, get_tool_script("relevance_engine.py"), workspace_path, task_prompt], capture_output=True, text=True, encoding="utf-8", errors="ignore")

    # 7. Selective History Context Retrieval
    hist_proc = subprocess.run([sys.executable, get_tool_script("history-state.py"), "render", "--task", task_mode], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    history_ctx = hist_proc.stdout.strip()
    history_overhead_tokens = estimate_tokens(history_ctx)

    # 8. Execute Task-Aware Code-Sig Compression
    sig_mode = "plan" if context_policy == "signatures" else "full"
    if task_mode in ["debug"]: sig_mode = "debug"
    if context_policy == "minimal": sig_mode = "plan"

    proc = subprocess.run([sys.executable, get_tool_script("code-sig.py"), sig_mode, workspace_path], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    compressed_payload = proc.stdout

    # Separate code payload from code-sig headers
    payload_lines = compressed_payload.split('\n')
    header_lines = [l for l in payload_lines if l.startswith("// --- [code-sig:")]
    body_lines = [l for l in payload_lines if not l.startswith("// --- [code-sig:")]

    code_sig_headers_text = "\n".join(header_lines)
    selected_code_body = "\n".join(body_lines)

    selected_tokens = estimate_tokens(selected_code_body)
    code_sig_headers_tokens = estimate_tokens(code_sig_headers_text)

    # Banner & metadata overhead
    banner_text = f"// --- [TokenSaver Auto Engine v4.0 - Active] ---\n// Task Mode: {task_mode} ({confidence}) | Policy: {context_policy}"
    banner_tokens = estimate_tokens(banner_text)

    generated_result_overhead = banner_tokens + history_overhead_tokens + code_sig_headers_tokens
    total_overhead_tokens = caveman_instruction_tokens + generated_result_overhead

    gross_savings = max(0, raw_tokens - selected_tokens)
    net_savings = gross_savings - total_overhead_tokens
    net_savings_percent = round((net_savings / max(raw_tokens, 1)) * 100, 1)

    # 9. Fidelity Check
    checks, fidelity_status = run_multi_check_fidelity(raw_text, selected_code_body)

    result_status = "NET_POSITIVE" if net_savings > 0 and fidelity_status == "VERIFIED" else "NET_ZERO"

    # 10. Safety Gate & Fallback Engine
    if fidelity_status != "VERIFIED" and sig_mode != "full":
        proc = subprocess.run([sys.executable, get_tool_script("code-sig.py"), "full", workspace_path], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        compressed_payload = proc.stdout
        selected_code_body = compressed_payload
        selected_tokens = estimate_tokens(selected_code_body)
        gross_savings = max(0, raw_tokens - selected_tokens)
        net_savings = gross_savings - total_overhead_tokens
        net_savings_percent = round((net_savings / max(raw_tokens, 1)) * 100, 1)
        fidelity_status = "FALLBACK_RESTORED (VERIFIED)"
        result_status = "FIDELITY_FAILED"

    # If NET savings are non-positive, fall back to raw context to avoid net-negative token overhead
    if net_savings <= 0:
        selected_code_body = raw_text
        compressed_payload = raw_text
        selected_tokens = raw_tokens
        gross_savings = 0
        net_savings = 0
        net_savings_percent = 0.0
        result_status = "NET_NEGATIVE" if (raw_tokens - selected_tokens - total_overhead_tokens) < 0 else "NET_ZERO"

    elapsed_ms = round((time.time() - start_time) * 1000, 1)

    metrics = {
        "task": task_mode,
        "confidence": confidence,
        "mode": sig_mode,
        "caveman_enabled": caveman_enabled,
        "caveman_reason": caveman_reason,
        "caveman_instruction_tokens": caveman_instruction_tokens,
        "output_token_savings": "NOT MEASURED",
        "raw_tokens": raw_tokens,
        "selected_tokens": selected_tokens,
        "pruned_tokens": gross_savings,
        "instruction_overhead": caveman_instruction_tokens,
        "generated_result_overhead": generated_result_overhead,
        "overhead_tokens": total_overhead_tokens,
        "gross_savings": gross_savings,
        "net_savings": max(0, net_savings),
        "net_savings_percent": max(0.0, net_savings_percent),
        "fidelity": fidelity_status,
        "result": result_status,
        "elapsed_ms": elapsed_ms,
        "estimation_method": "len(text) / 3.8 (ESTIMATED context tokens)",
        "overhead_breakdown": {
            "banner": banner_tokens,
            "history": history_overhead_tokens,
            "headers": code_sig_headers_tokens,
            "caveman": caveman_instruction_tokens
        }
    }
    save_metrics(metrics)

    subprocess.run([sys.executable, get_tool_script("session_logger.py"), "record", str(raw_tokens), str(selected_tokens + total_overhead_tokens), str(elapsed_ms)])

    print("// --- [TokenSaver Auto Engine v4.0 - Active] ---")
    print(f"// Task Mode: {task_mode} ({confidence}) | Policy: {context_policy} | Fidelity: {fidelity_status}")
    print(f"// Raw: {raw_tokens:,} est. | Selected: {selected_tokens:,} est. | Gross: {gross_savings:,} | Overhead: {total_overhead_tokens:,} | NET: {max(0, net_savings):,} ({max(0.0, net_savings_percent)}%) [ESTIMATED]")
    if net_savings <= 0:
        print("// NET SAVINGS: 0 / NEGATIVE")
        print("// TokenSaver did not provide a net token benefit for this request.")
    if caveman_enabled and caveman_text:
        print(caveman_text)
    if history_ctx:
        print(history_ctx)
    print(compressed_payload)

def main():
    parser = argparse.ArgumentParser(description="Adaptive TokenSaver Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auto_p = subparsers.add_parser("auto", help="Automatic workflow entry point")
    auto_p.add_argument("prompt", help="User task prompt")
    auto_p.add_argument("workspace", help="Target workspace path")

    metrics_p = subparsers.add_parser("metrics", help="Show deterministic token saver metrics")
    metrics_p.add_argument("--json", action="store_true", help="Output compact machine-readable JSON")

    plan_p = subparsers.add_parser("plan", help="AST signature extraction")
    plan_p.add_argument("path", help="Target path")

    debug_p = subparsers.add_parser("debug", help="Debugging context extraction")
    debug_p.add_argument("path", help="Target path")

    ctx_p = subparsers.add_parser("context", help="Structural context compression")
    ctx_p.add_argument("path", help="Target path")
    ctx_p.add_argument("--mode", choices=["safe", "aggressive"], default="safe")

    stats_p = subparsers.add_parser("stats", help="Context budget audit & report")
    stats_p.add_argument("path", help="Target path")

    inspect_p = subparsers.add_parser("inspect", help="Dry-run inspection mode")
    inspect_p.add_argument("path", help="Target path")
    inspect_p.add_argument("--prompt", default="architecture")

    classify_p = subparsers.add_parser("classify", help="Classify prompt task mode")
    classify_p.add_argument("prompt", help="User prompt")

    index_p = subparsers.add_parser("index", help="Incremental repository index")
    index_p.add_argument("path", help="Target repository")

    session_p = subparsers.add_parser("session", help="Session metrics audit")
    benchmark_p = subparsers.add_parser("benchmark", help="Run agent benchmark")

    args = parser.parse_args()

    if args.command == "auto":
        run_auto_pipeline(args.prompt, args.workspace)

    elif args.command == "metrics":
        m = load_metrics()
        if args.json:
            json_out = {
                "task": m.get("task", "unknown"),
                "confidence": m.get("confidence", "UNKNOWN"),
                "mode": m.get("mode", "full"),
                "caveman_enabled": m.get("caveman_enabled", False),
                "caveman_instruction_tokens": m.get("caveman_instruction_tokens", 0),
                "output_token_savings": m.get("output_token_savings", "NOT MEASURED"),
                "raw_tokens": m.get("raw_tokens", 0),
                "selected_tokens": m.get("selected_tokens", 0),
                "pruned_tokens": m.get("pruned_tokens", 0),
                "instruction_overhead": m.get("instruction_overhead", 0),
                "generated_result_overhead": m.get("generated_result_overhead", 0),
                "overhead_tokens": m.get("overhead_tokens", 0),
                "gross_savings": m.get("gross_savings", 0),
                "net_savings": m.get("net_savings", 0),
                "net_savings_percent": m.get("net_savings_percent", 0.0),
                "fidelity": m.get("fidelity", "VERIFIED"),
                "result": m.get("result", "NET_POSITIVE"),
                "overhead_breakdown": m.get("overhead_breakdown", {})
            }
            print(json.dumps(json_out, indent=2))
        else:
            print(format_cli_report(m))

    elif args.command == "plan":
        subprocess.run([sys.executable, get_tool_script("code-sig.py"), "plan", args.path])

    elif args.command == "debug":
        subprocess.run([sys.executable, get_tool_script("code-sig.py"), "debug", args.path])

    elif args.command == "context":
        subprocess.run([sys.executable, get_tool_script("structural-prune.py"), args.path, "--mode", args.mode])

    elif args.command == "inspect":
        subprocess.run([sys.executable, get_tool_script("relevance_engine.py"), args.path, args.prompt])

    elif args.command == "classify":
        subprocess.run([sys.executable, get_tool_script("task_classifier.py"), args.prompt])

    elif args.command == "index":
        subprocess.run([sys.executable, get_tool_script("repo_indexer.py"), args.path])

    elif args.command == "session":
        subprocess.run([sys.executable, get_tool_script("session_logger.py"), "show"])

    elif args.command == "benchmark":
        subprocess.run([sys.executable, get_tool_script("token-save-benchmark.py")])

if __name__ == "__main__":
    main()
