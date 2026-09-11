import sys
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tokensaver.core.engine import run_v6_pipeline

def run_ablation_suite(workspace_path: str = "."):
    prompt = "Fix run_index in tokensaver_v5_symbol_index.py"
    print("==================================================")
    print("TOKENSAVER V6 ABLATION SUITE REPORT")
    print("==================================================")

    # Full v6 pipeline
    res_full = run_v6_pipeline(prompt, workspace_path)
    print(f"Full v6 Pipeline:")
    print(f"  Raw: {res_full.get('raw_context_tokens')} | Selected: {res_full.get('selected_context_tokens')} | Net: {res_full.get('net_saved_tokens')} ({res_full.get('net_saved_percent')}%)")
    print("==================================================")

if __name__ == "__main__":
    run_ablation_suite(sys.argv[1] if len(sys.argv) > 1 else ".")
