import math
import re
from typing import List, Dict, Tuple, Set

def char_ngrams(text: str, n: int = 3) -> List[str]:
    text_clean = f" {text.lower().strip()} "
    return [text_clean[i:i+n] for i in range(len(text_clean) - n + 1)]

class LocalSemanticFallback:
    """
    Lightweight, deterministic local n-gram TF-IDF & sub-word cosine similarity fallback.
    Provides semantic candidate matching for natural-language queries without external daemons.
    """
    def __init__(self):
        self.doc_vocab: Dict[str, Set[str]] = {}
        self.idf_cache: Dict[str, float] = {}

    def fit_documents(self, documents: List[Tuple[str, str]]):
        # documents: List of (doc_id, text)
        doc_count = max(1, len(documents))
        df: Dict[str, int] = {}
        self.doc_vocab.clear()

        for doc_id, text in documents:
            ngrams = set(char_ngrams(text))
            self.doc_vocab[doc_id] = ngrams
            for ng in ngrams:
                df[ng] = df.get(ng, 0) + 1

        self.idf_cache = {ng: math.log((doc_count + 1) / (count + 1)) + 1.0 for ng, count in df.items()}

    def score_query(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not query or not self.doc_vocab:
            return []

        query_ngrams = set(char_ngrams(query))
        if not query_ngrams:
            return []

        query_vec = {ng: self.idf_cache.get(ng, 1.0) for ng in query_ngrams}
        query_norm = math.sqrt(sum(v * v for v in query_vec.values()))
        if query_norm == 0:
            return []

        scores = []
        for doc_id, doc_ngrams in self.doc_vocab.items():
            intersection = query_ngrams.intersection(doc_ngrams)
            if not intersection:
                scores.append((doc_id, 0.0))
                continue

            dot_product = sum(query_vec[ng] * self.idf_cache.get(ng, 1.0) for ng in intersection)
            doc_norm = math.sqrt(sum(self.idf_cache.get(ng, 1.0) ** 2 for ng in doc_ngrams))
            sim = dot_product / (query_norm * doc_norm) if (query_norm * doc_norm) > 0 else 0.0
            scores.append((doc_id, round(sim, 4)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

def compute_semantic_similarity(query: str, target_text: str) -> float:
    q_ngrams = set(char_ngrams(query))
    t_ngrams = set(char_ngrams(target_text))
    if not q_ngrams or not t_ngrams:
        return 0.0
    intersection = q_ngrams.intersection(t_ngrams)
    union = q_ngrams.union(t_ngrams)
    return round(len(intersection) / len(union), 4)
