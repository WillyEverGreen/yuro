"""
Adaptive TokenSaver Gate — Comprehensive Test Suite
====================================================

Purpose:
    Validate that the Adaptive Gate:
      1. SKIPs TokenSaver for genuinely normal conversation.
      2. INVOKES TokenSaver for workspace/repository tasks.
      3. Uses conservative INVOKE behavior for ambiguous coding requests.
      4. Does not rely incorrectly on individual topic keywords.
      5. Handles security/debugging/implementation tasks safely.
      6. Detects workspace intent even when wording is indirect.

Expected policy:
    GENERAL       -> SKIP
    WORKSPACE     -> INVOKE
    AMBIGUOUS     -> INVOKE (conservative)

Run:
    py C:\tools\test_adaptive_gate.py

The test assumes:
    C:\tools\task_classifier.py
exists and prints:
    Action: INVOKE
or:
    Action: SKIP
"""

import subprocess
import sys
import re
from dataclasses import dataclass

import os

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
local_classifier = os.path.join(repo_root, "src", "utilities", "task_classifier.py")
CLASSIFIER = local_classifier if os.path.exists(local_classifier) else r"C:\tools\task_classifier.py"


@dataclass
class TestCase:
    category: str
    prompt: str
    expected: str
    description: str


# ============================================================
# TEST DATA
# ============================================================

