#!/usr/bin/env python3
"""
Comprehensive Audit & Analysis for Cultural Hallucination Benchmark
Audits all 6 models:
- gemma2_9b
- llama31_8b
- gemma3_12b
- qwen3_8b
- sarvam_m
- llama-3.1-nemotron-70b-instruct
"""

import json
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_PATH = REPO_ROOT / "results/checkpoints/raw_responses.json"
JUDGE_PATH = REPO_ROOT / "data/judge_scores.json"
EMBED_PATH = REPO_ROOT / "data/embed_distances.json"

def main():
    print("=" * 80)
    print(" CULTURAL VALUE DRIFT BENCHMARK: DEEP AUDIT & STATISTICAL ANALYSIS")
    print("=" * 80)

    with open(RAW_PATH, encoding="utf-8") as f:
        raw_list = json.load(f)
    with open(JUDGE_PATH, encoding="utf-8") as f:
        judge_list = json.load(f)
    with open(EMBED_PATH, encoding="utf-8") as f:
        embed_list = json.load(f)

    rdf = pd.DataFrame(raw_list)
    jdf = pd.DataFrame(judge_list)
    edf = pd.DataFrame(embed_list)

    # Valid judge scores only
    jdf_valid = jdf[jdf["stance"] > 0].copy()
    jdf_gen = jdf_valid[jdf_valid["version"] == "generic"].copy()

    models = sorted(list(rdf["model"].unique()))
    print(f"\n[1] DATASET INVENTORY:")
    print(f"Total raw generations:        {len(rdf)} across {len(models)} models (200/model)")
    print(f"Total valid judge evaluations: {len(jdf_valid)} (out of {len(jdf)} raw judge attempts)")
    print(f"Total embedding drift pairs:   {len(edf)} (LaBSE cross-lingual cosine distances)")
    print(f"Models evaluated: {', '.join(models)}")

    print("\n" + "=" * 80)
    print(" [2] SCRIPT ADHERENCE & GENERATION PATHOLOGY AUDIT (Table 1)")
    print("=" * 80)
    audit_rows = []
    for m in models:
        m_rdf = rdf[rdf["model"] == m]
        m_jdf = jdf_valid[jdf_valid["model"] == m]
        n_raw = len(m_rdf)
        n_ok = (m_rdf["script_ok"] == True).sum() if "script_ok" in m_rdf else 0
        n_trunc = (m_rdf["truncated"] == True).sum() if "truncated" in m_rdf else 0
        n_loop = (m_rdf["degeneration_loop"] == True).sum() if "degeneration_loop" in m_rdf else 0
        n_scored = len(m_jdf)

        audit_rows.append({
            "Model": m,
            "Raw N": n_raw,
            "Script Adherence": f"{n_ok}/{n_raw} ({n_ok/n_raw*100:.1f}%)",
            "Truncation Rate": f"{n_trunc}/{n_raw} ({n_trunc/n_raw*100:.1f}%)",
            "Degeneration Loop": f"{n_loop}/{n_raw} ({n_loop/n_raw*100:.1f}%)",
            "Clean Scored N": f"{n_scored}/{n_raw} ({n_scored/n_raw*100:.1f}%)"
        })
    adf = pd.DataFrame(audit_rows)
    print(adf.to_string(index=False))

    print("\n" + "=" * 80)
    print(" [3] H1: CROSS-LINGUAL CULTURAL VALUE DRIFT (Generic Condition, Table 2)")
    print(" Hofstede Continuum: 1.0 (Western/Individualist) -> 5.0 (South Asian/Collectivist)")
    print("=" * 80)
    drift_rows = []
    stat_rows = []
    for m in models:
        sub = jdf_gen[jdf_gen["model"] == m]
        en_mean = sub[sub["lang"] == "en"]["stance"].mean()
        te_mean = sub[sub["lang"] == "te"]["stance"].mean()
        ta_mean = sub[sub["lang"] == "ta"]["stance"].mean()
        kn_mean = sub[sub["lang"] == "kn"]["stance"].mean()

        d_te = te_mean - en_mean if not pd.isna(te_mean) and not pd.isna(en_mean) else np.nan
        d_ta = ta_mean - en_mean if not pd.isna(ta_mean) and not pd.isna(en_mean) else np.nan
        d_kn = kn_mean - en_mean if not pd.isna(kn_mean) and not pd.isna(en_mean) else np.nan
        drav_mean = np.nanmean([te_mean, ta_mean, kn_mean])
        mean_drift = drav_mean - en_mean if not pd.isna(drav_mean) else np.nan

        drift_rows.append({
            "Model": m,
            "EN (Base)": f"{en_mean:.2f}",
            "TE Stance": f"{te_mean:.2f}",
            "TA Stance": f"{ta_mean:.2f}",
            "KN Stance": f"{kn_mean:.2f}",
            "Delta(TE)": f"{d_te:+.2f}",
            "Delta(TA)": f"{d_ta:+.2f}",
            "Delta(KN)": f"{d_kn:+.2f}",
            "Mean Drift (Delta)": f"{mean_drift:+.3f}"
        })

        # Paired statistics against EN
        en_sc = sub[sub["lang"] == "en"].set_index("scenario_id")["stance"]
        for l in ["te", "ta", "kn"]:
            l_sc = sub[sub["lang"] == l].set_index("scenario_id")["stance"]
            common = en_sc.index.intersection(l_sc.index)
            if len(common) >= 5:
                diff = l_sc.loc[common] - en_sc.loc[common]
                m_diff = diff.mean()
                s_diff = diff.std()
                t_val, p_val = stats.ttest_rel(l_sc.loc[common], en_sc.loc[common])
                d_val = m_diff / s_diff if s_diff > 0 else 0
                sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
                stat_rows.append({
                    "Model": m,
                    "Pair": f"EN -> {l.upper()}",
                    "N Pairs": len(common),
                    "Mean Delta": f"{m_diff:+.3f}",
                    "t-stat": f"{t_val:.3f}",
                    "p-value": f"{p_val:.4f}",
                    "Sig": sig,
                    "Cohen's d": f"{d_val:.2f}"
                })

    print(pd.DataFrame(drift_rows).to_string(index=False))

    print("\n--- H1 Paired Significance Tests (Paired Scenario t-tests) ---")
    print(pd.DataFrame(stat_rows).to_string(index=False))

    print("\n" + "=" * 80)
    print(" [4] H3: CULTURAL LOCALIZATION FRAMING SHIFT (Localized vs. Generic)")
    print(" Delta_loc = Stance(Localized) - Stance(Generic)")
    print("=" * 80)
    h3_rows = []
    for m in models:
        sub = jdf_valid[jdf_valid["model"] == m]
        m_row = {"Model": m}
        for l in ["en", "te", "ta", "kn"]:
            g = sub[(sub["version"] == "generic") & (sub["lang"] == l)]["stance"].mean()
            loc = sub[(sub["version"] == "localized") & (sub["lang"] == l)]["stance"].mean()
            delta = loc - g if not pd.isna(loc) and not pd.isna(g) else np.nan
            m_row[f"{l.upper()} Gen"] = f"{g:.2f}"
            m_row[f"{l.upper()} Loc"] = f"{loc:.2f}"
            m_row[f"Delta_{l.upper()}"] = f"{delta:+.2f}"
        h3_rows.append(m_row)
    print(pd.DataFrame(h3_rows).to_string(index=False))

    print("\n" + "=" * 80)
    print(" [5] CROSS-LINGUAL SEMANTIC DRIFT (LaBSE Embedding 1 - Cosine Sim)")
    print("=" * 80)
    edf_clean = edf.copy()
    edf_clean["lang_pair_clean"] = edf_clean["lang_pair"].str.replace("→", "->")
    embed_piv = edf_clean.pivot_table(index="model", columns="lang_pair_clean", values="drift", aggfunc="mean")
    embed_ranks = edf_clean.groupby("model")["drift"].agg(["mean", "std", "count"]).sort_values("mean")
    embed_ranks["cosine_sim"] = 1.0 - embed_ranks["mean"]
    
    print("\nMean Drift by Language Pair (1 - CosSim):")
    print(embed_piv.to_string())

    print("\nOverall Semantic Stability Ranking (Lowest Drift = Highest Cross-Lingual Alignment):")
    embed_ranks_fmt = embed_ranks.copy()
    embed_ranks_fmt["mean"] = embed_ranks_fmt["mean"].map("{:.4f}".format)
    embed_ranks_fmt["std"] = embed_ranks_fmt["std"].map("{:.4f}".format)
    embed_ranks_fmt["cosine_sim"] = embed_ranks_fmt["cosine_sim"].map("{:.4f}".format)
    print(embed_ranks_fmt.to_string())

    print("\n" + "=" * 80)
    print(" [6] HOFSTEDE DIMENSION BREAKDOWN (Which Values Drift Most?)")
    print("=" * 80)
    dim_rows = []
    for dim in sorted(jdf_gen["dimension"].unique()):
        sub_d = jdf_gen[jdf_gen["dimension"] == dim]
        en_m = sub_d[sub_d["lang"] == "en"]["stance"].mean()
        drav_m = sub_d[sub_d["lang"].isin(["te", "ta", "kn"])]["stance"].mean()
        delta = drav_m - en_m
        dim_rows.append({
            "Dimension": dim,
            "Total N": len(sub_d),
            "EN Mean": f"{en_m:.2f}",
            "Dravidian Mean": f"{drav_m:.2f}",
            "Mean Drift (Delta)": f"{delta:+.3f}"
        })
    print(pd.DataFrame(dim_rows).to_string(index=False))

    print("\n" + "=" * 80)
    print(" AUDIT EXECUTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
