"""
Stem-Agent: A Self-Differentiating QA Agent for Python Code

Usage:
    python main.py              # Run the full differentiation lifecycle
    python main.py --eval-only  # Re-evaluate an existing specialized/qa_agent.py
    python main.py --baseline   # Run baseline comparison only
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

load_dotenv()


def run_baseline(dataset_dir: str, ground_truth_path: str) -> dict:
    """
    Baseline: a naive static checker using only pyflakes.
    This is the 'before' in our before/after comparison.
    """
    import subprocess
    import json
    from pathlib import Path

    print("\n[Baseline] Running pyflakes on dataset...")

    with open(ground_truth_path) as f:
        ground_truth = json.load(f)

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for filename, expected_bugs in ground_truth.items():
        filepath = Path(dataset_dir) / filename
        if not filepath.exists():
            continue

        result = subprocess.run(
            [sys.executable, "-m", "pyflakes", str(filepath)],
            capture_output=True, text=True
        )
        output_lines = [l for l in result.stdout.strip().split("\n") if l]
        found_count = len(output_lines)
        expected_count = len(expected_bugs)

        # Rough type matching: pyflakes only catches undefined/unused names
        pyflakes_types = {"unused_variable", "undefined_name"}
        expected_pyflakes = [b for b in expected_bugs if b["type"] in pyflakes_types]
        tp = min(found_count, len(expected_pyflakes))
        fp = max(0, found_count - len(expected_pyflakes))
        fn = expected_count - tp

        total_tp += tp
        total_fp += fp
        total_fn += fn

    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    result = {"recall": round(recall, 4), "precision": round(precision, 4), "f1": round(f1, 4)}
    print(f"[Baseline] Recall={recall:.2%}  Precision={precision:.2%}  F1={f1:.2%}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Stem-Agent: Self-Differentiating QA Agent")
    parser.add_argument("--eval-only", action="store_true",
                        help="Re-evaluate existing specialized/qa_agent.py without regenerating")
    parser.add_argument("--baseline", action="store_true",
                        help="Run baseline comparison only")
    args = parser.parse_args()

    dataset_dir = "dataset"
    ground_truth_path = "dataset/ground_truth.json"

    print("=" * 60)
    print("  STEM-AGENT")
    print("  A Self-Differentiating Python QA Agent")
    print("=" * 60)

    # Always run baseline first for comparison
    print("\n[Step 0] Computing baseline (pyflakes)...")
    baseline = run_baseline(dataset_dir, ground_truth_path)

    if args.baseline:
        print("\nBaseline results:", json.dumps(baseline, indent=2))
        return

    if args.eval_only:
        from stem_agent.evaluator import evaluate
        agent_path = "specialized/qa_agent.py"
        if not os.path.exists(agent_path):
            print(f"ERROR: {agent_path} not found. Run without --eval-only first.")
            sys.exit(1)
        result = evaluate(agent_path, dataset_dir, ground_truth_path)
        print_comparison(baseline, result)
        return

    # Full lifecycle
    from stem_agent.loop import run_stem_agent
    history, final_result = run_stem_agent()

    if final_result:
        print_comparison(baseline, final_result)
        save_final_report(baseline, history, final_result)


def print_comparison(baseline: dict, final: dict):
    print("\n" + "=" * 60)
    print("  BEFORE / AFTER COMPARISON")
    print("=" * 60)
    print(f"  {'Metric':<15} {'Baseline (pyflakes)':<22} {'Stem-Agent':<15} {'Delta'}")
    print(f"  {'-'*60}")
    for metric in ["recall", "precision", "f1"]:
        b = baseline.get(metric, 0)
        a = final.get(metric, 0)
        delta = a - b
        sign = "+" if delta >= 0 else ""
        print(f"  {metric.capitalize():<15} {b:.2%}{'':>14} {a:.2%}{'':>7} {sign}{delta:.2%}")
    print("=" * 60)


def save_final_report(baseline, history, final):
    import os
    os.makedirs("specialized", exist_ok=True)
    report = {
        "baseline": baseline,
        "final": final,
        "iterations": len(history),
        "history_summary": [
            {"attempt": r["attempt"], "recall": r["recall"],
             "precision": r["precision"], "f1": r["f1"], "passed": r["passed"]}
            for r in history
        ]
    }
    with open("specialized/final_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\n[Report] Saved to specialized/final_report.json")


if __name__ == "__main__":
    main()
