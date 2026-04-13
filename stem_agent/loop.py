"""
StemAgent Loop — The core differentiation lifecycle.

Orchestrates: Explore → Architect → Evaluate → (iterate if needed) → Done
"""

import os
import json
import httpx
from pathlib import Path
from openai import OpenAI

from stem_agent.explorer import explore
from stem_agent.architect import generate
from stem_agent.evaluator import evaluate, RECALL_THRESHOLD, PRECISION_THRESHOLD


MAX_ATTEMPTS = 7
SPECIALIZED_DIR = "specialized"
DATASET_DIR = "dataset"
GROUND_TRUTH_PATH = "dataset/ground_truth.json"
PROBLEM_CLASS = "Python code quality assurance and bug detection"


def run_stem_agent():
    """
    Full lifecycle of the Stem Agent:
    1. Explore: discover how QA is typically done
    2. Architect: generate a QAAgent
    3. Evaluate: measure performance
    4. Loop: improve until good enough or max attempts reached
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set. Please add it to your .env file.")

    client = OpenAI(
        api_key=api_key,
        http_client=httpx.Client(timeout=120.0)
    )
    os.makedirs(SPECIALIZED_DIR, exist_ok=True)

    print("=" * 60)
    print("  STEM-AGENT — Differentiation Lifecycle")
    print("=" * 60)

    # ── Phase 1: Explore ──────────────────────────────────────────
    print("\n[Phase 1] EXPLORE — Researching problem class...")
    plan = explore(PROBLEM_CLASS, client)

    plan_path = os.path.join(SPECIALIZED_DIR, "plan.json")
    with open(plan_path, "w") as f:
        json.dump(plan, f, indent=2)
    print(f"[Explorer] Plan saved to {plan_path}")

    # ── Phase 2-4: Architect → Evaluate → Loop ───────────────────
    history = []
    feedback = None
    final_result = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n{'=' * 60}")
        print(f"[Phase 2] ARCHITECT — Generating QAAgent (attempt {attempt}/{MAX_ATTEMPTS})...")

        # Generate code
        code = generate(plan, client, feedback=feedback, attempt=attempt)

        # Save generated agent
        agent_path = os.path.join(SPECIALIZED_DIR, "qa_agent.py")
        with open(agent_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Also save versioned copy
        versioned_path = os.path.join(SPECIALIZED_DIR, f"qa_agent_v{attempt}.py")
        with open(versioned_path, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"[Architect] Agent saved to {agent_path}")

        # ── Phase 3: Evaluate ─────────────────────────────────────
        print(f"\n[Phase 3] EVALUATE — Testing QAAgent against dataset...")
        result = evaluate(agent_path, DATASET_DIR, GROUND_TRUTH_PATH)
        result["attempt"] = attempt
        history.append(result)

        # Save iteration result
        results_path = os.path.join(SPECIALIZED_DIR, f"result_v{attempt}.json")
        with open(results_path, "w") as f:
            json.dump(result, f, indent=2)

        # ── Decision: stop or iterate ─────────────────────────────
        if result["passed"]:
            print(f"\n✓ DIFFERENTIATION COMPLETE after {attempt} attempt(s).")
            print(f"  Final Recall:    {result['recall']:.2%}")
            print(f"  Final Precision: {result['precision']:.2%}")
            print(f"  Final F1:        {result['f1']:.2%}")
            final_result = result
            break
        else:
            if attempt < MAX_ATTEMPTS:
                print(f"\n[Loop] Score insufficient. Feeding back to Architect...")
                feedback = result.get("feedback", "")
            else:
                best = max(history, key=lambda r: r.get("f1", 0))
                print(f"\n✗ Max attempts reached.")
                print(f"  Best F1: {best['f1']:.2%} (attempt {best['attempt']})")
                # Restore best agent file
                best_path = os.path.join(SPECIALIZED_DIR, f"qa_agent_v{best['attempt']}.py")
                if os.path.exists(best_path):
                    import shutil
                    shutil.copy(best_path, os.path.join(SPECIALIZED_DIR, "qa_agent.py"))
                    print(f"  Best agent restored from attempt {best['attempt']}.")
                final_result = best

    # ── Save full history ─────────────────────────────────────────
    history_path = os.path.join(SPECIALIZED_DIR, "evolution_history.json")
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\n[Loop] Full evolution history saved to {history_path}")

    return history, final_result
