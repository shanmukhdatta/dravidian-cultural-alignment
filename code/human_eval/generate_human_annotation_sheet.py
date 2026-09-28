#!/usr/bin/env python3
"""
Generate Stratified Blind Human Annotation Sheet per Model.

This script samples a balanced 10% stratified subset (default: 20 prompts)
across the 4 Hofstede dimensions and 4 languages (EN, TE, TA, KN).
It exports:
1. response_checking/{model}/human_annotation_sheet.csv:
   Clean sheet for native speaker annotators with dilemma, response, rubrics,
   and empty scoring columns.
2. response_checking/{model}/human_annotation_key.json:
   Internal key mapping sample_id to GPT-4o score and model metadata (for double-blind verification).
"""

import argparse
import csv
import json
import random
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent
DATA_DIR = REPO_ROOT / "data"
SCENARIOS_FILE = DATA_DIR / "all_scenarios.json"

ap = argparse.ArgumentParser(description="Generate blind human annotation sheet for a model")
ap.add_argument("--model", type=str, required=True,
                help="Model identifier (e.g. gemma2_9b, llama31_8b, gemma3_12b)")
ap.add_argument("--samples", type=int, default=20,
                help="Number of samples to draw (default: 20, exactly 10%% of 200)")
ap.add_argument("--seed", type=int, default=42,
                help="Random seed for reproducibility")
args = ap.parse_args()

random.seed(args.seed)

# Paths
scores_file = DATA_DIR / f"judge_scores_{args.model}.json"
ckpt_file = REPO_ROOT / f"results/checkpoints/checkpoint_{args.model}.json"
if not ckpt_file.exists():
    alt_m = args.model.replace("-", "_")
    ckpt_file = REPO_ROOT / f"results/checkpoints/checkpoint_{alt_m}.json"

out_dir = REPO_ROOT / f"response_checking/{args.model}"
out_dir.mkdir(parents=True, exist_ok=True)

csv_path = out_dir / "human_annotation_sheet.csv"
key_path = out_dir / "human_annotation_key.json"

if not scores_file.exists():
    raise FileNotFoundError(f"Judge scores file not found: {scores_file}. Run 02_judge_responses.py first!")

if not SCENARIOS_FILE.exists():
    raise FileNotFoundError(f"Scenarios bank not found: {SCENARIOS_FILE}")

with open(scores_file, encoding="utf-8") as f:
    scored_records = json.load(f)

ckpt_map = {}
if ckpt_file.exists():
    with open(ckpt_file, encoding="utf-8") as f:
        for r in json.load(f):
            ckpt_map[(r["scenario_id"], r["version"], r["lang"], r.get("region"))] = r.get("response", "")

with open(SCENARIOS_FILE, encoding="utf-8") as f:
    scenarios_bank = json.load(f)

scenarios_by_id = {s["id"]: s for s in scenarios_bank["scenarios"]}

# Filter only valid scored records
valid_records = [r for r in scored_records if r.get("stance", -1) > 0]
print(f"Total valid scored records for {args.model}: {len(valid_records)}")

# Stratify by (Dimension, Language)
buckets = defaultdict(list)
for r in valid_records:
    buckets[(r["dimension"], r["lang"])].append(r)

# Sample evenly across buckets
selected = []
target_per_bucket = max(1, args.samples // len(buckets))
all_bucket_keys = sorted(list(buckets.keys()))

for k in all_bucket_keys:
    recs = buckets[k]
    count = min(len(recs), target_per_bucket)
    selected.extend(random.sample(recs, count))

# If need a few more to reach exact args.samples
if len(selected) < args.samples:
    remaining = [r for r in valid_records if r not in selected]
    needed = args.samples - len(selected)
    if remaining:
        selected.extend(random.sample(remaining, min(len(remaining), needed)))

# Shuffle selected samples so annotator sees random order
random.shuffle(selected)
selected = selected[:args.samples]

print(f"Sampled {len(selected)} records for human annotation.")

# Prepare CSV and Key
rows = []
key_data = []

lang_display = {
    "en": "English",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada"
}

for i, r in enumerate(selected, 1):
    sample_id = f"SAMP_{i:03d}"
    sid = r["scenario_id"]
    scenario = scenarios_by_id[sid]
    
    # English dilemma text shown to annotator
    en_dilemma = (
        scenario["generic"]["en"]
        if r["version"] == "generic" or not r.get("region")
        else scenario["localized"][r["region"]]["en"]
    )
    
    pole_1 = scenario["scale"]["pole_1"]
    pole_5 = scenario["scale"]["pole_5"]
    
    lookup_k = (r["scenario_id"], r["version"], r["lang"], r.get("region"))
    full_resp = ckpt_map.get(lookup_k, r.get("response", r.get("response_snippet", "")))

    # Human sheet row (BLIND to model name and GPT-4o score)
    rows.append({
        "sample_id": sample_id,
        "language": lang_display.get(r["lang"], r["lang"].upper()),
        "dimension": r["dimension"],
        "dilemma_english": en_dilemma,
        "response_to_rate": full_resp,
        "scale_pole_1 (Western norm)": f"1 = Strongly: {pole_1}",
        "scale_pole_3 (Neutral)": "3 = Neutral / balanced compromise",
        "scale_pole_5 (South Asian norm)": f"5 = Strongly: {pole_5}",
        "annotator_1_score (1-5)": "",
        "annotator_2_score (1-5)": "",
        "annotator_notes": ""
    })
    
    # Key row (Internal truth for kappa computation)
    key_data.append({
        "sample_id": sample_id,
        "model": r["model"],
        "scenario_id": sid,
        "dimension": r["dimension"],
        "version": r["version"],
        "lang": r["lang"],
        "region": r.get("region"),
        "gpt4o_score": r["stance"],
        "gpt4o_reasoning": r.get("reasoning", "")
    })

# Write CSV sheet
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

# Write Key JSON
with open(key_path, "w", encoding="utf-8") as f:
    json.dump(key_data, f, ensure_ascii=False, indent=2)

print(f"Generated human annotation sheet: {csv_path}")
print(f"Generated double-blind key file : {key_path}")
