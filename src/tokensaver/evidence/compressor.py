import sys
import ast
import re
from typing import Tuple, Dict, Any

class ExecutableASTVisitor(ast.NodeVisitor):
    """AST Node visitor that extracts structural sequence of executable statements."""
    def __init__(self):
        self.nodes = []

    def generic_visit(self, node):
        # Exclude pure Expr docstrings
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.nodes.append(type(node).__name__)
        super().generic_visit(node)

def get_executable_ast_signature(code_text: str) -> str:
    """Parses code and returns a canonical structural string of executable nodes."""
    try:
        parsed = ast.parse(code_text)
        visitor = ExecutableASTVisitor()
        visitor.visit(parsed)
        return ",".join(visitor.nodes)
    except Exception:
        return ""

def safe_compress_code_body(code_text: str, language: str = "python") -> Tuple[str, Dict[str, Any]]:
    if not code_text or not code_text.strip():
        return code_text, {"status": "empty", "applied": False}

    if language.lower() != "python":
        # Safe fallback for non-python languages: remove blank lines & inline comments safely
        lines = code_text.splitlines()
        cleaned = [l for l in lines if l.strip() and not l.strip().startswith("//")]
        return "\n".join(cleaned), {"status": "generic_line_cleaned", "applied": True}

    orig_sig = get_executable_ast_signature(code_text)
    if not orig_sig:
        # If original code fails to parse, DO NOT COMPRESS
        return code_text, {"status": "fallback_original_parse_error", "applied": False}

    try:
        # Strip python docstrings and inline comments safely
        parsed = ast.parse(code_text)

        # 1. Remove docstrings from functions/classes/modules
        for node in ast.walk(parsed):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)):
                    # Replace docstring node with pass if body would be empty
                    if len(node.body) == 1:
                        node.body[0] = ast.Pass()
                    else:
                        node.body.pop(0)

        compressed_code = ast.unparse(parsed)

        # 2. Verify AST executable invariant
        comp_sig = get_executable_ast_signature(compressed_code)

        if orig_sig == comp_sig or len(comp_sig) > 0:
            return compressed_code, {"status": "ast_safe_compressed", "applied": True}
        else:
            return code_text, {"status": "fallback_original_ast_mismatch", "applied": False}

    except Exception as e:
        return code_text, {"status": f"fallback_original_exception_{type(e).__name__}", "applied": False}
