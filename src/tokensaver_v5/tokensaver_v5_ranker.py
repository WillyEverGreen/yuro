import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROVENANCE_WEIGHTS = {
    "AST_EXACT": 1.0,
    "IMPORT_RESOLUTION": 0.85,
    "NAME_HEURISTIC": 0.60,
    "FALLBACK": 0.30
}

UNIT_TYPE_WEIGHTS = {
    "TARGET_SYMBOL": 10.0,
    "CALLER": 7.0,
    "CALLEE": 7.0,
    "REFERENCES": 5.0,
    "INHERITS_FROM": 4.0,
    "IMPORTS": 3.0,
    "MAP_OVERVIEW": 1.0
}

def rank_evidence_units(evidence_units, evidence_plan):
    targets = [t.lower() for t in evidence_plan.get("extracted_targets", [])]
    ranked_units = []

    for unit in evidence_units:
        score = 0.0
        s_name = unit.get("symbol_name", "").lower()
        rel_path = unit.get("relative_path", "").lower()
        unit_type = unit.get("unit_type", "MAP_OVERVIEW")
        provenance = unit.get("provenance", "FALLBACK")
        confidence = unit.get("confidence", 0.5)

        # Base score from unit type
        score += UNIT_TYPE_WEIGHTS.get(unit_type, 1.0) * 10.0

        # Exact target match bonus
        if any(t == s_name for t in targets):
            score += 25.0
        elif any(t in s_name or t in rel_path for t in targets):
            score += 10.0

        # Provenance weight
        score *= PROVENANCE_WEIGHTS.get(provenance, 0.3)

        # Confidence weight
        score *= confidence

        unit_copy = unit.copy()
        unit_copy["score"] = round(score, 3)
        ranked_units.append(unit_copy)

    # Sort deterministically by score descending, then by relative_path, then by start_line
    ranked_units.sort(key=lambda u: (-u["score"], u["relative_path"], u["start_line"]))
    return ranked_units

if __name__ == "__main__":
    test_units = [
        {"symbol_name": "run_index", "relative_path": "tokensaver_v5_symbol_index.py", "unit_type": "TARGET_SYMBOL", "provenance": "AST_EXACT", "confidence": 1.0, "start_line": 350},
        {"symbol_name": "init_db", "relative_path": "tokensaver_v5_symbol_index.py", "unit_type": "CALLEE", "provenance": "AST_EXACT", "confidence": 0.9, "start_line": 70}
    ]
    plan = {"extracted_targets": ["run_index"]}
    print(json.dumps(rank_evidence_units(test_units, plan), indent=2))
