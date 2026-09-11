import unittest
from tokensaver.core.budget import allocate_budget
from tokensaver.core.economics import compute_net_economics
from tokensaver.evidence.compressor import safe_compress_code_body, get_executable_ast_signature

class TestPropertyInvariants(unittest.TestCase):
    def test_invariant_budget_ceiling(self):
        units = [
            {"symbol_name": f"s_{i}", "signature": f"def s_{i}(): pass", "level": 2, "start_line": 1, "end_line": 50, "unit_type": "TARGET_SYMBOL" if i == 0 else "CALLEE"}
            for i in range(20)
        ]
        for budget in [100, 300, 500, 1000, 4000]:
            res = allocate_budget(units, token_budget=budget)
            self.assertLessEqual(res["used_tokens"], budget)

    def test_invariant_net_economics_math(self):
        raw = "def foo(): pass\n" * 500
        selected = "def foo(): pass\n" * 50
        overhead = "// Overhead header\n"
        econ = compute_net_economics(raw, selected, overhead)
        expected_gross = econ["raw_context_tokens"] - econ["selected_context_tokens"]
        expected_net = expected_gross - econ["tokensaver_overhead_tokens"]
        self.assertEqual(econ["input_gross_saved_tokens"], max(0, expected_gross))
        self.assertEqual(econ["input_net_saved_tokens"], max(0, expected_net))

    def test_invariant_ast_equivalence(self):
        code = "def process(item):\n    # Filter null\n    if item is None:\n        return None\n    return item.value\n"
        sig_before = get_executable_ast_signature(code)
        compressed, meta = safe_compress_code_body(code, language="python")
        sig_after = get_executable_ast_signature(compressed)
        self.assertEqual(sig_before, sig_after)

if __name__ == "__main__":
    unittest.main()
