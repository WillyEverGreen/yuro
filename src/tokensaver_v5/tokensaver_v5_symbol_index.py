import sys
import os
import sqlite3
import hashlib
import time
import json
import argparse
import re
import fnmatch

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Language capabilities mapping
SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.cs': 'c_sharp'
}

PARTIAL_EXTENSIONS = {
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.md': 'markdown',
    '.toml': 'toml',
    '.xml': 'xml',
    '.html': 'html',
    '.css': 'css'
}

DEFAULT_IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', 'dist', 'build', '.venv', 'venv',
    '.tokensaver', '.tokensaver-cache', '.idea', '.vscode', '.next', 'target',
    'bin', 'obj', '.pytest_cache', '.mypy_cache'
}

DEFAULT_IGNORE_EXTS = {
    '.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif', '.ico',
    '.zip', '.tar', '.gz', '.7z', '.pdf', '.pyc', '.pyo', '.pyd', '.db', '.sqlite'
}

STANDARD_EXTERNAL_MODULES = {
    'sys', 'os', 'sqlite3', 'hashlib', 'time', 'json', 'argparse', 're', 'fnmatch',
    'tempfile', 'unittest', 'shutil', 'math', 'pathlib', 'collections', 'typing',
    'fmt', 'net/http', 'io', 'fs', 'path', 'express', 'react', 'std', 'boost', 'asyncio'
}

def estimate_tokens(text):
    if not text:
        return 0
    return int(len(text) / 3.8)

def compute_hash(content_bytes):
    return hashlib.sha256(content_bytes).hexdigest()

