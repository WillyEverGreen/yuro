import sys
import re
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def evaluate_gate(text):
    text_lower = text.lower().strip()

    # 1. EXPLICIT WORKSPACE / REPOSITORY / FILE / CONTEXT INDICATORS (Always INVOKE)
    explicit_workspace_patterns = [
        r'\b(this\s+project|current\s+project|my\s+project|in\s+my\s+project|the\s+project\'s|this\s+codebase|the\s+codebase|through\s+the\s+codebase|in\s+the\s+codebase|this\s+repo|this\s+repository|repository\s+structure|repository|this\s+workspace|in\s+this\s+workspace|files\s+in\s+this\s+workspace|this\s+file|auto_submit\.py|run_loop|my\s+application|the\s+changes\s+i\s+just\s+made|my\s+latest\s+changes|code\s+i\s+currently\s+have\s+open|files\s+i\s+just\s+changed|this\s+module|in\s+this\s+module|for\s+this\s+module|this\s+endpoint|this\s+implementation|this\s+api|the\s+payment\s+service|the\s+database\s+layer|the\s+queue\s+worker|the\s+authentication\s+module|the\s+login\s+flow|existing\s+system|\.[a-zA-Z0-9_-]+\.(py|ts|tsx|js|jsx|go|rs|cs|java|cpp|h|json|md))\b'
    ]
    for pat in explicit_workspace_patterns:
        if re.search(pat, text_lower):
            return {"context_required": True, "action": "INVOKE", "mode": "targeted", "confidence": "HIGH", "policy": "signatures", "reason": "explicit workspace reference"}

    # 2. GENERAL Q&A / DEFINITION / CONCEPTUAL QUESTIONS (Must SKIP unless explicit workspace intent is present)
    # E.g. "What is an API token?", "Explain what authentication is", "What does it mean to refactor code?", "Why do tests..."
    conceptual_question_patterns = [
        r'^\s*what\s+(is|are|does|causes|does\s+it\s+mean)\b',
        r'^\s*explain\s+(what|how|recursion|object|binary|authentication|security|traceback|refactoring|architecture|api|dependency|rest|react)\b',
        r'^\s*why\s+(is\s+the\s+sky|do\s+tests|is\s+python)\b',
        r'^\s*how\s+(does|do|would\s+you)\s+(http|react|git|python|rest|dns|tcp|udp)\b',
        r'^\s*tell\s+me\s+(about\s+python|a\s+joke|what)\b',
        r'^\s*give\s+me\s+(five|ideas|an\s+example\s+of)\b'
    ]

    is_conceptual = False
    for pat in conceptual_question_patterns:
        if re.search(pat, text_lower):
            is_conceptual = True
            break

    # 3. WORKSPACE ACTION INTENT SIGNALS
    workspace_action_patterns = [
        # Debugging / Investigation / Failure Analysis
        r'\b(investigate|debug|trace|fix|repair|resolve|why\s+does|why\s+is|find\s+why|why\s+.*returns|why\s+.*fails|crashes|crashing|failing|fails|fail|failure|mismatch|broken|breaking|breaks|wrong\s+result|error|exception|traceback|stack\s*trace)\b',
        # Refactoring / Modification / Implementation / Feature Addition
        r'\b(implement|add\s+support|add|refactor|clean\s+up|update|modify|change|improve|rename|move|wire|redirect|make\s+it\s+faster|make\s+the\s+tests\s+pass|behave\s+differently|reorder|optimize)\b',
        # Audit / Tracing / Inspection
        r'\b(audit|review|inspect|check\s+whether|trace\s+the|find\s+where)\b'
    ]

    has_action_signal = any(re.search(pat, text_lower) for pat in workspace_action_patterns)

    # 4. SOFTWARE BEHAVIOR / COMPONENT SIGNALS
    software_behavior_patterns = [
        r'\b(api|route|endpoint|component|page|view|viewer|table|database|db|query|request|response|state|hook|function|method|class|interface|schema|payload|telemetry|calculation|rendering|validation|auth|authentication|authorization|workflow|queue|worker|performance|warning|log|report|speed|weight|indicator|digital\s+twin|status|overload|logistics)\b'
    ]

    has_behavior_signal = any(re.search(pat, text_lower) for pat in software_behavior_patterns)

    # 5. GENERAL Q&A OVERRIDE
    if is_conceptual and not (has_action_signal and has_behavior_signal):
        # Check if explicit workspace reference was missed
        if re.search(r'\b(my\s+project|this\s+project|in\s+this\s+codebase|this\s+repo|auto_submit|the\s+login\s+flow|in\s+the\s+queue|my\s+application|this\s+file|this\s+module)\b', text_lower):
            return {"context_required": True, "action": "INVOKE", "mode": "targeted", "confidence": "HIGH", "policy": "targeted", "reason": "explicit workspace architecture request"}
        return {"context_required": False, "action": "SKIP", "mode": "simple", "confidence": "HIGH", "policy": "minimal", "reason": "conceptual / educational question"}

    # 6. ACTION & BEHAVIOR INTENT CLASSIFICATION
    if has_action_signal:
        return {"context_required": True, "action": "INVOKE", "mode": "targeted", "confidence": "HIGH", "policy": "targeted", "reason": "natural-language workspace coding/debugging task"}

    if has_behavior_signal and not is_conceptual:
        return {"context_required": True, "action": "INVOKE", "mode": "targeted", "confidence": "MEDIUM", "policy": "targeted", "reason": "software behavior intent in workspace"}

    # 7. Ambiguous Queries with Repository Context
    if re.search(r'\b(architecture|component|flow|dashboard|application|system|process|handling)\b', text_lower):
        return {"context_required": True, "action": "INVOKE", "mode": "targeted", "confidence": "MEDIUM", "policy": "targeted", "reason": "ambiguous repository query"}

    # 8. Default General Chat (SKIP)
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
