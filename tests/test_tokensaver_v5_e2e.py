import os
import sys
import shutil
import tempfile
import time
import json
import unittest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, 'src', 'tokensaver_v5'))
sys.path.insert(0, os.path.join(repo_root, 'src', 'utilities'))
sys.path.insert(0, os.path.join(repo_root, 'src'))
sys.path.append(r'C:\tools')
import tokensaver_v5_engine as engine

class TestTokenSaverV5E2E(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ts_v5_e2e_")
        self.workspace = self.test_dir

        # Create multi-file project with sufficient size
        os.makedirs(os.path.join(self.workspace, "src"), exist_ok=True)
        
        with open(os.path.join(self.workspace, "src", "calculator.py"), "w", encoding="utf-8") as f:
            f.write("class Calculator:\n" + "".join([f"    def add_{i}(self, a, b):\n        return a + b\n" for i in range(100)]))

        with open(os.path.join(self.workspace, "src", "app.py"), "w", encoding="utf-8") as f:
            f.write("from src.calculator import Calculator\n" + "".join([f"def run_app_{i}():\n    calc = Calculator()\n" for i in range(100)]))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_pipeline_and_local_isolation(self):
        prompt = "Fix add_0 method in src/calculator.py in this project"
        res = engine.run_v5_pipeline(prompt, self.workspace)

        self.assertEqual(res["engine"], "v5")
        self.assertFalse(res.get("skipped", False))
        self.assertFalse(res.get("fallback", False))
        
        payload = res.get("payload", "")
        self.assertIn("TOKEN SAVER V5 SELECTED EVIDENCE", payload)
        
        # Local isolation assertion
        self.assertNotIn("CREATE TABLE", payload)
        self.assertNotIn("symbol_edges", payload)
        self.assertNotIn("SELECT * FROM", payload)
        
        # Database location assertion
        db_path = os.path.join(self.workspace, ".tokensaver", "index.db")
        self.assertTrue(os.path.exists(db_path))

if __name__ == "__main__":
    unittest.main()
