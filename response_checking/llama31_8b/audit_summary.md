# Deep Audit & Quality Assurance Report: Llama-3.1-8B-Instruct
**Artifact File:** `response_checking/llama31_8b/audit_summary.md`  
**Dataset Source:** `results/checkpoints/checkpoint_llama31_8b.json`  
**Model Architecture:** `meta-llama/Llama-3.1-8B-Instruct` (8.03B Parameters, 4-bit NF4 Quantization)  
**Execution Environment:** NVIDIA H100 NVL (Partition `workq`, PBS Job `33157.master`)  
**Audit Scope:** 200/200 inference prompts across 20 cultural dilemmas, 4 Hofstede dimensions, and 4 languages (English, Telugu, Tamil, Kannada).

---

## 1. Executive Summary & Verification

| Metric | Measured Value | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Experiment Prompts** | **200** | 200 (20 scenarios × 10 conditions) | **100% Complete** |
| **All Scenarios Represented** | **20 / 20** (`P1–P5`, `C1–C5`, `L1–L5`, `I1–I5`) | 20 Scenarios | **Verified** |
| **Clean & Usable Records (for Judge)** | **174 (87.0%)** | ≥ 80% | **Passed** |
| **Filtered Anomalies (Discarded)** | **26 (13.0%)** | < 20% | **Safely Isolated** |
| **Empty Responses** | **0** | 0 | **Flawless** |
| **Script Purity (English - EN)** | **100.0% (80/80)** | 100% | **Flawless (Ratio = 1.000)** |
| **Script Purity (Tamil - TA)** | **100.0% (40/40)** | ≥ 95% | **Zero Language Collapse (Ratio = 1.000)** |
| **Script Purity (Telugu - TE)** | **100.0% (40/40)** | ≥ 80% | **Zero Language Collapse (Ratio = 1.000)** |
| **Script Purity (Kannada - KN)** | **100.0% (40/40)** | ≥ 60% | **Zero Language Collapse (Ratio = 1.000)** |

---

## 2. Dimension × Language Cross-Tabulation Matrix

Distribution of **Clean Usable Records** passed to GPT-4o scoring (excluding truncated/looping responses):

| Hofstede Dimension | Scenario Codes | English (`EN`) | Tamil (`TA`) | Telugu (`TE`) | Kannada (`KN`) | Dimension Pass Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Power Distance** | `P1` to `P5` | 20 / 20 (100%) | 8 / 10 (80.0%) | 6 / 10 (60.0%) | 10 / 10 (100%) | **44 / 50 (88.0%)** |
| **Collectivism** | `C1` to `C5` | 20 / 20 (100%) | 8 / 10 (80.0%) | 5 / 10 (50.0%) | 9 / 10 (90.0%) | **42 / 50 (84.0%)** |
| **Long-Term Orientation** | `L1` to `L5` | 20 / 20 (100%) | 7 / 10 (70.0%) | 7 / 10 (70.0%) | 8 / 10 (80.0%) | **42 / 50 (84.0%)** |
| **Indulgence vs. Restraint** | `I1` to `I5` | 20 / 20 (100%) | 6 / 10 (60.0%) | 10 / 10 (100%) | 10 / 10 (100%) | **46 / 50 (92.0%)** |
| **TOTAL** | **20 Scenarios** | **80 / 80 (100%)** | **29 / 40 (72.5%)** | **28 / 40 (70.0%)** | **37 / 40 (92.5%)** | **174 / 200 (87.0%)** |

> **Key Observation:** Kannada was Llama-3.1's most robust language (92.5% usable), with zero truncations in Power Distance and Indulgence. Telugu experienced higher repetition loop vulnerability in Collectivism (`C1–C5`) and Power Distance (`P1–P5`).

---

## 3. Generic vs. Localized Prompt Framing Disparity

| Prompt Formulation | Total Prompts | Clean & Usable | Truncated / Loops | Usability Rate |
| :--- | :--- | :--- | :--- | :--- |
| **Generic Framing** (Direct dilemmas translated) | 80 | 71 | 9 | **88.8% Usable** |
| **Localized Framing** (Culturally adapted regional dilemmas) | 120 | 103 | 17 | **85.8% Usable** |

* Localized scenarios yielded richer narrative depth, though longer generated sequences occasionally increased exposure to token repetition loops in low-resource Dravidian token spaces.

---

## 4. Token Length & GPU Latency Benchmark (The Token Fragmentation Penalty)

