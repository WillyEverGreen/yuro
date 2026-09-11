import unittest
from tokensaver.core.engine import run_v6_pipeline

class TestRegressionKnownBugs(unittest.TestCase):
    def test_bug_001_symbol_index_lookup(self):
        res = run_v6_pipeline("Fix run_index in tokensaver_v5_symbol_index.py", ".")
        self.assertFalse(res.get("skipped", False))
        self.assertFalse(res.get("fallback", False))
        self.assertIn("run_index", res.get("payload", ""))

    def test_bug_002_budget_allocator_demotion(self):
        res = run_v6_pipeline("Refactor budget allocation in tokensaver_v5_budget.py", ".", token_budget=1000)
        self.assertLessEqual(res.get("selected_context_tokens", 0), 1000)

if __name__ == "__main__":
    unittest.main()
