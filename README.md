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
  <b>Simranjit Singh</b>
</p>

<p align="center">
  <i>Department of Information Technology, Dr. B.R. Ambedkar National Institute of Technology Jalandhar, Punjab, 144008, India</i><br>
  <code>{bodasd.ic.24, kumarprateek, singhsimranjit}@nitj.ac.in</code>
</p>

<p align="center">
  <a href="#overview">Overview</a> &nbsp;&bull;&nbsp;
  <a href="#key-findings">Key Findings</a> &nbsp;&bull;&nbsp;
  <a href="#evaluated-models">Models</a> &nbsp;&bull;&nbsp;
  <a href="#benchmark-results">Benchmark Results</a> &nbsp;&bull;&nbsp;
  <a href="#repository-structure">Repository Structure</a> &nbsp;&bull;&nbsp;
  <a href="#quickstart--reproducibility">Reproducibility</a> &nbsp;&bull;&nbsp;
  <a href="#human-evaluation">Human Validation</a> &nbsp;&bull;&nbsp;
  <a href="#citation">Citation</a>
</p>

---

## Overview

When multilingual large language models are queried on real-life ethical dilemmas, does their counsel shift depending on whether the query is framed in English, Telugu, Tamil, or Kannada?

This repository hosts the official benchmark, code, evaluation data, and pre-computed checkpoints for our AAAI 2027 study: **"The Scale Fallacy in Multilingual Alignment: Quantifying Cross-Lingual Cultural Value Drift Across Dravidian Languages"**. 

Investigating the **Dravidian language family** (Telugu, Tamil, Kannada; representing over 250 million native speakers), we evaluate $N = 1,200$ generations across 6 foundation models under generic and culturally localized conditions across 20 calibrated moral dilemmas. Using a dual-lens methodology that couples a continuous **Hofstede stance continuum (1.0 = Western Individualist $\rightarrow$ 5.0 = South Asian Collectivist)** with **LaBSE cross-lingual semantic representations**, we uncover fundamental limits of parameter scaling in multilingual alignment.

---

## Key Findings

1. **The Scale Fallacy in Dravidian Generation:** Scaling parameters in Western foundation models does not eliminate tokenization fragility. Nemotron-70B experiences severe repetition loops ($31.0\%$) and first-pass output truncations ($36.0\%$) under Dravidian prompts, leaving $64.0\%$ complete outputs. We note that decoding setups differed (commercial API under single pass without repetition penalties or retries vs. local models under 4-bit NF4 with repetition penalty and retries on truncation), meaning comparisons across parameter sizes are suggestive rather than a controlled test of scale.
2. **Indic Post-Trained Specialization:** The Indic post-trained model (**Sarvam-M**, 24B, fine-tuned from Mistral-Small) achieves **100% complete outputs** (0% loops, 0% truncations on initial pass), highest script fidelity ($100\%$), and lowest mean embedding drift ($\text{LaBSE drift} = 0.265$, not statistically distinguishable from Gemma-2 at $0.272$). Its Indic cultural stance and resilience are partly by design.
3. **Cross-Lingual Cultural Value Drift (H1):** Querying Western foundation models in native Dravidian languages induces mixed, generally collectivist-leaning drift ($\Delta = +0.12$ to $+0.40$), while Sarvam-M shifts toward individualism in Telugu ($\Delta = -0.70$, uncorrected $p = 0.003$, overall $\Delta = -0.28$). Paired scenario $t$-tests confirm nominal shifts for Gemma-3 in KN ($p=0.0421$) and Nemotron-70B in TA ($p=0.0415$), though none survive Holm correction; results are exploratory.
4. **Cultural Entity Priming (H3):** Introducing authentic regional entities raises cultural stance across all six models in Telugu ($\Delta_{\mathrm{loc}} \in [+0.24, +0.85]$), although the effect reaches statistical significance only for Sarvam-M (uncorrected $p = 0.002$). Localized framing in Tamil and Kannada yields mixed shifts across models.
5. **Double-Blind Human Agreement:** Independent evaluations by university-educated native speakers establish moderate agreement with the automated judge framework (inter-annotator linear $\kappa_w = 0.590$, unweighted $\kappa_u = 0.392$, with $95.8\%$ within $\pm 1$ point and $54.2\%$ exact match; automated judge vs. human $\kappa_w = 0.546$ with $87.5\%$ within $\pm 1$ point; Landis & Koch 1977). Note that automated judge agreement was lower on Sarvam-M ($\kappa_w = 0.380$) and Gemma-3 ($\kappa_w = 0.229$).

