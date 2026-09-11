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
import tokensaver_v5_capabilities as caps
import tokensaver_v5_evidence_planner as planner
import tokensaver_v5_retriever as retriever
import tokensaver_v5_ranker as ranker
import tokensaver_v5_budget as budget
import tokensaver_v5_assembler as assembler

class TestTokenSaverV5Adversarial(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ts_v5_adv_")
        self.workspace = self.test_dir

        # Create adversarial test files
        # 1. Duplicate symbol names across multiple modules
        os.makedirs(os.path.join(self.workspace, "mod_a"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "mod_b"), exist_ok=True)
        
        with open(os.path.join(self.workspace, "mod_a", "service.py"), "w", encoding="utf-8") as f:
            f.write("def execute():\n    return 'mod_a'\n")

        with open(os.path.join(self.workspace, "mod_b", "service.py"), "w", encoding="utf-8") as f:
            f.write("def execute():\n    return 'mod_b'\n")

        # 2. Unsupported / malformed source file
        with open(os.path.join(self.workspace, "malformed.custom"), "w", encoding="utf-8") as f:
            f.write("%%% INVALID DATA %%%\ndef raw_func(): pass\n")

        # 3. Security task file
        with open(os.path.join(self.workspace, "auth_sec.py"), "w", encoding="utf-8") as f:
            f.write("def authenticate_admin(token):\n    secret_key = 'SUPER_SECRET'\n    return token == secret_key\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_adversarial_scenarios(self):
        # 1. Duplicate symbol handling
        plan = planner.create_evidence_plan("debug", "Fix execute in service.py")
        units = retriever.retrieve_evidence(self.workspace, plan)
        self.assertGreaterEqual(len(units), 1)

        # 2. Unsupported language degrade safely
        cap_res = caps.analyze_workspace_capabilities(self.workspace)
        self.assertIn(".custom", cap_res["extensions"])
        self.assertEqual(cap_res["extensions"][".custom"]["symbols"], "FALLBACK")

        # 3. Security task high coverage check
        sec_plan = planner.create_evidence_plan("security", "Audit authenticate_admin in auth_sec.py")
        self.assertEqual(sec_plan["coverage_threshold"], 1.00)
        self.assertEqual(sec_plan["risk"], "CRITICAL")

        # 4. Zero benefit / general task admission SKIP
        gen_res = engine.run_v5_pipeline("What is TCP/IP?", self.workspace)
        self.assertTrue(gen_res.get("skipped"))
        self.assertEqual(gen_res.get("net_saved_tokens"), 0)

        # 5. Pipeline execution on adversarial workspace
        v5_res = engine.run_v5_pipeline("Fix execute in mod_a/service.py", self.workspace)
        self.assertIn("engine", v5_res)

if __name__ == "__main__":
    unittest.main()
