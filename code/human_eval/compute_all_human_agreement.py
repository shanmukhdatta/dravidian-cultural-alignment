#!/usr/bin/env python3
"""
Master Human Evaluation & Inter-Annotator Agreement Processor.

Processes all models in `response_checking/` that have completed human annotations:
1. Validates `human_annotation_sheet.csv` vs `human_annotation_key.json`
2. Calculates for each model and overall benchmark:
   - GPT-4o vs Annotator 1 (unweighted κ_u, linear-weighted κ_w, within ±1 agreement %, exact match %)
   - GPT-4o vs Annotator 2 (unweighted κ_u, linear-weighted κ_w, within ±1 agreement %, exact match %)
   - Inter-Annotator Agreement: Annotator 1 vs Annotator 2 (κ_u, κ_w, within ±1 %, exact match %)
   - Overall Mean Human vs GPT-4o Judge Agreement
3. Generates per-model `human_evaluation_report.md` in each model's folder
4. Generates a consolidated summary markdown report: `response_checking/ALL_MODELS_HUMAN_EVALUATION_SUMMARY.md`
5. Formats publication-ready Table 2 for the research paper in both Markdown and LaTeX.
"""

import csv
import json
import os
import sys
from pathlib import Path
import numpy as np
from sklearn.metrics import cohen_kappa_score

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESP_CHECK_DIR = REPO_ROOT / "response_checking"

def compute_metrics(y_true, y_pred):
    exact = np.mean(np.array(y_true) == np.array(y_pred)) * 100
    within_1 = np.mean(np.abs(np.array(y_true) - np.array(y_pred)) <= 1) * 100
    labels = [1, 2, 3, 4, 5]
    ku = cohen_kappa_score(y_true, y_pred, labels=labels)
    kw = cohen_kappa_score(y_true, y_pred, labels=labels, weights="linear")
    return ku, kw, within_1, exact

