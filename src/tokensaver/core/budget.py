import sys
from typing import List, Dict, Any, Optional
from tokensaver.core.tokenizer import get_default_token_counter, TokenCounter

def estimate_unit_tokens(unit: Dict[str, Any], counter: Optional[TokenCounter] = None) -> int:
    if counter is None:
        counter = get_default_token_counter()

    level = unit.get("level", 1)
    sig = unit.get("signature", "")
    content = unit.get("content", "")

    if content:
        return counter.count(content)

    if level == 0:
        return max(5, counter.count(f"• [{unit.get('symbol_kind', 'symbol')}] {unit.get('symbol_name', '')}"))
    elif level == 1:
        return max(15, counter.count(sig) + 10)
    else:
        lines_count = max(1, (unit.get("end_line", 1) - unit.get("start_line", 1)) + 1)
        return max(25, counter.count(sig) + int(lines_count * 4.5))

def allocate_budget(
    ranked_units: List[Dict[str, Any]],
    token_budget: int = 4000,
    counter: Optional[TokenCounter] = None
) -> Dict[str, Any]:
    if counter is None:
        counter = get_default_token_counter()

    selected_units = []
    accumulated_tokens = 0

    target_units = [u for u in ranked_units if u.get("unit_type") == "TARGET_SYMBOL"]
    other_units = [u for u in ranked_units if u not in target_units]

    # Target symbols get first budget priority at Level 2
    for unit in target_units:
        est_tokens = estimate_unit_tokens(unit, counter)
        if accumulated_tokens + est_tokens <= token_budget:
            unit_copy = unit.copy()
            unit_copy["allocated_tokens"] = est_tokens
            selected_units.append(unit_copy)
            accumulated_tokens += est_tokens
        else:
            # Demote Target symbol to Level 1 signature if full body overflows budget
            demoted_copy = unit.copy()
            demoted_copy["level"] = 1
            demoted_est = estimate_unit_tokens(demoted_copy, counter)
            if accumulated_tokens + demoted_est <= token_budget:
                demoted_copy["allocated_tokens"] = demoted_est
                selected_units.append(demoted_copy)
                accumulated_tokens += demoted_est

    # Secondary symbols fill remaining budget
    for unit in other_units:
        est_tokens = estimate_unit_tokens(unit, counter)
        if accumulated_tokens + est_tokens <= token_budget:
            unit_copy = unit.copy()
            unit_copy["allocated_tokens"] = est_tokens
            selected_units.append(unit_copy)
            accumulated_tokens += est_tokens
        else:
            if unit.get("level", 1) == 2:
                demoted_copy = unit.copy()
                demoted_copy["level"] = 1
                demoted_est = estimate_unit_tokens(demoted_copy, counter)
                if accumulated_tokens + demoted_est <= token_budget:
                    demoted_copy["allocated_tokens"] = demoted_est
                    selected_units.append(demoted_copy)
                    accumulated_tokens += demoted_est
            elif unit.get("level", 1) == 1:
                demoted_copy = unit.copy()
                demoted_copy["level"] = 0
                demoted_est = estimate_unit_tokens(demoted_copy, counter)
                if accumulated_tokens + demoted_est <= token_budget:
                    demoted_copy["allocated_tokens"] = demoted_est
                    selected_units.append(demoted_copy)
                    accumulated_tokens += demoted_est

    return {
        "budget": token_budget,
        "used_tokens": accumulated_tokens,
        "remaining_tokens": token_budget - accumulated_tokens,
        "selected_units": selected_units,
        "tokenizer_backend": counter.backend,
        "token_count_mode": counter.token_count_mode
    }
