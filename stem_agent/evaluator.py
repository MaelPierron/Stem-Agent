"""
Evaluator — Phase 3 of the Stem Agent lifecycle.

Loads the generated QAAgent, runs it against the dataset,
and computes precision/recall against ground truth.
Produces structured feedback for the Architect if scores are insufficient.
"""

import os
import sys
import json
import importlib.util
import traceback
from pathlib import Path


# Minimum score to stop evolving
RECALL_THRESHOLD = 0.70
PRECISION_THRESHOLD = 0.50


def load_agent(agent_path: str):
    """Dynamically loads the generated QAAgent class."""
    spec = importlib.util.spec_from_file_location("qa_agent", agent_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["qa_agent"] = module
    spec.loader.exec_module(module)
    return module.QAAgent()


def _types_match(expected: str, found: str) -> bool:
    """
    Flexible matching between expected and found bug type strings.
    Handles variations like 'unused_variable' vs 'unused_import',
    'resource_leak' vs 'resource-leak', 'bare_except' vs 'bare_exception', etc.
    """
    # Normalize: lowercase, replace hyphens and spaces with underscores
    exp = expected.lower().replace("-", "_").replace(" ", "_")
    fnd = found.lower().replace("-", "_").replace(" ", "_")

    if exp == fnd:
        return True
    # Substring match
    if exp in fnd or fnd in exp:
        return True
    # Word-level overlap: match if primary word matches (first word, length > 3)
    exp_words = set(exp.split("_"))
    fnd_words = set(fnd.split("_"))
    exp_primary = exp.split("_")[0]
    fnd_primary = fnd.split("_")[0]
    if exp_primary == fnd_primary and len(exp_primary) > 3:
        return True
    # Significant shared keyword (both must contain same meaningful word, length > 4)
    meaningful_overlap = {w for w in exp_words & fnd_words if len(w) > 4}
    if meaningful_overlap:
        return True
    # Accept if all non-trivial words of the shorter type appear in the longer
    short, long = (exp_words, fnd_words) if len(exp_words) <= len(fnd_words) else (fnd_words, exp_words)
    meaningful_short = {w for w in short if len(w) > 3}
    if meaningful_short and meaningful_short.issubset(long):
        return True
    return False


def evaluate(agent_path: str, dataset_dir: str, ground_truth_path: str) -> dict:
    """
    Runs the QAAgent on all dataset files and computes metrics.
    Returns a result dict with scores, per-file breakdown, and feedback text.
    """
    print(f"[Evaluator] Loading agent from {agent_path}...")

    # Load ground truth
    with open(ground_truth_path) as f:
        ground_truth = json.load(f)

    # Try to load the agent
    try:
        agent = load_agent(agent_path)
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"[Evaluator] FATAL: Could not load QAAgent: {e}")
        return {
            "success": False,
            "error": str(e),
            "recall": 0.0,
            "precision": 0.0,
            "f1": 0.0,
            "passed": False,
            "feedback": (
                f"The generated code failed to load with this error:\n{error_msg}\n"
                f"Fix all syntax and import errors. "
                f"Do NOT use BeautifulSoup or any HTML parser. "
                f"Do NOT access .next_sibling on AST nodes — that attribute does not exist in Python's ast module."
            )
        }

    total_tp = 0
    total_fp = 0
    total_fn = 0
    per_file_results = {}
    missed_categories = {}
    false_positive_examples = []
    all_runtime_errors = []

    dataset_path = Path(dataset_dir)

    for filename, expected_bugs in ground_truth.items():
        filepath = dataset_path / filename
        if not filepath.exists():
            print(f"[Evaluator] WARNING: {filename} not found, skipping.")
            continue

        # Run agent
        runtime_errors = []
        try:
            findings = agent.analyze(str(filepath))
            if not isinstance(findings, list):
                findings = []
        except Exception as e:
            print(f"[Evaluator] ERROR running agent on {filename}: {e}")
            runtime_errors.append(f"{filename}: {type(e).__name__}: {e}")
            findings = []
        all_runtime_errors.extend(runtime_errors)

        # Match findings to ground truth — flexible type matching
        matched_expected = set()
        matched_found = set()

        for i, exp in enumerate(expected_bugs):
            exp_type = exp["type"].lower().replace("-", "_")
            for j, found in enumerate(findings):
                if j in matched_found:
                    continue
                found_type = found.get("type", "").lower().replace("-", "_").replace(" ", "_")
                # Accept if types share significant overlap (substring or word match)
                if _types_match(exp_type, found_type):
                    matched_expected.add(i)
                    matched_found.add(j)
                    break

        tp = len(matched_expected)
        fn = len(expected_bugs) - tp
        fp = len(findings) - len(matched_found)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        # Track missed bug types for feedback
        for i, exp in enumerate(expected_bugs):
            if i not in matched_expected:
                cat = exp["type"]
                missed_categories[cat] = missed_categories.get(cat, 0) + 1

        # Track false positives
        for j, found in enumerate(findings):
            if j not in matched_found:
                false_positive_examples.append({
                    "file": filename,
                    "type": found.get("type"),
                    "description": found.get("description", "")
                })

        per_file_results[filename] = {
            "expected": len(expected_bugs),
            "found": len(findings),
            "tp": tp,
            "fp": fp,
            "fn": fn
        }

        status = "✓" if fn == 0 and fp == 0 else f"✗ (missed {fn}, false+ {fp})"
        print(f"  [{status}] {filename}: expected {len(expected_bugs)}, found {len(findings)}, TP={tp}")

    # Compute global metrics
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    passed = recall >= RECALL_THRESHOLD and precision >= PRECISION_THRESHOLD

    print(f"\n[Evaluator] Results: Recall={recall:.2%}  Precision={precision:.2%}  F1={f1:.2%}")
    print(f"[Evaluator] Thresholds: Recall≥{RECALL_THRESHOLD:.0%}  Precision≥{PRECISION_THRESHOLD:.0%}")
    print(f"[Evaluator] {'✓ PASSED — agent is ready' if passed else '✗ NOT PASSED — triggering new iteration'}")

    # Build feedback for Architect
    feedback_lines = []

    if all_runtime_errors:
        feedback_lines.append(f"\nRUNTIME ERRORS occurred during analysis (fix these first):")
        for err in all_runtime_errors[:5]:
            feedback_lines.append(f"  - {err}")
        feedback_lines.append(
            "  Common causes: using .next_sibling (not valid in ast module), "
            "using BeautifulSoup (never use it for Python source), "
            "accessing .lineno on Module nodes."
        )

    # False positives on clean file — most damaging to precision
    clean_fp = per_file_results.get("clean_10.py", {}).get("fp", 0)
    if clean_fp > 0:
        feedback_lines.append(
            f"CRITICAL: You reported {clean_fp} false positive(s) on 'clean_10.py' which has NO bugs. "
            f"Your detection rules are too broad. Add stricter conditions to avoid flagging valid Python patterns."
        )

    if missed_categories:
        sorted_missed = sorted(missed_categories.items(), key=lambda x: -x[1])
        feedback_lines.append("Bug categories most frequently missed (increase detection priority):")
        for cat, count in sorted_missed:
            feedback_lines.append(f"  - {cat}: missed {count} time(s)")

    if false_positive_examples[:5]:
        feedback_lines.append("\nFalse positives (things incorrectly reported as bugs):")
        for fp_ex in false_positive_examples[:5]:
            feedback_lines.append(f"  - [{fp_ex['file']}] type='{fp_ex['type']}': {fp_ex['description']}")

    if recall < RECALL_THRESHOLD:
        feedback_lines.append(
            f"\nRecall is {recall:.2%}, below threshold of {RECALL_THRESHOLD:.0%}. "
            f"You are missing too many real bugs. "
            f"Focus especially on: resource_leak (open() without 'with'), "
            f"comparison_to_none (== None), builtin_shadowing (params named list/dict/str), "
            f"class_shared_state (mutable class-level attributes)."
        )
    if precision < PRECISION_THRESHOLD:
        feedback_lines.append(
            f"\nPrecision is {precision:.2%}, below threshold of {PRECISION_THRESHOLD:.0%}. "
            f"Too many false positives. Do NOT flag: type annotations, correct use of 'with', "
            f"functions that intentionally return None, or standard library usage."
        )

    feedback = "\n".join(feedback_lines) if feedback_lines else "Good performance, minor improvements possible."

    return {
        "success": True,
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1": round(f1, 4),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "per_file": per_file_results,
        "missed_categories": missed_categories,
        "passed": passed,
        "feedback": feedback
    }
