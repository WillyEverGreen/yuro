import os
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def read_file_line_range(file_path, start_line, end_line):
    if not file_path or not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        s_idx = max(0, start_line - 1)
        e_idx = min(len(lines), end_line)
        return "".join(lines[s_idx:e_idx]).strip()
    except Exception:
        return ""

def assemble_evidence(workspace_path, selected_units, user_prompt, task_type):
    workspace_path = os.path.abspath(workspace_path)
    
    sections = {
        "TARGETS": [],
        "CALLERS": [],
        "CALLEES": [],
        "DEPENDENCIES": [],
        "REFERENCES": [],
        "MAP": []
    }

    for unit in selected_units:
        rel_path = unit.get("relative_path", "unknown")
        s_name = unit.get("symbol_name", "unknown")
        s_kind = unit.get("symbol_kind", "symbol")
        start_line = unit.get("start_line", 1)
        end_line = unit.get("end_line", 1)
        signature = unit.get("signature", "")
        level = unit.get("level", 1)
        unit_type = unit.get("unit_type", "MAP_OVERVIEW")
        abs_path = unit.get("file")

        line_str = f"L{start_line}" if start_line == end_line else f"L{start_line}-L{end_line}"

        if level == 0:
            entry = f"• [{s_kind.upper()}] {s_name} ({rel_path}:{line_str})"
        elif level == 1:
            entry = f"• [{s_kind.upper()}] {s_name} ({rel_path}:{line_str})\n  Signature: {signature}"
        else:
            body_code = read_file_line_range(abs_path, start_line, end_line) if abs_path else signature
            if not body_code:
                body_code = signature
            entry = f"• [{s_kind.upper()}] {s_name} ({rel_path}:{line_str})\n```\n{body_code}\n```"

        if unit_type == "TARGET_SYMBOL":
            sections["TARGETS"].append(entry)
        elif unit_type == "CALLER":
            sections["CALLERS"].append(entry)
        elif unit_type == "CALLEE":
            sections["CALLEES"].append(entry)
        elif unit_type in ["IMPORTS", "INHERITS_FROM"]:
            sections["DEPENDENCIES"].append(entry)
        elif unit_type == "REFERENCES":
            sections["REFERENCES"].append(entry)
        else:
            sections["MAP"].append(entry)

    out_lines = [
        "==================================================",
        f"TOKEN SAVER V5 SELECTED EVIDENCE [{task_type.upper()}]",
        "=================================================="
    ]

    for sec_name, items in sections.items():
        if items:
            out_lines.append(f"\n--- {sec_name} ---")
            out_lines.extend(items)

    out_lines.append("\n==================================================")
    
    final_payload = "\n".join(out_lines)
    return {
        "payload": final_payload,
        "sections": {k: len(v) for k, v in sections.items()},
        "total_units_emitted": len(selected_units)
    }

if __name__ == "__main__":
    test_units = [
        {"relative_path": "tokensaver_v5_symbol_index.py", "symbol_name": "run_index", "symbol_kind": "function", "start_line": 350, "end_line": 355, "signature": "def run_index():", "level": 2, "unit_type": "TARGET_SYMBOL"},
        {"relative_path": "tokensaver_v5_symbol_index.py", "symbol_name": "init_db", "symbol_kind": "function", "start_line": 70, "end_line": 75, "signature": "def init_db():", "level": 1, "unit_type": "CALLEE"}
    ]
    res = assemble_evidence(".", test_units, "Fix run_index", "debug")
    print(res["payload"])
