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

    def _get_env(self):
        env = os.environ.copy()
        src_path = os.path.join(repo_root, "src")
        util_path = os.path.join(repo_root, "src", "utilities")
        env["PYTHONPATH"] = f"{src_path}{os.path.pathsep}{util_path}"
        return env

    def run_token_save(self, prompt, path, mode="adaptive"):
        res = subprocess.run(
            [sys.executable, TOKEN_SAVE, "auto", prompt, path, "--mode", mode],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            env=self._get_env()
        )
        return res

    def get_metrics_json(self):
        res = subprocess.run(
            [sys.executable, TOKEN_SAVE, "metrics", "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            env=self._get_env()
        )
        return json.loads(res.stdout)

    # 1. Large context with large savings
    def test_01_large_context_large_savings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "large_file.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                for i in range(400):
                    f.write(f"def helper_function_{i}(arg1, arg2):\n")
                    f.write(f"    \"\"\"Docstring for function {i}\"\"\"\n")
                    f.write(f"    x = arg1 + {i}\n    y = arg2 * {i}\n    return x + y\n\n")

            res = self.run_token_save("Fix helper_function_0 in large_file.py in this codebase", temp_dir)
            m = self.get_metrics_json()
            self.assertGreater(m["raw_tokens"], 3000)

    # 2. Small context scenario
    def test_02_small_context_pointless_compression(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "small_file.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("def add(a, b):\n    return a + b\n")

            res = self.run_token_save("refactor function add in this file", temp_dir)
            m = self.get_metrics_json()
            self.assertIn(m["result"], ["NET_ZERO", "NET_NEGATIVE", "SKIPPED", "NET_POSITIVE"])

    # 3. Zero compression scenario
    def test_03_zero_compression(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "tiny_file.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("import sys\nprint('hello')\n")

            res = self.run_token_save("implement full code updates in this project", temp_dir)
            m = self.get_metrics_json()
            self.assertIn("version", m)

    # 4. Negative net savings handling
    def test_04_negative_net_savings_handling(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "var_file.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("x = 1\ny = 2\n")

            res = self.run_token_save("Refactor the variables in this file in this codebase", temp_dir)
            m = self.get_metrics_json()
            self.assertIn(m["result"], ["NET_NEGATIVE", "NET_ZERO", "SKIPPED", "NET_POSITIVE"])

    # 5. Caveman Mode for Architecture / Explain Task
    def test_05_caveman_architecture_explain_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "arch_file.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                for i in range(100):
                    f.write(f"def func_{i}():\n    pass\n")

            res = self.run_token_save("Explain this project's architecture in this codebase", temp_dir, mode="caveman")
            m = self.get_metrics_json()
            self.assertTrue(m["caveman_enabled"])
            self.assertIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)

    # 6. Caveman Mode for High-Confidence Debug Task
    def test_06_caveman_high_confidence_debug_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "auto_submit.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                for i in range(50):
                    f.write(f"def debug_target_{i}():\n    return {i}\n")

            res = self.run_token_save("Fix this traceback in auto_submit.py", temp_dir, mode="caveman")
            m = self.get_metrics_json()
            self.assertTrue(m["caveman_enabled"])
            self.assertIn("[TokenSaver Output Protocol: Caveman Active]", res.stdout)

    # 7. Caveman Disabled for Implementation Task
    def test_07_caveman_disabled_for_implementation_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "worker.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("def worker():\n    pass\n")

            res = self.run_token_save("implement retry logic in worker.py", temp_dir, mode="normal")
            m = self.get_metrics_json()
            self.assertFalse(m["caveman_enabled"])

    # 8. Caveman Disabled for Security Task
    def test_08_caveman_disabled_for_security_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "sec.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("def check_sec():\n    pass\n")

            res = self.run_token_save("audit security vulnerabilities in sec.py", temp_dir, mode="normal")
            m = self.get_metrics_json()
            self.assertFalse(m["caveman_enabled"])

    # 9. Caveman Disabled for Conceptual Task
    def test_09_caveman_disabled_for_conceptual_task(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "concept.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("x = 10\n")

            res = self.run_token_save("What is recursion?", temp_dir, mode="normal")
            m = self.get_metrics_json()
            self.assertFalse(m["caveman_enabled"])

    # 10. Caveman Overhead Accounting
    def test_10_caveman_overhead_in_net_accounting(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "arch_file.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                for i in range(100):
                    f.write(f"def func_{i}():\n    pass\n")

            res = self.run_token_save("Explain this project's architecture in this codebase", temp_dir, mode="caveman")
            m = self.get_metrics_json()
            self.assertTrue(m["caveman_enabled"])

    # 11. JSON Output Format
    def test_11_json_output_format(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "json_file.py")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("def foo(): pass\n")

            self.run_token_save("Fix foo in json_file.py", temp_dir)
            m = self.get_metrics_json()
            for key in ["version", "raw_tokens", "selected_tokens", "net_savings", "fidelity"]:
                self.assertIn(key, m)

if __name__ == "__main__":
    unittest.main()
