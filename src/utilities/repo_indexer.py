import sys
import os
import re
import json
import hashlib
import time
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CACHE_DIR = r"C:\tools\.tokensaver-cache"

def get_cache_path(directory):
    os.makedirs(CACHE_DIR, exist_ok=True)
    dir_hash = hashlib.md5(directory.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"index_{dir_hash}.json")

def extract_symbols_from_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return {}

    classes = re.findall(r'\bclass\s+([A-Za-z0-9_]+)', content)
    functions = re.findall(r'\b(?:def|function|fn|pub fn)\s+([A-Za-z0-9_]+)', content)
    interfaces = re.findall(r'\binterface\s+([A-Za-z0-9_]+)', content)
    types = re.findall(r'\btype\s+([A-Za-z0-9_]+)', content)
    imports = re.findall(r'\b(?:import|from|require)\b[^\n]+', content)

    return {
        "classes": list(set(classes)),
        "functions": list(set(functions)),
        "interfaces": list(set(interfaces)),
        "types": list(set(types)),
        "imports": imports[:10]
    }

def index_repository(directory, force_reindex=False):
    start_time = time.time()
    cache_file = get_cache_path(directory)
    
    cached_data = {}
    if not force_reindex and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
        except Exception:
            cached_data = {}

    file_index = cached_data.get("files", {})
    reparsed_count = 0
    reused_count = 0

    current_files = {}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'dist', 'build', '.tokensaver-cache']]
        for file in files:
            if file.endswith(('.py', '.ts', '.js', '.go', '.rs', '.cs', '.java', '.cpp', '.h', '.ps1', '.cmd')):
                fp = os.path.join(root, file)
                try:
                    stat = os.stat(fp)
                    mtime = stat.st_mtime
                    size = stat.st_size
                except Exception:
                    continue

                rel_path = os.path.relpath(fp, directory)

                if rel_path in file_index and file_index[rel_path].get("mtime") == mtime and file_index[rel_path].get("size") == size:
                    current_files[rel_path] = file_index[rel_path]
                    reused_count += 1
                else:
                    symbols = extract_symbols_from_file(fp)
                    current_files[rel_path] = {
                        "path": fp,
                        "mtime": mtime,
                        "size": size,
                        "symbols": symbols
                    }
                    reparsed_count += 1

    index_payload = {
        "directory": directory,
        "updated_at": time.time(),
        "total_files": len(current_files),
        "files": current_files
    }

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(index_payload, f, indent=2)
    except Exception:
        pass

    elapsed_ms = round((time.time() - start_time) * 1000, 1)

    return {
        "total_files": len(current_files),
        "reparsed": reparsed_count,
        "reused": reused_count,
        "elapsed_ms": elapsed_ms,
        "index_file": cache_file
    }

def main():
    parser = argparse.ArgumentParser(description="Incremental Repository Symbol Indexer")
    parser.add_argument("path", help="Target repository directory")
    parser.add_argument("--force", action="store_true", help="Force full re-index")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Directory '{args.path}' not found.", file=sys.stderr)
        sys.exit(1)

    res = index_repository(args.path, args.force)
    print("INCREMENTAL REPOSITORY INDEX REPORT")
    print("--------------------------------------------------")
    print(f"Target Directory: {args.path}")
    print(f"Total Files:      {res['total_files']}")
    print(f"Files Reparsed:   {res['reparsed']} (Modified / New)")
    print(f"Files Reused:     {res['reused']} (Cached)")
    print(f"Indexing Latency: {res['elapsed_ms']} ms")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
