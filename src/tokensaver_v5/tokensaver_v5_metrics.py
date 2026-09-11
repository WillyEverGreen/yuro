import os
import sys
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

METRICS_CACHE_FILE = r"C:\tools\.tokensaver-cache\v5_metrics.json"

def record_v5_run(metrics_data):
    os.makedirs(os.path.dirname(METRICS_CACHE_FILE), exist_ok=True)
    metrics_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(METRICS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2)
    except Exception:
        pass
    return metrics_data

def get_last_metrics():
    if not os.path.exists(METRICS_CACHE_FILE):
        return {"status": "No metrics recorded yet."}
    try:
        with open(METRICS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if "--json" in sys.argv:
        print(json.dumps(get_last_metrics(), indent=2))
    else:
        m = get_last_metrics()
        print("TOKEN SAVER V5 METRICS REPORT")
        print("=" * 50)
        for k, v in m.items():
            print(f"{k:<30}: {v}")
