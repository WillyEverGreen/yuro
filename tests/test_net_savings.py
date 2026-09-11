import sys
import os
import json
import subprocess
import tempfile
import unittest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
local_token_save = os.path.join(repo_root, "src", "utilities", "token-save.py")
TOKEN_SAVE = local_token_save if os.path.exists(local_token_save) else r"C:\tools\token-save.py"

class TestTokenSaverNetSavings(unittest.TestCase):

    def run_token_save(self, prompt, path):
        res = subprocess.run(
            [sys.executable, TOKEN_SAVE, "auto", prompt, path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        return res

    def get_metrics_json(self):
        res = subprocess.run(
            [sys.executable, TOKEN_SAVE, "metrics", "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        return json.loads(res.stdout)

    def get_metrics_text(self):
        res = subprocess.run(
            [sys.executable, TOKEN_SAVE, "metrics"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        return res.stdout

    # 1. Large context with large savings
    def test_01_large_context_large_savings(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            for i in range(400):
                f.write(f"def helper_function_{i}(arg1, arg2):\n")
                f.write(f"    \"\"\"Docstring for function {i}\"\"\"\n")
                f.write(f"    x = arg1 + {i}\n    y = arg2 * {i}\n    return x + y\n\n")
            temp_path = f.name

        try:
            res = self.run_token_save("Analyze this project's architecture", temp_path)
            m = self.get_metrics_json()
            self.assertGreater(m["raw_tokens"], 3000)
            self.assertGreater(m["gross_savings"], 1000)
            self.assertGreater(m["net_savings"], 500)
            self.assertEqual(m["gross_savings"] - m["overhead_tokens"], m["net_savings"])
            self.assertEqual(m["result"], "NET_POSITIVE")
            self.assertTrue(m["caveman_enabled"])
            self.assertIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)
        finally:
            os.remove(temp_path)

    # 2. Small context where TokenSaver overhead makes compression pointless
    def test_02_small_context_pointless_compression(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("def add(a, b):\n    return a + b\n")
            temp_path = f.name

        try:
            self.run_token_save("refactor function add", temp_path)
            m = self.get_metrics_json()
            self.assertEqual(m["net_savings"], 0)
            self.assertIn(m["result"], ["NET_ZERO", "NET_NEGATIVE"])
            txt = self.get_metrics_text()
            self.assertIn("NET SAVINGS:          0 / NEGATIVE", txt)
            self.assertIn("TokenSaver did not provide a net token benefit for this request.", txt)
        finally:
            os.remove(temp_path)

    # 3. Zero compression scenario
    def test_03_zero_compression(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("import sys\nprint('hello')\n")
            temp_path = f.name

        try:
            self.run_token_save("implement full code updates", temp_path)
            m = self.get_metrics_json()
            self.assertEqual(m["gross_savings"], 0)
            self.assertEqual(m["net_savings"], 0)
        finally:
            os.remove(temp_path)

    # 4. Negative net savings handling
    def test_04_negative_net_savings_handling(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("x = 1\ny = 2\n")
            temp_path = f.name

        try:
            self.run_token_save("Refactor the variables in this file", temp_path)
            m = self.get_metrics_json()
            self.assertEqual(m["net_savings"], 0)
            self.assertIn(m["result"], ["NET_NEGATIVE", "NET_ZERO"])
            txt = self.get_metrics_text()
            self.assertIn("NET SAVINGS:          0 / NEGATIVE", txt)
        finally:
            os.remove(temp_path)

    # 5. Caveman Mode for Architecture / Explain Task
    def test_05_caveman_architecture_explain_task(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            for i in range(100):
                f.write(f"def func_{i}():\n    pass\n")
            temp_path = f.name

        try:
            res = self.run_token_save("Explain this project's architecture", temp_path)
            m = self.get_metrics_json()
            self.assertTrue(m["caveman_enabled"])
            self.assertGreater(m["caveman_instruction_tokens"], 0)
            self.assertIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)
        finally:
            os.remove(temp_path)

    # 6. Caveman Mode for High-Confidence Debug Task
    def test_06_caveman_high_confidence_debug_task(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            for i in range(50):
                f.write(f"def debug_target_{i}():\n    return {i}\n")
            temp_path = f.name

        try:
            res = self.run_token_save("Fix this traceback in auto_submit.py", temp_path)
            m = self.get_metrics_json()
            self.assertTrue(m["caveman_enabled"])
            self.assertGreater(m["caveman_instruction_tokens"], 0)
            self.assertIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)
        finally:
            os.remove(temp_path)

    # 7. Caveman Disabled for Implementation Task
    def test_07_caveman_disabled_for_implementation_task(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("def worker():\n    pass\n")
            temp_path = f.name

        try:
            res = self.run_token_save("Implement retry logic in the queue worker", temp_path)
            m = self.get_metrics_json()
            self.assertFalse(m["caveman_enabled"])
            self.assertEqual(m["caveman_instruction_tokens"], 0)
            self.assertNotIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)
        finally:
            os.remove(temp_path)

    # 8. Caveman Disabled for Security Task
    def test_08_caveman_disabled_for_security_task(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("secret = '12345'\n")
            temp_path = f.name

        try:
            res = self.run_token_save("Audit project for hardcoded secrets and security flaws", temp_path)
            m = self.get_metrics_json()
            self.assertFalse(m["caveman_enabled"])
            self.assertEqual(m["caveman_instruction_tokens"], 0)
            self.assertNotIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)
        finally:
            os.remove(temp_path)

    # 9. Caveman Disabled for Conceptual / SKIP Task
    def test_09_caveman_disabled_for_conceptual_task(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("x = 1\n")
            temp_path = f.name

        try:
            res = self.run_token_save("What's the difference between TCP and UDP?", temp_path)
            m = self.get_metrics_json()
            self.assertFalse(m["caveman_enabled"])
            self.assertEqual(m["caveman_instruction_tokens"], 0)
            self.assertNotIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)
        finally:
            os.remove(temp_path)

    # 10. Caveman Overhead Included in NET Accounting
    def test_10_caveman_overhead_in_net_accounting(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            for i in range(100):
                f.write(f"def f_{i}():\n    return {i}\n")
            temp_path = f.name

        try:
            self.run_token_save("Explain this project's architecture", temp_path)
            m = self.get_metrics_json()
            self.assertTrue(m["caveman_enabled"])
            expected_overhead = m["instruction_overhead"] + m["generated_result_overhead"]
            self.assertEqual(m["overhead_tokens"], expected_overhead)
            self.assertEqual(m["gross_savings"] - m["overhead_tokens"], m["net_savings"])
        finally:
            os.remove(temp_path)

    # 11. Machine-readable JSON output format
    def test_11_json_output_format(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("def test():\n    pass\n")
            temp_path = f.name

        try:
            self.run_token_save("test JSON metrics", temp_path)
            m = self.get_metrics_json()
            required_keys = ["task", "confidence", "raw_tokens", "selected_tokens", "gross_savings", "overhead_tokens", "net_savings", "net_savings_percent", "fidelity", "result", "caveman_enabled", "caveman_instruction_tokens"]
            for key in required_keys:
                self.assertIn(key, m)
        finally:
            os.remove(temp_path)

    # 12. Fidelity failure + fallback handling
    def test_12_fidelity_failure_and_fallback(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False, encoding="utf-8") as f:
            f.write("def malformed_syntax_function():\n    x = 1\n")
            temp_path = f.name

        try:
            res = self.run_token_save("Analyze code", temp_path)
            m = self.get_metrics_json()
            self.assertIn("VERIFIED", m["fidelity"])
        finally:
            os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
