import sys
import os
import json
import hashlib
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DELTA_FILE = r"C:\tools\.tokensaver-cache\last_context_delta.json"

def compute_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def check_context_delta(content_text):
    os.makedirs(os.path.dirname(DELTA_FILE), exist_ok=True)
    curr_hash = compute_hash(content_text)

    prev_hash = None
    if os.path.exists(DELTA_FILE):
        try:
            with open(DELTA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                prev_hash = data.get("hash")
        except Exception:
            pass

    is_unchanged = (prev_hash == curr_hash)

    # Save new hash
    try:
        with open(DELTA_FILE, "w", encoding="utf-8") as f:
            json.dump({"hash": curr_hash, "updated_at": os.path.getmtime(DELTA_FILE) if os.path.exists(DELTA_FILE) else 0}, f)
    except Exception:
        pass

    return {
        "is_unchanged": is_unchanged,
        "current_hash": curr_hash[:8],
        "previous_hash": prev_hash[:8] if prev_hash else None
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: delta_tracker.py <filepath>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        res = check_context_delta(text)
        print(f"DELTA STATUS: Unchanged={res['is_unchanged']} | CurrHash={res['current_hash']} | PrevHash={res['previous_hash']}")

if __name__ == "__main__":
    main()
