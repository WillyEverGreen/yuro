"""
TokenSaver CLI Python Entrypoint (PEP 508 / setuptools compatible).
"""
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import importlib.util

spec = importlib.util.spec_from_file_location("token_save_impl", os.path.join(SCRIPT_DIR, "token-save.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["token_save_impl"] = mod
spec.loader.exec_module(mod)

main = mod.main

if __name__ == "__main__":
    main()
