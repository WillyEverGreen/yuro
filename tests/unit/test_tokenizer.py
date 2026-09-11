import unittest
from tokensaver.core.tokenizer import TokenCounter, count_tokens

class TestTokenizer(unittest.TestCase):
    def test_token_counter_init(self):
        counter = TokenCounter("cl100k_base")
        self.assertIn(counter.backend, ["tiktoken", "heuristic"])
        self.assertIn(counter.token_count_mode, ["exact", "estimated"])

    def test_empty_string(self):
        counter = TokenCounter()
        self.assertEqual(counter.count(""), 0)
        self.assertEqual(counter.count(None), 0)

    def test_code_string_counting(self):
        code = "def hello_world():\n    print('Hello World')\n"
        count = count_tokens(code)
        self.assertGreater(count, 0)

if __name__ == "__main__":
    unittest.main()
