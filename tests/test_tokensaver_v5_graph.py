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

class TestTokenSaverV5Graph(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ts_v52_test_")
        self.workspace = self.test_dir
        
        # Create synthetic multi-file project
        os.makedirs(os.path.join(self.workspace, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "tests"), exist_ok=True)
        
        # 1. src/db.py
        with open(os.path.join(self.workspace, "src", "db.py"), "w", encoding="utf-8") as f:
            f.write("def query(sql):\n    return f'result for {sql}'\n")

        # 2. src/utils.py
        with open(os.path.join(self.workspace, "src", "utils.py"), "w", encoding="utf-8") as f:
            f.write("def hash_password(pwd):\n    return f'hashed_{pwd}'\n")

        # 3. src/auth.py (has IMPORTS, CALLS, INHERITS_FROM, DEFINES, EXACT, EXTERNAL, UNRESOLVED)
        with open(os.path.join(self.workspace, "src", "auth.py"), "w", encoding="utf-8") as f:
            f.write("""import os
import sys
from src.db import query
from src.utils import hash_password

class BaseAuth:
    def validate(self):
        pass

class AuthManager(BaseAuth):
    def login(self, username, pwd):
        h = hash_password(pwd)
        res = query(f"SELECT * FROM users WHERE user={username}")
        unknown_func_call()
        return res
""")

        # 4. src/helper.py (has unique symbol for HEURISTIC resolution)
        with open(os.path.join(self.workspace, "src", "helper.py"), "w", encoding="utf-8") as f:
            f.write("def unique_workspace_helper():\n    pass\n")

        # 5. src/caller_heuristic.py (calls unique_workspace_helper without explicit import)
        with open(os.path.join(self.workspace, "src", "caller_heuristic.py"), "w", encoding="utf-8") as f:
            f.write("def run_helper():\n    unique_workspace_helper()\n")

        # 6. tests/test_auth.py
        with open(os.path.join(self.workspace, "tests", "test_auth.py"), "w", encoding="utf-8") as f:
            f.write("""from src.auth import AuthManager

def test_login_flow():
    mgr = AuthManager()
    result = mgr.login("admin", "secret")
    assert result is not None
""")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_graph_lifecycle_and_invariants(self):
        # 1. First Indexing & Edge Extraction
        t0 = time.time()
        res1 = idx.run_index(self.workspace, force=True)
        t_index_ms = (time.time() - t0) * 1000

        self.assertGreaterEqual(res1["files"], 6)
        self.assertGreater(res1["symbols"], 0)
        self.assertGreater(res1["edges"], 0)

        # 2. Graph Stats & Resolution Verification
        gstats = idx.run_graph_stats(self.workspace)
        self.assertIn("total_edges", gstats)
        self.assertIn("by_kind", gstats)
        self.assertIn("by_resolution_status", gstats)
        self.assertIn("by_evidence_source", gstats)
        self.assertIn("resolution_rate", gstats)

        # Verify edge kinds
        kinds = gstats["by_kind"]
        self.assertIn("DEFINES", kinds)
        self.assertIn("IMPORTS", kinds)
        self.assertIn("CALLS", kinds)
        self.assertIn("INHERITS_FROM", kinds)

        # Verify resolution statuses
        statuses = gstats["by_resolution_status"]
        self.assertIn("EXACT", statuses)
        self.assertIn("EXTERNAL", statuses)
        self.assertIn("UNRESOLVED", statuses)
        self.assertIn("HEURISTIC", statuses)

        # Verify evidence sources
        provenance = gstats["by_evidence_source"]
        self.assertIn("AST_EXACT", provenance)
        self.assertIn("IMPORT_RESOLUTION", provenance)
        self.assertIn("NAME_HEURISTIC", provenance)

        # 3. Callers Query (1-hop reverse lookup)
        t0 = time.time()
        callers_res = idx.run_callers(self.workspace, "login")
        t_callers_ms = callers_res["query_time_ms"]
        self.assertGreaterEqual(callers_res["total_callers"], 1)

        # 4. Callees Query (1-hop forward lookup)
        t0 = time.time()
        callees_res = idx.run_callees(self.workspace, "login")
        t_callees_ms = callees_res["query_time_ms"]
        self.assertGreaterEqual(callees_res["total_callees"], 1)

        # 5. Dependencies Query (2-hop neighborhood)
        t0 = time.time()
        deps_res = idx.run_dependencies(self.workspace, "auth.py", depth=2)
        t_deps_ms = deps_res["query_time_ms"]
        self.assertGreaterEqual(deps_res["total_edges"], 1)

        # 6. Incremental Single-File Edge Update
        time.sleep(0.05)
        with open(os.path.join(self.workspace, "src", "auth.py"), "a", encoding="utf-8") as f:
            f.write("\ndef logout():\n    return True\n")

        t0 = time.time()
        res_inc = idx.run_index(self.workspace)
        t_inc_ms = (time.time() - t0) * 1000

        self.assertEqual(res_inc["changed"], 1)
        self.assertEqual(res_inc["reused"], res1["files"] - 1)

        # 7. Deleted File Cascade & Foreign Key Consistency
        os.remove(os.path.join(self.workspace, "src", "caller_heuristic.py"))
        res_del = idx.run_index(self.workspace)
        self.assertEqual(res_del["deleted"], 1)

        # Check DB foreign key integrity
        db_path = idx.get_db_path(self.workspace)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_check;")
        fk_violations = cursor.fetchall()
        self.assertEqual(len(fk_violations), 0, "No foreign key violations allowed")
        conn.close()

        # 8. CRITICAL LOCAL-ISOLATION TEST
        # Verify database is on disk locally and CLI query output is compact, never dumping raw database
        self.assertTrue(os.path.exists(db_path))
        self.assertTrue(db_path.endswith(os.path.join(".tokensaver", "index.db")))

        # Check compact formatting of CLI callers report
        caller_lines = idx.run_callers(self.workspace, "login")["callers"]
        for c in caller_lines:
            self.assertIn("caller_symbol", c)
            self.assertIn("caller_file", c)
            self.assertIn("line_number", c)
            self.assertNotIn("select * from", str(c).lower())

        print("\n--- GRANULAR LATENCY BENCHMARK REPORT ---")
        print(f"Full Index & Graph Build: {t_index_ms:.2f} ms ({res1['files']} files, {res1['symbols']} symbols, {res1['edges']} edges)")
        print(f"Incremental File Update:   {t_inc_ms:.2f} ms (1 changed, {res_inc['reused']} reused)")
        print(f"1-Hop Callers Query:       {t_callers_ms:.3f} ms ({callers_res['total_callers']} callers found)")
        print(f"1-Hop Callees Query:       {t_callees_ms:.3f} ms ({callees_res['total_callees']} callees found)")
        print(f"2-Hop Neighborhood Query:  {t_deps_ms:.3f} ms ({deps_res['total_edges']} edges returned)")

if __name__ == "__main__":
    unittest.main()
