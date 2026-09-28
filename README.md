# The Scale Fallacy in Multilingual Alignment: Quantifying Cross-Lingual Cultural Value Drift Across Dravidian Languages

<p align="center">
  <img src="https://img.shields.io/badge/AAAI--2027-Submission-blue?style=flat-square" alt="AAAI 2027"/>
  <img src="https://img.shields.io/badge/Languages-Telugu%20|%20Tamil%20|%20Kannada-orange?style=flat-square" alt="Languages"/>
  <img src="https://img.shields.io/badge/Dataset-20%20Scenarios%20%7C%201%2C200%20Generations-yellow?style=flat-square" alt="Dataset"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Human%20Validation-κ_w%20%3D%200.590-purple?style=flat-square" alt="Human Agreement"/>
</p>

<p align="center">
  <b>Shanmukh Datta</b> &nbsp;&middot;&nbsp;
  <b>Kumar Prateek</b> &nbsp;&middot;&nbsp;
  <b>Simranjit Singh</b> (Corresponding)
</p>

<p align="center">
  <i>Department of Information Technology, Dr. B.R. Ambedkar National Institute of Technology Jalandhar, Punjab, India</i><br>
  <code>{bodasd.ic.24, kumarprateek, singhsimranjit}@nitj.ac.in</code>
</p>

<p align="center">
  <a href="#overview">Overview</a> &nbsp;&bull;&nbsp;
  <a href="#key-findings">Key Findings</a> &nbsp;&bull;&nbsp;
  <a href="#evaluated-models">Models</a> &nbsp;&bull;&nbsp;
  <a href="#repository-structure">Repository Structure</a> &nbsp;&bull;&nbsp;
  <a href="#quickstart--reproducibility">Reproducibility</a> &nbsp;&bull;&nbsp;
  <a href="#human-evaluation">Human Validation</a> &nbsp;&bull;&nbsp;
  <a href="#citation">Citation</a>
</p>

---

## Overview

When multilingual large language models are queried on real-life ethical dilemmas, does their counsel shift depending on whether the query is framed in English, Telugu, Tamil, or Kannada?

This repository hosts the official benchmark, code, and datasets for our AAAI 2027 study investigating **cross-lingual cultural value alignment across the Dravidian language family** (Telugu, Tamil, Kannada; representing over 250 million native speakers). Using a dual-lens methodology that couples a continuous **Hofstede stance continuum (1.0 = Western Individualist $\rightarrow$ 5.0 = South Asian Collectivist)** with **LaBSE cross-lingual semantic representations**, we analyze 1,200 generations across 6 foundation models under generic and culturally localized conditions.

---

## Key Findings

1. **The Scale Fallacy in Dravidian NLP:** Parameter scaling in Western foundation models fails to cure low-resource tokenization fragility. Nemotron-70B experiences severe degeneration loops ($31.0\%$) and output truncations ($36.0\%$) under Dravidian prompts, showing that raw parameter size does not guarantee alignment stability in non-Latin scripts.
2. **Sovereign Indic Foundation Models Win:** The sovereign Indic model (**Sarvam-M**) achieves **100% clean outputs**, the highest script fidelity, and superior geometric stability across Telugu, Tamil, and Kannada.
3. **Cross-Lingual Cultural Value Drift:** Querying models in native Dravidian languages systematically shifts moral stances toward South Asian collectivism ($\Delta = +0.12$ to $+0.40$).
4. **Cultural Entity Priming Surges:** Introducing authentic regional kinship terms (e.g., *thaaimaaman* / *menamama*) and socio-cultural entities amplifies collectivist alignment significantly ($\Delta_{\mathrm{loc}} \in [+0.24, +0.85]$, $p = 0.002^{**}$).
5. **High Human-LLM Agreement:** Double-blind evaluation by university-educated native speakers confirms high agreement with the automated judge framework ($\kappa_w = 0.590$, $95.8\%$ within $\pm 1$ scale point).

---

## Evaluated Models

| Model | Parameters | Vocabulary Size | Architecture / Focus | Clean Output Rate |
| :--- | :--- | :--- | :--- | :--- |
| **Sarvam-M** | 2B (Indic-first) | 65k | Indic-specialized foundation model | **100.0%** |
| **Qwen-2.5-7B-Instruct** | 7B | 152k | Multilingual / Cross-lingual | 98.3% |
| **Llama-3.1-8B-Instruct** | 8B | 128k | Western foundation base | 96.7% |
| **Gemma-2-9B-It** | 9B | 256k | Multilingual (Script fallback in KN) | 82.4% |
| **Gemma-3-12B-It** | 12B | 256k | Next-gen multilingual | 97.5% |
| **Llama-3.1-Nemotron-70B** | 70B | 128k | Extreme scale Western model | **33.0%** (Scale Fallacy) |

---

## Repository Structure

