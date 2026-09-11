import unittest
from tokensaver.retrieval.ranker import rank_evidence_units

class TestRanker(unittest.TestCase):
    def test_ranking_signals_and_ordering(self):
        units = [
            {"symbol_name": "helper_func", "signature": "def helper_func():", "relative_path": "utils.py", "unit_type": "CALLEE", "level": 1},
            {"symbol_name": "target_func", "signature": "def target_func():", "relative_path": "main.py", "unit_type": "TARGET_SYMBOL", "level": 2}
        ]
        plan = {"extracted_targets": ["target_func"], "user_prompt": "Fix target_func in main.py"}
        ranked = rank_evidence_units(units, plan)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["symbol_name"], "target_func")
        self.assertIn("signals", ranked[0])
        self.assertEqual(ranked[0]["signals"]["target_match"], 1.0)

if __name__ == "__main__":
    unittest.main()
