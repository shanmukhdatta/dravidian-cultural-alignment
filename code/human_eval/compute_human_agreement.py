#!/usr/bin/env python3
"""
Compute Inter-Annotator & GPT-4o Human Agreement (Cohen's Kappa).

Calculates:
1. Linear-weighted Cohen's Kappa (κ_w)
2. Unweighted Cohen's Kappa (κ_u)
3. Within-±1 Agreement (%)
4. Exact Match Agreement (%)

Outputs formatted Table 2 mirroring the paper.
"""

import argparse
import csv
import json
import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
from pathlib import Path
from sklearn.metrics import cohen_kappa_score

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent
DATA_DIR = REPO_ROOT / "data"

ap = argparse.ArgumentParser(description="Compute Kappa agreement between human annotators and GPT-4o")
ap.add_argument("--model", type=str, required=True,
                help="Model identifier (e.g. gemma2_9b, llama31_8b, gemma3_12b)")
args = ap.parse_args()

model_dir = REPO_ROOT / f"response_checking/{args.model}"
csv_path = model_dir / "human_annotation_sheet.csv"
key_path = model_dir / "human_annotation_key.json"

if not csv_path.exists():
    raise FileNotFoundError(f"Annotation sheet not found: {csv_path}. Run generate_human_annotation_sheet.py first!")

if not key_path.exists():
    raise FileNotFoundError(f"Key file not found: {key_path}")

with open(key_path, encoding="utf-8") as f:
    key_dict = {r["sample_id"]: r for r in json.load(f)}

with open(csv_path, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

gpt_scores = []
ann1_scores = []
ann2_scores = []

for r in rows:
    sid = r["sample_id"]
    if sid not in key_dict:
        continue
    
    gpt_val = key_dict[sid]["gpt4o_score"]
    
    # Check Annotator 1
    val1_str = r.get("annotator_1_score (1-5)", "").strip()
    val2_str = r.get("annotator_2_score (1-5)", "").strip()
    
    if val1_str:
        try:
            val1 = float(val1_str)
            if 1 <= val1 <= 5:
                gpt_scores.append(gpt_val)
                ann1_scores.append(val1)
                if val2_str:
                    try:
                        val2 = float(val2_str)
                        if 1 <= val2 <= 5:
                            ann2_scores.append(val2)
                    except ValueError:
                        pass
        except ValueError:
            pass

n_rated = len(ann1_scores)
if n_rated == 0:
    print(f"==================================================================")
    print(f"No human scores detected in: {csv_path}")
    print(f"Please open {csv_path} and fill in the 'annotator_1_score (1-5)' column.")
    print(f"==================================================================")
    exit(0)

print(f"==================================================================")
print(f"HUMAN EVALUATION AGREEMENT REPORT: {args.model}")
print(f"Total Evaluated Sample Size: n = {n_rated}")
print(f"==================================================================")

def compute_metrics(y_true, y_pred):
    exact = np.mean(np.array(y_true) == np.array(y_pred)) * 100
    within_1 = np.mean(np.abs(np.array(y_true) - np.array(y_pred)) <= 1) * 100
    
    # Labels 1 to 5
    labels = [1, 2, 3, 4, 5]
    ku = cohen_kappa_score(y_true, y_pred, labels=labels)
    kw = cohen_kappa_score(y_true, y_pred, labels=labels, weights="linear")
    return ku, kw, within_1, exact

# 1. GPT-4o vs Annotator 1
ku_1, kw_1, w1_1, ex_1 = compute_metrics(gpt_scores, ann1_scores)

print(f"\nTable 2: Inter-Annotator & Judge Agreement (linear-weighted Cohen's κ)")
print(f"{'Comparison Pair':<25} {'n':<6} {'κ_u (unweighted)':<18} {'κ_w (linear)':<16} {'Within ±1 (%)':<16} {'Exact Match (%)'}")
print("-" * 95)
print(f"{'GPT-4o vs Annotator 1':<25} {n_rated:<6} {ku_1:<18.3f} {kw_1:<16.3f} {f'{w1_1:.1f}%':<16} {f'{ex_1:.1f}%'}")

has_ann2 = len(ann2_scores) == n_rated
if has_ann2:
    ku_2, kw_2, w1_2, ex_2 = compute_metrics(gpt_scores, ann2_scores)
    ku_12, kw_12, w1_12, ex_12 = compute_metrics(ann1_scores, ann2_scores)
    mean_kw = (kw_1 + kw_2) / 2
    mean_w1 = (w1_1 + w1_2) / 2
    print(f"{'GPT-4o vs Annotator 2':<25} {n_rated:<6} {ku_2:<18.3f} {kw_2:<16.3f} {f'{w1_2:.1f}%':<16} {f'{ex_2:.1f}%'}")
    print(f"{'Annotator 1 vs Ann. 2':<25} {n_rated:<6} {ku_12:<18.3f} {kw_12:<16.3f} {f'{w1_12:.1f}%':<16} {f'{ex_12:.1f}%'}")
    print("-" * 95)
    print(f"{'Mean (GPT-4o vs Human)':<25} {n_rated:<6} {'-':<18} {mean_kw:<16.3f} {f'{mean_w1:.1f}%':<16} {'-'}")

# Save report
report_path = model_dir / "human_evaluation_report.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# Human Validation & Kappa Agreement Report: {args.model}\n\n")
    f.write(f"- **Evaluated Sample Size:** $n = {n_rated}$\n")
    f.write(f"- **GPT-4o vs. Annotator 1 Linear Kappa (κ_w):** `{kw_1:.3f}`\n")
    f.write(f"- **Within ±1 Agreement:** `{w1_1:.1f}%`\n")
    f.write(f"- **Exact Match Agreement:** `{ex_1:.1f}%`\n\n")
    f.write("```\n")
    f.write(f"Pair                      n    κ_u     κ_w     Within ±1\n")
    f.write(f"GPT-4o vs Annotator 1     {n_rated:<4} {ku_1:.3f}   {kw_1:.3f}   {w1_1:.1f}%\n")
    if has_ann2:
        f.write(f"GPT-4o vs Annotator 2     {n_rated:<4} {ku_2:.3f}   {kw_2:.3f}   {w1_2:.1f}%\n")
        f.write(f"Annotator 1 vs Ann. 2     {n_rated:<4} {ku_12:.3f}   {kw_12:.3f}   {w1_12:.1f}%\n")
    f.write("```\n")

print(f"\nReport saved to: {report_path}")
