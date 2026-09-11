import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tokensaver.indexing.language_adapters import (
    PythonIndexer, TypeScriptIndexer, TSXIndexer, JavaScriptIndexer, get_indexer_for_file
)
from tokensaver.retrieval.query_expansion import expand_query_terms
from tokensaver.retrieval.ranker import is_test_filepath, rank_evidence_units

class TestMultiLanguageIndexer(unittest.TestCase):

    def test_python_indexer(self):
        py_code = """
import sys

class RiskCalculator:
    def calculate_var(self, portfolio_id: str) -> float:
        return 0.05
"""
        indexer = get_indexer_for_file("risk_metrics.py")
        symbols = indexer.extract_symbols(py_code, "risk_metrics.py")
        names = [s.name for s in symbols]
        self.assertIn("RiskCalculator", names)
        self.assertIn("calculate_var", names)

    def test_typescript_indexer(self):
        ts_code = """
export interface PortfolioSummary {
    id: string;
    valueAtRisk: number;
}

export type RiskMetricType = 'VAR' | 'CVAR';

export async function fetchRiskMetrics(id: string): Promise<PortfolioSummary> {
    return { id, valueAtRisk: 0.05 };
}
"""
        indexer = get_indexer_for_file("types.ts")
        symbols = indexer.extract_symbols(ts_code, "types.ts")
        names = [s.name for s in symbols]
        self.assertIn("PortfolioSummary", names)
        self.assertIn("RiskMetricType", names)
        self.assertIn("fetchRiskMetrics", names)

    def test_tsx_indexer(self):
        tsx_code = """
import React from 'react';

export interface ViewerProps {
    wagonId: string;
}

export const WagonViewer: React.FC<ViewerProps> = ({ wagonId }) => {
    const [speed, setSpeed] = React.useState(0);
    return <div>Wagon {wagonId}</div>;
};

export function useWagonTelemetry(id: string) {
    return { speed: 80 };
}
"""
        indexer = get_indexer_for_file("WagonViewer.tsx")
        symbols = indexer.extract_symbols(tsx_code, "WagonViewer.tsx")
        names = [s.name for s in symbols]
        self.assertIn("WagonViewer", names)
        self.assertIn("useWagonTelemetry", names)
        self.assertIn("ViewerProps", names)

    def test_query_expansion(self):
        prompt = "Why is Value at Risk returning NaN for payloadWeight?"
        terms = expand_query_terms(prompt)
        self.assertIn("value_at_risk", terms)
        self.assertIn("var", terms)
        self.assertIn("payload", terms)
        self.assertIn("weight", terms)

    def test_test_file_penalty_ranking(self):
        units = [
            {
                "symbol_name": "calculate_var",
                "relative_path": "tests/test_risk_metrics.py",
                "unit_type": "TARGET_SYMBOL",
                "level": 2,
                "signature": "def test_calculate_var():"
            },
            {
                "symbol_name": "calculate_var",
                "relative_path": "services/risk_metrics.py",
                "unit_type": "TARGET_SYMBOL",
                "level": 2,
                "signature": "def calculate_var():"
            }
        ]
        evidence_plan = {"extracted_targets": ["calculate_var"], "user_prompt": "Fix calculate_var implementation"}
        ranked = rank_evidence_units(units, evidence_plan)
        # Production file must rank #1 above test file
        self.assertEqual(ranked[0]["relative_path"], "services/risk_metrics.py")
        self.assertTrue(ranked[1]["signals"]["test_penalty"] > 0)

if __name__ == "__main__":
    unittest.main()