---

## Evaluated Models

| Model Identifier | Developer / Provider | Parameters | Vocabulary Size | Tokenizer Type | Architecture / Focus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`sarvam_m`** | Sarvam AI (India) | **24B** | 131,072 | Mistral BPE (Indic post-trained) | Indic post-trained on Mistral-Small 24B (stance partly by design) |
| **`gemma3_12b`** | Google DeepMind | 12B | 256,000 | Multilingual BPE | Next-gen dense multilingual |
| **`gemma2_9b`** | Google DeepMind | 9B | 256,000 | Multilingual BPE | Multilingual (Script fallback in KN) |
| **`llama31_8b`** | Meta AI | 8B | 128,256 | Tiktoken BPE | Western foundation base |
| **`qwen3_8b`** | Alibaba Cloud | 8B | 152,064 | Multilingual BPE | Multilingual / Cross-lingual |
| **`llama-3.1-nemotron-70b`** | NVIDIA / Meta | 70B | 128,256 | Tiktoken BPE | High-parameter Western base (API single-pass evaluation) |

---

## Benchmark Results

All empirical results reported below exactly match the paper (*AAAI 2027 Main Track & Supplementary Material*).

### Table 1: Main Benchmark Summary (Paper Table 1)

> **Metric Definitions:**  
> - **Clean% ($\uparrow$):** Complete non-truncated and script-adherent outputs (loops not excluded).  
> - **1st-Tr% ($\downarrow$):** Initial first-pass context truncation rate (51/200 Llama-8B, 68/200 Qwen-8B, 72/200 Nemotron-70B).  
> - **Fin-Tr% ($\downarrow$):** Final truncation rate after retry (where applicable).  
> - **Loop% ($\downarrow$):** Degenerative repetition loop rate.  
> - **Drift $\Delta$:** Mean Dravidian stance shift relative to English base ($+ = \text{Collectivist shift}$).  
> - **$\kappa_w$ ($\uparrow$):** Linear-weighted inter-annotator agreement on 20 stratified items (not a model-quality score; Landis & Koch 1977).  
> - **LaBSE ($\downarrow$):** Cross-lingual representation drift ($1 - \cos$).

| Model | Clean% $\uparrow$ | 1st-Tr% $\downarrow$ | Fin-Tr% $\downarrow$ | Loop% $\downarrow$ | Drift $\Delta$ | $\kappa_w \uparrow$ | LaBSE $\downarrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Sarvam-M** | **100.0%** | **0.0%** | **0.0%** | **0.0%** | -0.280$^{\dag}$ | 0.649 | **0.265** |
| **Gemma-3-12B** | 99.0% | **0.0%** | **0.0%** | **0.0%** | +0.117 | 0.336 | 0.325 |
| **Gemma-2-9B** | 89.0% | 0.5% | 0.5% | 1.0% | **+0.396** | 0.638 | 0.272 |
| **Llama-3.1-8B** | 87.0% | 25.5% | 13.0% | 39.0% | +0.374 | 0.609 | 0.369 |
| **Qwen-3-8B** | 85.5% | 34.0% | 14.0% | 47.5% | +0.136 | **0.654** | 0.345 |
| **Nemotron-70B** | 64.0% | **36.0%** | **36.0%** | **31.0%** | +0.330 | 0.539 | 0.323 |
| **Pooled Benchmark** | **87.4%** | **15.9%** | **10.6%** | **19.8%** | **+0.178** | **0.590** | **0.316** |

$^{\dag}$*Sarvam-M's base English stance is $3.05$ (its Indic stance is partly by design).*
---

### Table 2: Generation Quality & Pathology Audit across 1,200 Outputs (Supp. Table 4)

