import re
from typing import List, Dict, Any
from tokensaver.retrieval.bm25 import BM25Retriever
from tokensaver.retrieval.query_expansion import expand_query_terms
from tokensaver.retrieval.semantic_fallback import compute_semantic_similarity

def calculate_graph_centrality(units: List[Dict[str, Any]]) -> Dict[str, float]:
    """Lightweight PageRank / Degree Centrality calculation over retrieved units."""
    if not units:
        return {}

    symbol_counts = {}
    total_refs = 0
    for u in units:
        name = u.get("symbol_name", "")
        if name:
            symbol_counts[name] = symbol_counts.get(name, 0) + 1
            total_refs += 1

    centrality_map = {}
    for name, cnt in symbol_counts.items():
        centrality_map[name] = round(cnt / max(1, total_refs), 4)
    return centrality_map

def is_test_filepath(filepath: str) -> bool:
    if not filepath:
        return False
    fp_lower = filepath.lower()
    return bool(re.search(r'test_|_test|\.spec\.|\.test\.|__tests__|/tests/|\\tests\\', fp_lower))

def rank_evidence_units(
    retrieved_units: List[Dict[str, Any]],
    evidence_plan: Dict[str, Any],
    weights: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    if not retrieved_units:
        return []

    if weights is None:
        weights = {
            "target_match": 10.0,
            "bm25": 4.0,
            "semantic": 3.0,
            "graph_proximity": 3.0,
            "centrality": 2.0,
            "production_prior": 2.0,
            "test_penalty": 6.0
        }

    targets = [t.lower() for t in evidence_plan.get("extracted_targets", [])]
    raw_query_text = evidence_plan.get("user_prompt", "")

    # Query expansion
    expanded_terms = expand_query_terms(raw_query_text)
    expanded_query_str = f"{raw_query_text} {' '.join(expanded_terms)}"

    query_asks_tests = bool(re.search(r'\b(test|spec|suite|unit|fixture)\b', raw_query_text, re.IGNORECASE))

    # Build corpus for BM25 ranking
    corpus = []
    for u in retrieved_units:
        s_name = u.get("symbol_name", "")
        s_sig = u.get("signature", "")
        rel_p = u.get("relative_path", "")
        corpus.append(f"{s_name} {s_sig} {rel_p}")

    bm25_retriever = BM25Retriever(corpus)
    bm25_scores = bm25_retriever.score(expanded_query_str) if expanded_query_str else [0.0] * len(retrieved_units)
    max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0

    centrality_map = calculate_graph_centrality(retrieved_units)

    ranked_units = []
    for idx, unit in enumerate(retrieved_units):
        s_name = unit.get("symbol_name", "").lower()
        rel_p = unit.get("relative_path", "").lower()
        unit_type = unit.get("unit_type", "MAP_OVERVIEW")

        # 1. Target match score
        target_match = 1.0 if any(t in s_name or t in rel_p for t in targets) else 0.0

        # 2. Normalized BM25 score
        bm25_score = round(bm25_scores[idx] / max_bm25, 4) if idx < len(bm25_scores) else 0.0

        # 3. Local semantic similarity score
        candidate_text = f"{s_name} {unit.get('signature', '')} {rel_p}"
        semantic_score = compute_semantic_similarity(raw_query_text, candidate_text)

        # 4. Graph proximity score
        graph_proximity = 1.0 if unit_type == "TARGET_SYMBOL" else (0.7 if unit_type in ["CALLER", "CALLEE"] else 0.3)

        # 5. Centrality score
        centrality = centrality_map.get(unit.get("symbol_name", ""), 0.0)

        # 6. Production prior vs Test penalty
        is_test = is_test_filepath(rel_p)
        production_prior = 1.0 if not is_test else 0.0
        test_penalty = 1.0 if (is_test and not query_asks_tests) else 0.0

        final_score = round(
            weights["target_match"] * target_match +
            weights["bm25"] * bm25_score +
            weights["semantic"] * semantic_score +
            weights["graph_proximity"] * graph_proximity +
            weights["centrality"] * centrality +
            weights["production_prior"] * production_prior -
            weights["test_penalty"] * test_penalty,
            4
        )

        unit_copy = unit.copy()
        unit_copy["score"] = final_score
        unit_copy["signals"] = {
            "target_match": target_match,
            "bm25": bm25_score,
            "semantic": semantic_score,
            "graph_proximity": graph_proximity,
            "centrality": centrality,
            "production_prior": production_prior,
            "test_penalty": test_penalty
        }
        ranked_units.append(unit_copy)

    # Deterministic sorting: highest score first, ties broken by relative path & symbol name
    ranked_units.sort(
        key=lambda u: (u["score"], u.get("relative_path", ""), u.get("symbol_name", "")),
        reverse=True
    )
    return ranked_units
