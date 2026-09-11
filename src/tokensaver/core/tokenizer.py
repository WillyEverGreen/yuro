import sys
import os

class TokenCounter:
    def __init__(self, encoding_name: str = "cl100k_base"):
        self.encoding_name = encoding_name
        self._encoder = None
        self._backend = "heuristic"
        self._mode = "estimated"

        try:
            import tiktoken
            self._encoder = tiktoken.get_encoding(encoding_name)
            self._backend = "tiktoken"
            self._mode = "exact"
        except Exception:
            self._encoder = None
            self._backend = "heuristic"
            self._mode = "estimated"

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def token_count_mode(self) -> str:
        return self._mode

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._encoder is not None:
            try:
                return len(self._encoder.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Graceful fallback heuristic
        return max(1, int(len(text) / 3.8))

_default_counter = None

def get_default_token_counter(encoding_name: str = "cl100k_base") -> TokenCounter:
    global _default_counter
    if _default_counter is None or _default_counter.encoding_name != encoding_name:
        _default_counter = TokenCounter(encoding_name)
    return _default_counter

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    return get_default_token_counter(encoding_name).count(text)