def get_db_path(workspace_path):
    tokensaver_dir = os.path.join(workspace_path, ".tokensaver")
    os.makedirs(tokensaver_dir, exist_ok=True)
    return os.path.join(tokensaver_dir, "index.db")

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE,
        relative_path TEXT,
        extension TEXT,
        size_bytes INTEGER,
        mtime_ns INTEGER,
        content_hash TEXT,
        language TEXT,
        parse_status TEXT,
        indexed_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER,
        name TEXT,
        qualified_name TEXT,
        kind TEXT,
        parent_symbol TEXT,
        signature TEXT,
        start_line INTEGER,
        end_line INTEGER,
        start_byte INTEGER,
        end_byte INTEGER,
        visibility TEXT,
        content_hash TEXT,
        FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symbol_edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file_id INTEGER NOT NULL,
        source_symbol_id INTEGER,
        target_name TEXT NOT NULL,
        target_qualified_name TEXT,
        target_file TEXT,
        target_symbol_id INTEGER,
        kind TEXT NOT NULL,
        line_number INTEGER,
        resolution_status TEXT NOT NULL,
        evidence_source TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        FOREIGN KEY(source_file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY(source_symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
        FOREIGN KEY(target_symbol_id) REFERENCES symbols(id) ON DELETE SET NULL
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file_id ON symbols(file_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_qualified ON symbols(qualified_name);")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source_symbol ON symbol_edges(source_symbol_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target_symbol ON symbol_edges(target_symbol_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source_file ON symbol_edges(source_file_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_kind ON symbol_edges(kind);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target_name ON symbol_edges(target_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_resolution ON symbol_edges(resolution_status);")

    conn.commit()
    return conn

def parse_ignore_patterns(workspace_path):
    patterns = []
    for ignore_filename in ['.gitignore', '.tokensaverignore']:
        ipath = os.path.join(workspace_path, ignore_filename)
        if os.path.exists(ipath):
            try:
                with open(ipath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception:
                pass
    return patterns

def is_ignored(rel_path, is_dir, ignore_patterns):
    parts = rel_path.replace('\\', '/').split('/')
    for part in parts:
        if part in DEFAULT_IGNORE_DIRS:
            return True
            
    norm_path = rel_path.replace('\\', '/')
    for pat in ignore_patterns:
        pat_clean = pat.rstrip('/')
        if fnmatch.fnmatch(norm_path, pat_clean) or fnmatch.fnmatch(os.path.basename(norm_path), pat_clean):
            return True
        if is_dir and fnmatch.fnmatch(norm_path + '/', pat_clean + '/'):
            return True
    return False

def extract_symbols_and_edges_treesitter(content, language_name):
    try:
        import tree_sitter_languages
        parser = tree_sitter_languages.get_parser(language_name)
        tree = parser.parse(content.encode('utf-8'))
    except Exception:
        syms, raw_edges = extract_symbols_and_edges_regex(content)
        return syms, raw_edges, "FALLBACK"

    lines = content.split('\n')
    symbols = []
    raw_edges = []
    seen_edges = set()

    def add_raw_edge(src_sym_idx, target_name, kind, line_no):
        key = (src_sym_idx, target_name, kind, line_no)
        if key not in seen_edges:
            seen_edges.add(key)
            raw_edges.append({
                "source_symbol_idx": src_sym_idx,
                "target_name": target_name,
                "kind": kind,
                "line_number": line_no
            })

    def get_node_text(node):
        return content[node.start_byte:node.end_byte].strip()

    def get_node_signature(node):
        start_row = node.start_point[0]
        first_line = lines[start_row].strip() if start_row < len(lines) else ""
        if len(first_line) > 120:
            first_line = first_line[:117] + "..."
        return first_line

    def traverse(node, current_symbol_idx=None, parent_name=""):
        node_type = node.type

        is_func = node_type in ['function_definition', 'async_function_definition', 'function_declaration', 'function_item', 'method_definition']
        is_class = node_type in ['class_definition', 'class_declaration', 'struct_item', 'trait_item']
        is_interface = node_type in ['interface_declaration', 'type_alias_declaration', 'enum_item']
        is_import = node_type in ['import_statement', 'import_from_statement', 'import_declaration', 'use_declaration']
        is_call = node_type in ['call_expression', 'call', 'method_invocation', 'command']

        current_name = None
        kind = None

        if is_func:
            kind = "method" if (parent_name and is_class) else "function"
            name_node = node.child_by_field_name('name')
            if not name_node:
                for child in node.children:
                    if child.type in ['identifier', 'property_identifier', 'name']:
                        name_node = child
                        break
            if name_node:
                current_name = get_node_text(name_node)

        elif is_class:
            kind = "class"
            name_node = node.child_by_field_name('name')
            if not name_node:
                for child in node.children:
                    if child.type in ['identifier', 'type_identifier']:
                        name_node = child
                        break
            if name_node:
                current_name = get_node_text(name_node)

            # Inheritance
            super_node = node.child_by_field_name('superclasses') or node.child_by_field_name('heritage')
            if super_node:
                super_text = get_node_text(super_node)
                for super_name in re.findall(r'[A-Za-z0-9_]+', super_text):
                    if super_name not in ['extends', 'implements', 'class']:
                        add_raw_edge(len(symbols), super_name, "INHERITS_FROM", node.start_point[0] + 1)

        elif is_interface:
            kind = "interface" if "interface" in node_type else "type"
            name_node = node.child_by_field_name('name')
            if not name_node:
                for child in node.children:
                    if child.type in ['identifier', 'type_identifier']:
                        name_node = child
                        break
            if name_node:
                current_name = get_node_text(name_node)

        elif is_import:
            imp_sig = get_node_signature(node)
            for imp_name in re.findall(r'[A-Za-z0-9_.]+', imp_sig):
                if imp_name not in ['import', 'from', 'as', 'use', 'const', 'let', 'var', 'require']:
                    add_raw_edge(None, imp_name, "IMPORTS", node.start_point[0] + 1)

        elif is_call:
            fn_node = node.child_by_field_name('function') or (node.children[0] if node.children else None)
            if fn_node:
                fn_text = get_node_text(fn_node)
                call_target = fn_text.split('.')[-1].split('(')[0].strip()
                if call_target and re.match(r'^[A-Za-z0-9_]+$', call_target):
                    add_raw_edge(current_symbol_idx, call_target, "CALLS", node.start_point[0] + 1)

        new_symbol_idx = current_symbol_idx
        if current_name and kind:
            qual_name = f"{parent_name}.{current_name}" if parent_name else current_name
            sig = get_node_signature(node)
            symbols.append({
                "name": current_name,
                "qualified_name": qual_name,
                "kind": kind,
                "parent_symbol": parent_name,
                "signature": sig,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "visibility": "private" if current_name.startswith("_") else "public",
                "content_hash": hashlib.sha256(get_node_text(node).encode('utf-8')).hexdigest()[:16]
            })
            new_symbol_idx = len(symbols) - 1
            next_parent = qual_name
        else:
            next_parent = parent_name

        for child in node.children:
            traverse(child, new_symbol_idx, next_parent)

    traverse(tree.root_node)
    return symbols, raw_edges, "PARSED"

def extract_symbols_and_edges_python_ast(content):
    import ast
    try:
        tree = ast.parse(content)
    except Exception:
        return extract_symbols_and_edges_regex(content) + ("FALLBACK",)

    lines = content.split('\n')
    symbols = []
    raw_edges = []
    seen_edges = set()

    def add_raw_edge(src_sym_idx, target_name, kind, line_no):
        key = (src_sym_idx, target_name, kind, line_no)
        if key not in seen_edges:
            seen_edges.add(key)
            raw_edges.append({
                "source_symbol_idx": src_sym_idx,
                "target_name": target_name,
                "kind": kind,
                "line_number": line_no
            })

    class ASTVisitor(ast.NodeVisitor):
        def __init__(self):
            self.parent_stack = []
            self.current_symbol_idx = None

        def visit_Import(self, node):
            for alias in node.names:
                add_raw_edge(None, alias.name, "IMPORTS", node.lineno)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            mod = node.module or ""
            for alias in node.names:
                target = f"{mod}.{alias.name}" if mod else alias.name
                add_raw_edge(None, target, "IMPORTS", node.lineno)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            parent_name = ".".join(self.parent_stack)
            qual_name = f"{parent_name}.{node.name}" if parent_name else node.name
            sig = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else f"class {node.name}:"
            
            sym_idx = len(symbols)
            symbols.append({
                "name": node.name,
                "qualified_name": qual_name,
                "kind": "class",
                "parent_symbol": parent_name,
                "signature": sig,
                "start_line": node.lineno,
                "end_line": getattr(node, 'end_lineno', node.lineno),
                "start_byte": 0,
                "end_byte": 0,
                "visibility": "private" if node.name.startswith("_") else "public",
                "content_hash": hashlib.sha256(node.name.encode('utf-8')).hexdigest()[:16]
            })

            for base in node.bases:
                base_name = getattr(base, 'id', None) or getattr(base, 'attr', None)
                if base_name:
                    add_raw_edge(sym_idx, base_name, "INHERITS_FROM", node.lineno)

            old_idx = self.current_symbol_idx
            self.current_symbol_idx = sym_idx
            self.parent_stack.append(node.name)
            self.generic_visit(node)
            self.parent_stack.pop()
            self.current_symbol_idx = old_idx

        def visit_FunctionDef(self, node):
            self.add_func(node)

        def visit_AsyncFunctionDef(self, node):
            self.add_func(node)

        def add_func(self, node):
            parent_name = ".".join(self.parent_stack)
            qual_name = f"{parent_name}.{node.name}" if parent_name else node.name
            kind = "method" if self.parent_stack else "function"
            sig = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else f"def {node.name}():"
            
            sym_idx = len(symbols)
            symbols.append({
                "name": node.name,
                "qualified_name": qual_name,
                "kind": kind,
                "parent_symbol": parent_name,
                "signature": sig,
                "start_line": node.lineno,
                "end_line": getattr(node, 'end_lineno', node.lineno),
                "start_byte": 0,
                "end_byte": 0,
                "visibility": "private" if node.name.startswith("_") else "public",
                "content_hash": hashlib.sha256(node.name.encode('utf-8')).hexdigest()[:16]
            })

            old_idx = self.current_symbol_idx
            self.current_symbol_idx = sym_idx
            self.parent_stack.append(node.name)
            self.generic_visit(node)
            self.parent_stack.pop()
            self.current_symbol_idx = old_idx

        def visit_Call(self, node):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name:
                add_raw_edge(self.current_symbol_idx, func_name, "CALLS", getattr(node, 'lineno', 1))
            self.generic_visit(node)

    visitor = ASTVisitor()
    visitor.visit(tree)
    return symbols, raw_edges, "PARSED"

def extract_symbols_and_edges_regex(content):
    lines = content.split('\n')
    symbols = []
    raw_edges = []
    seen_edges = set()
    current_sym_idx = None

    def add_raw_edge(src_sym_idx, target_name, kind, line_no):
        key = (src_sym_idx, target_name, kind, line_no)
        if key not in seen_edges:
            seen_edges.add(key)
            raw_edges.append({
                "source_symbol_idx": src_sym_idx,
                "target_name": target_name,
                "kind": kind,
                "line_number": line_no
            })

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        m = re.match(r'^(export\s+)?(async\s+)?(def|class|function|interface|type|enum|struct|pub\s+fn)\s+([A-Za-z0-9_]+)', stripped)
        if m:
            kind_kw = m.group(3)
            name = m.group(4)
            kind = "function" if kind_kw in ["def", "function", "fn"] else ("class" if kind_kw in ["class", "struct"] else "interface")
            current_sym_idx = len(symbols)
            symbols.append({
                "name": name,
                "qualified_name": name,
                "kind": kind,
                "parent_symbol": "",
                "signature": stripped,
                "start_line": idx,
                "end_line": idx,
                "start_byte": 0,
                "end_byte": 0,
                "visibility": "private" if name.startswith("_") else "public",
                "content_hash": hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]
            })

        imp_m = re.match(r'^(import|from|require|use)\s+([A-Za-z0-9_./]+)', stripped)
        if imp_m:
            add_raw_edge(None, imp_m.group(2), "IMPORTS", idx)

        call_matches = re.findall(r'([A-Za-z0-9_]+)\s*\(', stripped)
        for call_target in call_matches:
            if call_target not in ['def', 'class', 'if', 'while', 'for', 'switch', 'return', 'function']:
                add_raw_edge(current_sym_idx, call_target, "CALLS", idx)

    return symbols, raw_edges

def process_file_content(ext, content):
    if ext == '.py':
        symbols, raw_edges, status = extract_symbols_and_edges_treesitter(content, 'python')
        if not symbols:
            symbols, raw_edges, status = extract_symbols_and_edges_python_ast(content)
        return symbols, raw_edges, status, "Python"
        
    elif ext in SUPPORTED_EXTENSIONS:
        lang = SUPPORTED_EXTENSIONS[ext]
        symbols, raw_edges, status = extract_symbols_and_edges_treesitter(content, lang)
        return symbols, raw_edges, status, lang.capitalize()
        
    elif ext in PARTIAL_EXTENSIONS:
        lang = PARTIAL_EXTENSIONS[ext]
        symbols, raw_edges = extract_symbols_and_edges_regex(content)
        return symbols, raw_edges, "FALLBACK", lang.capitalize()
        
    else:
        symbols, raw_edges = extract_symbols_and_edges_regex(content)
        return symbols, raw_edges, "FALLBACK", ext.lstrip('.').upper() or "Unknown"

def resolve_edges(conn):
    cursor = conn.cursor()
    
    # PASS 1: Same-file / scope resolution (AST_EXACT)
    cursor.execute("""
    UPDATE symbol_edges
    SET target_symbol_id = (
        SELECT s.id FROM symbols s 
        WHERE s.file_id = symbol_edges.source_file_id AND s.name = symbol_edges.target_name
        LIMIT 1
    ),
    target_qualified_name = (
        SELECT s.qualified_name FROM symbols s 
        WHERE s.file_id = symbol_edges.source_file_id AND s.name = symbol_edges.target_name
        LIMIT 1
    ),
    target_file = (
        SELECT f.relative_path FROM files f WHERE f.id = symbol_edges.source_file_id
    ),
    resolution_status = 'EXACT',
    evidence_source = 'AST_EXACT',
    confidence = 1.0
    WHERE target_symbol_id IS NULL AND EXISTS (
        SELECT 1 FROM symbols s WHERE s.file_id = symbol_edges.source_file_id AND s.name = symbol_edges.target_name
    );
    """)

    # PASS 2 & 3 & 4: Unresolved edges
    cursor.execute("""
    SELECT e.id, e.source_file_id, e.target_name, e.kind
    FROM symbol_edges e
    WHERE e.resolution_status = 'UNRESOLVED' OR e.target_symbol_id IS NULL
    """)
    unresolved = cursor.fetchall()

    for edge_id, src_file_id, target_name, edge_kind in unresolved:
        if edge_kind == 'DEFINES':
            continue

        base_mod = target_name.split('.')[0]
        if base_mod in STANDARD_EXTERNAL_MODULES:
            cursor.execute("""
            UPDATE symbol_edges
            SET resolution_status = 'EXTERNAL',
                evidence_source = 'FALLBACK',
                confidence = 1.0
            WHERE id = ?
            """, (edge_id,))
            continue

        # Check if source_file has explicit import targeting the module/file
        cursor.execute("""
        SELECT e_imp.target_name
        FROM symbol_edges e_imp
        WHERE e_imp.source_file_id = ? AND e_imp.kind = 'IMPORTS'
        """, (src_file_id,))
        imported_names = {row[0] for row in cursor.fetchall()}

        # Match against symbols across workspace
        cursor.execute("""
        SELECT s.id, s.qualified_name, f.relative_path
        FROM symbols s
        JOIN files f ON s.file_id = f.id
        WHERE (s.name = ? OR s.qualified_name = ?)
        """, (target_name, target_name))
        candidates = cursor.fetchall()

        resolved_import = False
        for cand in candidates:
            cand_rel_path = cand[2].replace('\\', '/').replace('/', '.')
            if any(imp in cand_rel_path or imp == target_name or target_name.startswith(imp) for imp in imported_names):
                cursor.execute("""
                UPDATE symbol_edges
                SET target_symbol_id = ?,
                    target_qualified_name = ?,
                    target_file = ?,
                    resolution_status = 'EXACT',
                    evidence_source = 'IMPORT_RESOLUTION',
                    confidence = 0.9
                WHERE id = ?
                """, (cand[0], cand[1], cand[2], edge_id))
                resolved_import = True
                break

        if resolved_import:
            continue

        # PASS 3: Name-based workspace heuristic (NAME_HEURISTIC)
        if len(candidates) == 1:
            cand = candidates[0]
            cursor.execute("""
            UPDATE symbol_edges
            SET target_symbol_id = ?,
                target_qualified_name = ?,
                target_file = ?,
                resolution_status = 'HEURISTIC',
                evidence_source = 'NAME_HEURISTIC',
                confidence = 0.6
            WHERE id = ?
            """, (cand[0], cand[1], cand[2], edge_id))
        else:
            cursor.execute("""
            UPDATE symbol_edges
            SET resolution_status = 'UNRESOLVED',
                evidence_source = 'FALLBACK',
                confidence = 0.0
            WHERE id = ?
            """, (edge_id,))

    conn.commit()

def run_index(workspace_path, force=False):
    start_time = time.time()
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    conn = init_db(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    ignore_patterns = parse_ignore_patterns(workspace_path)

    # Load existing DB state
    cursor.execute("SELECT path, mtime_ns, content_hash, id FROM files")
    db_files = {row[0]: {"mtime_ns": row[1], "content_hash": row[2], "id": row[3]} for row in cursor.fetchall()}

    added = 0
    changed = 0
    reused = 0
    deleted = 0
    seen_paths = set()

    for root, dirs, files in os.walk(workspace_path):
        rel_root = os.path.relpath(root, workspace_path)
        if rel_root != '.' and is_ignored(rel_root, True, ignore_patterns):
            dirs[:] = []
            continue
            
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(rel_root, d) if rel_root != '.' else d, True, ignore_patterns)]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in DEFAULT_IGNORE_EXTS:
                continue

            full_path = os.path.abspath(os.path.join(root, file))
            rel_path = os.path.relpath(full_path, workspace_path)

            if is_ignored(rel_path, False, ignore_patterns):
                continue

            seen_paths.add(full_path)

            try:
                stat = os.stat(full_path)
                size_bytes = stat.st_size
                mtime_ns = stat.st_mtime_ns
            except Exception:
                continue

            existing = db_files.get(full_path)

            if existing and not force and existing["mtime_ns"] == mtime_ns:
                reused += 1
                continue

            try:
                with open(full_path, 'rb') as f:
                    content_bytes = f.read()
                content_hash = compute_hash(content_bytes)
                content_text = content_bytes.decode('utf-8', errors='ignore')
            except Exception:
                continue

            if existing and not force and existing["content_hash"] == content_hash:
                reused += 1
                continue

            symbols, raw_edges, parse_status, language = process_file_content(ext, content_text)
            indexed_at = time.strftime("%Y-%m-%d %H:%M:%S")

            if existing:
                file_id = existing["id"]
                cursor.execute("""
                UPDATE files SET relative_path=?, extension=?, size_bytes=?, mtime_ns=?, content_hash=?, language=?, parse_status=?, indexed_at=?
                WHERE id=?
                """, (rel_path, ext, size_bytes, mtime_ns, content_hash, language, parse_status, indexed_at, file_id))
                cursor.execute("DELETE FROM symbols WHERE file_id=?", (file_id,))
                cursor.execute("DELETE FROM symbol_edges WHERE source_file_id=?", (file_id,))
                changed += 1
            else:
                cursor.execute("""
                INSERT INTO files (path, relative_path, extension, size_bytes, mtime_ns, content_hash, language, parse_status, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (full_path, rel_path, ext, size_bytes, mtime_ns, content_hash, language, parse_status, indexed_at))
                file_id = cursor.lastrowid
                added += 1

            sym_id_map = {}
            for idx, sym in enumerate(symbols):
                cursor.execute("""
                INSERT INTO symbols (file_id, name, qualified_name, kind, parent_symbol, signature, start_line, end_line, start_byte, end_byte, visibility, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (file_id, sym["name"], sym["qualified_name"], sym["kind"], sym["parent_symbol"], sym["signature"], sym["start_line"], sym["end_line"], sym["start_byte"], sym["end_byte"], sym["visibility"], sym["content_hash"]))
                sym_id_map[idx] = cursor.lastrowid

                # DEFINES Edge (AST_EXACT, EXACT, 1.0)
                cursor.execute("""
                INSERT INTO symbol_edges (source_file_id, source_symbol_id, target_name, target_qualified_name, target_file, target_symbol_id, kind, line_number, resolution_status, evidence_source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (file_id, None, sym["name"], sym["qualified_name"], rel_path, sym_id_map[idx], "DEFINES", sym["start_line"], "EXACT", "AST_EXACT", 1.0))

            for edge in raw_edges:
                src_sym_id = sym_id_map.get(edge["source_symbol_idx"]) if edge["source_symbol_idx"] is not None else None
                cursor.execute("""
                INSERT INTO symbol_edges (source_file_id, source_symbol_id, target_name, target_qualified_name, target_file, target_symbol_id, kind, line_number, resolution_status, evidence_source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (file_id, src_sym_id, edge["target_name"], None, None, None, edge["kind"], edge["line_number"], "UNRESOLVED", "FALLBACK", 0.0))

    # Handle deleted files
    for db_path_key, db_info in db_files.items():
        if db_path_key not in seen_paths:
            cursor.execute("DELETE FROM symbol_edges WHERE source_file_id=?", (db_info["id"],))
            cursor.execute("DELETE FROM symbols WHERE file_id=?", (db_info["id"],))
            cursor.execute("DELETE FROM files WHERE id=?", (db_info["id"],))
            deleted += 1

    conn.commit()

    if added > 0 or changed > 0 or deleted > 0 or force:
        resolve_edges(conn)

    cursor.execute("SELECT count(*) FROM files")
    total_files = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM files WHERE parse_status='PARSED'")
    parsed_files = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM files WHERE parse_status='FALLBACK'")
    fallback_files = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM symbols")
    total_symbols = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM symbol_edges")
    total_edges = cursor.fetchone()[0]

    conn.close()

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "workspace": workspace_path,
        "files": total_files,
        "parsed": parsed_files,
        "fallback": fallback_files,
        "symbols": total_symbols,
        "edges": total_edges,
        "added": added,
        "changed": changed,
        "deleted": deleted,
        "reused": reused,
        "duration_ms": elapsed_ms
    }

def run_stats(workspace_path):
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    if not os.path.exists(db_path):
        return {"error": "Database not found. Run index first."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM files")
    total_files = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM files WHERE parse_status='PARSED'")
    parsed_files = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM files WHERE parse_status='FALLBACK'")
    fallback_files = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM symbols")
    total_symbols = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM symbol_edges")
    total_edges = cursor.fetchone()[0]

    cursor.execute("SELECT language, count(*) FROM files GROUP BY language")
    lang_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT MAX(indexed_at) FROM files")
    last_indexed = cursor.fetchone()[0] or "Never"

    conn.close()

    return {
        "workspace": workspace_path,
        "database": db_path,
        "files": total_files,
        "parsed": parsed_files,
        "fallback": fallback_files,
        "symbols": total_symbols,
        "edges": total_edges,
        "language_breakdown": lang_breakdown,
        "last_indexed": last_indexed
    }

def run_graph_stats(workspace_path):
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    if not os.path.exists(db_path):
        return {"error": "Database not found. Run index first."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM symbol_edges")
    total_edges = cursor.fetchone()[0]

    cursor.execute("SELECT kind, count(*) FROM symbol_edges GROUP BY kind")
    kind_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT resolution_status, count(*) FROM symbol_edges GROUP BY resolution_status")
    res_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT evidence_source, count(*) FROM symbol_edges GROUP BY evidence_source")
    prov_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT count(*) FROM symbol_edges WHERE resolution_status IN ('EXACT', 'HEURISTIC')")
    resolved_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM symbol_edges WHERE resolution_status = 'UNRESOLVED'")
    unresolved_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM symbol_edges WHERE resolution_status = 'EXTERNAL'")
    external_count = cursor.fetchone()[0]

    denom = total_edges - external_count
    res_rate = round((resolved_count / denom) * 100.0, 2) if denom > 0 else 100.0

    conn.close()

    return {
        "workspace": workspace_path,
        "total_edges": total_edges,
        "by_kind": kind_breakdown,
        "by_resolution_status": res_breakdown,
        "by_evidence_source": prov_breakdown,
        "resolved_count": resolved_count,
        "unresolved_count": unresolved_count,
        "external_count": external_count,
        "resolution_rate": res_rate
    }

def run_callers(workspace_path, target_query):
    t0 = time.time()
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    if not os.path.exists(db_path):
        return {"error": "Database not found. Run index first."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    pattern = f"%{target_query}%"
    cursor.execute("""
    SELECT e.id, f.relative_path, s.name, s.qualified_name, e.target_name, e.kind, e.line_number, e.resolution_status, e.evidence_source
    FROM symbol_edges e
    JOIN files f ON e.source_file_id = f.id
    LEFT JOIN symbols s ON e.source_symbol_id = s.id
    WHERE (e.target_name LIKE ? OR e.target_qualified_name LIKE ?) AND e.kind IN ('CALLS', 'REFERENCES')
    LIMIT 100
    """, (pattern, pattern))

    results = []
    for r in cursor.fetchall():
        results.append({
            "caller_file": r[1],
            "caller_symbol": r[2] or f"<file-level: {r[1]}>",
            "caller_qualified_name": r[3] or r[1],
            "target_name": r[4],
            "kind": r[5],
            "line_number": r[6],
            "resolution_status": r[7],
            "evidence_source": r[8]
        })

    conn.close()
    duration_ms = (time.time() - t0) * 1000

    return {
        "query": target_query,
        "total_callers": len(results),
        "query_time_ms": round(duration_ms, 3),
        "callers": results
    }

def run_callees(workspace_path, source_query):
    t0 = time.time()
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    if not os.path.exists(db_path):
        return {"error": "Database not found. Run index first."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    pattern = f"%{source_query}%"
    cursor.execute("""
    SELECT e.id, f.relative_path, s.name, e.target_name, e.target_qualified_name, e.target_file, e.kind, e.line_number, e.resolution_status, e.evidence_source
    FROM symbol_edges e
    JOIN files f ON e.source_file_id = f.id
    LEFT JOIN symbols s ON e.source_symbol_id = s.id
    WHERE (s.name LIKE ? OR s.qualified_name LIKE ? OR f.relative_path LIKE ?) AND e.kind IN ('CALLS', 'REFERENCES')
    LIMIT 100
    """, (pattern, pattern, pattern))

    results = []
    for r in cursor.fetchall():
        results.append({
            "source_file": r[1],
            "source_symbol": r[2] or f"<file-level: {r[1]}>",
            "target_name": r[3],
            "target_qualified_name": r[4] or r[3],
            "target_file": r[5] or "unknown",
            "kind": r[6],
            "line_number": r[7],
            "resolution_status": r[8],
            "evidence_source": r[9]
        })

    conn.close()
    duration_ms = (time.time() - t0) * 1000

    return {
        "query": source_query,
        "total_callees": len(results),
        "query_time_ms": round(duration_ms, 3),
        "callees": results
    }

def run_dependencies(workspace_path, target_query, depth=2):
    t0 = time.time()
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    if not os.path.exists(db_path):
        return {"error": "Database not found. Run index first."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    pattern = f"%{target_query}%"
    cursor.execute("""
    SELECT e.id, f.relative_path, s.name, e.target_name, e.target_file, e.kind, e.resolution_status, e.evidence_source
    FROM symbol_edges e
    JOIN files f ON e.source_file_id = f.id
    LEFT JOIN symbols s ON e.source_symbol_id = s.id
    WHERE f.relative_path LIKE ? OR s.name LIKE ? OR e.target_name LIKE ?
    LIMIT 100
    """, (pattern, pattern, pattern))

    edges = []
    for r in cursor.fetchall():
        edges.append({
            "source_file": r[1],
            "source_symbol": r[2] or r[1],
            "target_name": r[3],
            "target_file": r[4] or "unknown",
            "kind": r[5],
            "resolution_status": r[6],
            "evidence_source": r[7]
        })

    conn.close()
    duration_ms = (time.time() - t0) * 1000

    return {
        "query": target_query,
        "depth": depth,
        "total_edges": len(edges),
        "query_time_ms": round(duration_ms, 3),
        "dependencies": edges
    }

def run_symbols_query(workspace_path, query):
    t0 = time.time()
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    if not os.path.exists(db_path):
        return {"error": "Database not found. Run index first."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    pattern = f"%{query}%"
    cursor.execute("""
    SELECT s.name, s.qualified_name, s.kind, f.path, f.relative_path, s.start_line, s.end_line, s.signature
    FROM symbols s
    JOIN files f ON s.file_id = f.id
    WHERE s.name LIKE ? OR s.qualified_name LIKE ? OR f.relative_path LIKE ? OR f.path LIKE ?
    LIMIT 100
    """, (pattern, pattern, pattern, pattern))

    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "name": r[0],
            "qualified_name": r[1],
            "kind": r[2],
            "file": r[3],
            "relative_path": r[4],
            "start_line": r[5],
            "end_line": r[6],
            "signature": r[7]
        })

    conn.close()
    duration_ms = (time.time() - t0) * 1000

    return {
        "query": query,
        "total_results": len(results),
        "query_time_ms": round(duration_ms, 3),
        "symbols": results
    }

def run_file_inspect(workspace_path, rel_file_path):
    workspace_path = os.path.abspath(workspace_path)
    db_path = get_db_path(workspace_path)
    if not os.path.exists(db_path):
        return {"error": "Database not found. Run index first."}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    norm_rel = os.path.normpath(rel_file_path).replace('\\', '/')
    cursor.execute("""
    SELECT id, path, relative_path, language, parse_status, size_bytes
    FROM files
    WHERE relative_path = ? OR relative_path LIKE ? OR path LIKE ?
    """, (rel_file_path, f"%{norm_rel}", f"%{norm_rel}"))

    file_row = cursor.fetchone()
    if not file_row:
        conn.close()
        return {"error": f"File '{rel_file_path}' not found in index."}

    file_id = file_row[0]
    cursor.execute("""
    SELECT name, qualified_name, kind, signature, start_line, end_line
    FROM symbols
    WHERE file_id = ?
    ORDER BY start_line
    """, (file_id,))

    symbols = []
    for r in cursor.fetchall():
        symbols.append({
            "name": r[0],
            "qualified_name": r[1],
            "kind": r[2],
            "signature": r[3],
            "start_line": r[4],
            "end_line": r[5]
        })

    conn.close()

    return {
        "file": file_row[1],
        "relative_path": file_row[2],
        "language": file_row[3],
        "parse_status": file_row[4],
        "size_bytes": file_row[5],
        "est_tokens": estimate_tokens("x" * file_row[5]),
        "symbols_count": len(symbols),
        "symbols": symbols
    }

def format_compact_index_report(res):
    lines = [
        "TOKEN SAVER V5 INDEX",
        f"Files:       {res['files']:,}",
        f"Parsed:      {res['parsed']:,}",
        f"Fallback:    {res['fallback']:,}",
        f"Symbols:    {res['symbols']:,}",
        f"Edges:      {res.get('edges', 0):,}",
        f"Added:       {res['added']:,}",
        f"Changed:     {res['changed']:,}",
        f"Deleted:     {res['deleted']:,}",
        f"Reused:      {res['reused']:,}",
        f"Time:        {res['duration_ms'] / 1000:.2f}s"
    ]
    return "\n".join(lines)

def format_compact_stats_report(res):
    lines = [
        "TOKEN SAVER V5 STATS",
        f"Workspace:   {res['workspace']}",
        f"Database:    {res['database']}",
        f"Files:       {res['files']:,} (Parsed: {res['parsed']:,} | Fallback: {res['fallback']:,})",
        f"Symbols:     {res['symbols']:,}",
        f"Edges:       {res.get('edges', 0):,}",
        f"Indexed At:  {res['last_indexed']}",
        "\nLanguage Breakdown:"
    ]
    for lang, count in res.get('language_breakdown', {}).items():
        lines.append(f"  {lang:<12}: {count:,} files")
    return "\n".join(lines)

def format_compact_graph_stats_report(res):
    lines = [
        "TOKEN SAVER V5 GRAPH STATS",
        f"Total Edges:     {res['total_edges']:,}",
        f"Resolved Count:  {res['resolved_count']:,}",
        f"Unresolved Count:{res['unresolved_count']:,}",
        f"External Count:  {res['external_count']:,}",
        f"Resolution Rate: {res['resolution_rate']}%",
        "\nBy Kind:"
    ]
    for k, c in res.get('by_kind', {}).items():
        lines.append(f"  {k:<16}: {c:,}")
    lines.append("\nBy Resolution Status:")
    for r, c in res.get('by_resolution_status', {}).items():
        lines.append(f"  {r:<16}: {c:,}")
    lines.append("\nBy Evidence Source:")
    for p, c in res.get('by_evidence_source', {}).items():
        lines.append(f"  {p:<16}: {c:,}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="TokenSaver v5.0 Engine CLI")
    parser.add_argument("--version", action="version", version="TokenSaver v5.0.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    idx_p = subparsers.add_parser("index", help="Index workspace symbols and relationships")
    idx_p.add_argument("workspace", help="Target workspace path")
    idx_p.add_argument("--force", action="store_true", help="Force re-indexing all files")
    idx_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    graph_p = subparsers.add_parser("graph", help="Extract and build relationship graph")
    graph_p.add_argument("workspace", help="Target workspace path")
    graph_p.add_argument("--force", action="store_true", help="Force re-indexing all files")
    graph_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    stats_p = subparsers.add_parser("stats", help="Show workspace index statistics")
    stats_p.add_argument("workspace", help="Target workspace path")
    stats_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    gstats_p = subparsers.add_parser("graph-stats", help="Show relationship graph statistics")
    gstats_p.add_argument("workspace", help="Target workspace path")
    gstats_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    callers_p = subparsers.add_parser("callers", help="Find callers of a target symbol")
    callers_p.add_argument("workspace", help="Target workspace path")
    callers_p.add_argument("target", help="Target symbol query")
    callers_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    callees_p = subparsers.add_parser("callees", help="Find callees invoked by a symbol/file")
    callees_p.add_argument("workspace", help="Target workspace path")
    callees_p.add_argument("source", help="Source symbol or file query")
    callees_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    deps_p = subparsers.add_parser("dependencies", help="Find dependency graph neighborhood")
    deps_p.add_argument("workspace", help="Target workspace path")
    deps_p.add_argument("target", help="Target symbol or file query")
    deps_p.add_argument("--depth", type=int, default=2, help="Graph depth")
    deps_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    ret_p = subparsers.add_parser("retrieve", help="Run V5 adaptive evidence retrieval")
    ret_p.add_argument("workspace", help="Target workspace path")
    ret_p.add_argument("prompt", help="User task prompt")
    ret_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    metrics_p = subparsers.add_parser("metrics", help="Show deterministic V5 metrics")
    metrics_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    bench_p = subparsers.add_parser("benchmark", help="Run multi-task A/B benchmark")
    bench_p.add_argument("workspace", nargs="?", default=r"C:\tools", help="Target workspace path")
    bench_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    doc_p = subparsers.add_parser("doctor", help="Run diagnostic health checks")
    doc_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    sym_p = subparsers.add_parser("symbols", help="Query indexed symbols")
    sym_p.add_argument("workspace", help="Target workspace path")
    sym_p.add_argument("query", help="Symbol search query")
    sym_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    file_p = subparsers.add_parser("file", help="Inspect file symbols")
    file_p.add_argument("workspace", help="Target workspace path")
    file_p.add_argument("relative_path", help="Relative file path")
    file_p.add_argument("--json", action="store_true", help="Output JSON metrics")

    args = parser.parse_args()

    if args.command in ["index", "graph"]:
        res = run_index(args.workspace, args.force)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(format_compact_index_report(res))

    elif args.command == "stats":
        res = run_stats(args.workspace)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(format_compact_stats_report(res))

    elif args.command == "graph-stats":
        res = run_graph_stats(args.workspace)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(format_compact_graph_stats_report(res))

    elif args.command == "callers":
        res = run_callers(args.workspace, args.target)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            lines = [
                f"CALLERS: {res['query']}",
                "─" * 80,
                f"{'Symbol':<26} {'File':<26} {'Line':<8} {'Status':<10}",
                "─" * 80
            ]
            for c in res['callers']:
                lines.append(f"{c['caller_symbol']:<26} {c['caller_file']:<26} {c['line_number']:<8} {c['resolution_status']:<10}")
            if not res['callers']:
                lines.append("No callers found.")
            print("\n".join(lines))

    elif args.command == "callees":
        res = run_callees(args.workspace, args.source)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            lines = [
                f"CALLEES: {res['query']}",
                "─" * 80,
                f"{'Target Name':<26} {'Target File':<26} {'Line':<8} {'Status':<10}",
                "─" * 80
            ]
            for c in res['callees']:
                lines.append(f"{c['target_name']:<26} {c['target_file']:<26} {c['line_number']:<8} {c['resolution_status']:<10}")
            if not res['callees']:
                lines.append("No callees found.")
            print("\n".join(lines))

    elif args.command == "dependencies":
        res = run_dependencies(args.workspace, args.target, args.depth)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            lines = [
                f"DEPENDENCIES: {res['query']} [Depth: {res['depth']}]",
                "─" * 80,
                f"{'Source':<24} {'Target':<24} {'Kind':<10} {'Status':<10}",
                "─" * 80
            ]
            for d in res['dependencies']:
                lines.append(f"{d['source_symbol']:<24} {d['target_name']:<24} {d['kind']:<10} {d['resolution_status']:<10}")
            if not res['dependencies']:
                lines.append("No dependencies found.")
            print("\n".join(lines))

    elif args.command == "retrieve":
        import tokensaver_v5_engine as eng
        res = eng.run_v5_pipeline(args.prompt, args.workspace)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(res.get("payload", res.get("reason", "Skipped")))

    elif args.command == "metrics":
        import tokensaver_v5_metrics as met
        m = met.get_last_metrics()
        if args.json:
            print(json.dumps(m, indent=2))
        else:
            print("TOKEN SAVER V5 METRICS REPORT")
            print("=" * 50)
            for k, v in m.items():
                print(f"{k:<30}: {v}")

    elif args.command == "benchmark":
        import tokensaver_v5_benchmark as bm
        res = bm.run_v5_benchmark(args.workspace)
        if args.json:
            print(json.dumps(res, indent=2))

    elif args.command == "doctor":
        import tokensaver_v5_doctor as doc
        res = doc.run_doctor()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("TOKENSAVER DOCTOR REPORT")
            print("=" * 45)
            for component, status in res["checks"].items():
                print(f"{component:<22}: {status}")
            print("=" * 45)
            print(f"Overall Status        : {res['status']}")

    elif args.command == "symbols":
        res = run_symbols_query(args.workspace, args.query)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            lines = [
                f"TOKEN SAVER V5 SYMBOLS [Query: \"{res['query']}\"]",
                "─" * 80,
                f"{'Symbol':<26} {'Kind':<12} {'File':<30} {'Line Range':<10}",
                "─" * 80
            ]
            for s in res['symbols']:
                lines.append(f"{s['name']:<26} {s['kind']:<12} {s['relative_path']:<30} L{s['start_line']}-L{s['end_line']}")
            if not res['symbols']:
                lines.append("No matching symbols found.")
            print("\n".join(lines))

    elif args.command == "file":
        res = run_file_inspect(args.workspace, args.relative_path)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if "error" in res:
                print(res["error"])
            else:
                print(f"TOKEN SAVER V5 FILE [Path: {res['relative_path']}]")
                print(f"Language:     {res['language']} ({res['parse_status']})")
                print(f"Size:         {res['size_bytes']:,} bytes ({res['est_tokens']:,} est. tokens)")
                print(f"Symbols:      {res['symbols_count']:,}")
                print("─" * 80)
                print(f"{'Symbol':<26} {'Kind':<12} {'Line Range':<12} {'Signature'}")
                print("─" * 80)
                for s in res['symbols']:
                    print(f"{s['name']:<26} {s['kind']:<12} L{s['start_line']}-L{s['end_line']:<6} {s['signature']}")

if __name__ == "__main__":
    main()