TESTS = [

    # --------------------------------------------------------
    # 1. PURE GENERAL CHAT
    # --------------------------------------------------------

    TestCase(
        "GENERAL",
        "What's the difference between TCP and UDP?",
        "SKIP",
        "General networking knowledge",
    ),

    TestCase(
        "GENERAL",
        "Explain recursion in simple terms.",
        "SKIP",
        "General programming concept",
    ),

    TestCase(
        "GENERAL",
        "What is dependency injection?",
        "SKIP",
        "General software concept",
    ),

    TestCase(
        "GENERAL",
        "Tell me a joke.",
        "SKIP",
        "Casual conversation",
    ),

    TestCase(
        "GENERAL",
        "Give me five startup ideas.",
        "SKIP",
        "Brainstorming",
    ),

    TestCase(
        "GENERAL",
        "What's the difference between REST and GraphQL?",
        "SKIP",
        "General technical knowledge",
    ),

    TestCase(
        "GENERAL",
        "Explain binary search with an example.",
        "SKIP",
        "General educational question",
    ),

    TestCase(
        "GENERAL",
        "What is a hash table?",
        "SKIP",
        "General educational question",
    ),

    TestCase(
        "GENERAL",
        "Why is the sky blue?",
        "SKIP",
        "Non-coding general knowledge",
    ),

    TestCase(
        "GENERAL",
        "Help me prepare for my exam.",
        "SKIP",
        "General assistance",
    ),

    TestCase(
        "GENERAL",
        "Write me a funny birthday message.",
        "SKIP",
        "Creative writing",
    ),

    TestCase(
        "GENERAL",
        "Explain object oriented programming.",
        "SKIP",
        "General programming education",
    ),

    TestCase(
        "GENERAL",
        "What are the advantages of Rust?",
        "SKIP",
        "General technology question",
    ),

    TestCase(
        "GENERAL",
        "Give me ideas for a portfolio project.",
        "SKIP",
        "Idea generation, no workspace requested",
    ),

    TestCase(
        "GENERAL",
        "How does HTTPS work?",
        "SKIP",
        "General security knowledge",
    ),


    # --------------------------------------------------------
    # 2. CLEAR WORKSPACE / CODING TASKS
    # --------------------------------------------------------

    TestCase(
        "WORKSPACE",
        "Analyze this project's architecture.",
        "INVOKE",
        "Explicit project architecture",
    ),

    TestCase(
        "WORKSPACE",
        "Analyze the repository structure.",
        "INVOKE",
        "Explicit repository analysis",
    ),

    TestCase(
        "WORKSPACE",
        "Refactor the authentication module.",
        "INVOKE",
        "Codebase refactoring",
    ),

    TestCase(
        "WORKSPACE",
        "Find why the tests are failing.",
        "INVOKE",
        "Workspace debugging",
    ),

    TestCase(
        "WORKSPACE",
        "Fix the bug in the login flow.",
        "INVOKE",
        "Workspace bug fixing",
    ),

    TestCase(
        "WORKSPACE",
        "Review this repository for security issues.",
        "INVOKE",
        "Repository security review",
    ),

    TestCase(
        "WORKSPACE",
        "Add an email validation function to my project.",
        "INVOKE",
        "Explicit project modification",
    ),

    TestCase(
        "WORKSPACE",
        "Implement retry logic in the queue worker.",
        "INVOKE",
        "Implementation task",
    ),

    TestCase(
        "WORKSPACE",
        "Update the API client in this project.",
        "INVOKE",
        "Project modification",
    ),

    TestCase(
        "WORKSPACE",
        "Change the login flow so expired sessions redirect to /login.",
        "INVOKE",
        "Implicit implementation task",
    ),

    TestCase(
        "WORKSPACE",
        "Clean up the caller functions for this module.",
        "INVOKE",
        "Refactoring",
    ),

    TestCase(
        "WORKSPACE",
        "Explain how auto_submit.py works.",
        "INVOKE",
        "Specific workspace file",
    ),

    TestCase(
        "WORKSPACE",
        "Explain this file.",
        "INVOKE",
        "Workspace file reference",
    ),

    TestCase(
        "WORKSPACE",
        "Trace the authentication flow through the codebase.",
        "INVOKE",
        "Codebase tracing",
    ),

    TestCase(
        "WORKSPACE",
        "Find all callers of run_loop().",
        "INVOKE",
        "Symbol-level repository analysis",
    ),

    TestCase(
        "WORKSPACE",
        "Rename the process_order function and update its callers.",
        "INVOKE",
        "Refactoring",
    ),

    TestCase(
        "WORKSPACE",
        "Add logging to the payment service.",
        "INVOKE",
        "Code modification",
    ),

    TestCase(
        "WORKSPACE",
        "Run the project's tests and fix the failures.",
        "INVOKE",
        "Testing + debugging",
    ),

    TestCase(
        "WORKSPACE",
        "Review the changes I just made.",
        "INVOKE",
        "Workspace change review",
    ),

    TestCase(
        "WORKSPACE",
        "Check whether this implementation introduces a race condition.",
        "INVOKE",
        "Implementation-level analysis",
    ),


    # --------------------------------------------------------
    # 3. DEBUGGING
    # --------------------------------------------------------

    TestCase(
        "DEBUG",
        "Why is my application crashing?",
        "INVOKE",
        "Likely workspace debugging",
    ),

    TestCase(
        "DEBUG",
        "Find the cause of this exception.",
        "INVOKE",
        "Debugging",
    ),

    TestCase(
        "DEBUG",
        "The test runner throws an error. Fix it.",
        "INVOKE",
        "Test debugging",
    ),

    TestCase(
        "DEBUG",
        "This function returns the wrong result. Find the bug.",
        "INVOKE",
        "Code debugging",
    ),

    TestCase(
        "DEBUG",
        "The server crashes after login.",
        "INVOKE",
        "Application debugging",
    ),

    TestCase(
        "DEBUG",
        "Why does the database connection keep failing?",
        "INVOKE",
        "Likely project debugging",
    ),

    TestCase(
        "DEBUG",
        "Investigate this traceback and fix the root cause.",
        "INVOKE",
        "Explicit traceback debugging",
    ),

    TestCase(
        "DEBUG",
        "The build broke after my latest changes.",
        "INVOKE",
        "Workspace build debugging",
    ),


    # --------------------------------------------------------
    # 4. SECURITY — MUST BE CONSERVATIVE
    # --------------------------------------------------------

    TestCase(
        "SECURITY",
        "Audit this repository for vulnerabilities.",
        "INVOKE",
        "Security audit",
    ),

    TestCase(
        "SECURITY",
        "Check the authentication implementation for security flaws.",
        "INVOKE",
        "Authentication security review",
    ),

    TestCase(
        "SECURITY",
        "Look for hardcoded secrets in the project.",
        "INVOKE",
        "Secret scanning",
    ),

    TestCase(
        "SECURITY",
        "Review how credentials are handled in this codebase.",
        "INVOKE",
        "Credential handling",
    ),

    TestCase(
        "SECURITY",
        "Check whether user input is safely sanitized.",
        "INVOKE",
        "Input validation security",
    ),

    TestCase(
        "SECURITY",
        "Find potential SQL injection vulnerabilities in this project.",
        "INVOKE",
        "Security analysis",
    ),

    TestCase(
        "SECURITY",
        "Review the authorization logic.",
        "INVOKE",
        "Authorization security",
    ),

    TestCase(
        "SECURITY",
        "Check this API for authentication vulnerabilities.",
        "INVOKE",
        "API security",
    ),


    # --------------------------------------------------------
    # 5. AMBIGUOUS — CONSERVATIVE INVOKE
    # --------------------------------------------------------

    TestCase(
        "AMBIGUOUS",
        "Help me write a Python function that validates an email address.",
        "SKIP",
        "Standalone code generation; no project context",
    ),

    TestCase(
        "AMBIGUOUS",
        "Write a function to parse JSON.",
        "SKIP",
        "Standalone coding help",
    ),

    TestCase(
        "AMBIGUOUS",
        "Show me how to implement a binary search.",
        "SKIP",
        "Standalone educational implementation",
    ),

    TestCase(
        "AMBIGUOUS",
        "How would you implement authentication?",
        "SKIP",
        "Conceptual question",
    ),

    TestCase(
        "AMBIGUOUS",
        "Add an email validation function to my project.",
        "INVOKE",
        "Explicit project context",
    ),

    TestCase(
        "AMBIGUOUS",
        "Make the login behavior better.",
        "INVOKE",
        "Implicit workspace modification",
    ),

    TestCase(
        "AMBIGUOUS",
        "Change the way this works.",
        "INVOKE",
        "Implicit workspace modification",
    ),

    TestCase(
        "AMBIGUOUS",
        "Can you improve this?",
        "INVOKE",
        "Ambiguous workspace request; conservative",
    ),

    TestCase(
        "AMBIGUOUS",
        "Fix this.",
        "INVOKE",
        "Ambiguous but likely workspace task",
    ),

    TestCase(
        "AMBIGUOUS",
        "Make it faster.",
        "INVOKE",
        "Likely code optimization",
    ),

    TestCase(
        "AMBIGUOUS",
        "Make the tests pass.",
        "INVOKE",
        "Likely workspace debugging",
    ),

    TestCase(
        "AMBIGUOUS",
        "Clean this up.",
        "INVOKE",
        "Likely workspace refactoring",
    ),


    # --------------------------------------------------------
    # 6. KEYWORD FALSE-POSITIVE TESTS
    # --------------------------------------------------------

    TestCase(
        "FALSE_POSITIVE",
        "Explain what an authentication system is.",
        "SKIP",
        "General concept, not repository task",
    ),

    TestCase(
        "FALSE_POSITIVE",
        "What is a security vulnerability?",
        "SKIP",
        "General security education",
    ),

    TestCase(
        "FALSE_POSITIVE",
        "Explain what a traceback is.",
        "SKIP",
        "General debugging concept",
    ),

    TestCase(
        "FALSE_POSITIVE",
        "What is refactoring?",
        "SKIP",
        "General programming concept",
    ),

    TestCase(
        "FALSE_POSITIVE",
        "What does architecture mean in software?",
        "SKIP",
        "General concept",
    ),

    TestCase(
        "FALSE_POSITIVE",
        "What is an API token?",
        "SKIP",
        "General knowledge",
    ),

    TestCase(
        "FALSE_POSITIVE",
        "Why do tests sometimes fail?",
        "SKIP",
        "General educational question",
    ),

    TestCase(
        "FALSE_POSITIVE",
        "Explain how login systems normally work.",
        "SKIP",
        "General explanation",
    ),


    # --------------------------------------------------------
    # 7. KEYWORD FALSE-NEGATIVE TESTS
    # --------------------------------------------------------

    TestCase(
        "FALSE_NEGATIVE",
        "Change the login flow so expired sessions redirect to /login.",
        "INVOKE",
        "No explicit 'project' keyword",
    ),

    TestCase(
        "FALSE_NEGATIVE",
        "Make the checkout process handle duplicate payments.",
        "INVOKE",
        "Implicit implementation",
    ),

    TestCase(
        "FALSE_NEGATIVE",
        "Stop the application from sending duplicate emails.",
        "INVOKE",
        "Implicit bug fix",
    ),

    TestCase(
        "FALSE_NEGATIVE",
        "Improve error handling around the database layer.",
        "INVOKE",
        "Implicit codebase modification",
    ),

    TestCase(
        "FALSE_NEGATIVE",
        "Make this module work with the new API.",
        "INVOKE",
        "Workspace modification",
    ),

    TestCase(
        "FALSE_NEGATIVE",
        "Move this logic into a helper.",
        "INVOKE",
        "Refactoring without keyword",
    ),

    TestCase(
        "FALSE_NEGATIVE",
        "Stop this endpoint from accepting invalid input.",
        "INVOKE",
        "Implementation/security task",
    ),

    TestCase(
        "FALSE_NEGATIVE",
        "Make the worker recover when the connection drops.",
        "INVOKE",
        "Implementation/debugging",
    ),


    # --------------------------------------------------------
    # 8. ADVERSARIAL / NATURAL LANGUAGE
    # --------------------------------------------------------

    TestCase(
        "ADVERSARIAL",
        "I don't understand why this thing keeps breaking.",
        "INVOKE",
        "Natural-language debugging",
    ),

    TestCase(
        "ADVERSARIAL",
        "Something is wrong with the login stuff.",
        "INVOKE",
        "Implicit debugging",
    ),

    TestCase(
        "ADVERSARIAL",
        "Can you take a look and tell me what's going on?",
        "INVOKE",
        "Ambiguous workspace request",
    ),

    TestCase(
        "ADVERSARIAL",
        "Can you make this code less messy?",
        "INVOKE",
        "Natural-language refactoring",
    ),

    TestCase(
        "ADVERSARIAL",
        "I want this feature to behave differently.",
        "INVOKE",
        "Implicit modification",
    ),

    TestCase(
        "ADVERSARIAL",
        "Something changed and now the app doesn't work.",
        "INVOKE",
        "Natural-language debugging",
    ),

    TestCase(
        "ADVERSARIAL",
        "Can you check whether we introduced any dangerous behavior?",
        "INVOKE",
        "Security/review intent",
    ),

    TestCase(
        "ADVERSARIAL",
        "I need this wired into the existing system.",
        "INVOKE",
        "Explicit existing-system context",
    ),


    # --------------------------------------------------------
    # 9. NORMAL CHAT CONTAINING CODING KEYWORDS
    # --------------------------------------------------------

    TestCase(
        "KEYWORD_CHAT",
        "What does it mean to refactor code?",
        "SKIP",
        "Keyword but conceptual",
    ),

    TestCase(
        "KEYWORD_CHAT",
        "Explain authentication to a beginner.",
        "SKIP",
        "Keyword but educational",
    ),

    TestCase(
        "KEYWORD_CHAT",
        "What causes a traceback?",
        "SKIP",
        "Keyword but conceptual",
    ),

    TestCase(
        "KEYWORD_CHAT",
        "What is a security audit?",
        "SKIP",
        "Keyword but conceptual",
    ),

    TestCase(
        "KEYWORD_CHAT",
        "Explain software architecture with an example.",
        "SKIP",
        "Keyword but educational",
    ),

    TestCase(
        "KEYWORD_CHAT",
        "How does debugging usually work?",
        "SKIP",
        "General educational question",
    ),


    # --------------------------------------------------------
    # 10. EXPLICIT WORKSPACE REFERENCES
    # --------------------------------------------------------

    TestCase(
        "EXPLICIT_WORKSPACE",
        "Look at the files in this workspace.",
        "INVOKE",
        "Explicit workspace",
    ),

    TestCase(
        "EXPLICIT_WORKSPACE",
        "Search this repository for the authentication code.",
        "INVOKE",
        "Explicit repository",
    ),

    TestCase(
        "EXPLICIT_WORKSPACE",
        "Inspect the current project.",
        "INVOKE",
        "Explicit project",
    ),

    TestCase(
        "EXPLICIT_WORKSPACE",
        "Review the code I currently have open.",
        "INVOKE",
        "Explicit code context",
    ),

    TestCase(
        "EXPLICIT_WORKSPACE",
        "Check the files I just changed.",
        "INVOKE",
        "Explicit changed files",
    ),
]


