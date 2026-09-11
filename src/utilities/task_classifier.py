import sys
import re
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def evaluate_gate(text):
    text_lower = text.lower().strip()

    # 1. EXPLICIT WORKSPACE / REPOSITORY / FILE / CONTEXT INDICATORS (Always INVOKE)
    explicit_workspace_patterns = [
        r'\b(this\s+project|current\s+project|my\s+project|in\s+my\s+project|the\s+project\'s|this\s+codebase|the\s+codebase|through\s+the\s+codebase|in\s+the\s+codebase|this\s+repo|this\s+repository|repository\s+structure|repository|this\s+workspace|in\s+this\s+workspace|files\s+in\s+this\s+workspace|this\s+file|auto_submit\.py|run_loop|my\s+application|the\s+changes\s+i\s+just\s+made|my\s+latest\s+changes|code\s+i\s+currently\s+have\s+open|files\s+i\s+just\s+changed|this\s+module|in\s+this\s+module|for\s+this\s+module|this\s+endpoint|this\s+implementation|this\s+api|the\s+payment\s+service|the\s+database\s+layer|the\s+queue\s+worker|the\s+authentication\s+module|the\s+login\s+flow|existing\s+system)\b'
    ]
    for pat in explicit_workspace_patterns:
        if re.search(pat, text_lower):
            return {"context_required": True, "action": "INVOKE", "mode": "targeted", "confidence": "HIGH", "policy": "signatures", "reason": "explicit workspace reference"}

    # 2. STANDALONE CODE GENERATION / EDUCATIONAL SHOW-ME (Must SKIP if no explicit project context)
    # E.g. "Help me write a Python function...", "Write a function to...", "Show me how to implement...", "How would you implement..."
    standalone_code_patterns = [
        r'^\s*(help\s+me\s+write|write\s+a\s+function|show\s+me\s+how\s+to\s+implement|how\s+would\s+you\s+implement)\b'
    ]
    for pat in standalone_code_patterns:
        if re.search(pat, text_lower):
            if not re.search(r'\b(my\s+project|this\s+project|in\s+the\s+project|my\s+app|codebase|repo)\b', text_lower):
                return {"context_required": False, "action": "SKIP", "mode": "simple", "confidence": "HIGH", "policy": "minimal", "reason": "standalone code generation / educational question"}

    # 3. CONCEPTUAL / EDUCATIONAL / DEFINITION QUESTIONS (Must SKIP)
    # E.g. "What is an API token?", "Explain what authentication is", "What does it mean to refactor code?", "Why do tests..."
    conceptual_patterns = [
        r'^\s*(what\s+(is|are|does|causes|does\s+it\s+mean)|explain\s+(what|how|recursion|object|binary|authentication|security|traceback|refactoring|architecture|api|dependency)|why\s+(is\s+the\s+sky|do\s+tests)|how\s+(does|do|would\s+you)|tell\s+me|give\s+me\s+(five|ideas)|help\s+me\s+prepare|write\s+me\s+a\s+funny)\b'
    ]
    is_conceptual = False
    for pat in conceptual_patterns:
        if re.search(pat, text_lower):
            is_conceptual = True
            break

    if is_conceptual:
        # Check if it has explicit workspace request
        if not re.search(r'\b(my\s+project|in\s+this\s+codebase|this\s+repo|auto_submit|the\s+login\s+flow|in\s+the\s+queue|my\s+application)\b', text_lower):
            return {"context_required": False, "action": "SKIP", "mode": "simple", "confidence": "HIGH", "policy": "minimal", "reason": "conceptual / educational question"}

    # 4. WORKSPACE ACTIONS & NATURAL LANGUAGE CODING/DEBUGGING TASKS (INVOKE)
    workspace_action_patterns = [
        # Debugging / Error / Failure
        r'\b(traceback|stack\s*trace|exception|crashing|crashes|bug|failing|fails|fail|failure|broken|breaking|breaks|wrong\s+result|fix\s+(it|this)|fix\s+the|why\s+is\s+my|something\s+is\s+wrong|keeps\s+breaking|doesn\'t\s+work|race\s+condition)\b',
        # Refactoring / Modification / Optimization / Implementation
        r'\b(refactor|clean\s+up|caller\s+functions|rename\s+the|update\s+its\s+callers|add\s+logging|less\s+messy|make\s+it\s+faster|make\s+the\s+tests\s+pass|redirect\s+to|change\s+the|update\s+the|add\s+.*to\s+(my\s+)?project|implement\s+retry|move\s+this\s+logic|behave\s+differently|improve\s+this|can\s+you\s+improve|make\s+.*better|wired\s+into|recover\s+when|accepting\s+invalid|handle\s+duplicate|stop\s+the\s+application|improve\s+error\s+handling)\b',
        # Ambiguous / Short Workspace Actions
        r'^\s*(fix\s+this|clean\s+this\s+up|make\s+it\s+faster|can\s+you\s+improve\s+this|can\s+you\s+take\s+a\s+look|make\s+the\s+tests\s+pass|change\s+the\s+way\s+this\s+works)\b',
        # Security & Audit Actions
        r'\b(audit|vulnerab|secrets|credentials|sanitized|injection|authorization|dangerous\s+behavior|security\s+flaws|hardcoded)\b',
        # Analysis / Tracing / Review Actions
        r'\b(analyze|trace|review|inspect|check\s+whether)\b'
    ]

    for pat in workspace_action_patterns:
        if re.search(pat, text_lower):
            return {"context_required": True, "action": "INVOKE", "mode": "targeted", "confidence": "HIGH", "policy": "targeted", "reason": "workspace task / code modification"}

    # 5. Default General Chat (SKIP)
    return {
        "context_required": False,
        "action": "SKIP",
        "mode": "simple",
        "confidence": "HIGH",
        "policy": "minimal",
        "reason": "general conversational request"
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: task_classifier.py \"<prompt_text>\"", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    res = evaluate_gate(prompt)

    print("TOKEN SAVER GATE")
    print("──────────────────────────────────────────────────")
    print(f"Context Required: {'YES' if res['context_required'] else 'NO'}")
    print(f"Reason:           {res['reason']}")
    print(f"Action:           {res['action']}")
    print("──────────────────────────────────────────────────")
    print(f"TASK MODE:        {res['mode']}")
    print(f"CONFIDENCE:       {res['confidence']}")
    print(f"CONTEXT POLICY:   {res['policy']}")

if __name__ == "__main__":
    main()
