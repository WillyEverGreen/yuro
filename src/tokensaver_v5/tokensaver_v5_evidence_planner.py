import sys
import json
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

EVIDENCE_SPECS = {
    "debug": {
        "required_evidence": ["traceback_frame", "target_symbol", "callers", "callees", "references", "recent_changes", "tests", "config"],
        "graph_depth": 2,
        "coverage_threshold": 0.98,
        "risk": "HIGH",
        "history_mode": "recent_edits",
        "retrieval_mode": "precise_graph",
        "target_level": 2
    },
    "refactor": {
        "required_evidence": ["target_symbol", "callers", "references", "dependencies", "tests", "contracts"],
        "graph_depth": 2,
        "coverage_threshold": 0.95,
        "risk": "HIGH",
        "history_mode": "none",
        "retrieval_mode": "precise_graph",
        "target_level": 2
    },
    "implementation": {
        "required_evidence": ["target_implementation", "dependencies", "tests", "config", "integration_points"],
        "graph_depth": 1,
        "coverage_threshold": 0.95,
        "risk": "MEDIUM",
        "history_mode": "none",
        "retrieval_mode": "hybrid",
        "target_level": 2
    },
    "architecture": {
        "required_evidence": ["entry_points", "major_modules", "key_symbols", "relationships"],
        "graph_depth": 2,
        "coverage_threshold": 0.90,
        "risk": "MEDIUM",
        "history_mode": "summary",
        "retrieval_mode": "map_overview",
        "target_level": 1
    },
    "security": {
        "required_evidence": ["auth_symbols", "security_symbols", "config_references", "dependencies"],
        "graph_depth": 2,
        "coverage_threshold": 1.00,
        "risk": "CRITICAL",
        "history_mode": "full",
        "retrieval_mode": "conservative_all",
        "target_level": 2
    },
    "explain": {
        "required_evidence": ["target_symbol", "callers", "callees"],
        "graph_depth": 1,
        "coverage_threshold": 0.90,
        "risk": "LOW",
        "history_mode": "none",
        "retrieval_mode": "summary",
        "target_level": 1
    },
    "general": {
        "required_evidence": [],
        "graph_depth": 0,
        "coverage_threshold": 0.00,
        "risk": "MINIMAL",
        "history_mode": "none",
        "retrieval_mode": "skip",
        "target_level": 1
    }
}

COMMON_PROSE_WORDS = {
    'the', 'and', 'for', 'that', 'this', 'with', 'from', 'code', 'file', 'class', 'function',
    'import', 'test', 'explain', 'project', 'architecture', 'identify', 'major', 'components',
    'describe', 'main', 'execution', 'flow', 'moves', 'between', 'them', 'investigate', 'how',
    'works', 'src', 'lib', 'app', 'determine', 'what', 'other', 'parts', 'would', 'affected',
    'were', 'refactored', 'trace', 'implementation', 'across', 'repository', 'smallest', 'set',
    'files', 'symbols', 'must', 'understood', 'modify', 'safely', 'audit', 'security', 'area',
    'relevant', 'authentication', 'authorization', 'credential', 'sanitization', 'paths', 'most',
    'likely', 'failure', 'points', 'dependencies', 'callers', 'callees', 'analyze', 'interface',
    'logistics', 'data', 'symbol', 'pdf', 'generator', 'page', 'its', 'their', 'which'
}

DEBUG_KEYWORDS = [
    'traceback', 'error line', 'why does this fail', 'find the bug', 'diagnose',
    'investigate', 'failure points', 'bug', 'fix', 'issue', 'failure', 'broken', 'error'
]

def is_line_level_debug_prompt(user_prompt):
    prompt_lower = user_prompt.lower()
    return any(kw in prompt_lower for kw in DEBUG_KEYWORDS)

def extract_target_symbols_from_prompt(prompt):
    code_symbols = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]{2,})\b', prompt)
    targets = []
    for sym in code_symbols:
        if sym.lower() not in COMMON_PROSE_WORDS and not sym.isdigit():
            if any(c.isupper() for c in sym[1:]) or '_' in sym:
                targets.append(sym)
    for sym in code_symbols:
        if sym.lower() not in COMMON_PROSE_WORDS and not sym.isdigit() and sym not in targets:
            targets.append(sym)
    return list(dict.fromkeys(targets))[:5]

def create_evidence_plan(task_class, user_prompt):
    task_class_clean = task_class.lower()
    spec = EVIDENCE_SPECS.get(task_class_clean, EVIDENCE_SPECS["general"]).copy()
    target_symbols = extract_target_symbols_from_prompt(user_prompt)
    
    spec["task"] = task_class_clean
    spec["user_prompt"] = user_prompt
    spec["extracted_targets"] = target_symbols
    
    if task_class_clean in ("debug", "refactor", "implementation", "security") or is_line_level_debug_prompt(user_prompt):
        spec["target_level"] = 2
        spec["full_body_targets"] = target_symbols[:2]
    else:
        spec["target_level"] = 1
        spec["full_body_targets"] = []
        
    return spec

if __name__ == "__main__":
    t_class = sys.argv[1] if len(sys.argv) > 1 else "debug"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Fix run_index in tokensaver_v5_symbol_index.py"
    print(json.dumps(create_evidence_plan(t_class, prompt), indent=2))
