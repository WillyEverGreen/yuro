import unittest
import tempfile
import os
from tokensaver.core.engine import run_v6_pipeline
from tokensaver.core.tokenizer import TokenCounter
from tokensaver.evidence.compressor import safe_compress_code_body

class TestEdgeCases(unittest.TestCase):
    def test_empty_workspace(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            res = run_v6_pipeline("Fix bug in main.py", empty_dir)
            self.assertEqual(res.get("version"), "6.0")
            self.assertIn("payload", res)

    def test_huge_budget(self):
        res = run_v6_pipeline("Fix run_index", ".", token_budget=100000)
        self.assertLessEqual(res.get("selected_context_tokens", 0), 100000)

    def test_zero_budget(self):
        res = run_v6_pipeline("Fix run_index", ".", token_budget=0)
        self.assertLessEqual(res.get("selected_context_tokens", 0), 50)

    def test_unicode_and_tricky_literals(self):
        counter = TokenCounter()
        unicode_str = "def 😀_func():\n    msg = 'Hello 世界 🌍'\n    return msg\n"
        count = counter.count(unicode_str)
        self.assertGreater(count, 0)
        compressed, meta = safe_compress_code_body(unicode_str, language="python")
        self.assertIn("Hello 世界 🌍", compressed)

if __name__ == "__main__":
    unittest.main()
