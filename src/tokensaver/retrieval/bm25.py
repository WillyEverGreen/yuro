import math
import re
from typing import List, Dict, Any, Tuple

class BM25Retriever:
    def __init__(self, corpus: List[str]):
        self.corpus = corpus
        self.backend = "builtin_bm25"
        self._bm25s_model = None

        try:
            import bm25s
            tokenized_corpus = bm25s.tokenize(corpus)
            self._bm25s_model = bm25s.BM25()
            self._bm25s_model.index(tokenized_corpus)
            self.backend = "bm25s"
        except Exception:
            self.backend = "builtin_bm25"
            self._init_builtin_bm25(corpus)

    def _init_builtin_bm25(self, corpus: List[str]):
        self.doc_tokens = [self._tokenize(doc) for doc in corpus]
        self.num_docs = len(corpus)
        self.avgdl = sum(len(d) for d in self.doc_tokens) / max(1, self.num_docs)
        self.df = {}
        for d in self.doc_tokens:
            for term in set(d):
                self.df[term] = self.df.get(term, 0) + 1

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\b[A-Za-z0-9_]+\b', text) if len(w) > 1]

    def score(self, query: str) -> List[float]:
        if not self.corpus:
            return []

        if self.backend == "bm25s" and self._bm25s_model is not None:
            import bm25s
            try:
                tokens = bm25s.tokenize([query])
                results, scores = self._bm25s_model.retrieve(tokens, k=len(self.corpus))
                # Map back scores in original order
                score_map = {idx: sc for idx, sc in zip(results[0], scores[0])}
                return [float(score_map.get(i, 0.0)) for i in range(len(self.corpus))]
            except Exception:
                pass

        # Built-in BM25 scoring fallback
        k1 = 1.5
        b = 0.75
        query_tokens = self._tokenize(query)
        scores = []

        for d_tokens in self.doc_tokens:
            doc_len = len(d_tokens)
            doc_score = 0.0
            tf_map = {}
            for t in d_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            for qt in query_tokens:
                if qt in tf_map:
                    freq = tf_map[qt]
                    doc_freq = self.df.get(qt, 0)
                    idf = math.log((self.num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
                    num = freq * (k1 + 1.0)
                    den = freq + k1 * (1.0 - b + b * (doc_len / max(1, self.avgdl)))
                    doc_score += idf * (num / den)

            scores.append(round(doc_score, 4))

        return scores
