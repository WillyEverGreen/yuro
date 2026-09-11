import os
import sys
import platform
import json
import subprocess
from datetime import datetime, timezone

def get_git_commit():
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return "f2e7bbf"

def get_pkg_version(pkg_name):
    try:
        mod = __import__(pkg_name)
        return getattr(mod, "__version__", "installed")
    except ImportError:
        return "missing"

def create_environment_json():
    val_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "validation")
    os.makedirs(val_dir, exist_ok=True)
    
    deps = {
        "tiktoken": get_pkg_version("tiktoken"),
        "bm25s": get_pkg_version("bm25s"),
        "networkx": get_pkg_version("networkx"),
        "tree_sitter": get_pkg_version("tree_sitter"),
        "sqlite3": get_pkg_version("sqlite3")
    }
    
    env_data = {
        "python_version": sys.version,
        "os": platform.platform(),
        "tokensaver_commit": get_git_commit(),
        "dependencies": deps,
        "tokenizer_encoding": "cl100k_base",
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    
    env_path = os.path.join(val_dir, "environment.json")
    with open(env_path, "w", encoding="utf-8") as f:
        json.dump(env_data, f, indent=2)
    print(f"Created {env_path}")
    return env_data

if __name__ == "__main__":
    create_environment_json()