# ============================================================
# RUN CLASSIFIER
# ============================================================

def classify(prompt):
    try:
        result = subprocess.run(
            [sys.executable, CLASSIFIER, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

        output = result.stdout + "\n" + result.stderr

        match = re.search(r"Action:\s*(INVOKE|SKIP)", output)

        if not match:
            return "ERROR", output.strip()

        return match.group(1), output.strip()

    except Exception as exc:
        return "ERROR", str(exc)


# ============================================================
# TEST RUNNER
# ============================================================

def main():

    print("=" * 100)
    print(" ADAPTIVE TOKENSAVER GATE — COMPREHENSIVE TEST SUITE")
    print("=" * 100)
    print()

    total = len(TESTS)
    passed = 0
    failed = 0
    errors = 0

    category_stats = {}

    failures = []

    for i, test in enumerate(TESTS, 1):

        actual, raw_output = classify(test.prompt)

        if test.category not in category_stats:
            category_stats[test.category] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
            }

        category_stats[test.category]["total"] += 1

        if actual == "ERROR":
            status = "ERROR"
            errors += 1

        elif actual == test.expected:
            status = "PASS"
            passed += 1
            category_stats[test.category]["passed"] += 1

        else:
            status = "FAIL"
            failed += 1
            category_stats[test.category]["failed"] += 1

            failures.append({
                "number": i,
                "category": test.category,
                "prompt": test.prompt,
                "expected": test.expected,
                "actual": actual,
                "description": test.description,
            })

        print(
            f"[{status:<5}] "
            f"#{i:03d} "
            f"{test.category:<18} "
            f"Expected={test.expected:<6} "
            f"Actual={actual:<6} "
            f"| {test.prompt}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    accuracy = (passed / total) * 100 if total else 0

    print()
    print("=" * 100)
    print(" CATEGORY RESULTS")
    print("=" * 100)

    for category, stats in category_stats.items():

        cat_accuracy = (
            stats["passed"] / stats["total"] * 100
            if stats["total"]
            else 0
        )

        print(
            f"{category:<20} "
            f"{stats['passed']:>3}/{stats['total']:<3} "
            f"({cat_accuracy:>5.1f}%)"
        )

    print()
    print("=" * 100)
    print(" FINAL RESULTS")
    print("=" * 100)

    print(f"Total Tests:       {total}")
    print(f"Passed:            {passed}")
    print(f"Failed:            {failed}")
    print(f"Errors:            {errors}")
    print(f"Accuracy:          {accuracy:.1f}%")
    print()

    # ========================================================
    # FAILURE DETAILS
    # ========================================================

    if failures:

        print("=" * 100)
        print(" FAILURES")
        print("=" * 100)

        for failure in failures:

            print()
            print(f"Test #{failure['number']}")
            print(f"Category:  {failure['category']}")
            print(f"Prompt:    {failure['prompt']}")
            print(f"Expected:  {failure['expected']}")
            print(f"Actual:    {failure['actual']}")
            print(f"Reason:    {failure['description']}")

    else:

        print("=" * 100)
        print(" [PASS] ALL TESTS PASSED")
        print("=" * 100)

    # ========================================================
    # SAFETY VERDICT
    # ========================================================

    print()
    print("=" * 100)
    print(" SAFETY VERDICT")
    print("=" * 100)

    if errors > 0:

        print("NOT READY")
        print("Classifier produced execution errors.")

    elif failed == 0:

        print("EXCELLENT")
        print("Adaptive gate passed every test.")

    elif accuracy >= 95:

        print("STRONG")
        print("Gate accuracy is >= 95%. Review failures before deployment.")

    elif accuracy >= 90:

        print("ACCEPTABLE")
        print("Gate needs additional refinement before being considered robust.")

    else:

        print("NEEDS WORK")
        print("Gate accuracy is below 90%.")

    print("=" * 100)

    # Exit code for automation / CI
    sys.exit(0 if failed == 0 and errors == 0 else 1)


if __name__ == "__main__":
    main()
