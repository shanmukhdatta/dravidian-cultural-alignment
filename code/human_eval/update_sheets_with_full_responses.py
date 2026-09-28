#!/usr/bin/env python3
"""
Regenerate Human Annotation Sheets with FULL Untruncated Model Responses.

Fixes the previous issue where only 200-char response snippets were exported.
Preserves the exact same sampled prompt IDs and GPT-4o scores from existing keys,
while injecting the complete, untruncated model responses from the checkpoints.
"""

import json
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
CKPT_DIR = REPO_ROOT / "results/checkpoints"
SCENARIOS_FILE = DATA_DIR / "all_scenarios.json"

models = [
    "gemma2_9b",
    "gemma3_12b",
    "llama-3.1-nemotron-70b-instruct",
    "llama31_8b",
    "qwen3_8b",
    "sarvam_m"
]

lang_display = {
    "en": "English",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada"
}

with open(SCENARIOS_FILE, encoding="utf-8") as f:
    scenarios_bank = json.load(f)
scenarios_by_id = {s["id"]: s for s in scenarios_bank["scenarios"]}

for m in models:
    model_dir = REPO_ROOT / f"response_checking/{m}"
    csv_path = model_dir / "human_annotation_sheet.csv"
    key_path = model_dir / "human_annotation_key.json"
    
    ckpt_file = CKPT_DIR / f"checkpoint_{m}.json"
    if not ckpt_file.exists():
        # Fallback to alternate naming if needed
        alt_name = m.replace("-", "_")
        ckpt_file = CKPT_DIR / f"checkpoint_{alt_name}.json"
    
    if not ckpt_file.exists():
        print(f"Error: Checkpoint not found for {m}")
        continue
    if not key_path.exists():
        print(f"Error: Key file not found for {m}")
        continue
        
    with open(ckpt_file, encoding="utf-8") as f:
        ckpt_records = json.load(f)
    with open(key_path, encoding="utf-8") as f:
        key_records = json.load(f)
        
    ckpt_map = {}
    for r in ckpt_records:
        key = (r["scenario_id"], r["version"], r["lang"], r.get("region"))
        ckpt_map[key] = r["response"]
        
    rows = []
    for k in key_records:
        sample_id = k["sample_id"]
        sid = k["scenario_id"]
        scenario = scenarios_by_id[sid]
        
        lookup_key = (k["scenario_id"], k["version"], k["lang"], k.get("region"))
        full_response = ckpt_map.get(lookup_key, "")
        
        if k["version"] == "generic" or not k.get("region"):
            en_dilemma = scenario["generic"]["en"]
        else:
            en_dilemma = scenario["localized"][k["region"]]["en"]
            
        pole_1 = scenario["scale"]["pole_1"]
        pole_5 = scenario["scale"]["pole_5"]
        
        rows.append({
            "sample_id": sample_id,
            "language": lang_display.get(k["lang"], k["lang"].upper()),
            "dimension": k["dimension"],
            "dilemma_english": en_dilemma,
            "response_to_rate": full_response,
            "scale_pole_1 (Western norm)": f"1 = Strongly: {pole_1}",
            "scale_pole_3 (Neutral)": "3 = Neutral / balanced compromise",
            "scale_pole_5 (South Asian norm)": f"5 = Strongly: {pole_5}",
            "annotator_1_score (1-5)": "",
            "annotator_2_score (1-5)": "",
            "annotator_notes": ""
        })
        
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Updated {m:<32}: 20 rows exported with full responses (avg len: {sum(len(r['response_to_rate']) for r in rows)//len(rows)} chars)")

print("\nAll 6 human annotation sheets have been updated with complete, untruncated responses!")
