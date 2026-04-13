"""
Explorer — Phase 1 of the Stem Agent lifecycle.

Asks the LLM: "How is this class of problem typically solved?"
Produces a structured PLAN that the Architect will use to generate code.
"""

import os
import json
from openai import OpenAI


EXPLORER_SYSTEM_PROMPT = """You are the Explorer module of a Stem Agent.
Your role is to research and document how a given class of software problems
is typically approached by experts. You must produce a structured, actionable
PLAN that another module (the Architect) will use to generate working Python code.

Your output must be valid JSON with this exact structure:
{
  "problem_class": "string — the class of problem",
  "typical_approaches": ["list of standard techniques used by experts"],
  "bug_categories": ["list of specific bug/issue types to detect"],
  "detection_strategies": {
    "category_name": "how to detect this category programmatically"
  },
  "output_format": "description of what the agent should report per issue found",
  "known_tools": ["existing tools in this space, for reference"],
  "suggested_architecture": "description of the class structure to implement"
}

Return ONLY valid JSON. No markdown, no explanations, no preamble."""


def explore(problem_class: str, client: OpenAI) -> dict:
    """
    Given a problem class (e.g. 'Python code quality assurance'),
    returns a structured plan for solving it.
    """
    print(f"[Explorer] Researching: '{problem_class}'...")

    user_prompt = f"""Problem class to research: "{problem_class}"

Produce a comprehensive plan for how expert software engineers and static
analysis tools typically approach this problem. Focus on what can be detected
through static analysis of Python source code (AST, regex, pattern matching).
Be specific about which bug categories matter most and how to detect them."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": EXPLORER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        timeout=60
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        plan = json.loads(raw)
        print(f"[Explorer] Plan generated with {len(plan.get('bug_categories', []))} bug categories.")
        return plan
    except json.JSONDecodeError as e:
        print(f"[Explorer] WARNING: Could not parse plan as JSON: {e}")
        print(f"[Explorer] Raw response: {raw[:300]}")
        # Return a minimal fallback plan
        return {
            "problem_class": problem_class,
            "typical_approaches": ["AST analysis", "pattern matching"],
            "bug_categories": ["unused_variable", "bare_except", "mutable_default_argument"],
            "detection_strategies": {
                "unused_variable": "Use AST to find assigned names never referenced",
                "bare_except": "Find except clauses with no exception type",
                "mutable_default_argument": "Find function defaults that are list/dict literals"
            },
            "output_format": "list of dicts with keys: line, type, description",
            "known_tools": ["pylint", "flake8", "pyflakes"],
            "suggested_architecture": "A class QAAgent with an analyze(filepath) method"
        }
