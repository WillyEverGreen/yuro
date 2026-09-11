import os
import sys
import time
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UTILITIES_DIR = os.path.join(BASE_DIR, "utilities")
if UTILITIES_DIR not in sys.path:
    sys.path.insert(0, UTILITIES_DIR)
if r'C:\tools' not in sys.path:
    sys.path.append(r'C:\tools')

from tokensaver.core.tokenizer import get_default_token_counter, TokenCounter
from tokensaver.core.economics import compute_net_economics, EconomicsGate
from tokensaver.core.budget import allocate_budget
from tokensaver.retrieval.ranker import rank_evidence_units
from tokensaver.evidence.assembler import assemble_evidence

from utilities import task_classifier
import tokensaver_v5.tokensaver_v5_capabilities as caps
import tokensaver_v5.tokensaver_v5_evidence_planner as planner
import tokensaver_v5.tokensaver_v5_retriever as retriever
import tokensaver_v5.tokensaver_v5_coverage as coverage
import tokensaver_v5.tokensaver_v5_metrics as metrics

def run_v6_pipeline(
    user_prompt: str,
    workspace_path: str,
    token_budget: int = 4000,
    caveman_active: bool = False,
    tokenizer_name: str = "cl100k_base"
) -> Dict[str, Any]:
    t_start = time.time()
    workspace_path = os.path.abspath(workspace_path)
    counter = get_default_token_counter(tokenizer_name)

    # 1. Classification & Admission Gate
    task_res = task_classifier.evaluate_gate(user_prompt)
    action = task_res.get("action", "INVOKE")
    task_class = task_res.get("mode", "targeted")
    confidence = task_res.get("confidence", "MEDIUM")
    reason = task_res.get("reason", "General task admitted directly")

    if action == "SKIP":
        return {
            "version": "6.0",
            "skipped": True,
            "reason": reason,
            "task": task_class,
            "task_class": task_class,
            "confidence": confidence,
            "raw_context_tokens": 0,
            "selected_context_tokens": 0,
            "net_saved_tokens": 0,
            "net_saved_percent": 0.0,
            "payload": "",
            "tokenizer_backend": counter.backend,
            "token_count_mode": counter.token_count_mode,
            "raw_tokens": 0,
            "selected_tokens": 0,
            "gross_savings": 0,
            "net_savings": 0,
            "caveman_enabled": False,
            "fidelity": "VERIFIED"
        }

    # 2. Capability Analysis
    cap_res = caps.analyze_workspace_capabilities(workspace_path)

    # 3. Evidence Planning
    plan = planner.create_evidence_plan(task_class, user_prompt)

    # 4. Symbol Retrieval
    t_ret = time.time()
    retrieved_units = retriever.retrieve_evidence(workspace_path, plan)
    t_ret_ms = round((time.time() - t_ret) * 1000, 2)

    # 5. Hybrid BM25 + Graph Relevance Ranking
    t_rank = time.time()
    ranked_units = rank_evidence_units(retrieved_units, plan)
    t_rank_ms = round((time.time() - t_rank) * 1000, 2)

    # 6. Budget Allocation via TokenCounter
    t_bud = time.time()
    budget_res = allocate_budget(ranked_units, token_budget, counter)
    selected_units = budget_res["selected_units"]
    t_bud_ms = round((time.time() - t_bud) * 1000, 2)

    # 7. Evidence Assembly with AST-Safe Code Compression
    t_asm = time.time()
    assembly_res = assemble_evidence(workspace_path, selected_units, user_prompt, task_class, enable_compression=True)
    selected_payload = assembly_res["payload"]
    t_asm_ms = round((time.time() - t_asm) * 1000, 2)

    # 8. Coverage Evaluation
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
    if not raw_text and os.path.exists(workspace_path):
        if os.path.isfile(workspace_path):
            try:
                with open(workspace_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()
            except Exception:
                pass
    if not raw_text:
        raw_text = selected_payload

    banner = (
        f"// --- [TokenSaver Auto Engine v6.0 - Active] ---\n"
        f"// Task: {task_class} ({confidence}) | Coverage: {cov_res['coverage_score']} (Threshold: {cov_res['threshold']})\n"
        f"// Tokenizer: {counter.backend} ({counter.token_count_mode})"
    )

    econ_res = compute_net_economics(
        raw_text,
        selected_payload,
        overhead_text=banner,
        caveman_active=caveman_active,
        counter=counter
    )

    gate = EconomicsGate()
    gate_decision = gate.evaluate(econ_res, cov_res["passed"])

    total_local_ms = round((time.time() - t_start) * 1000, 2)

    metric_record = {
        "version": "6.0",
        "task": task_class,
        "confidence": confidence,
        "raw_estimated_tokens": econ_res["raw_context_tokens"],
        "selected_estimated_tokens": econ_res["selected_context_tokens"],
        "gross_saved": econ_res["input_gross_saved_tokens"],
        "overhead_tokens": econ_res["tokensaver_overhead_tokens"],
        "net_saved": econ_res["input_net_saved_tokens"],
        "net_saved_percent": econ_res["input_net_saved_percent"],
        "coverage": cov_res["coverage_score"],
        "coverage_passed": cov_res["passed"],
        "gate_accepted": gate_decision["accepted"],
        "gate_reason": gate_decision["reason"],
        "retrieval_latency_ms": t_ret_ms,
        "ranking_latency_ms": t_rank_ms,
        "assembly_latency_ms": t_asm_ms,
        "total_local_latency_ms": total_local_ms,
        "units_emitted": len(selected_units),
        "tokenizer_backend": counter.backend,
        "token_count_mode": counter.token_count_mode
    }
    metrics.record_v5_run(metric_record)

    if not gate_decision["accepted"]:
        return {
            "version": "6.0",
            "fallback": True,
            "reason": gate_decision["reason"],
            "task": task_class,
            "task_class": task_class,
            "confidence": confidence,
            "raw_context_tokens": econ_res["raw_context_tokens"],
            "selected_context_tokens": econ_res["raw_context_tokens"],
            "net_saved_tokens": 0,
            "net_saved_percent": 0.0,
            "payload": raw_text,
            "tokenizer_backend": counter.backend,
            "token_count_mode": counter.token_count_mode,
            "raw_tokens": econ_res["raw_context_tokens"],
            "selected_tokens": econ_res["raw_context_tokens"],
            "gross_savings": 0,
            "net_savings": 0,
            "result": "NET_ZERO",
            "caveman_enabled": caveman_active,
            "fidelity": "FALLBACK"
        }

    return {
        "version": "6.0",
        "fallback": False,
        "task": task_class,
        "task_class": task_class,
        "confidence": confidence,
        "raw_context_tokens": econ_res["raw_context_tokens"],
        "selected_context_tokens": econ_res["selected_context_tokens"],
        "gross_saved_tokens": econ_res["input_gross_saved_tokens"],
        "overhead_tokens": econ_res["tokensaver_overhead_tokens"],
        "net_saved_tokens": econ_res["input_net_saved_tokens"],
        "net_saved_percent": econ_res["input_net_saved_percent"],
        "coverage_score": cov_res["coverage_score"],
        "banner": banner,
        "payload": banner + "\n" + selected_payload,
        "tokenizer_backend": counter.backend,
        "token_count_mode": counter.token_count_mode,
        "output_metrics": econ_res["output_metrics"],
        "raw_tokens": econ_res["raw_context_tokens"],
        "selected_tokens": econ_res["selected_context_tokens"],
        "gross_savings": econ_res["input_gross_saved_tokens"],
        "net_savings": econ_res["input_net_saved_tokens"],
        "result": "NET_POSITIVE",
        "caveman_enabled": caveman_active,
        "fidelity": "VERIFIED"
    }