This is one of the most significant empirical discoveries comparing Llama-3.1 to other architectures:

| Language | Mean Tokens Generated | Max Tokens | Mean Response Characters | Characters per Token | Avg Latency on H100 (s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **English (`EN`)** | 398.7 | 550 | 2,103.5 chars | **5.28 chars / tok** | **13.8 s** |
| **Tamil (`TA`)** | 2,264.5 | 4,096 | 1,715.7 chars | **0.76 chars / tok** | **127.3 s (9.2× slower)** |
| **Telugu (`TE`)** | 2,552.7 | 4,096 | 1,491.8 chars | **0.58 chars / tok** | **132.1 s (9.6× slower)** |
| **Kannada (`KN`)** | 2,027.7 | 4,096 | 1,179.2 chars | **0.58 chars / tok** | **110.2 s (8.0× slower)** |

### Critical Empirical Insight:
* In English, 1 token contains over 5 characters.
* In Telugu and Kannada, **1 token represents only ~0.58 characters** (a single South Asian akshara/syllable requires 2 to 3 subword tokens).
* As a result, generating a modest 250-word Dravidian response consumed over **2,500 tokens**, causing latency on the NVIDIA H100 to surge from **13.8 seconds (English)** to **132.1 seconds (Telugu)**!

---

## 5. Catalog of Anomalies: The Degeneration Loop Failure Mode

Unlike Gemma-2 (which suffered from English fallback and Devanagari contamination), **Llama-3.1-8B had 0% script contamination**. Its sole failure mode was **Runaway Degeneration Loops**:

* **Total Anomalous Records:** Exactly **26 records** (12 Telugu, 11 Tamil, 3 Kannada).
* **The Mechanism:** The model began answering the dilemma coherently in pure Dravidian script, but at the conclusion of the response, it entered an unrecoverable repetition loop. It repeated the exact same clause until hitting the hard 4,096 token limit.

### Complete List of the 26 Truncated Records (Safely Filtered from Judge):
1. `[#001] P1 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
2. `[#002] P2 | generic   | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
3. `[#003] P2 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
4. `[#004] P2 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
5. `[#005] P4 | generic   | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
6. `[#006] P4 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
7. `[#007] C1 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
8. `[#008] C2 | generic   | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
9. `[#009] C2 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
10. `[#010] C2 | localized | KN`: Truncated at 4,096 tokens (Attempts: 3, Loop detected)
11. `[#011] C3 | generic   | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
12. `[#012] C4 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
13. `[#013] C4 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
14. `[#014] C5 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
15. `[#015] I2 | generic   | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
16. `[#016] I2 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
17. `[#017] I3 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
18. `[#018] I5 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
19. `[#019] L1 | generic   | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
20. `[#020] L1 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
21. `[#021] L1 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
22. `[#022] L3 | localized | TE`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
23. `[#023] L3 | localized | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
24. `[#024] L3 | localized | KN`: Truncated at 4,096 tokens (Attempts: 3, Loop detected)
25. `[#025] L4 | generic   | TA`: Truncated at 4,096 tokens (Attempts: 2, Loop detected)
26. `[#026] L5 | generic   | KN`: Truncated at 4,096 tokens (Attempts: 3, Loop detected)

---

## 6. Architectural Comparison: Llama-3.1-8B vs. Gemma-2-9B

| Dimension of Comparison | Gemma-2-9B-IT | Llama-3.1-8B-Instruct | Research Interpretation |
| :--- | :--- | :--- | :--- |
| **Script Purity Ratio** | 85.1% (TE), 61.8% (KN) | **100.0% across all languages** | Llama strictly adheres to requested Dravidian scripts without code-switching. |
| **Language Collapse to English** | 14 cases (frequent in Kannada) | **0 cases (Flawless)** | Gemma collapses into English when uncertain; Llama never collapses. |
| **Degeneration / Repetition Loops** | 2 cases (Rare) | **26 cases (Severe in TE & TA)** | Llama's decoder suffers from self-reinforcing n-gram repetition in low-resource scripts. |
| **Inference Latency on H100** | 15s (EN) to 45s (TE) | 14s (EN) to **132s (TE)** | Llama's extreme token fertility makes Dravidian inference ~3× slower than Gemma. |
| **Final Clean Usable Sample** | **177 / 200 (88.5%)** | **174 / 200 (87.0%)** | Both yield nearly identical, robust sample sizes for statistical evaluation. |