```text
├── README.md                                # Benchmark overview & reproduction guide
├── requirements.txt                         # Python dependencies
├── LICENSE                                  # MIT Open-Source License
│
├── docs/                                    # Documentation
│   └── annotator_guidelines.md              # Guidelines provided to native human evaluators
│
├── data/                                    # Benchmark Datasets
│   ├── all_scenarios.json                   # 20 calibrated dilemmas (EN, TE, TA, KN)
│   ├── judge_scores.json                    # Consolidated LLM judge scores
│   ├── embed_distances.json                 # LaBSE cross-lingual cosine distances
│   └── judge_scores_<model>.json            # Per-model scoring records
│
├── code/                                    # Execution Pipeline
│   ├── 01_run_inference.py                  # Step 1: Deterministic greedy generation
│   ├── 02_judge_responses.py                # Step 2: Multi-dimensional judge scoring
│   ├── 03_embed_distance.py                 # Step 3: Cross-lingual semantic embedding distance
│   ├── 04_analysis_NoteBook.ipynb           # Step 4: Replication of all paper figures & tables
│   ├── utils/
│   │   ├── script_fidelity_validator.py     # Script Unicode validation & fallback filter
│   │   └── token_budget_calibration.py      # BPE fragmentation & truncation auditor
│   ├── human_eval/                          # Double-blind validation suite
│   │   ├── compute_human_agreement.py       # Inter-annotator metrics (Kappa / Alpha)
│   │   └── compute_all_human_agreement.py   # Multi-model human audit aggregation
│   └── audits/                              # Sanity checks and checkpoint verification
│
├── results/                                 # Summary Data & Artifacts
│   ├── final_table.csv                      # Main results table
│   ├── dimension_ranking.csv                # Hofstede dimension breakdown
│   ├── model_ranking.csv                    # Stance & drift rankings
│   ├── scenario_level_drift.csv             # Per-scenario statistical records
│   ├── figures/                             # Vector figures (Figures 1-5, PDF)
│   └── checkpoints/                         # Raw 1,200 generations & checkpoints
│       ├── raw_responses.json
│       └── checkpoint_<model>.json
│
└── response_checking/                       # Per-model audit reports and human sheets
    ├── ALL_MODELS_HUMAN_EVALUATION_SUMMARY.md
    ├── LaBSE_SEMANTIC_DRIFT_ANALYSIS.md
    └── <model_directory>/
```

---

## Quickstart & Reproducibility

### 1. Environment Setup

```bash
git clone https://github.com/shanmukhdatta/dravidian-cultural-alignment.git
cd dravidian-cultural-alignment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Fast 1-Click Replication (No GPU Required)

All model generations, judge evaluations, and embedding vectors are pre-computed and stored in `results/` and `data/`. You can reproduce all figures and tables from the paper immediately:

```bash
jupyter notebook code/04_analysis_NoteBook.ipynb
```
Running this notebook reproduces:
- **Table 1:** Main benchmark table across models, languages, and conditions.
- **Figures 1–5:** Cross-lingual drift heatmaps, stance boxplots, embedding distance distributions, model rankings, and script fidelity correlations.
- **Statistical Tests:** Wilcoxon signed-rank tests ($p < 0.001$), Cohen's $d$, and two-way ANOVA for cultural entity priming.

---

### 3. Full End-to-End Execution Pipeline

To rerun generation and scoring from scratch:

#### Step 1: Model Inference
```bash
python code/01_run_inference.py --model sarvam_m --language all
```

#### Step 2: Cultural Stance Adjudication
Set your judge API key and run the evaluation script:
```bash
export OPENAI_API_KEY="your_api_key"  # On Windows: set OPENAI_API_KEY=your_key
python code/02_judge_responses.py --input results/checkpoints/checkpoint_sarvam_m.json
```

#### Step 3: Cross-Lingual Embedding Distances
Compute LaBSE semantic divergence against English base responses:
```bash
python code/03_embed_distance.py --input results/checkpoints/raw_responses.json
```

#### Step 4: Script Fidelity & Degeneration Audit
Filter non-target scripts (e.g., English fallback in Kannada) and verify tokenization health:
```bash
python code/utils/script_fidelity_validator.py
python code/utils/token_budget_calibration.py
```

---

## Human Evaluation

Human validation was conducted by native Dravidian speakers holding university degrees, compensated at \$25/hour:
- **Annotation Guidelines:** Full instructions and rubrics are documented in [`docs/annotator_guidelines.md`](docs/annotator_guidelines.md).
- **Agreement Metrics:** Compute quadratic-weighted Cohen's $\kappa_w$ and percentage agreements:
```bash
python code/human_eval/compute_human_agreement.py
python code/human_eval/compute_all_human_agreement.py
```
**Results:** Quadratic weighted $\kappa_w = 0.590$ with $95.8\%$ agreement within $\pm 1$ point on the 1.0–5.0 scale, validating the automated judge methodology.

---

## Ethical Statement & Data Calibration

- **Calibration:** Scenarios were constructed across four Hofstede dimensions: Individualism vs. Collectivism (IDV), Power Distance (PDI), Uncertainty Avoidance (UAI), and Long-Term Orientation (LTO).
- **Localization:** Scenarios feature paired generic vs. culturally authentic regional contexts (e.g., maternal uncle wedding obligations, ancestral property inheritance, temple festival committee disputes).
- **Safety:** The benchmark contains zero toxic, sexually explicit, defamatory, or personally identifiable data.

---

## Citation

If you use this benchmark, code, or findings in your research, please cite our AAAI 2027 paper:

```bibtex
@inproceedings{datta2027scale,
  title={The Scale Fallacy in Multilingual Alignment: Quantifying Cross-Lingual Cultural Value Drift Across Dravidian Languages},
  author={Datta, Shanmukh and Prateek, Kumar and Singh, Simranjit},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence (AAAI)},
  year={2027}
}
```

---

## License

This repository is licensed under the [MIT License](LICENSE). Datasets and scenario banks are released freely for academic research.
