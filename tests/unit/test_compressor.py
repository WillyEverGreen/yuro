import unittest
from tokensaver.evidence.compressor import safe_compress_code_body, get_executable_ast_signature

class TestCompressorAdversarial(unittest.TestCase):
    def test_docstring_and_comment_removal(self):
        py_code = (
            "def calculate_sum(a, b):\n"
            "    \"\"\"Calculates sum of two numbers.\"\"\"\n"
            "    # This is a comment\n"
            "    return a + b\n"
        )
        compressed, meta = safe_compress_code_body(py_code, language="python")
        self.assertTrue(meta["applied"])
        self.assertNotIn("Calculates sum of two numbers", compressed)
        self.assertIn("return a + b", compressed)

    def test_ast_invariant_preservation(self):
        py_code = "def foo():\n    x = 10\n    if x > 5:\n        return True\n    return False\n"
        sig_before = get_executable_ast_signature(py_code)
        compressed, _ = safe_compress_code_body(py_code, language="python")
        sig_after = get_executable_ast_signature(compressed)
        self.assertEqual(sig_before, sig_after)

    def test_string_containing_comment_syntax(self):
        py_code = "def query_db():\n    sql = 'SELECT * FROM users -- filter active'\n    return sql\n"
        compressed, meta = safe_compress_code_body(py_code, language="python")
        self.assertIn("-- filter active", compressed)

    def test_multiline_string_assignment_preserved(self):
        py_code = "def get_template():\n    template = \"\"\"Hello\nWorld\"\"\"\n    return template\n"
        compressed, meta = safe_compress_code_body(py_code, language="python")
        self.assertTrue("Hello" in compressed and "World" in compressed)

    def test_async_and_decorators_preserved(self):
        py_code = "@my_decorator\nasync def fetch_data(url: str) -> dict:\n    \"\"\"Fetch remote JSON.\"\"\"\n    res = await http_get(url)\n    return res\n"
        compressed, meta = safe_compress_code_body(py_code, language="python")
        self.assertIn("my_decorator", compressed)
        self.assertIn("async def fetch_data", compressed)
        self.assertIn("await http_get", compressed)

    def test_try_except_finally_preserved(self):
        py_code = "def safe_run():\n    try:\n        do_work()\n    except Exception as e:\n        log_err(e)\n    finally:\n        cleanup()\n"
        sig_before = get_executable_ast_signature(py_code)
        compressed, meta = safe_compress_code_body(py_code, language="python")
        sig_after = get_executable_ast_signature(compressed)
        self.assertEqual(sig_before, sig_after)

    def test_invalid_syntax_fallback(self):
        bad_code = "def broken_func(:\n    pass"
        compressed, meta = safe_compress_code_body(bad_code, language="python")
        self.assertFalse(meta["applied"])
        self.assertEqual(compressed, bad_code)

if __name__ == "__main__":
    unittest.main()
