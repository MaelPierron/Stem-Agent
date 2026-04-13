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

Requirements for the generated class:
1. Class name must be exactly: QAAgent
2. Must have a method: analyze(self, filepath: str) -> list[dict]
3. Each dict in the returned list must have keys: "line" (int), "type" (str), "description" (str)
4. Use Python's 'ast' module as the PRIMARY analysis tool
5. Also use direct string scanning on source lines where AST is insufficient
6. Must handle file read errors gracefully (return empty list on failure)
7. Must import everything it needs at the top of the file
8. No external dependencies beyond Python stdlib
9. NEVER use BeautifulSoup, lxml, or any HTML/XML parser — source code is NOT HTML
10. NEVER use ast.walk on the Module node directly for lineno — Module has no lineno

CONCRETE DETECTION PATTERNS to implement:

resource_leak: find `open(` calls NOT inside a `with` statement
  → Walk ast.Call nodes, check if parent chain contains ast.With

missing_return: find functions where some branches return a value but others don't
  → Check if any ast.Return has a value, but not all code paths do

sql_injection: find string formatting used in SQL-like strings
  → Look for "%" operator or .format() on strings containing SELECT/INSERT/UPDATE/DELETE

off_by_one: find slice patterns like lst[len(lst)-n : len(lst)-1]
  → Look for ast.Subscript with ast.Slice where upper is BinOp(Call(len), Sub, Constant(1))

logic_error: find `if x: ... if y:` where second `if` should be `elif` (overwrites first)
  → Two consecutive if statements modifying the same variable

comparison_to_none: find `== None` or `!= None` in ast.Compare
comparison_to_true: find `== True` or `== False` in ast.Compare

Return ONLY raw Python code. No markdown fences, no explanations."""


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
