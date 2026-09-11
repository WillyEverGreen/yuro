import unittest
from tokensaver.core.economics import compute_net_economics, EconomicsGate

class TestEconomics(unittest.TestCase):
    def test_compute_net_economics(self):
        raw = "def foo():\n" * 200
        selected = "def foo():\n" * 20
        overhead = "// --- Header ---\n"
        econ = compute_net_economics(raw, selected, overhead)
        self.assertGreater(econ["input_gross_saved_tokens"], 0)
        self.assertGreater(econ["input_net_saved_tokens"], 0)
        self.assertTrue(econ["input_net_positive"])

    def test_economics_gate_bypass(self):
        gate = EconomicsGate(min_net_tokens=10)
        econ_fail = {
            "input_net_saved_tokens": -5,
            "input_net_saved_percent": -10.0,
            "input_net_positive": False
        }
        res = gate.evaluate(econ_fail, coverage_passed=True)
        self.assertFalse(res["accepted"])

if __name__ == "__main__":
    unittest.main()
