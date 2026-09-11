import sys
import os
import json
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

STATE_FILE = r"C:\Users\advdi\tools\history_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "provenance": {
            "decisions": [],
            "constraints": [],
            "errors": [],
            "commands_run": []
        },
        "state": {
            "goal": "",
            "files": [],
            "current_state": "",
            "open_issues": [],
            "next_action": ""
        }
    }

def save_state(data):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def append_provenance(category, value, source="agent"):
    data = load_state()
    if category in data["provenance"]:
        entry = {"value": value, "source": source}
        if entry not in data["provenance"][category]:
            data["provenance"][category].append(entry)
            save_state(data)
            print(f"Recorded provenance [{category}]: {value}")

def update_active_state(key, value):
    data = load_state()
    if key in data["state"]:
        data["state"][key] = value
        save_state(data)
        print(f"Updated active state [{key}]: {value}")

def render_selective_context(task_type="code"):
    # Selective injection rule: simple tasks skip history injection completely
    if task_type in ["simple", "format", "rename"]:
        return ""

    data = load_state()
    st = data.get("state", {})
    prov = data.get("provenance", {})

    lines = []
    if st.get("goal"):
        lines.append(f"Goal: {st['goal']}")
    if st.get("current_state"):
        lines.append(f"State: {st['current_state']}")
    if st.get("files"):
        lines.append(f"Files: {', '.join(st['files'])}")
    if prov.get("constraints"):
        const_vals = [c['value'] for c in prov['constraints']]
        lines.append(f"Constraints: {'; '.join(const_vals)}")

    if not lines:
        return ""

    return "// [TokenSaver Selective History Context]\n" + "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Persistent State History Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # set-state command
    set_parser = subparsers.add_parser("set", help="Set active state field")
    set_parser.add_argument("key", choices=["goal", "files", "current_state", "open_issues", "next_action"])
    set_parser.add_argument("value")

    # record-prov command
    prov_parser = subparsers.add_parser("add", help="Append immutable provenance entry")
    prov_parser.add_argument("category", choices=["decisions", "constraints", "errors", "commands_run"])
    prov_parser.add_argument("value")

    # render command
    render_parser = subparsers.add_parser("render", help="Render selective context for prompt")
    render_parser.add_argument("--task", default="code", choices=["simple", "code", "architecture", "debug"])

    args = parser.parse_args()

    if args.command == "set":
        val = args.value.split(",") if args.key == "files" else args.value
        update_active_state(args.key, val)
    elif args.command == "add":
        append_provenance(args.category, args.value)
    elif args.command == "render":
        ctx = render_selective_context(args.task)
        if ctx:
            print(ctx)

if __name__ == "__main__":
    main()
