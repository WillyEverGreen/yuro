import os
import sys
from typing import List, Dict, Any
from tokensaver.evidence.compressor import safe_compress_code_body

def read_file_line_range(file_path: str, start_line: int, end_line: int) -> str:
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

def assemble_evidence(
    workspace_path: str,
    selected_units: List[Dict[str, Any]],
    user_prompt: str,
    task_type: str,
    enable_compression: bool = True
) -> Dict[str, Any]:
    workspace_path = os.path.abspath(workspace_path)

    sections = {
        "TARGETS": [],
        "CALLERS": [],
        "CALLEES": [],
        "DEPENDENCIES": [],
        "REFERENCES": [],
        "MAP": []
    }

    compression_applied_count = 0

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

            if enable_compression and abs_path and abs_path.endswith('.py'):
                compressed_body, meta = safe_compress_code_body(body_code, language="python")
                if meta.get("applied"):
                    compression_applied_count += 1
                body_code = compressed_body

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
        f"TOKEN SAVER V6 SELECTED EVIDENCE [{task_type.upper()}]",
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
        "total_units_emitted": len(selected_units),
        "compression_applied_count": compression_applied_count
    }