def main():
    print("=" * 85)
    print(" CULTURAL ALIGNMENT BENCHMARK: HUMAN EVALUATION & KAPPA AGREEMENT AUDIT")
    print("=" * 85)

    subdirs = sorted([d for d in RESP_CHECK_DIR.iterdir() if d.is_dir()])
    
    all_models_summary = []
    
    # Global pooling
    global_gpt = []
    global_ann1 = []
    global_ann2 = []

    for d in subdirs:
        model_name = d.name
        csv_path = d / "human_annotation_sheet.csv"
        key_path = d / "human_annotation_key.json"

        if not csv_path.exists() or not key_path.exists():
            continue

        with open(key_path, encoding="utf-8") as f:
            key_dict = {r["sample_id"]: r for r in json.load(f)}

        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        gpt_scores = []
        ann1_scores = []
        ann2_scores = []

        for r in rows:
            sid = r["sample_id"]
            if sid not in key_dict:
                continue
            gpt_val = key_dict[sid]["gpt4o_score"]
            v1_str = r.get("annotator_1_score (1-5)", "").strip()
            v2_str = r.get("annotator_2_score (1-5)", "").strip()

            try:
                v1 = float(v1_str)
                v2 = float(v2_str)
                if 1 <= v1 <= 5 and 1 <= v2 <= 5:
                    gpt_scores.append(gpt_val)
                    ann1_scores.append(v1)
                    ann2_scores.append(v2)
            except ValueError:
                pass

        n_rated = len(ann1_scores)
        if n_rated == 0:
            print(f"Skipping {model_name}: No complete ratings found.")
            continue

        # Accumulate globals
        global_gpt.extend(gpt_scores)
        global_ann1.extend(ann1_scores)
        global_ann2.extend(ann2_scores)

        # Compute model metrics
        ku_1, kw_1, w1_1, ex_1 = compute_metrics(gpt_scores, ann1_scores)
        ku_2, kw_2, w1_2, ex_2 = compute_metrics(gpt_scores, ann2_scores)
        ku_12, kw_12, w1_12, ex_12 = compute_metrics(ann1_scores, ann2_scores)

        mean_kw = (kw_1 + kw_2) / 2
        mean_w1 = (w1_1 + w1_2) / 2
        mean_ex = (ex_1 + ex_2) / 2

        all_models_summary.append({
            "model": model_name,
            "n": n_rated,
            "ann1_kw": kw_1,
            "ann1_w1": w1_1,
            "ann1_ex": ex_1,
            "ann2_kw": kw_2,
            "ann2_w1": w1_2,
            "ann2_ex": ex_2,
            "inter_kw": kw_12,
            "inter_w1": w1_12,
            "inter_ex": ex_12,
            "mean_judge_human_kw": mean_kw,
            "mean_judge_human_w1": mean_w1,
            "mean_judge_human_ex": mean_ex,
        })

        # Save per-model report
        per_model_report = d / "human_evaluation_report.md"
        with open(per_model_report, "w", encoding="utf-8") as rf:
            rf.write(f"# Human Validation & Kappa Agreement Report: {model_name}\n\n")
            rf.write(f"- **Evaluated Sample Size:** $n = {n_rated}$\n")
            rf.write(f"- **Inter-Annotator Linear Kappa (Ann 1 vs Ann 2):** `{kw_12:.3f}`\n")
            rf.write(f"- **Inter-Annotator Within ±1 Agreement:** `{w1_12:.1f}%`\n")
            rf.write(f"- **GPT-4o Judge vs Human Mean Linear Kappa (κ_w):** `{mean_kw:.3f}`\n")
            rf.write(f"- **GPT-4o Judge vs Human Mean Within ±1 Agreement:** `{mean_w1:.1f}%`\n\n")
            rf.write("### Detailed Breakdown\n\n")
            rf.write("| Comparison Pair | n | κ_u (Unweighted) | κ_w (Linear) | Within ±1 (%) | Exact Match (%) |\n")
            rf.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            rf.write(f"| **Annotator 1 vs Annotator 2** | {n_rated} | {ku_12:.3f} | {kw_12:.3f} | {w1_12:.1f}% | {ex_12:.1f}% |\n")
            rf.write(f"| GPT-4o vs Annotator 1 | {n_rated} | {ku_1:.3f} | {kw_1:.3f} | {w1_1:.1f}% | {ex_1:.1f}% |\n")
            rf.write(f"| GPT-4o vs Annotator 2 | {n_rated} | {ku_2:.3f} | {kw_2:.3f} | {w1_2:.1f}% | {ex_2:.1f}% |\n")
            rf.write(f"| **Mean (GPT-4o vs Human)** | {n_rated} | - | **{mean_kw:.3f}** | **{mean_w1:.1f}%** | {mean_ex:.1f}% |\n")

        print(f"[{model_name}] Evaluated n={n_rated} | Inter-Ann κ_w: {kw_12:.3f} (Within ±1: {w1_12:.1f}%) | Judge-Human κ_w: {mean_kw:.3f} (Within ±1: {mean_w1:.1f}%)")

    # Global benchmark computation
    n_global = len(global_ann1)
    g_ku_1, g_kw_1, g_w1_1, g_ex_1 = compute_metrics(global_gpt, global_ann1)
    g_ku_2, g_kw_2, g_w1_2, g_ex_2 = compute_metrics(global_gpt, global_ann2)
    g_ku_12, g_kw_12, g_w1_12, g_ex_12 = compute_metrics(global_ann1, global_ann2)
    g_mean_kw = (g_kw_1 + g_kw_2) / 2
    g_mean_w1 = (g_w1_1 + g_w1_2) / 2
    g_mean_ex = (g_ex_1 + g_ex_2) / 2

    print("\n" + "=" * 85)
    print(" OVERALL BENCHMARK HUMAN EVALUATION SUMMARY (All Models Combined)")
    print("=" * 85)
    print(f"Total Evaluated Samples: N = {n_global} ({len(all_models_summary)} models × 20 samples each)")
    print(f"Inter-Annotator Agreement (Ann 1 vs Ann 2): κ_w = {g_kw_12:.3f}, Within ±1 = {g_w1_12:.1f}%, Exact = {g_ex_12:.1f}%")
    print(f"GPT-4o Judge vs Human Mean Agreement:    κ_w = {g_mean_kw:.3f}, Within ±1 = {g_mean_w1:.1f}%, Exact = {g_mean_ex:.1f}%")
    print("=" * 85)

    # Master markdown report
    summary_path = RESP_CHECK_DIR / "ALL_MODELS_HUMAN_EVALUATION_SUMMARY.md"
    with open(summary_path, "w", encoding="utf-8") as sf:
        sf.write("# Human Evaluation & Inter-Annotator Agreement Summary (All Models)\n\n")
        sf.write(f"This report presents the validation results across all **{len(all_models_summary)} evaluated LLMs**.\n")
        sf.write("Each model was evaluated on a stratified double-blind sample of **20 dilemmas** across all 4 Dravidian/English languages and Hofstede dimensions, independently rated by two human judges.\n\n")
        
        sf.write("## 1. Benchmark-Wide Reliability (Combined N = 120)\n\n")
        sf.write("| Metric | Ann 1 vs Ann 2 (Inter-Annotator) | GPT-4o vs Annotator 1 | GPT-4o vs Annotator 2 | Mean (Judge vs Human) |\n")
        sf.write("| :--- | :---: | :---: | :---: | :---: |\n")
        sf.write(f"| **Linear Cohen's κ (κ_w)** | **{g_kw_12:.3f}** | {g_kw_1:.3f} | {g_kw_2:.3f} | **{g_mean_kw:.3f}** |\n")
        sf.write(f"| **Unweighted Cohen's κ (κ_u)** | {g_ku_12:.3f} | {g_ku_1:.3f} | {g_ku_2:.3f} | {(g_ku_1 + g_ku_2)/2:.3f} |\n")
        sf.write(f"| **Within ±1 Agreement (%)** | **{g_w1_12:.1f}%** | {g_w1_1:.1f}% | {g_w1_2:.1f}% | **{g_mean_w1:.1f}%** |\n")
        sf.write(f"| **Exact Match Agreement (%)** | {g_ex_12:.1f}% | {g_ex_1:.1f}% | {g_ex_2:.1f}% | {g_mean_ex:.1f}% |\n\n")

        sf.write("## 2. Per-Model Agreement Table (Table 2 for Paper)\n\n")
        sf.write("| Model Identifier | Sample Size ($n$) | Inter-Annotator κ_w | Inter-Annotator Within ±1 | Judge vs Human κ_w | Judge vs Human Within ±1 |\n")
        sf.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for m in all_models_summary:
            sf.write(f"| `{m['model']}` | {m['n']} | {m['inter_kw']:.3f} | {m['inter_w1']:.1f}% | {m['mean_judge_human_kw']:.3f} | {m['mean_judge_human_w1']:.1f}% |\n")
        sf.write(f"| **Overall Benchmark (Pooled)** | **{n_global}** | **{g_kw_12:.3f}** | **{g_w1_12:.1f}%** | **{g_mean_kw:.3f}** | **{g_mean_w1:.1f}%** |\n\n")

        sf.write("## 3. LaTeX Table 2 Code for Publication\n\n")
        sf.write("```latex\n")
        sf.write("\\begin{table}[t]\n")
        sf.write("\\centering\n")
        sf.write("\\caption{Inter-Annotator and Automated Judge Validation Agreement (Linear-Weighted Cohen's $\\kappa$).}\n")
        sf.write("\\label{tab:human_agreement}\n")
        sf.write("\\small\n")
        sf.write("\\begin{tabular}{lccccc}\n")
        sf.write("\\toprule\n")
        sf.write("\\textbf{Model} & $n$ & \\textbf{Inter-Ann $\\kappa_w$} & \\textbf{Inter-Ann $\\pm 1$} & \\textbf{Judge-Human $\\kappa_w$} & \\textbf{Judge-Human $\\pm 1$} \\\\\n")
        sf.write("\\midrule\n")
        for m in all_models_summary:
            sf.write(f"{m['model']} & {m['n']} & {m['inter_kw']:.3f} & {m['inter_w1']:.1f}\\% & {m['mean_judge_human_kw']:.3f} & {m['mean_judge_human_w1']:.1f}\\% \\\\\n")
        sf.write("\\midrule\n")
        sf.write(f"\\textbf{{Pooled Benchmark}} & \\textbf{{{n_global}}} & \\textbf{{{g_kw_12:.3f}}} & \\textbf{{{g_w1_12:.1f}\\%}} & \\textbf{{{g_mean_kw:.3f}}} & \\textbf{{{g_mean_w1:.1f}\\%}} \\\\\n")
        sf.write("\\bottomrule\n")
        sf.write("\\end{tabular}\n")
        sf.write("\\end{table}\n")
        sf.write("```\n")

    print(f"\nAll per-model reports saved to response_checking/{{model}}/human_evaluation_report.md")
    print(f"Master summary saved to: {summary_path}")

if __name__ == "__main__":
    main()
