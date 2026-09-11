import unittest
import time
from tokensaver.core.engine import run_v6_pipeline

class TestPerformance(unittest.TestCase):
    def test_pipeline_latency(self):
        t0 = time.time()
        res = run_v6_pipeline("Fix run_index in tokensaver_v5_symbol_index.py", ".")
        lat_ms = (time.time() - t0) * 1000
        self.assertLess(lat_ms, 2000)  # Must execute under 2 seconds locally

if __name__ == "__main__":
    unittest.main()
