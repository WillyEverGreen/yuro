import re
from typing import List, Set

ACRONYM_MAP = {
    "var": ["value_at_risk", "calculate_var", "risk_metrics", "variance"],
    "cvar": ["conditional_value_at_risk", "calculate_cvar", "risk_metrics"],
    "value at risk": ["value_at_risk", "var", "calculate_var", "risk_metrics"],
    "conditional value at risk": ["conditional_value_at_risk", "cvar", "calculate_cvar"],
    "api": ["route", "endpoint", "controller", "handler"],
    "pdf": ["pdf_generator", "report", "export"],
    "db": ["database", "schema", "query", "model"],
    "auth": ["authentication", "authorization", "token", "login", "jwt"]
}

def expand_query_terms(prompt: str) -> List[str]:
    """
    Derives natural-language query expansion terms for candidate retrieval and ranking.
    Does NOT mutate prompt or pollute LLM context.
    """
    if not prompt or not prompt.strip():
        return []

    prompt_lower = prompt.lower()
    expanded: Set[str] = set()

    # Multi-word phrase mapping
    for phrase, mapped_list in ACRONYM_MAP.items():
        if ' ' in phrase and phrase in prompt_lower:
            for m in mapped_list:
                expanded.add(m)

    tokens = re.findall(r'\b[a-zA-Z0-9_]+\b', prompt)
    for token in tokens:
        token_lower = token.lower()
        expanded.add(token)
        expanded.add(token_lower)

        # 1. CamelCase splitting (payloadWeight -> payload, weight)
        camel_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|[0-9]+', token)
        if len(camel_parts) > 1:
            for part in camel_parts:
                expanded.add(part.lower())

        # 2. Snake_case splitting (value_at_risk -> value, at, risk)
        if '_' in token:
            snake_parts = token.split('_')
            for part in snake_parts:
                if len(part) > 2:
                    expanded.add(part.lower())

        # 3. Single-token acronym mapping
        if token_lower in ACRONYM_MAP and ' ' not in token_lower:
            for mapped in ACRONYM_MAP[token_lower]:
                expanded.add(mapped)

    # Clean short stop words
    stopwords = {"a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "is", "are", "why", "how", "what"}
    return [t for t in sorted(expanded) if t not in stopwords and len(t) > 1]
