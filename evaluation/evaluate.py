"""Evaluation Suite for Natural Language Command Parsing.

Evaluates and compares:
1. Teacher Model (phi3.5:latest, 3.8B)
2. Untrained Student Baseline (EleutherAI/pythia-70m)
3. Trained Student Model (Pythia-70M fine-tuned / v1 / v2)

against the ground-truth validation set (cloud_assignment/data/validation.jsonl)
using the official scoring script (cloud_assignment/tools/score.py).
Zero heuristic fallbacks, zero synthetic outputs.
"""
import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

GOLD_PATH = os.path.join(PROJECT_ROOT, "cloud_assignment", "data", "validation.jsonl")
SCORE_TOOL = os.path.join(PROJECT_ROOT, "cloud_assignment", "tools", "score.py")


def run_score(predictions_path: str, gold_path: str, out_path: Optional[str] = None, min_validity: Optional[float] = None) -> Dict[str, Any]:
    """Run cloud_assignment/tools/score.py and return the resulting score dictionary."""
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    if not os.path.exists(gold_path):
        raise FileNotFoundError(f"Gold validation file not found: {gold_path}")

    cmd = [sys.executable, SCORE_TOOL, predictions_path, gold_path]
    if out_path:
        cmd.extend(["--out", out_path])
    if min_validity is not None:
        cmd.extend(["--min-validity", str(min_validity)])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0 and min_validity is None:
        raise RuntimeError(f"score.py failed with returncode {result.returncode}:\n{result.stderr}")

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        stdout = result.stdout.strip()
        start = stdout.find("{")
        end = stdout.rfind("}") + 1
        if start != -1 and end != -1:
            report = json.loads(stdout[start:end])
        else:
            raise RuntimeError(f"Could not parse score.py JSON output:\n{stdout}")

    return report


def print_comparison_table(teacher: Dict[str, Any], untrained: Dict[str, Any], trained: Dict[str, Any]) -> None:
    """Print an aligned markdown and terminal comparison table."""
    metrics = [
        ("JSON Validity (%)", "json_validity"),
        ("Intent Accuracy (%)", "intent_accuracy"),
        ("Date Accuracy (%)", "date_accuracy"),
        ("Time Accuracy (%)", "time_accuracy"),
        ("Place Accuracy (%)", "place_accuracy"),
        ("Full Frame Accuracy (%)", "full_frame"),
    ]

    header = f"{'Metric':<26} | {'Teacher (phi3.5)':<18} | {'Untrained Student':<18} | {'Trained Student (v1)':<20}"
    separator = "-" * len(header)

    print("\n" + separator)
    print("EVALUATION & BENCHMARK COMPARISON TABLE")
    print(separator)
    print(header)
    print(separator)

    for label, key in metrics:
        t_val = f"{teacher.get(key, 0.0):.2f}%" if teacher else "N/A"
        u_val = f"{untrained.get(key, 0.0):.2f}%" if untrained else "N/A"
        s_val = f"{trained.get(key, 0.0):.2f}%" if trained else "N/A"
        print(f"{label:<26} | {t_val:<18} | {u_val:<18} | {s_val:<20}")

    print(separator)
    if trained and "examples" in trained:
        print(f"Total Validation Examples: {trained['examples']}")
    print(separator + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", default=GOLD_PATH, help="Path to validation.jsonl")
    parser.add_argument("--teacher-preds", default="results/teacher_predictions.jsonl")
    parser.add_argument("--untrained-preds", default="results/untrained_predictions.jsonl")
    parser.add_argument("--trained-preds", default="results/student_v1_predictions.jsonl")
    parser.add_argument("--min-validity", type=float, default=95.0, help="Fail if trained student validity < min")
    args = parser.parse_args()

    os.makedirs("results", exist_ok=True)

    # 1. Untrained Student
    print("\nScoring Untrained Student baseline...")
    untrained_score = run_score(args.untrained_preds, args.gold, out_path="results/untrained_validation.json")

    # 2. Teacher Model
    teacher_score = {}
    if os.path.exists(args.teacher_preds):
        print("Scoring Teacher Model (phi3.5:latest)...")
        teacher_score = run_score(args.teacher_preds, args.gold, out_path="results/teacher_validation.json")

    # 3. Trained Student Model
    print("Scoring Trained Student Model (v1)...")
    trained_score = run_score(
        args.trained_preds,
        args.gold,
        out_path="results/student_v1_validation.json",
        min_validity=args.min_validity,
    )

    # Comparison summary
    print_comparison_table(teacher_score, untrained_score, trained_score)


if __name__ == "__main__":
    main()
