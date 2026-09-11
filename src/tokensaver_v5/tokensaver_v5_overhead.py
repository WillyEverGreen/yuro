import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def estimate_tokens(text):
    if not text:
        return 0
    return int(len(text) / 3.8)

def compute_net_economics(raw_text, selected_payload, overhead_text=""):
    raw_tokens = estimate_tokens(raw_text)
    selected_tokens = estimate_tokens(selected_payload)
    overhead_tokens = estimate_tokens(overhead_text)

    gross_saved = max(0, raw_tokens - selected_tokens)
    net_saved = gross_saved - overhead_tokens
    net_percent = round((net_saved / raw_tokens) * 100.0, 2) if raw_tokens > 0 else 0.0

    net_positive = net_saved > 0

    return {
        "raw_context_tokens": raw_tokens,
        "selected_context_tokens": selected_tokens,
        "gross_saved_tokens": gross_saved,
        "tokensaver_overhead_tokens": overhead_tokens,
        "net_saved_tokens": net_saved,
        "net_saved_percent": net_percent,
        "net_positive": net_positive
    }

if __name__ == "__main__":
    raw = "def foo():\n" * 1000
    sel = "def foo():\n" * 100
    ovh = "[TOKEN SAVER HEADER]\n"
    print(json.dumps(compute_net_economics(raw, sel, ovh), indent=2))
