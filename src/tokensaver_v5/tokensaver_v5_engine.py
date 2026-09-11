import os
import sys
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if r'C:\tools' not in sys.path:
    sys.path.append(r'C:\tools')
import tokensaver_v5_capabilities as caps
import tokensaver_v5_evidence_planner as planner
import tokensaver_v5_retriever as retriever
import tokensaver_v5_ranker as ranker
import tokensaver_v5_budget as budget
import tokensaver_v5_assembler as assembler
import tokensaver_v5_coverage as coverage
import tokensaver_v5_overhead as overhead
import tokensaver_v5_metrics as metrics
import task_classifier

def run_v5_pipeline(user_prompt, workspace_path, token_budget=4000):
    t_start = time.time()
    workspace_path = os.path.abspath(workspace_path)
    
    # 1. Classification & Admission Gate
    task_res = task_classifier.evaluate_gate(user_prompt)
    action = task_res.get("action", "INVOKE")
    task_class = task_res.get("mode", "targeted")
    confidence = task_res.get("confidence", "MEDIUM")
    reason = task_res.get("reason", "General task admitted directly")
    
    if action == "SKIP":
        return {
            "engine": "v5",
            "skipped": True,
            "reason": reason,
            "task_class": task_class,
            "confidence": confidence,
            "raw_context_tokens": 0,
            "selected_context_tokens": 0,
            "net_saved_tokens": 0,
            "net_saved_percent": 0.0,
            "payload": ""
        }

    # 2. Capability Analysis
    cap_res = caps.analyze_workspace_capabilities(workspace_path)

    # 3. Evidence Planning
    plan = planner.create_evidence_plan(task_class, user_prompt)

    # 4. Symbol Retrieval
    t_ret = time.time()
    retrieved_units = retriever.retrieve_evidence(workspace_path, plan)
    t_ret_ms = round((time.time() - t_ret) * 1000, 2)

    # 5. Relevance Ranking
    t_rank = time.time()
    ranked_units = ranker.rank_evidence_units(retrieved_units, plan)
    t_rank_ms = round((time.time() - t_rank) * 1000, 2)

    # 6. Budget Allocation
    t_bud = time.time()
    budget_res = budget.allocate_budget(ranked_units, token_budget)
    selected_units = budget_res["selected_units"]
    t_bud_ms = round((time.time() - t_bud) * 1000, 2)

    # 7. 3-Level Evidence Assembly
    t_asm = time.time()
    assembly_res = assembler.assemble_evidence(workspace_path, selected_units, user_prompt, task_class)
    selected_payload = assembly_res["payload"]
    t_asm_ms = round((time.time() - t_asm) * 1000, 2)

    # 8. Coverage & Fidelity Evaluation
    t_cov = time.time()
    cov_res = coverage.evaluate_coverage(plan, selected_units)
    t_cov_ms = round((time.time() - t_cov) * 1000, 2)

    # 9. Overhead Governor & Net Economics Gate
    raw_text = ""
    for unit in retrieved_units:
        abs_p = unit.get("file")
        if abs_p and os.path.exists(abs_p):
            try:
                with open(abs_p, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text += f.read() + "\n"
            except Exception:
                pass
    if not raw_text:
        raw_text = selected_payload

    banner = f"// --- [TokenSaver Auto Engine v5.0 - Active] ---\n// Task: {task_class} ({confidence}) | Coverage: {cov_res['coverage_score']} (Threshold: {cov_res['threshold']})"
    econ_res = overhead.compute_net_economics(raw_text, selected_payload, banner)

    total_local_ms = round((time.time() - t_start) * 1000, 2)

    metric_record = {
        "engine": "v5",
        "task": task_class,
        "confidence": confidence,
        "raw_estimated_tokens": econ_res["raw_context_tokens"],
        "selected_estimated_tokens": econ_res["selected_context_tokens"],
        "gross_saved": econ_res["gross_saved_tokens"],
        "overhead_tokens": econ_res["tokensaver_overhead_tokens"],
        "net_saved": econ_res["net_saved_tokens"],
        "net_saved_percent": econ_res["net_saved_percent"],
        "coverage": cov_res["coverage_score"],
        "coverage_passed": cov_res["passed"],
        "fidelity": "VERIFIED" if cov_res["passed"] else "FALLBACK",
        "fallback": not (cov_res["passed"] and econ_res["net_positive"]),
        "retrieval_latency_ms": t_ret_ms,
        "ranking_latency_ms": t_rank_ms,
        "assembly_latency_ms": t_asm_ms,
        "total_local_latency_ms": total_local_ms,
        "units_emitted": len(selected_units)
    }
    metrics.record_v5_run(metric_record)

    if not cov_res["passed"] or not econ_res["net_positive"]:
        return {
            "engine": "v5",
            "fallback": True,
            "reason": "Coverage threshold or Net savings non-positive",
            "task_class": task_class,
            "confidence": confidence,
            "raw_context_tokens": econ_res["raw_context_tokens"],
            "selected_context_tokens": econ_res["raw_context_tokens"],
            "net_saved_tokens": 0,
            "net_saved_percent": 0.0,
            "payload": raw_text
        }

    return {
        "engine": "v5",
        "fallback": False,
        "task_class": task_class,
        "confidence": confidence,
        "raw_context_tokens": econ_res["raw_context_tokens"],
        "selected_context_tokens": econ_res["selected_context_tokens"],
        "gross_saved_tokens": econ_res["gross_saved_tokens"],
        "overhead_tokens": econ_res["tokensaver_overhead_tokens"],
        "net_saved_tokens": econ_res["net_saved_tokens"],
        "net_saved_percent": econ_res["net_saved_percent"],
        "coverage_score": cov_res["coverage_score"],
        "banner": banner,
        "payload": banner + "\n" + selected_payload
    }

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Fix run_index in tokensaver_v5_symbol_index.py"
    workspace = sys.argv[2] if len(sys.argv) > 2 else "C:\\tools"
    res = run_v5_pipeline(prompt, workspace)
    print(json.dumps(res, indent=2))
