# Human Evaluation & Inter-Annotator Agreement Summary (All Models)

This report presents the validation results across all **6 evaluated LLMs**.
Each model was evaluated on a stratified double-blind sample of **20 dilemmas** across all 4 Dravidian/English languages and Hofstede dimensions, independently rated by two human judges.

## 1. Benchmark-Wide Reliability (Combined N = 120)

| Metric | Ann 1 vs Ann 2 (Inter-Annotator) | GPT-4o vs Annotator 1 | GPT-4o vs Annotator 2 | Mean (Judge vs Human) |
| :--- | :---: | :---: | :---: | :---: |
| **Linear Cohen's κ (κ_w)** | **0.590** | 0.489 | 0.603 | **0.546** |
| **Unweighted Cohen's κ (κ_u)** | 0.392 | 0.329 | 0.467 | 0.398 |
| **Within ±1 Agreement (%)** | **95.8%** | 89.2% | 85.8% | **87.5%** |
| **Exact Match Agreement (%)** | 54.2% | 49.2% | 60.0% | 54.6% |

## 2. Per-Model Agreement Table (Table 2 for Paper)

| Model Identifier | Sample Size ($n$) | Inter-Annotator κ_w | Inter-Annotator Within ±1 | Judge vs Human κ_w | Judge vs Human Within ±1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `gemma2_9b` | 20 | 0.638 | 100.0% | 0.515 | 92.5% |
| `gemma3_12b` | 20 | 0.336 | 95.0% | 0.229 | 80.0% |
| `llama-3.1-nemotron-70b-instruct` | 20 | 0.539 | 80.0% | 0.764 | 90.0% |
| `llama31_8b` | 20 | 0.609 | 100.0% | 0.556 | 87.5% |
| `qwen3_8b` | 20 | 0.654 | 100.0% | 0.568 | 85.0% |
| `sarvam_m` | 20 | 0.649 | 100.0% | 0.380 | 90.0% |
| **Overall Benchmark (Pooled)** | **120** | **0.590** | **95.8%** | **0.546** | **87.5%** |

## 3. LaTeX Table 2 Code for Publication

```latex
\begin{table}[t]
\centering
\caption{Inter-Annotator and Automated Judge Validation Agreement (Linear-Weighted Cohen's $\kappa$).}
\label{tab:human_agreement}
\small
\begin{tabular}{lccccc}
\toprule
\textbf{Model} & $n$ & \textbf{Inter-Ann $\kappa_w$} & \textbf{Inter-Ann $\pm 1$} & \textbf{Judge-Human $\kappa_w$} & \textbf{Judge-Human $\pm 1$} \\
\midrule
gemma2_9b & 20 & 0.638 & 100.0\% & 0.515 & 92.5\% \\
gemma3_12b & 20 & 0.336 & 95.0\% & 0.229 & 80.0\% \\
llama-3.1-nemotron-70b-instruct & 20 & 0.539 & 80.0\% & 0.764 & 90.0\% \\
llama31_8b & 20 & 0.609 & 100.0\% & 0.556 & 87.5\% \\
qwen3_8b & 20 & 0.654 & 100.0\% & 0.568 & 85.0\% \\
sarvam_m & 20 & 0.649 & 100.0\% & 0.380 & 90.0\% \\
\midrule
\textbf{Pooled Benchmark} & \textbf{120} & \textbf{0.590} & \textbf{95.8\%} & \textbf{0.546} & \textbf{87.5\%} \\
\bottomrule
\end{tabular}
\end{table}
```
