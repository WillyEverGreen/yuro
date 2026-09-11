import os
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CAPABILITY_MATRIX = {
    'python': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PRECISE',
        'calls': 'PRECISE',
        'references': 'PARTIAL',
        'inheritance': 'PRECISE'
    },
    'javascript': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PRECISE',
        'calls': 'PARTIAL',
        'references': 'PARTIAL',
        'inheritance': 'PARTIAL'
    },
    'typescript': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PRECISE',
        'calls': 'PARTIAL',
        'references': 'PARTIAL',
        'inheritance': 'PRECISE'
    },
    'go': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PRECISE',
        'calls': 'PRECISE',
        'references': 'PARTIAL',
        'inheritance': 'PARTIAL'
    },
    'rust': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PRECISE',
        'calls': 'PARTIAL',
        'references': 'PARTIAL',
        'inheritance': 'PRECISE'
    },
    'java': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PRECISE',
        'calls': 'PARTIAL',
        'references': 'PARTIAL',
        'inheritance': 'PRECISE'
    },
    'cpp': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PARTIAL',
        'calls': 'PARTIAL',
        'references': 'PARTIAL',
        'inheritance': 'PRECISE'
    },
    'c': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PARTIAL',
        'calls': 'PARTIAL',
        'references': 'PARTIAL',
        'inheritance': 'UNSUPPORTED'
    },
    'c_sharp': {
        'parser': 'TREE_SITTER',
        'symbols': 'PRECISE',
        'imports': 'PRECISE',
        'calls': 'PARTIAL',
        'references': 'PARTIAL',
        'inheritance': 'PRECISE'
    },
    'json': {
        'parser': 'REGEX_FALLBACK',
        'symbols': 'FALLBACK',
        'imports': 'UNSUPPORTED',
        'calls': 'UNSUPPORTED',
        'references': 'UNSUPPORTED',
        'inheritance': 'UNSUPPORTED'
    },
    'yaml': {
        'parser': 'REGEX_FALLBACK',
        'symbols': 'FALLBACK',
        'imports': 'UNSUPPORTED',
        'calls': 'UNSUPPORTED',
        'references': 'UNSUPPORTED',
        'inheritance': 'UNSUPPORTED'
    },
    'markdown': {
        'parser': 'REGEX_FALLBACK',
        'symbols': 'FALLBACK',
        'imports': 'UNSUPPORTED',
        'calls': 'UNSUPPORTED',
        'references': 'UNSUPPORTED',
        'inheritance': 'UNSUPPORTED'
    }
}

def analyze_workspace_capabilities(workspace_path):
    workspace_path = os.path.abspath(workspace_path)
    detected_exts = set()
    
    for root, dirs, files in os.walk(workspace_path):
        rel_root = os.path.relpath(root, workspace_path)
        if any(ignored in rel_root.split(os.sep) for ignored in ['.git', 'node_modules', '__pycache__', '.tokensaver']):
            dirs[:] = []
            continue

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                detected_exts.add(ext)

    has_treesitter = False
    try:
        import tree_sitter
        import tree_sitter_languages
        has_treesitter = True
    except Exception:
        pass

    results = {}
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
        '.go': 'go', '.rs': 'rust', '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.cs': 'c_sharp',
        '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown'
    }

    for ext in sorted(detected_exts):
        lang = ext_map.get(ext, 'unknown')
        if lang in CAPABILITY_MATRIX:
            cap = CAPABILITY_MATRIX[lang].copy()
            if not has_treesitter and cap['parser'] == 'TREE_SITTER':
                cap['parser'] = 'AST_OR_REGEX'
                cap['symbols'] = 'PARTIAL'
            results[ext] = cap
        else:
            results[ext] = {
                'parser': 'UNSUPPORTED',
                'symbols': 'FALLBACK',
                'imports': 'UNSUPPORTED',
                'calls': 'UNSUPPORTED',
                'references': 'UNSUPPORTED',
                'inheritance': 'UNSUPPORTED'
            }

    overall_quality = 'PRECISE'
    if any(c['symbols'] == 'FALLBACK' for c in results.values()):
        overall_quality = 'MIXED_FALLBACK'

    return {
        'workspace': workspace_path,
        'has_treesitter': has_treesitter,
        'overall_quality': overall_quality,
        'extensions': results
    }

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(json.dumps(analyze_workspace_capabilities(target), indent=2))
