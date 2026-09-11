import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(REPO_ROOT, "src")
UTIL_DIR = os.path.join(SRC_DIR, "utilities")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from task_classifier import evaluate_gate

class TestAdmissionGateGeneralization(unittest.TestCase):

    def test_natural_language_tasks(self):
        natural_language_prompts = [
            ("Investigate why total wagon weight calculation and overload status warning mismatch across the fleet monitor and pdf report", "INVOKE"),
            ("Investigate how generateSingleWagonBpcPdf works, identify its dependencies and callers, and explain the most likely failure points.", "INVOKE"),
            ("Add support for filtering wagons by telemetry speed range in logistics telemetry table and updating aggregate statistics", "INVOKE"),
            ("Analyze RakeDetails and determine what other parts of this repository would be affected if this symbol were refactored.", "INVOKE"),
            ("Trace the implementation of live wagon tracking and camera stream monitoring across this repository and identify the smallest set of files and symbols that must be understood to modify it safely.", "INVOKE"),
            ("Find why Estimator API route returns NaN when payloadWeight is omitted or zero", "INVOKE"),
            ("Implement dynamic speed limit compliance indicator inside Digital Twin 3D wagon viewer", "INVOKE"),
            ("Audit security and authentication area and identify all relevant authentication, authorization, credential, and sanitization paths.", "INVOKE"),
            ("Explain this project's architecture, identify the major components, and describe how the main execution flow moves between them.", "INVOKE"),
            ("What is the difference between TCP and UDP?", "SKIP")
        ]

        for prompt, expected_action in natural_language_prompts:
            res = evaluate_gate(prompt)
            self.assertEqual(
                res["action"],
                expected_action,
                f"Failed for coding prompt: '{prompt}' (got {res['action']}, expected {expected_action})"
            )

    def test_must_run_natural_language_coding_tasks(self):
        must_run = [
            "Fix a bug in the payment flow.",
            "Investigate why users are logged out.",
            "Add filtering to the telemetry dashboard.",
            "Refactor the PDF generation logic.",
            "Trace how authentication requests flow through the application.",
            "Why does this API return 500?",
            "Implement retry handling for failed requests."
        ]
        for prompt in must_run:
            res = evaluate_gate(prompt)
            self.assertEqual(res["action"], "INVOKE", f"Should RUN for: '{prompt}'")

    def test_must_skip_general_qna(self):
        must_skip = [
            "What is an API?",
            "Explain Python decorators.",
            "What is React?",
            "How does HTTP work?",
            "What does dependency injection mean?",
            "What is a binary tree?",
            "Explain REST architecture."
        ]
        for prompt in must_skip:
            res = evaluate_gate(prompt)
            self.assertEqual(res["action"], "SKIP", f"Should SKIP for: '{prompt}'")

    def test_ambiguous_repository_queries(self):
        ambiguous = [
            "How does the application handle errors?",
            "Tell me about the dashboard.",
            "Explain the project architecture.",
            "Why is this slow?"
        ]
        for prompt in ambiguous:
            res = evaluate_gate(prompt)
            self.assertEqual(res["action"], "INVOKE", f"Should RUN (medium confidence) for ambiguous query: '{prompt}'")

    def test_classifier_metrics(self):
        test_dataset = [
            # (prompt, is_true_workspace_task)
            ("Fix a bug in the payment flow", True),
            ("Investigate why users are logged out", True),
            ("Add filtering to telemetry table", True),
            ("Refactor the PDF generation logic", True),
            ("Find why Estimator API route returns NaN", True),
            ("Implement dynamic speed limit indicator", True),
            ("Investigate why total wagon weight calculation mismatches", True),
            ("Trace authentication requests through application", True),
            ("What is an API?", False),
            ("Explain Python decorators", False),
            ("What is React?", False),
            ("How does HTTP work?", False),
            ("What does dependency injection mean?", False),
            ("What is a binary tree?", False),
            ("Explain REST architecture", False)
        ]

        tp = fp = fn = tn = 0
        for prompt, is_workspace in test_dataset:
            res = evaluate_gate(prompt)
            admitted = (res["action"] == "INVOKE")
            if is_workspace and admitted:
                tp += 1
            elif not is_workspace and admitted:
                fp += 1
            elif is_workspace and not admitted:
                fn += 1
            else:
                tn += 1

        precision = tp / max(1, (tp + fp))
        recall = tp / max(1, (tp + fn))

        print(f"\n--- ADMISSION GATE CLASSIFIER METRICS ---")
        print(f"True Positives (TP):  {tp}")
        print(f"False Positives (FP): {fp}")
        print(f"False Negatives (FN): {fn}")
        print(f"True Negatives (TN):  {tn}")
        print(f"Workspace Precision:  {precision:.2%}")
        print(f"Workspace Recall:     {recall:.2%}")
        print(f"----------------------------------------\n")

        self.assertEqual(fn, 0, "Workspace recall must be 100% (zero false negatives on workspace tasks)")
        self.assertEqual(fp, 0, "General Q&A precision must be 100% (zero false positives on general questions)")

if __name__ == "__main__":
    unittest.main()
