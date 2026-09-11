import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def evaluate_coverage(evidence_plan, selected_units):
    required = evidence_plan.get("required_evidence", [])
    threshold = evidence_plan.get("coverage_threshold", 0.90)
    
    if not required or threshold <= 0.0:
        return {
            "passed": True,
            "coverage_score": 1.0,
            "threshold": threshold,
            "missing_evidence": []
        }

    extracted_targets = evidence_plan.get("extracted_targets", [])
    retrieved_targets = {u.get("symbol_name") for u in selected_units if u.get("symbol_name")}

    covered_items = 0
    missing_items = []

    for req in required:
        if req in ["target_symbol", "target_implementation"]:
            if any(t in retrieved_targets for t in extracted_targets) or not extracted_targets:
                covered_items += 1
            else:
                missing_items.append(req)
        elif req in ["callers", "callees", "references", "dependencies"]:
            unit_types = {u.get("unit_type") for u in selected_units}
            if req.upper().rstrip('S') in unit_types or req.upper() in unit_types or len(selected_units) > 0:
                covered_items += 1
            else:
                missing_items.append(req)
        else:
            if len(selected_units) > 0:
                covered_items += 1
            else:
                missing_items.append(req)

    coverage_score = round(covered_items / len(required), 3) if len(required) > 0 else 1.0
    passed = coverage_score >= threshold

    return {
        "passed": passed,
        "coverage_score": coverage_score,
        "threshold": threshold,
        "missing_evidence": missing_items
    }

if __name__ == "__main__":
    plan = {
        "required_evidence": ["target_symbol", "callers", "callees"],
        "coverage_threshold": 0.95,
        "extracted_targets": ["run_index"]
    }
    units = [
        {"symbol_name": "run_index", "unit_type": "TARGET_SYMBOL"},
        {"symbol_name": "init_db", "unit_type": "CALLEE"}
    ]
    print(json.dumps(evaluate_coverage(plan, units), indent=2))
