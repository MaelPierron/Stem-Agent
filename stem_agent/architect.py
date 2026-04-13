"""
Architect — Phase 2 of the Stem Agent lifecycle.

Takes the Explorer's plan and generates a specialized QAAgent Python class.
On subsequent iterations, takes the Evaluator's feedback to improve the code.
"""

import json
from openai import OpenAI


ARCHITECT_SYSTEM_PROMPT = """You are the Architect module of a Stem Agent.
Your role is to generate a complete, working Python class called 'QAAgent'
based on a structured plan and optional feedback from previous attempts.

Requirements:
1. Class name must be exactly: QAAgent
2. Must have a method: analyze(self, filepath: str) -> list[dict]
3. Each dict must have keys: "line" (int), "type" (str), "description" (str)
4. Use ONLY Python stdlib: ast, re, os — NO external libraries whatsoever
5. NEVER use BeautifulSoup, lxml, bs4, or any HTML parser
6. NEVER use .next_sibling, .prev_sibling — these do NOT exist in Python's ast module
7. NEVER call .lineno on ast.Module or ast.arguments nodes — they have no lineno
8. Handle all exceptions per-file gracefully

You MUST start from this exact skeleton and fill in the detection methods:

```python
import ast
import re
from typing import Any

class QAAgent:
    def analyze(self, filepath: str) -> list:
        findings = []
        try:
            source = open(filepath, encoding="utf-8").read()
            tree = ast.parse(source)
            lines = source.splitlines()
        except Exception:
            return []
        self._check_unused_variables(tree, findings)
        self._check_mutable_defaults(tree, findings)
        self._check_bare_except(tree, findings)
        self._check_comparison_to_none(tree, findings)
        self._check_comparison_to_true(tree, findings)
        self._check_builtin_shadowing(tree, findings)
        self._check_resource_leak(tree, source, findings)
        self._check_class_shared_state(tree, findings)
        self._check_missing_return(tree, findings)
        self._check_unreachable_code(tree, findings)
        self._check_division_by_zero(tree, findings)
        return findings

    def _check_unused_variables(self, tree, findings):
        # Find assigned names that are never loaded in the same function scope
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assigned = {}
                loaded = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Name):
                        if isinstance(child.ctx, ast.Store):
                            assigned[child.id] = child.lineno
                        elif isinstance(child.ctx, ast.Load):
                            loaded.add(child.id)
                for name, lineno in assigned.items():
                    if name not in loaded and not name.startswith('_'):
                        findings.append({"line": lineno, "type": "unused_variable",
                                         "description": f"Variable '{name}' assigned but never used"})

    def _check_mutable_defaults(self, tree, findings):
        pass  # IMPLEMENT: find function defs with list/dict/set as default argument value

    def _check_bare_except(self, tree, findings):
        pass  # IMPLEMENT: find ExceptHandler nodes where .type is None

    def _check_comparison_to_none(self, tree, findings):
        pass  # IMPLEMENT: find Compare nodes with Eq op and None constant

    def _check_comparison_to_true(self, tree, findings):
        pass  # IMPLEMENT: find Compare nodes with Eq op and True/False constant

    def _check_builtin_shadowing(self, tree, findings):
        pass  # IMPLEMENT: find function args named list, dict, str, int, float, bool, type, set, tuple

    def _check_resource_leak(self, tree, source, findings):
        pass  # IMPLEMENT: find open() calls not inside a 'with' statement

    def _check_class_shared_state(self, tree, findings):
        pass  # IMPLEMENT: find ClassDef with mutable class-level attributes (list/dict assigned directly)

    def _check_missing_return(self, tree, findings):
        pass  # IMPLEMENT: find functions where some branches return value but function can return None implicitly

    def _check_unreachable_code(self, tree, findings):
        pass  # IMPLEMENT: find statements after return/raise in same block

    def _check_division_by_zero(self, tree, findings):
        pass  # IMPLEMENT: find BinOp with Div where right operand is 0 or len() without guard
```

Replace every `pass` with a real implementation.
Return ONLY raw Python code. No markdown, no explanations."""


def generate(plan: dict, client: OpenAI, feedback: str = None, attempt: int = 1) -> str:
    """
    Generates the QAAgent source code from the plan.
    If feedback is provided, it incorporates lessons from the previous attempt.
    """
    print(f"[Architect] Generating QAAgent (attempt {attempt})...")

    plan_summary = json.dumps(plan, indent=2)

    if feedback:
        feedback_section = f"""
FEEDBACK FROM PREVIOUS ATTEMPT (attempt {attempt - 1}):
{feedback}

You MUST fix all the issues mentioned above. Pay special attention to:
- Bug categories that were missed (low recall)
- False positives that were incorrectly reported
- Any runtime errors that occurred
"""
    else:
        feedback_section = "This is the first attempt. Implement as many bug categories as possible."

    user_prompt = f"""Generate a QAAgent class based on this plan:

{plan_summary}

{feedback_section}

The class must detect as many of the bug_categories as possible using AST analysis.
Prioritize: unused_variable, mutable_default_argument, bare_except, 
comparison_to_none, comparison_to_true, builtin_shadowing, resource_leak,
division_by_zero, unreachable_code, missing_return, class_shared_state.

CRITICAL: The "type" field in each finding dict MUST use EXACTLY these snake_case strings:
- "unused_variable" (not "unused_import", not "UnusedVariable")
- "mutable_default_argument"
- "bare_except"
- "comparison_to_none"
- "comparison_to_true"
- "builtin_shadowing"
- "resource_leak"
- "division_by_zero"
- "unreachable_code"
- "missing_return"
- "class_shared_state"
- "type_error"
- "off_by_one"
- "logic_error"
- "sql_injection"

Do NOT invent new type names. Use only the names from this list."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        timeout=60
    )

    code = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

    print(f"[Architect] Generated {len(code.splitlines())} lines of code.")
    return code
