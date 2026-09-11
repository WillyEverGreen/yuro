import os
import sys
from typing import Dict, Any, Tuple
from tokensaver.core.tokenizer import get_default_token_counter

CAVEMAN_DIRECTIVE = (
    "// [TokenSaver Output Protocol: Caveman Active]\n"
    "// - Direct answers. No greetings, prompt restatements, or filler.\n"
    "// - Prefer code blocks and concise bullet lists over prose.\n"
    "// - Auto-expand ONLY for: security, destructive commands, breaking API changes, ambiguity, complex root causes, or explicit 'why' queries."
)

class CavemanGovernor:
    def __init__(self, mode: str = "adaptive"):
        self.mode = mode.lower()

    def should_enable(self, task_mode: str, confidence: str, prompt_text: str) -> Tuple[bool, str]:
        if self.mode == "normal":
            return False, "disabled by configuration mode='normal'"
        if self.mode == "caveman":
            return True, "forced enabled by configuration mode='caveman'"

        # Adaptive mode logic
        prompt_lower = prompt_text.lower()
        if task_mode in ["security"]:
            return False, "security mode requires full verbose precision"
        if task_mode in ["implement"] or "implement" in prompt_lower:
            return False, "implementation task defaults to full output"
        if task_mode in ["plan", "architecture", "explain"] or any(k in prompt_lower for k in ["explain", "architecture"]):
            return True, "explanation query benefits from high-density response protocol"
        if task_mode in ["debug", "refactor"] or any(k in prompt_lower for k in ["fix", "traceback", "refactor"]):
            if confidence == "HIGH":
                return True, "high-confidence task benefits from concise response protocol"
            return False, "low-confidence task defaults to full output"

        return False, "default conservative policy"

    def get_directive(self) -> str:
        return CAVEMAN_DIRECTIVE

    def measure_output_savings(self, baseline_output: str, actual_output: str) -> Dict[str, Any]:
        counter = get_default_token_counter()
        base_tok = counter.count(baseline_output)
        act_tok = counter.count(actual_output)
        saved = max(0, base_tok - act_tok)
        return {
            "baseline_output_tokens": base_tok,
            "actual_output_tokens": act_tok,
            "output_tokens_saved": saved,
            "savings_percent": round((saved / base_tok) * 100.0, 2) if base_tok > 0 else 0.0
        }
