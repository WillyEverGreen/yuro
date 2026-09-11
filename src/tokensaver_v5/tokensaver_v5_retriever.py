import os
import sys
import sqlite3
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if r'C:\tools' not in sys.path:
    sys.path.append(r'C:\tools')
import tokensaver_v5_symbol_index as idx

def retrieve_evidence(workspace_path, evidence_plan):
    workspace_path = os.path.abspath(workspace_path)
    db_path = idx.get_db_path(workspace_path)
    
    if not os.path.exists(db_path):
        idx.run_index(workspace_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    retrieved_units = []
    seen_unit_keys = set()

    def add_unit(file_path, rel_path, symbol_id, symbol_name, symbol_kind, start_line, end_line, signature, unit_type, confidence, provenance, level=1):
        key = (rel_path, symbol_name, start_line, end_line, unit_type)
        if key not in seen_unit_keys:
            seen_unit_keys.add(key)
            retrieved_units.append({
                "file": file_path,
                "relative_path": rel_path,
                "symbol_id": symbol_id,
                "symbol_name": symbol_name,
                "symbol_kind": symbol_kind,
                "start_line": start_line,
                "end_line": end_line,
                "signature": signature,
                "unit_type": unit_type,
                "confidence": confidence,
                "provenance": provenance,
                "level": level
            })

    targets = evidence_plan.get("extracted_targets", [])
    depth = evidence_plan.get("graph_depth", 1)
    target_lvl = evidence_plan.get("target_level", 2)

    # 1. Exact Target Symbols & Direct Definitions
    for target in targets:
        cursor.execute("""
        SELECT s.id, f.path, f.relative_path, s.name, s.kind, s.start_line, s.end_line, s.signature
        FROM symbols s
        JOIN files f ON s.file_id = f.id
        WHERE s.name = ? OR s.qualified_name LIKE ?
        """, (target, f"%{target}%"))
        
        for r in cursor.fetchall():
            add_unit(r[1], r[2], r[0], r[3], r[4], r[5], r[6], r[7], "TARGET_SYMBOL", 1.0, "AST_EXACT", level=target_lvl)

    # 2. Callers & Callees via Graph Edges
    for target in targets:
        # Callers
        cursor.execute("""
        SELECT s.id, f.path, f.relative_path, s.name, s.kind, s.start_line, s.end_line, s.signature, e.resolution_status, e.evidence_source
        FROM symbol_edges e
        JOIN files f ON e.source_file_id = f.id
        LEFT JOIN symbols s ON e.source_symbol_id = s.id
        WHERE (e.target_name = ? OR e.target_qualified_name LIKE ?) AND e.kind IN ('CALLS', 'REFERENCES')
        LIMIT 20
        """, (target, f"%{target}%"))
        for r in cursor.fetchall():
            sym_name = r[3] or f"<file: {r[2]}>"
            add_unit(r[1], r[2], r[0], sym_name, r[4] or "file", r[5] or 1, r[6] or 1, r[7] or sym_name, "CALLER", 0.9, r[9], level=1)

        # Callees
        cursor.execute("""
        SELECT s.id, f.path, f.relative_path, s.name, s.kind, s.start_line, s.end_line, s.signature, e.resolution_status, e.evidence_source
        FROM symbol_edges e
        JOIN files f ON e.source_file_id = f.id
        LEFT JOIN symbols s ON e.source_symbol_id = s.id
        WHERE (s.name = ? OR s.qualified_name LIKE ?) AND e.kind IN ('CALLS', 'REFERENCES')
        LIMIT 20
        """, (target, f"%{target}%"))
        for r in cursor.fetchall():
            sym_name = r[3] or f"<file: {r[2]}>"
            add_unit(r[1], r[2], r[0], sym_name, r[4] or "file", r[5] or 1, r[6] or 1, r[7] or sym_name, "CALLEE", 0.9, r[9], level=1)

    # 3. Imports & Inheritance
    for target in targets:
        cursor.execute("""
        SELECT e.target_name, e.target_file, e.kind, e.resolution_status, e.evidence_source
        FROM symbol_edges e
        JOIN files f ON e.source_file_id = f.id
        LEFT JOIN symbols s ON e.source_symbol_id = s.id
        WHERE (s.name = ? OR f.relative_path LIKE ?) AND e.kind IN ('IMPORTS', 'INHERITS_FROM')
        LIMIT 20
        """, (target, f"%{target}%"))
        for r in cursor.fetchall():
            add_unit("unknown", r[1] or "unknown", None, r[0], r[2].lower(), 1, 1, f"{r[2]}: {r[0]}", r[2], 0.8, r[4], level=0)

    # 4. Overview Map fallback if empty
    if not retrieved_units:
        cursor.execute("""
        SELECT s.id, f.path, f.relative_path, s.name, s.kind, s.start_line, s.end_line, s.signature
        FROM symbols s
        JOIN files f ON s.file_id = f.id
        LIMIT 30
        """)
        for r in cursor.fetchall():
            add_unit(r[1], r[2], r[0], r[3], r[4], r[5], r[6], r[7], "MAP_OVERVIEW", 0.5, "FALLBACK", level=0)

    conn.close()
    return retrieved_units

if __name__ == "__main__":
    from tokensaver_v5_evidence_planner import create_evidence_plan
    plan = create_evidence_plan("debug", "Fix run_index in tokensaver_v5_symbol_index.py")
    units = retrieve_evidence(sys.argv[1] if len(sys.argv) > 1 else ".", plan)
    print(json.dumps({"total_units": len(units), "units": units[:5]}, indent=2))