| Model | Raw $N$ | Script Adherence | 1st-Pass Trunc. | Final Trunc. | Degeneration Loop Rate | Clean Scored $N$ | Complete % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`sarvam_m`** | 200 | **200 / 200 (100.0%)** | **0.0% (0 / 200)** | **0.0% (0 / 200)** | **0.0% (0 / 200)** | **200 / 200** | **100.0%** |
| **`gemma3_12b`** | 200 | 198 / 200 (99.0%) | **0.0% (0 / 200)** | **0.0% (0 / 200)** | **0.0% (0 / 200)** | 198 / 200 | 99.0% |
| **`gemma2_9b`** | 200 | 179 / 200 (89.5%) | 0.5% (1 / 200) | 0.5% (1 / 200) | 1.0% (2 / 200) | 178 / 200 | 89.0% |
| **`llama31_8b`** | 200 | 200 / 200 (100.0%) | 25.5% (51 / 200) | 13.0% (26 / 200) | 39.0% (78 / 200) | 174 / 200 | 87.0% |
| **`qwen3_8b`** | 200 | 200 / 200 (100.0%) | 34.0% (68 / 200) | 14.0% (28 / 200) | 47.5% (95 / 200) | 171 / 200 | 85.5% |
| **`llama-3.1-nemotron-70b`** | 200 | 200 / 200 (100.0%) | **36.0% (72 / 200)** | **36.0% (72 / 200)** | **31.0% (62 / 200)** | **128 / 200** | **64.0%** |
| **Total / Average** | **1,200** | **1,177 / 1,200 (98.1%)** | **15.9% (191 / 1,200)** | **10.6% (127 / 1,200)** | **19.8% (237 / 1,200)** | **1,049 / 1,200** | **87.4%** |

*Note: Complete % represents complete, non-truncated and script-adherent outputs (loops not excluded from scoring).*
---

### Table 3: Cross-Lingual Cultural Value Drift by Language (Generic Condition)

Stance measured on Hofstede's 1.0 to 5.0 continuum:
- **1.0**: Western Individualist / Personal Autonomy / Egalitarian
- **5.0**: South Asian Collectivist / Kinship Solidarity / Hierarchy
- **$\Delta = \text{Stance}_{\text{Dravidian}} - \text{Stance}_{\text{English}}$**

