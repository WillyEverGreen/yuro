import sys
import os
import re
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def extract_python_signatures(content, mode="plan", traceback_targets=None):
    import ast
    try:
        tree = ast.parse(content)
    except Exception:
        return fallback_regex_signatures(content, mode)

    lines = content.split('\n')

    class SignatureVisitor(ast.NodeVisitor):
        def __init__(self):
            self.extracted_ranges = []

        def visit_FunctionDef(self, node):
            self.record_func(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.record_func(node)
            self.generic_visit(node)

        def record_func(self, node):
            header = lines[node.lineno - 1]
            docstring = ast.get_docstring(node)
            indent = " " * (len(header) - len(header.lstrip()))
            
            sig = f"{header.strip()}"
            if not sig.endswith(":"):
                sig += ":"

            # Mode handling logic
            if mode in ["plan", "architecture"]:
                body_summary = f"{indent}    \"\"\"{docstring}\"\"\"\n{indent}    ..." if docstring else f"{indent}    ..."
                self.extracted_ranges.append((node.lineno, node.end_lineno, f"{indent}{sig}\n{body_summary}"))
            elif mode == "debug":
                # In debug mode, if function name matches traceback targets, keep full body!
                is_target = traceback_targets and any(t.lower() in node.name.lower() for t in traceback_targets)
                if not is_target:
                    body_summary = f"{indent}    \"\"\"{docstring}\"\"\"\n{indent}    ..." if docstring else f"{indent}    ..."
                    self.extracted_ranges.append((node.lineno, node.end_lineno, f"{indent}{sig}\n{body_summary}"))

    visitor = SignatureVisitor()
    visitor.visit(tree)

    if not visitor.extracted_ranges:
        return content

    skip_until = -1
    result = []
    for idx, line in enumerate(lines, 1):
        matching_range = next((r for r in visitor.extracted_ranges if r[0] == idx), None)
        if matching_range:
            result.append(matching_range[2])
            skip_until = matching_range[1]
        elif idx > skip_until:
            result.append(line)

    return "\n".join(result)

def fallback_regex_signatures(content, mode="plan"):
    if mode in ["implement", "security", "full"]:
        return content

    lines = content.split('\n')
    result = []
    in_function = False

    for line in lines:
        stripped = line.strip()
        if re.match(r'^(export\s+)?(async\s+)?(def|class|function|interface|type|enum|struct|pub\s+fn)\b', stripped):
            result.append(line)
            in_function = True
            indent_level = len(line) - len(line.lstrip())
            result.append(" " * (indent_level + 4) + "...")
        elif re.match(r'^(import|from|require|using|package|include)\b', stripped):
            result.append(line)
        elif not stripped:
            result.append("")

    return "\n".join(result)

def process_file(filepath, mode="plan", traceback_targets=None):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        return ""

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if mode in ["implement", "security", "full"]:
        return content

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".py":
        return extract_python_signatures(content, mode, traceback_targets)
    else:
        return fallback_regex_signatures(content, mode)

def main():
    parser = argparse.ArgumentParser(description="Task-Aware Code Signature Extractor (code-sig)")
    parser.add_argument("mode", choices=["plan", "architecture", "debug", "refactor", "implement", "security", "full"], help="Task mode")
    parser.add_argument("path", help="File or directory path")
    parser.add_argument("--targets", nargs="*", help="Target function or traceback symbols for debug mode")
    args = parser.parse_args()

    if os.path.isfile(args.path):
        sig = process_file(args.path, args.mode, args.targets)
        print(f"// --- [code-sig: {args.mode}] {args.path} ---")
        print(sig)
    elif os.path.isdir(args.path):
        for root, dirs, files in os.walk(args.path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'dist', 'build']]
            for file in files:
                if file.endswith(('.py', '.ts', '.js', '.go', '.rs', '.cs', '.java', '.cpp', '.h')):
                    fp = os.path.join(root, file)
                    sig = process_file(fp, args.mode, args.targets)
                    print(f"\n// --- [code-sig: {args.mode}] {fp} ---")
                    print(sig)

if __name__ == "__main__":
    main()
