import sys
import os
import json
import re
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def deduplicate_logs(text):
    lines = text.split('\n')
    cleaned = []
    prev_line = None
    repeat_count = 0

    for line in lines:
        stripped = line.strip()
        if stripped == prev_line and stripped != "":
            repeat_count += 1
        else:
            if repeat_count > 0:
                cleaned.append(f"  [... Repeated {repeat_count} times ...]")
                repeat_count = 0
            cleaned.append(line)
            prev_line = stripped

    if repeat_count > 0:
        cleaned.append(f"  [... Repeated {repeat_count} times ...]")

    return "\n".join(cleaned)

def collapse_stack_frames(text):
    lines = text.split('\n')
    cleaned = []
    frame_pattern = re.compile(r'^\s*at\s+.*|^\s*File\s+".*",\s*line\s+\d+')
    
    seen_frames = set()
    dup_counter = 0

    for line in lines:
        if frame_pattern.match(line):
            key = line.strip()
            if key in seen_frames:
                dup_counter += 1
                continue
            else:
                seen_frames.add(key)
                if dup_counter > 0:
                    cleaned.append(f"  [... Collapsed {dup_counter} duplicate stack frame(s) ...]")
                    dup_counter = 0
                cleaned.append(line)
        else:
            if dup_counter > 0:
                cleaned.append(f"  [... Collapsed {dup_counter} duplicate stack frame(s) ...]")
                dup_counter = 0
            cleaned.append(line)

    if dup_counter > 0:
        cleaned.append(f"  [... Collapsed {dup_counter} duplicate stack frame(s) ...]")

    return "\n".join(cleaned)

def prune_json(text, mode="safe"):
    try:
        data = json.loads(text)
    except Exception:
        return text, 0

    removed_keys_count = 0

    def clean_obj(obj):
        nonlocal removed_keys_count
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                if mode == "aggressive" and (v is None or v == "" or (isinstance(v, list) and len(v) == 0)):
                    removed_keys_count += 1
                    continue
                new_dict[k] = clean_obj(v)
            return new_dict
        elif isinstance(obj, list):
            return [clean_obj(item) for item in obj]
        return obj

    cleaned = clean_obj(data)
    minified = json.dumps(cleaned, separators=(',', ':'))
    return minified, removed_keys_count

def normalize_whitespace(text):
    # Reduce 3+ consecutive blank lines to 1
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip trailing whitespace on lines
    lines = [line.rstrip() for line in text.split('\n')]
    return "\n".join(lines)

def process_structural_prune(text, mode="safe"):
    step1 = deduplicate_logs(text)
    step2 = collapse_stack_frames(step1)
    step3 = normalize_whitespace(step2)

    removed_json_keys = 0
    if step3.strip().startswith('{') or step3.strip().startswith('['):
        step3, removed_json_keys = prune_json(step3, mode)

    return step3, removed_json_keys

def main():
    parser = argparse.ArgumentParser(description="Structural Context Pruner")
    parser.add_argument("path", help="Input file path")
    parser.add_argument("--mode", choices=["safe", "aggressive"], default="safe", help="Pruning mode")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: File '{args.path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    pruned, removed_count = process_structural_prune(content, args.mode)
    print(pruned)
    if args.mode == "aggressive" and removed_count > 0:
        print(f"\n// [TokenSaver Structural Pruner: Removed {removed_count} null/empty JSON keys (--aggressive)]", file=sys.stderr)

if __name__ == "__main__":
    main()