| Model | EN Baseline | Telugu (TE) | Tamil (TA) | Kannada (KN) | $\Delta$(TE) | $\Delta$(TA) | $\Delta$(KN) | Mean Drift ($\Delta$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`gemma2_9b`** | 2.55 | 2.69 | 2.65 | 3.50 | $+0.14$ | $+0.10$ | $+0.95$ | **$+0.396$** |
| **`llama31_8b`** | 2.60 | 3.13 | 3.00 | 2.79 | $+0.53$ | $+0.40$ | $+0.19$ | **$+0.374$** |
| **`llama-3.1-nemotron-70b`** | 2.55 | 2.33 | 3.56 | 2.75 | $-0.22$ | $+1.01$ | $+0.20$ | **$+0.330$** |
| **`qwen3_8b`** | 2.35 | 2.33 | 2.86 | 2.27 | $-0.02$ | $+0.51$ | $-0.08$ | **$+0.136$** |
| **`gemma3_12b`** | 2.65 | 2.50 | 2.75 | 3.05 | $-0.15$ | $+0.10$ | $+0.40$ | **$+0.117$** |
| **`sarvam_m`** | 3.05 | 2.35 | 3.00 | 2.95 | $-0.70$ | $-0.05$ | $-0.10$ | **$-0.283$** |

---

### Table 4: Cultural Localization Shift (Hypothesis 3: Generic vs. Localized Framing)

$$\Delta_{\text{loc}} = \text{Stance}_{\text{Localized}} - \text{Stance}_{\text{Generic}}$$

| Model Identifier | $\Delta_{\text{loc}}$(EN) | Telugu ($\Delta_{\text{loc}}$) | Tamil ($\Delta_{\text{loc}}$) | Kannada ($\Delta_{\text{loc}}$) | Key Empirical Finding |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`sarvam_m`** | $-0.13$ | **$+0.85$** ($2.35 \rightarrow 3.20$) | $-0.20$ | $+0.00$ | **Significant Telugu collectivist shift (uncorrected $p = 0.002$)** |
| **`llama-3.1-nemotron-70b`** | $+0.35$ | **$+0.78$** ($2.33 \rightarrow 3.11$) | $-0.92$ | $-0.15$ | High Telugu shift |
| **`llama31_8b`** | $+0.25$ | **$+0.41$** ($3.13 \rightarrow 3.54$) | $+0.33$ | $+0.10$ | Positive shift across all Dravidian languages |
| **`gemma3_12b`** | $-0.03$ | **$+0.35$** ($2.50 \rightarrow 2.85$) | $-0.10$ | $-0.44$ | Telugu collectivist shift |
| **`gemma2_9b`** | $-0.02$ | **$+0.25$** ($2.69 \rightarrow 2.94$) | $-0.10$ | $-0.63$ | Telugu collectivist shift |
| **`qwen3_8b`** | $+0.42$ | **$+0.24$** ($2.33 \rightarrow 2.57$) | $-0.72$ | $+0.07$ | Telugu collectivist shift |

*Telugu localization raises stance in all six models (+0.24 to +0.85), but the effect is statistically significant only for Sarvam-M (uncorrected $p=0.002$). Localized framing in Tamil and Kannada yields mixed shifts across models.*

---

### Table 5: Cross-Lingual Semantic Stability (LaBSE Embeddings: $1 - \cos$)

| Model | $\text{EN}\rightarrow\text{TE}$ | $\text{EN}\rightarrow\text{TA}$ | $\text{EN}\rightarrow\text{KN}$ | Mean Drift ($\downarrow$) | Cosine Sim ($\uparrow$) | Valid Pairs | Benchmark Ranking |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`sarvam_m`** | **0.261** | **0.254** | **0.280** | **0.2653** | **0.7347** | 120 / 120 | Lowest mean drift (indistinguishable from Gemma-2) |
| **`gemma2_9b`** | 0.264 | 0.267 | 0.290 | 0.2719 | 0.7281 | 98 / 120 | High Semantic Stability |
| **`llama-3.1-nemotron-70b`** | 0.311 | 0.323 | 0.337 | 0.3231 | 0.6769 | 48 / 120 | High Scale Semantic Preservation |
| **`gemma3_12b`** | 0.323 | 0.324 | 0.327 | 0.3246 | 0.6754 | 118 / 120 | Dense Multilingual Geometry |
| **`qwen3_8b`** | 0.336 | 0.329 | 0.366 | 0.3445 | 0.6555 | 92 / 120 | Moderate Semantic Drift |
| **`llama31_8b`** | 0.352 | 0.369 | 0.382 | 0.3691 | 0.6309 | 94 / 120 | Highest Semantic Drift |

---

### Table 6: Double-Blind Human Validation & Inter-Annotator Agreement ($N=120$)

| Model Identifier | Sample $n$ | Inter-Ann $\kappa_u$ | Inter-Ann $\kappa_w$ | Inter-Ann $\pm 1$ (%) | Exact Match (%) | Judge-Human $\kappa_w$ | Judge-Human $\pm 1$ (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`qwen3_8b`** | 20 | 0.433 | **0.654** | **100.0%** | 60.0% | 0.568 | 85.0% |
| **`sarvam_m`** | 20 | 0.542 | **0.649** | **100.0%** | 70.0% | 0.380 | 90.0% |
| **`gemma2_9b`** | 20 | **0.558** | **0.638** | **100.0%** | **75.0%** | 0.515 | 92.5% |
| **`llama31_8b`** | 20 | 0.373 | **0.609** | **100.0%** | 50.0% | 0.556 | 87.5% |
| **`llama-3.1-nemotron-70b`** | 20 | 0.375 | 0.539 | 80.0% | 50.0% | **0.764** | 90.0% |
| **`gemma3_12b`** | 20 | 0.106 | 0.336 | 95.0% | 20.0% | 0.229 | 80.0% |
| **Pooled Benchmark** | **120** | **0.392** | **0.590** | **95.8%** | **54.2%** | **0.546** | **87.5%** |

*Linear-weighted $\kappa_w = 0.590$ denotes moderate agreement per Landis & Koch (1977); unweighted $\kappa_u = 0.392$. Note that automated judge agreement is lower for Sarvam-M ($\kappa_w = 0.380$) and Gemma-3 ($\kappa_w = 0.229$).*
---

### Table 7: Hofstede Dimension Vulnerability Hierarchy (Descriptive Analysis, 5 Scenarios per Dimension)

*Evaluates $N = 404$ generic-condition responses across the four dimensions to probe Hypothesis 2.*

| Hofstede Cultural Dimension | Scored $N$ | EN Baseline | Dravidian Mean | Net Drift ($\Delta$) | Mean $|\Delta|$ | Vulnerability Hierarchy |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Collectivism vs. Individualism** | 100 | 2.57 | 2.83 | **+0.262** | 0.62 | **Highest Net Shift** |
| **Indulgence vs. Restraint** | 105 | 3.27 | 3.48 | **+0.213** | 0.44 | **High Net Shift** |
| **Long-Term Orientation** | 94 | 2.20 | 2.27 | +0.066 | 0.38 | Low Net Shift |
| **Power Distance Index** | 105 | 2.47 | 2.49 | +0.027 | **0.54** | near-zero net drift |

---

## Repository Structure

```text
├── README.md                                # Benchmark overview, complete tables & reproduction guide
├── requirements.txt                         # Python dependencies
├── LICENSE                                  # MIT Open-Source License
├── paper_audit_and_novelty_report.md        # Deep audit & publication readiness assessment
│
├── AAL_Submission/                          # AAAI 2027 Submission LaTeX Source
│   ├── main.tex                             # Main conference paper (8 pages)
│   ├── supplement.tex                       # Supplementary technical appendix
│   ├── refs.bib                             # Bibliography
│   ├── aaai2027.sty / aaai2027.bst          # AAAI style and bibliography files
│   ├── figures/                             # High-resolution vector figures (PDF)
│   └── tables/                              # Modular LaTeX table sources
│
├── docs/                                    # Documentation
│   └── annotator_guidelines.md              # Guidelines provided to native human evaluators
│
├── data/                                    # Benchmark Datasets & Precomputed Evaluations
│   ├── all_scenarios.json                   # 20 calibrated dilemmas (EN, TE, TA, KN)
│   ├── judge_scores.json                    # Consolidated LLM judge scores (1,049 clean evaluations)
│   ├── embed_distances.json                 # LaBSE cross-lingual cosine distances (570 pairs)
│   └── judge_scores_<model>.json            # Per-model scoring records
│
├── code/                                    # Execution Pipeline
│   ├── 01_run_inference.py                  # Step 1: Model inference & generation
│   ├── 02_judge_responses.py                # Step 2: Cultural stance adjudication (GPT-4o)
│   ├── 03_embed_distance.py                 # Step 3: Cross-lingual semantic embedding distance (LaBSE)
│   ├── 04_analysis_NoteBook.ipynb           # Step 4: Replication of all paper figures & tables
│   ├── utils/
│   │   ├── script_fidelity_validator.py     # Script Unicode validation (>=70% threshold)
│   │   └── token_budget_calibration.py      # BPE fragmentation & truncation auditor
│   ├── audits/                              # Sanity checks and checkpoint verification
│   │   └── run_full_paper_audit.py          # Master audit reproducing all paper tables in CLI
│   └── human_eval/                          # Double-blind validation suite
│       ├── compute_human_agreement.py       # Inter-annotator metrics (Kappa / Alpha)
│       └── compute_all_human_agreement.py   # Multi-model human audit aggregation
│
├── results/                                 # Summary Data & Publication Figures
│   ├── final_table.csv                      # Main results table
│   ├── dimension_ranking.csv                # Hofstede dimension breakdown
│   ├── model_ranking.csv                    # Stance & drift rankings
│   ├── figures/                             # Vector figures (Figures 1-5, PDF)
│   └── checkpoints/                         # Raw 1,200 generations & checkpoints
│       ├── raw_responses.json               # All 1,200 generations
│       └── checkpoint_<model>.json          # Per-model raw generation checkpoints
│
└── response_checking/                       # Per-model audit reports and human evaluation sheets
    ├── ALL_MODELS_HUMAN_EVALUATION_SUMMARY.md
    ├── LaBSE_SEMANTIC_DRIFT_ANALYSIS.md
    └── <model_directory>/                   # Per-model sheets & reports
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

### 2. Fast 10-Second Paper Replication (No GPU Required)

All model generations, judge evaluations, and embedding vectors are pre-computed and stored in `results/` and `data/`. You can reproduce all numbers, tables, and hypothesis tests immediately:

```bash
# Run the master audit script that prints all benchmark tables & significance tests:
python code/audits/run_full_paper_audit.py

# Recompute double-blind human validation & Cohen's kappa statistics:
python code/human_eval/compute_all_human_agreement.py

# Generate all paper figures and statistical plots:
jupyter notebook code/04_analysis_NoteBook.ipynb
```

Running these commands reproduces:
- **Table 1:** Main benchmark table across models, languages, and conditions.
- **Table 2:** Generation pathology breakdown (Clean%, Trunc%, Loop%).
- **Table 3 & 4:** Cross-lingual drift and Telugu cultural localization surge ($p = 0.002^{**}$).
- **Table 5 & 6:** LaBSE geometric distances and double-blind human agreement ($\kappa_w = 0.590$).
- **Figures 1–5:** Cross-lingual drift heatmaps, stance boxplots, embedding distance distributions, model rankings, and script fidelity correlations.

---

### 3. Full End-to-End Execution Pipeline

To rerun generation and scoring from scratch:

#### Step 1: Model Inference
```bash
# Run a dry-run test without GPU:
python code/01_run_inference.py --dry_run

# Run inference for a specific model (e.g. sarvam_m):
python code/01_run_inference.py --models sarvam_m
```

#### Step 2: Cultural Stance Adjudication
Set your OpenAI API key and score responses with GPT-4o:
```bash
export OPENAI_API_KEY="your_api_key"  # On Windows: set OPENAI_API_KEY=your_key
python code/02_judge_responses.py --model sarvam_m
```

#### Step 3: Cross-Lingual Embedding Distances
Compute LaBSE semantic divergence against English base responses:
```bash
python code/03_embed_distance.py
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
- **Agreement Metrics:** Compute quadratic/linear-weighted Cohen's $\kappa_w$ and percentage agreements:
```bash
python code/human_eval/compute_all_human_agreement.py
```
**Results:** Linear-weighted inter-annotator $\kappa_w = 0.590$ (unweighted $\kappa_u = 0.392$, indicating moderate agreement; Landis & Koch 1977) with $95.8\%$ agreement within $\pm 1$ point ($54.2\%$ exact match); Automated Judge vs. Human agreement $\kappa_w = 0.546$ with $87.5\%$ agreement within $\pm 1$ point. We note as a limitation that automated judge-human agreement is lower on Sarvam-M ($\kappa_w = 0.380$) and Gemma-3 ($\kappa_w = 0.229$).

---

## Ethical Statement & Data Calibration

- **Calibration:** Scenarios were constructed across four Hofstede dimensions: Individualism vs. Collectivism (IDV), Power Distance (PDI), Long-Term Orientation (LTO), and Indulgence vs. Restraint (IVR).
- **Localization:** Scenarios feature paired generic vs. culturally authentic regional contexts (e.g., maternal uncle wedding obligations, ancestral property inheritance, village panchayat disputes).
- **Safety:** The benchmark contains zero toxic, sexually explicit, defamatory, or personally identifiable data.

---

## Citation

If you use this benchmark, code, or findings in your research, please cite our AAAI 2027 paper:

```bibtex
@inproceedings{datta2027scale,
  title={The Scale Fallacy in Multilingual Alignment: Quantifying Cross-Lingual Cultural Value Drift Across Dravidian Languages},
  author={Shanmukh Datta and Kumar Prateek and Simranjit Singh},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence (AAAI)},
  year={2027}
}
```

---

## License

This repository is licensed under the [MIT License](LICENSE). Datasets and scenario banks are released freely for academic research.
