import sys
from typing import Dict, Any, Optional
from tokensaver.core.tokenizer import get_default_token_counter, TokenCounter

def compute_net_economics(
    raw_text: str,
    selected_payload: str,
    overhead_text: str = "",
    caveman_active: bool = False,
    output_baseline_text: str = "",
    output_caveman_text: str = "",
    counter: Optional[TokenCounter] = None
) -> Dict[str, Any]:
    if counter is None:
        counter = get_default_token_counter()

    raw_tokens = counter.count(raw_text)
    selected_tokens = counter.count(selected_payload)
    overhead_tokens = counter.count(overhead_text)

    input_gross_saved = max(0, raw_tokens - selected_tokens)
    input_net_saved = input_gross_saved - overhead_tokens
    input_net_percent = round((input_net_saved / raw_tokens) * 100.0, 2) if raw_tokens > 0 else 0.0

    input_net_positive = input_net_saved > 0

    # Output Caveman economics (tracked separately)
    output_baseline_tokens = counter.count(output_baseline_text) if output_baseline_text else 0
    output_caveman_tokens = counter.count(output_caveman_text) if output_caveman_text else 0
    output_saved = max(0, output_baseline_tokens - output_caveman_tokens) if caveman_active else 0

    total_net_saved = max(0, input_net_saved) + output_saved

    return {
        "tokenizer_backend": counter.backend,
        "token_count_mode": counter.token_count_mode,
        "raw_context_tokens": raw_tokens,
        "selected_context_tokens": selected_tokens,
        "tokensaver_overhead_tokens": overhead_tokens,
        "input_gross_saved_tokens": input_gross_saved,
        "input_net_saved_tokens": max(0, input_net_saved),
        "input_net_saved_percent": max(0.0, input_net_percent),
        "input_net_positive": input_net_positive,
        "output_metrics": {
            "caveman_enabled": caveman_active,
            "output_baseline_tokens": output_baseline_tokens,
            "output_caveman_tokens": output_caveman_tokens,
            "output_saved_tokens": output_saved
        },
        "total_net_saved_tokens": total_net_saved
    }

class EconomicsGate:
    def __init__(self, min_net_tokens: int = 1, min_savings_percent: float = 0.0):
        self.min_net_tokens = min_net_tokens
        self.min_savings_percent = min_savings_percent

    def evaluate(self, econ_res: Dict[str, Any], coverage_passed: bool) -> Dict[str, Any]:
        input_net = econ_res.get("input_net_saved_tokens", 0)
        input_pct = econ_res.get("input_net_saved_percent", 0.0)
        net_pos = econ_res.get("input_net_positive", False)

        if not coverage_passed:
            return {"accepted": False, "reason": "Coverage threshold failed"}

        if not net_pos or input_net < self.min_net_tokens or input_pct < self.min_savings_percent:
            return {"accepted": False, "reason": f"Input net savings non-positive ({input_net} tokens, {input_pct}%)"}

        return {"accepted": True, "reason": "Positive net token savings verified"}
