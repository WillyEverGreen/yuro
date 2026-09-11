import sys
import os
import re
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_WEIGHTS = {
    "target_file": 100,
    "traceback_file": 90,
    "mentioned_symbol": 80,
    "direct_import": 60,
    "related_symbol": 40,
    "unrelated_file": 0
}

def load_relevance_weights():
    config_path = r"C:\tools\token-save.config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("relevance_weights", DEFAULT_WEIGHTS)
        except Exception:
            pass
    return DEFAULT_WEIGHTS

def score_file_relevance(filepath, prompt_text, traceback_files=None, target_files=None):
    weights = load_relevance_weights()
    score = 0
    reasons = []

    filename = os.path.basename(filepath)
    filename_no_ext = os.path.splitext(filename)[0]

    if target_files and filepath in target_files:
        score += weights["target_file"]
        reasons.append("target_file (+100)")

    if traceback_files and any(tb in filepath for tb in traceback_files):
        score += weights["traceback_file"]
        reasons.append("traceback_file (+90)")

    if filename_no_ext.lower() in prompt_text.lower() or filename.lower() in prompt_text.lower():
        score += weights["mentioned_symbol"]
        reasons.append("mentioned_symbol (+80)")

    # Read file content for direct import or symbol match
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(2048) # Read first 2KB
            if "import " in content or "require(" in content:
                score += weights["direct_import"]
                reasons.append("direct_import (+60)")
        except Exception:
            pass

    return score, reasons

def filter_relevant_files(directory, prompt_text, min_score=30):
    traceback_files = re.findall(r'[\w\/\\]+\.(?:py|ts|js|go|cs)', prompt_text)
    results = []

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'dist', 'build']]
        for file in files:
            if file.endswith(('.py', '.ts', '.js', '.go', '.rs', '.cs', '.java', '.json', '.cmd', '.ps1')):
                fp = os.path.join(root, file)
                score, reasons = score_file_relevance(fp, prompt_text, traceback_files)
                if score >= min_score:
                    results.append({"path": fp, "score": score, "reasons": reasons})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def main():
    if len(sys.argv) < 3:
        print("Usage: relevance_engine.py <directory> \"<prompt_text>\"", file=sys.stderr)
        sys.exit(1)

    directory = sys.argv[1]
    prompt = " ".join(sys.argv[2:])
    scored = filter_relevant_files(directory, prompt)

    print(f"RELEVANCE SCORE AUDIT FOR: '{directory}'")
    print("--------------------------------------------------")
    for item in scored:
        print(f"  Score: {item['score']:<3} | Path: {item['path']} ({', '.join(item['reasons'])})")

if __name__ == "__main__":
    main()
