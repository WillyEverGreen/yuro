import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def estimate_unit_tokens(unit):
    level = unit.get("level", 1)
    sig = unit.get("signature", "")
    start_line = unit.get("start_line", 1)
    end_line = unit.get("end_line", 1)
    
    if level == 0:
        return max(5, int(len(sig) / 3.8))
    elif level == 1:
        return max(15, int(len(sig) / 3.5) + 10)
    else:
        lines_count = max(1, (end_line - start_line) + 1)
        return max(25, int(lines_count * 4.5))

def allocate_budget(ranked_units, token_budget=4000):
    selected_units = []
    accumulated_tokens = 0
    
    # 1. Target symbols at Level 2 get priority allocation
    target_units = [u for u in ranked_units if u.get("unit_type") == "TARGET_SYMBOL"]
    other_units = [u for u in ranked_units if u not in target_units]

    for unit in target_units:
        est_tokens = estimate_unit_tokens(unit)
        if accumulated_tokens + est_tokens <= token_budget:
            unit_copy = unit.copy()
            unit_copy["allocated_tokens"] = est_tokens
            selected_units.append(unit_copy)
            accumulated_tokens += est_tokens
        else:
            unit_copy = unit.copy()
            unit_copy["allocated_tokens"] = est_tokens
            selected_units.append(unit_copy)
            accumulated_tokens += est_tokens

    # 2. Callers, Callees, and Overviews fill remaining budget
    for unit in other_units:
        est_tokens = estimate_unit_tokens(unit)
        if accumulated_tokens + est_tokens <= token_budget:
            unit_copy = unit.copy()
            unit_copy["allocated_tokens"] = est_tokens
            selected_units.append(unit_copy)
            accumulated_tokens += est_tokens
        else:
            if unit.get("level", 1) == 2:
                demoted_copy = unit.copy()
                demoted_copy["level"] = 1
                demoted_est = estimate_unit_tokens(demoted_copy)
                if accumulated_tokens + demoted_est <= token_budget:
                    demoted_copy["allocated_tokens"] = demoted_est
                    selected_units.append(demoted_copy)
                    accumulated_tokens += demoted_est

    return {
        "budget": token_budget,
        "used_tokens": accumulated_tokens,
        "remaining_tokens": token_budget - accumulated_tokens,
        "selected_units": selected_units
    }

if __name__ == "__main__":
    units = [
        {"symbol_name": "run_index", "signature": "def run_index():", "level": 2, "start_line": 1, "end_line": 100, "score": 35.0, "unit_type": "TARGET_SYMBOL"},
        {"symbol_name": "init_db", "signature": "def init_db():", "level": 1, "start_line": 1, "end_line": 30, "score": 20.0, "unit_type": "CALLEE"}
    ]
    print(json.dumps(allocate_budget(units, 2000), indent=2))
