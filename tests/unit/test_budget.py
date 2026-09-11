import unittest
from tokensaver.core.budget import allocate_budget, estimate_unit_tokens

class TestBudget(unittest.TestCase):
    def test_estimate_unit_tokens(self):
        unit = {
            "symbol_name": "test_func",
            "symbol_kind": "function",
            "start_line": 1,
            "end_line": 10,
            "signature": "def test_func():",
            "level": 2
        }
        tokens = estimate_unit_tokens(unit)
        self.assertGreater(tokens, 0)

    def test_budget_never_exceeded(self):
        units = [
            {"symbol_name": f"func_{i}", "signature": f"def func_{i}(): pass", "level": 2, "start_line": 1, "end_line": 20, "unit_type": "TARGET_SYMBOL" if i == 0 else "CALLEE"}
            for i in range(10)
        ]
        budget_limit = 200
        res = allocate_budget(units, token_budget=budget_limit)
        self.assertLessEqual(res["used_tokens"], budget_limit)

if __name__ == "__main__":
    unittest.main()
