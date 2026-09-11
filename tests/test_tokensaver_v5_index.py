import os
import sys
import shutil
import tempfile
import time
import json
import sqlite3
import unittest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(repo_root, 'src', 'tokensaver_v5'))
sys.path.insert(0, os.path.join(repo_root, 'src', 'utilities'))
sys.path.insert(0, os.path.join(repo_root, 'src'))
sys.path.append(r'C:\tools')
import tokensaver_v5_symbol_index as idx

class TestTokenSaverV5Index(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ts_v5_test_")
        self.workspace = self.test_dir
        
        # Create synthetic repo structure
        os.makedirs(os.path.join(self.workspace, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "ignored_dir"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "node_modules", "package"), exist_ok=True)
        
        # Create .gitignore
        with open(os.path.join(self.workspace, ".gitignore"), "w", encoding="utf-8") as f:
            f.write("ignored_dir/\n*.tmp\n")
            
        # Create Python file
        with open(os.path.join(self.workspace, "src", "math_utils.py"), "w", encoding="utf-8") as f:
            f.write("class Calculator:\n    def add(self, a, b):\n        return a + b\n\ndef multiply(x, y):\n    return x * y\n")
            
        # Create TS file
        with open(os.path.join(self.workspace, "src", "service.ts"), "w", encoding="utf-8") as f:
            f.write("export interface User {\n  id: number;\n  name: string;\n}\n\nexport class UserService {\n  getUser() {}\n}\n")
            
        # Create unsupported / raw file (e.g. .custom)
        with open(os.path.join(self.workspace, "src", "notes.custom"), "w", encoding="utf-8") as f:
            f.write("def custom_func(): pass\n")
            
        # Create file in ignored_dir
        with open(os.path.join(self.workspace, "ignored_dir", "secret.py"), "w", encoding="utf-8") as f:
            f.write("def secret(): pass\n")

        # Create file in node_modules
        with open(os.path.join(self.workspace, "node_modules", "package", "lib.js"), "w", encoding="utf-8") as f:
            f.write("function lib() {}\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_lifecycle_and_benchmarks(self):
        # 1. First index
        t0 = time.time()
        res1 = idx.run_index(self.workspace)
        t1_ms = int((time.time() - t0) * 1000)
        
        db_path = os.path.join(self.workspace, ".tokensaver", "index.db")
        self.assertTrue(os.path.exists(db_path), "Database should persist between runs")
        
        self.assertGreaterEqual(res1["files"], 3)
        self.assertGreaterEqual(res1["added"], 3)
        self.assertEqual(res1["reused"], 0)
        self.assertEqual(res1["changed"], 0)
        self.assertEqual(res1["deleted"], 0)
        
        # Verify symbol extraction
        sym_res = idx.run_symbols_query(self.workspace, "Calculator")
        calc_symbols = [s for s in sym_res["symbols"] if s["name"] == "Calculator"]
        self.assertEqual(len(calc_symbols), 1)
        self.assertEqual(calc_symbols[0]["kind"], "class")

        sym_res2 = idx.run_symbols_query(self.workspace, "multiply")
        self.assertEqual(len(sym_res2["symbols"]), 1)
        self.assertEqual(sym_res2["symbols"][0]["name"], "multiply")
        self.assertEqual(sym_res2["symbols"][0]["kind"], "function")

        sym_res3 = idx.run_symbols_query(self.workspace, "User")
        user_symbols = [s for s in sym_res3["symbols"] if s["name"] == "User"]
        self.assertEqual(len(user_symbols), 1)

        # Verify unsupported language fallback
        file_res = idx.run_file_inspect(self.workspace, os.path.join("src", "notes.custom"))
        self.assertEqual(file_res["parse_status"], "FALLBACK")

        # Verify gitignore / default ignore skipped secret.py and lib.js
        sym_secret = idx.run_symbols_query(self.workspace, "secret")
        self.assertEqual(len(sym_secret["symbols"]), 0)
        sym_lib = idx.run_symbols_query(self.workspace, "lib")
        self.assertEqual(len(sym_lib["symbols"]), 0)

        # 2. Second index (Unchanged)
        t0 = time.time()
        res2 = idx.run_index(self.workspace)
        t2_ms = int((time.time() - t0) * 1000)
        
        self.assertEqual(res2["reused"], res1["files"])
        self.assertEqual(res2["added"], 0)
        self.assertEqual(res2["changed"], 0)
        self.assertEqual(res2["deleted"], 0)

        # 3. Modify one file
        time.sleep(0.05) # ensure mtime change
        with open(os.path.join(self.workspace, "src", "math_utils.py"), "a", encoding="utf-8") as f:
            f.write("\ndef subtract(a, b):\n    return a - b\n")

        t0 = time.time()
        res3 = idx.run_index(self.workspace)
        t3_ms = int((time.time() - t0) * 1000)

        self.assertEqual(res3["changed"], 1)
        self.assertEqual(res3["reused"], res1["files"] - 1)
        self.assertEqual(res3["added"], 0)
        self.assertEqual(res3["deleted"], 0)

        sym_sub = idx.run_symbols_query(self.workspace, "subtract")
        self.assertEqual(len(sym_sub["symbols"]), 1)

        # 4. Delete one file
        os.remove(os.path.join(self.workspace, "src", "notes.custom"))
        res4 = idx.run_index(self.workspace)
        self.assertEqual(res4["deleted"], 1)

        # 5. JSON format verification
        stats_json = idx.run_stats(self.workspace)
        self.assertIn("workspace", stats_json)
        self.assertIn("files", stats_json)

        print("\n--- BENCHMARK REPORT ---")
        print(f"First Indexing:           {t1_ms} ms ({res1['files']} files, {res1['symbols']} symbols)")
        print(f"Second Unchanged Indexing: {t2_ms} ms ({res2['reused']} files reused)")
        print(f"One-File Modification:     {t3_ms} ms (1 changed, {res3['reused']} reused)")

if __name__ == "__main__":
    unittest.main()
