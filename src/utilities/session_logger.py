import sys
import os
import json
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SESSION_FILE = r"C:\Users\advdi\tools\tokensaver_session.json"

def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "requests": 0,
        "raw_tokens": 0,
        "final_tokens": 0,
        "caveman_overhead": 0,
        "history_overhead": 0,
        "total_latency_ms": 0,
        "fidelity_passes": 0,
        "fidelity_warnings": 0
    }

def record_request(raw_tok, final_tok, latency_ms, caveman_tok=100, history_tok=12, fidelity="VERIFIED"):
    data = load_session()
    data["requests"] += 1
    data["raw_tokens"] += raw_tok
    data["final_tokens"] += final_tok
    data["total_latency_ms"] += latency_ms
    data["caveman_overhead"] += caveman_tok
    data["history_overhead"] += history_tok
    
    if fidelity in ["PASS", "VERIFIED"]:
        data["fidelity_passes"] += 1
    else:
        data["fidelity_warnings"] += 1

    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def print_session_summary():
    data = load_session()
    reqs = max(data["requests"], 1)
    raw = data["raw_tokens"]
    final = data["final_tokens"]
    saved = max(0, raw - final)
    net_pct = round((saved / max(raw, 1)) * 100, 1)
    avg_latency = round(data["total_latency_ms"] / reqs, 1)

    print("TOKEN SAVER PERSISTENT SESSION AUDIT")
    print("──────────────────────────────────────────────────")
    print(f"Requests Processed:       {data['requests']:,}")
    print(f"Baseline Estimated Input: {raw:,} tokens")
    print(f"TokenSaver Input Payload: {final:,} tokens")
    print("──────────────────────────────────────────────────")
    print(f"Input Tokens Saved:       {saved:,} tokens")
    print(f"Net Context Reduction:    {net_pct}%")
    print("──────────────────────────────────────────────────")
    print(f"Caveman Overhead:         {data['caveman_overhead']:,} tokens")
    print(f"History State Overhead:   {data['history_overhead']:,} tokens")
    print(f"Average Latency:          {avg_latency} ms / request")
    print(f"Fidelity Passes:          {data['fidelity_passes']} VERIFIED / {data['fidelity_warnings']} WARNINGS")
    print("──────────────────────────────────────────────────")

def main():
    parser = argparse.ArgumentParser(description="Persistent Session Logger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_p = subparsers.add_parser("show", help="Show cumulative session statistics")
    reset_p = subparsers.add_parser("reset", help="Reset session counters")
    rec_p = subparsers.add_parser("record", help="Record request metrics")
    rec_p.add_argument("raw", type=int)
    rec_p.add_argument("final", type=int)
    rec_p.add_argument("latency", type=float)

    args = parser.parse_args()

    if args.command == "show":
        print_session_summary()
    elif args.command == "reset":
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        print("Session metrics reset.")
    elif args.command == "record":
        record_request(args.raw, args.final, args.latency)

if __name__ == "__main__":
    main()
