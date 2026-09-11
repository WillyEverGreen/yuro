import unittest
import os
import tempfile
import json
from tokensaver.core.engine import run_v6_pipeline

class TestE2EFixtureRepos(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = self.temp_dir.name

        # Create sample repo files
        auth_code = (
            "def authenticate_user(username, password):\n"
            "    \"\"\"Authenticate user credential.\"\"\"\n"
            "    if not username or not password:\n"
            "        return False\n"
            "    return verify_hash(username, password)\n\n"
            "def verify_hash(u, p):\n"
            "    return True\n"
        )
        db_code = (
            "def connect_db():\n"
            "    \"\"\"Database connection.\"\"\"\n"
            "    return 'db_conn'\n"
        )
        with open(os.path.join(self.workspace, "auth.py"), "w", encoding="utf-8") as f:
            f.write(auth_code)
        with open(os.path.join(self.workspace, "database.py"), "w", encoding="utf-8") as f:
            f.write(db_code)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_e2e_fixture_task(self):
        res = run_v6_pipeline("Fix authenticate_user in auth.py", self.workspace)
        self.assertEqual(res.get("version"), "6.0")
        self.assertIn("payload", res)
        self.assertIn("authenticate_user", res.get("payload", ""))

if __name__ == "__main__":
    unittest.main()
