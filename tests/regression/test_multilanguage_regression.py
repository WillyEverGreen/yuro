import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(REPO_ROOT, "src")
UTIL_DIR = os.path.join(SRC_DIR, "utilities")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from tokensaver.indexing.language_adapters import get_indexer_for_file
from tokensaver.retrieval.query_expansion import expand_query_terms
from tokensaver.retrieval.ranker import rank_evidence_units, is_test_filepath
from tokensaver.retrieval.semantic_fallback import compute_semantic_similarity

class TestMultiLanguageRegression(unittest.TestCase):

    def test_cross_language_frontend_to_backend(self):
        """Task 02: TSX frontend component to Python FastAPI backend route."""
        tsx_api_code = "export async function fetchVaR(params) { return fetch('/api/var', params); }"
        py_route_code = "@app.get('/api/var')\ndef get_var_endpoint(): return calculate_var()"
        
        ts_idx = get_indexer_for_file("api.ts")
        py_idx = get_indexer_for_file("router.py")

        ts_syms = [s.name for s in ts_idx.extract_symbols(tsx_api_code, "api.ts")]
        py_syms = [s.name for s in py_idx.extract_symbols(py_route_code, "router.py")]

        self.assertIn("fetchVaR", ts_syms)
        self.assertIn("get_var_endpoint", py_syms)

    def test_test_file_penalty(self):
        """Task 04: Production implementation ranks above test file."""
        units = [
            {"symbol_name": "RiskDashboard", "relative_path": "components/__tests__/RiskDashboard.test.tsx", "unit_type": "TARGET_SYMBOL"},
            {"symbol_name": "RiskDashboard", "relative_path": "components/RiskDashboard.tsx", "unit_type": "TARGET_SYMBOL"}
        ]
        plan = {"extracted_targets": ["RiskDashboard"], "user_prompt": "Fix rendering in RiskDashboard component"}
        ranked = rank_evidence_units(units, plan)
        self.assertEqual(ranked[0]["relative_path"], "components/RiskDashboard.tsx")

    def test_typescript_interface_refactor(self):
        """Task 05: TS interface extraction and refactoring impact."""
        ts_code = "export interface PortfolioSummary { var: number; cvar: number; }"
        ts_idx = get_indexer_for_file("types.ts")
        syms = ts_idx.extract_symbols(ts_code, "types.ts")
        names = [s.name for s in syms]
        self.assertIn("PortfolioSummary", names)

    def test_natural_language_var_query_expansion(self):
        """Task 06: NL query 'Why is Value at Risk returning NaN?' expands to VaR/calculate_var."""
        prompt = "Why is Value at Risk returning NaN?"
        expanded = expand_query_terms(prompt)
        self.assertIn("value_at_risk", expanded)
        self.assertIn("var", expanded)

    def test_nextjs_route_tracing(self):
        """Task 09: Next.js API route to React component tracing."""
        route_code = "export async function GET(request) { return Response.json({ var: 0.05 }); }"
        ts_idx = get_indexer_for_file("app/api/var/route.ts")
        exports = ts_idx.extract_exports(route_code, "app/api/var/route.ts")
        export_names = [e["symbol"] for e in exports]
        self.assertIn("GET", export_names)

    def test_fastapi_endpoint_resolution(self):
        """Task 10: FastAPI @app.get endpoint resolution."""
        py_code = "@router.get('/api/risk/var')\ndef compute_var_route(): pass"
        py_idx = get_indexer_for_file("backend/routes/risk.py")
        syms = py_idx.extract_symbols(py_code, "backend/routes/risk.py")
        names = [s.name for s in syms]
        self.assertIn("compute_var_route", names)

if __name__ == "__main__":
    unittest.main()
