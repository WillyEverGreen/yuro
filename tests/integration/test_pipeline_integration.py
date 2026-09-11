import unittest
import os
from tokensaver.core.engine import run_v6_pipeline

class TestPipelineIntegration(unittest.TestCase):
    def test_full_pipeline_invocation(self):
        res = run_v6_pipeline("Fix run_index in tokensaver_v5_symbol_index.py", ".")
        self.assertEqual(res.get("version"), "6.0")
        self.assertIn("raw_context_tokens", res)
        self.assertIn("selected_context_tokens", res)
        self.assertIn("net_saved_tokens", res)
        self.assertFalse(res.get("skipped", False))
        self.assertGreater(res.get("net_saved_tokens", 0), 0)

    def test_conceptual_skip_invocation(self):
        res = run_v6_pipeline("What is an API token?", ".")
        self.assertTrue(res.get("skipped", False))
        self.assertEqual(res.get("net_saved_tokens"), 0)

if __name__ == "__main__":
    unittest.main()
