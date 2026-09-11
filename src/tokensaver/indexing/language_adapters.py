import os
import re
import ast
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

class SymbolDefinition:
    def __init__(
        self,
        name: str,
        kind: str,
        file_path: str,
        start_line: int,
        end_line: int,
        language: str,
        container: str = "",
        docstring: str = "",
        signature: str = ""
    ):
        self.name = name
        self.kind = kind  # function, class, interface, type, component, hook, variable
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.language = language
        self.container = container
        self.docstring = docstring
        self.signature = signature

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "container": self.container,
            "signature": self.signature
        }

class LanguageIndexer(ABC):
    @abstractmethod
    def extract_symbols(self, code_text: str, file_path: str) -> List[SymbolDefinition]:
        pass

    @abstractmethod
    def extract_imports(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def extract_exports(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def extract_calls(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        pass

class PythonIndexer(LanguageIndexer):
    def extract_symbols(self, code_text: str, file_path: str) -> List[SymbolDefinition]:
        symbols = []
        try:
            tree = ast.parse(code_text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sig = f"def {node.name}(...)"
                    symbols.append(SymbolDefinition(
                        name=node.name,
                        kind="function",
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, 'end_lineno', node.lineno),
                        language="python",
                        signature=sig
                    ))
                elif isinstance(node, ast.ClassDef):
                    sig = f"class {node.name}"
                    symbols.append(SymbolDefinition(
                        name=node.name,
                        kind="class",
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, 'end_lineno', node.lineno),
                        language="python",
                        signature=sig
                    ))
        except Exception:
            # Fallback regex extraction if ast parse fails
            for idx, line in enumerate(code_text.splitlines(), 1):
                m_def = re.match(r'^\s*(async\s+)?def\s+([a-zA-Z0-9_]+)', line)
                if m_def:
                    symbols.append(SymbolDefinition(
                        name=m_def.group(2), kind="function", file_path=file_path,
                        start_line=idx, end_line=idx, language="python"
                    ))
                m_cls = re.match(r'^\s*class\s+([a-zA-Z0-9_]+)', line)
                if m_cls:
                    symbols.append(SymbolDefinition(
                        name=m_cls.group(1), kind="class", file_path=file_path,
                        start_line=idx, end_line=idx, language="python"
                    ))
        return symbols

    def extract_imports(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        imports = []
        for line in code_text.splitlines():
            m_imp = re.match(r'^\s*from\s+([a-zA-Z0-9_\.]+)\s+import\s+(.+)', line)
            if m_imp:
                imports.append({"source": m_imp.group(1), "targets": [t.strip() for t in m_imp.group(2).split(',')]})
            m_imp2 = re.match(r'^\s*import\s+([a-zA-Z0-9_\.]+)', line)
            if m_imp2:
                imports.append({"source": m_imp2.group(1), "targets": []})
        return imports

    def extract_exports(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        return []

    def extract_calls(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        calls = []
        for idx, line in enumerate(code_text.splitlines(), 1):
            matches = re.findall(r'\b([a-zA-Z0-9_]+)\s*\(', line)
            for m in matches:
                if m not in ("if", "for", "while", "with", "print", "range", "len", "str", "int"):
                    calls.append({"caller_line": idx, "callee_name": m})
        return calls

class TypeScriptIndexer(LanguageIndexer):
    def extract_symbols(self, code_text: str, file_path: str) -> List[SymbolDefinition]:
        symbols = []
        lines = code_text.splitlines()
        for idx, line in enumerate(lines, 1):
            # Interfaces & Types
            m_iface = re.search(r'\bexport\s+interface\s+([a-zA-Z0-9_]+)|\binterface\s+([a-zA-Z0-9_]+)', line)
            if m_iface:
                sym_name = m_iface.group(1) or m_iface.group(2)
                symbols.append(SymbolDefinition(
                    name=sym_name, kind="interface", file_path=file_path,
                    start_line=idx, end_line=idx, language="typescript", signature=f"interface {sym_name}"
                ))

            m_type = re.search(r'\bexport\s+type\s+([a-zA-Z0-9_]+)|\btype\s+([a-zA-Z0-9_]+)', line)
            if m_type:
                sym_name = m_type.group(1) or m_type.group(2)
                symbols.append(SymbolDefinition(
                    name=sym_name, kind="type", file_path=file_path,
                    start_line=idx, end_line=idx, language="typescript", signature=f"type {sym_name}"
                ))

            # Functions & Arrow Functions
            m_fn = re.search(r'\b(export\s+)?(async\s+)?function\s+([a-zA-Z0-9_]+)', line)
            if m_fn:
                sym_name = m_fn.group(3)
                symbols.append(SymbolDefinition(
                    name=sym_name, kind="function", file_path=file_path,
                    start_line=idx, end_line=idx, language="typescript", signature=f"function {sym_name}"
                ))

            m_const_fn = re.search(r'\b(export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(async\s*)?\(', line)
            if m_const_fn:
                sym_name = m_const_fn.group(2)
                symbols.append(SymbolDefinition(
                    name=sym_name, kind="function", file_path=file_path,
                    start_line=idx, end_line=idx, language="typescript", signature=f"const {sym_name}"
                ))

            # Classes
            m_cls = re.search(r'\b(export\s+)?class\s+([a-zA-Z0-9_]+)', line)
            if m_cls:
                sym_name = m_cls.group(2)
                symbols.append(SymbolDefinition(
                    name=sym_name, kind="class", file_path=file_path,
                    start_line=idx, end_line=idx, language="typescript", signature=f"class {sym_name}"
                ))
        return symbols

    def extract_imports(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        imports = []
        for line in code_text.splitlines():
            m_imp = re.search(r'import\s+\{?([a-zA-Z0-9_,\s]+)\}?\s+from\s+[\'"]([^\'"]+)[\'"]', line)
            if m_imp:
                raw_targets = m_imp.group(1).split(',')
                targets = [t.strip().split(' as ')[0] for t in raw_targets if t.strip()]
                imports.append({"source": m_imp.group(2), "targets": targets})
        return imports

    def extract_exports(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        exports = []
        for line in code_text.splitlines():
            m_exp = re.search(r'export\s+(default\s+)?(function|class|const|interface|type)\s+([a-zA-Z0-9_]+)', line)
            if m_exp:
                exports.append({"symbol": m_exp.group(3), "is_default": bool(m_exp.group(1))})
        return exports

    def extract_calls(self, code_text: str, file_path: str) -> List[Dict[str, Any]]:
        calls = []
        for idx, line in enumerate(code_text.splitlines(), 1):
            matches = re.findall(r'\b([a-zA-Z0-9_]+)\s*\(', line)
            for m in matches:
                if m not in ("if", "for", "while", "switch", "catch", "import", "require"):
                    calls.append({"caller_line": idx, "callee_name": m})
        return calls

class TSXIndexer(TypeScriptIndexer):
    def extract_symbols(self, code_text: str, file_path: str) -> List[SymbolDefinition]:
        symbols = super().extract_symbols(code_text, file_path)
        lines = code_text.splitlines()
        for idx, line in enumerate(lines, 1):
            # React Components (UpperCamelCase function or const)
            m_comp = re.search(r'\b(export\s+)?(default\s+)?(function|const)\s+([A-Z][a-zA-Z0-9_]+)', line)
            if m_comp:
                comp_name = m_comp.group(4)
                if not any(s.name == comp_name for s in symbols):
                    symbols.append(SymbolDefinition(
                        name=comp_name, kind="component", file_path=file_path,
                        start_line=idx, end_line=idx, language="tsx", signature=f"Component {comp_name}"
                    ))
            # Custom Hooks (use*)
            m_hook = re.search(r'\b(export\s+)?(const|function)\s+(use[A-Z][a-zA-Z0-9_]+)', line)
            if m_hook:
                hook_name = m_hook.group(3)
                if not any(s.name == hook_name for s in symbols):
                    symbols.append(SymbolDefinition(
                        name=hook_name, kind="hook", file_path=file_path,
                        start_line=idx, end_line=idx, language="tsx", signature=f"Hook {hook_name}"
                    ))
        return symbols

class JavaScriptIndexer(TypeScriptIndexer):
    pass

class JSXIndexer(TSXIndexer):
    pass

def get_indexer_for_file(file_path: str) -> LanguageIndexer:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".py":
        return PythonIndexer()
    elif ext == ".tsx":
        return TSXIndexer()
    elif ext == ".ts":
        return TypeScriptIndexer()
    elif ext == ".jsx":
        return JSXIndexer()
    elif ext in (".js", ".mjs", ".cjs"):
        return JavaScriptIndexer()
    else:
        return PythonIndexer()
