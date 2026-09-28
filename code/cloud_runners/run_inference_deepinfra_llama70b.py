"""
Prompt-by-Prompt DeepInfra Inference Runner for Llama-3.3-70B-Instruct
=======================================================================
Designed for zero out-of-pocket research inference using DeepInfra accounts.

Key Features:
1. Prompt-by-prompt execution across the 200-condition Dravidian scenario bank.
2. Incremental atomic checkpoint saving: Saves to checkpoint_llama33_70b.json
   immediately after EACH prompt.
3. Credit / Quota Exhaustion Detection: If an account's credits are depleted
   (HTTP 402, 429, Insufficient Balance, Quota Exceeded), execution pauses,
   saves all progress cleanly, and prompts for the next API key.
4. Seamless Resumption: Re-running with a new API key picks up from the exact
   next prompt without duplicating tokens or re-running previous prompts.
"""

import os
import sys
import json
import time
import argparse
import datetime
from pathlib import Path

# Force UTF-8 on Windows consoles
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

try:
    from openai import OpenAI, APIStatusError, AuthenticationError, RateLimitError
except ImportError:
    print("Error: openai python package not found. Install with: pip install openai")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
CODE_DIR = BASE_DIR.parent
sys.path.append(str(CODE_DIR))

# Import script fidelity checker
from script_fidelity_checker import check_fidelity, detect_degeneration_loop

# ── Paths ─────────────────────────────────────────────────────────────────────
SCENARIOS_PATH = REPO_ROOT / "data" / "all_scenarios.json"
RESULTS_DIR = REPO_ROOT / "results" / "checkpoints"
CHECKPOINT_PATH = RESULTS_DIR / "checkpoint_llama33_70b.json"

MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"
MODEL_NAME = "llama33_70b"

TOKENS_BY_LANG = {"en": 1500, "te": 2950, "ta": 2750, "kn": 2300}
LOCALIZED_KEY = {"te": "telugu", "ta": "tamil", "kn": "kannada"}


def log(msg, level="INFO"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag = {"INFO": "   ", "OK": "✓  ", "WARN": "!  ", "ERR": "ERR", "HDR": ">>>"}
    print(f"[{ts}] [{tag.get(level, '   ')}] {msg}", flush=True)


def build_prompt_list(bank):
    """
    Constructs the canonical 200-prompt evaluation matrix:
    - 1 EN generic baseline
    - 3 EN localized anchors (telugu, tamil, kannada)
    - 3 native langs x 2 conditions (generic, localized)
    Total = 10 prompts per scenario x 20 scenarios = 200 prompts.
    """
    prompt_list = []
    wrapper = bank.get("advisor_wrapper", {})

    def get_prompt(s, version, lang, region=None):
        w = wrapper.get(lang, "")
        if version == "generic":
            t = s["generic"][lang]
        else:
            region = region or LOCALIZED_KEY[lang]
            t = s["localized"][region][lang]
        return (w + "\n\n" + t) if w else t

    for s in bank["scenarios"]:
        # (1) Generic EN baseline
        prompt_list.append({
            "scenario_id": s["id"],
            "dimension": s["dimension"],
            "version": "generic",
            "lang": "en",
            "region": None,
            "prompt": get_prompt(s, "generic", "en"),
        })

        # (2) Localized EN anchors (one per region)
        for lang in ("te", "ta", "kn"):
            reg = LOCALIZED_KEY[lang]
            prompt_list.append({
                "scenario_id": s["id"],
                "dimension": s["dimension"],
                "version": "localized",
                "lang": "en",
                "region": reg,
                "prompt": get_prompt(s, "localized", "en", region=reg),
            })

        # (3) Native-script Dravidian prompts (generic + localized)
        for lang in ("te", "ta", "kn"):
            reg = LOCALIZED_KEY[lang]
            prompt_list.append({
                "scenario_id": s["id"],
                "dimension": s["dimension"],
                "version": "generic",
                "lang": lang,
                "region": reg,
                "prompt": get_prompt(s, "generic", lang),
            })
            prompt_list.append({
                "scenario_id": s["id"],
                "dimension": s["dimension"],
                "version": "localized",
                "lang": lang,
                "region": reg,
                "prompt": get_prompt(s, "localized", lang, region=reg),
            })

    return prompt_list


def load_checkpoint():
    if not CHECKPOINT_PATH.exists():
        return []
    try:
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)
            if isinstance(records, list):
                return records
    except Exception as e:
        log(f"Warning: Failed to load existing checkpoint: {e}", "WARN")
    return []


def save_checkpoint(records):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = CHECKPOINT_PATH.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    tmp_path.replace(CHECKPOINT_PATH)


def is_credit_or_auth_error(exc):
    msg = str(exc).lower()
    if isinstance(exc, (AuthenticationError, RateLimitError)):
        return True
    if hasattr(exc, "status_code") and exc.status_code in (401, 402, 403, 429):
        return True
    indicators = [
        "insufficient balance",
        "insufficient_balance",
        "credit",
        "balance",
        "quota",
        "exceeded",
        "402",
        "unauthorized",
        "payment required",
        "trial expired",
    ]
    return any(ind in msg for ind in indicators)


def run_inference(api_key, limit=None):
    if not api_key:
        log("No API key provided. Set DEEPINFRA_API_KEY environment variable or pass --api_key", "ERR")
        return False, "NO_API_KEY"

    client = OpenAI(
        api_key=api_key.strip(),
        base_url="https://api.deepinfra.com/v1/openai",
        timeout=120.0
    )

    with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
        bank = json.load(f)

    all_prompts = build_prompt_list(bank)
    existing_records = load_checkpoint()

    # Index completed prompts by (scenario_id, version, lang, region)
    completed_keys = set()
    for r in existing_records:
        if r.get("response", "").strip():
            k = (r["scenario_id"], r["version"], r["lang"], r.get("region"))
            completed_keys.add(k)

    log(f"Total scenario prompts: {len(all_prompts)}")
    log(f"Already completed in checkpoint: {len(completed_keys)}/{len(all_prompts)}")

    if len(completed_keys) >= len(all_prompts):
        log("🎉 All 200 prompts have ALREADY been successfully completed!", "OK")
        return True, "COMPLETE"

    prompts_to_run = []
    for idx, p in enumerate(all_prompts, 1):
        k = (p["scenario_id"], p["version"], p["lang"], p.get("region"))
        if k not in completed_keys:
            prompts_to_run.append((idx, p))

    if limit:
        prompts_to_run = prompts_to_run[:limit]

    log(f"Remaining prompts to process: {len(prompts_to_run)}")
    log("=" * 70)

    for step_num, (global_idx, p_data) in enumerate(prompts_to_run, 1):
        s_id = p_data["scenario_id"]
        dim = p_data["dimension"]
        ver = p_data["version"]
        lang = p_data["lang"]
        reg = p_data["region"]
        user_prompt = p_data["prompt"]

        max_tokens = TOKENS_BY_LANG.get(lang, 2000)

        log(f"[{global_idx}/200] Inferencing {s_id} | {dim} | {lang.upper()} | {ver} (region={reg})...")

        messages = [
            {"role": "system", "content": "You are a helpful advisor giving practical life advice."},
            {"role": "user", "content": user_prompt}
        ]

        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=MODEL_ID,
                messages=messages,
                temperature=0.0,
                max_tokens=max_tokens,
            )
            elapsed = round(time.time() - t0, 2)
            choice = resp.choices[0]
            answer = choice.message.content or ""
            finish_reason = choice.finish_reason

            n_in = resp.usage.prompt_tokens if resp.usage else len(user_prompt.split())
            n_out = resp.usage.completion_tokens if resp.usage else len(answer.split())

            # Script fidelity check
            if lang == "en":
                script_ok = True
                script_ratio = 1.0
                other_hits = {}
            else:
                fid = check_fidelity(answer, lang)
                script_ok = fid["passed"]
                script_ratio = fid["script_ratio"]
                other_hits = fid["other_script_hits"]

            loop_detected = detect_degeneration_loop(answer)
            truncated = (finish_reason == "length")

            record = {
                "model": MODEL_NAME,
                "scenario_id": s_id,
                "dimension": dim,
                "version": ver,
                "lang": lang,
                "region": reg,
                "prompt": user_prompt,
                "response": answer,
                "script_ok": script_ok,
                "script_ratio": script_ratio,
                "other_script_hits": other_hits,
                "degeneration_loop": loop_detected,
                "truncated": truncated,
                "n_tokens_generated": n_out,
                "n_input_tokens": n_in,
                "max_tokens_used": max_tokens,
                "attempts": 1,
                "elapsed_s": elapsed
            }

            existing_records.append(record)
            save_checkpoint(existing_records)

            status_str = f"Done in {elapsed}s | gen={n_out} toks | script_ok={script_ok}"
            if truncated:
                status_str += " | [TRUNCATED]"
            if loop_detected:
                status_str += " | [LOOP DETECTED]"
            log(f"   -> {status_str}", "OK")

        except Exception as exc:
            elapsed = round(time.time() - t0, 2)
            log(f"Exception during inference for prompt #{global_idx}: {exc}", "ERR")

            if is_credit_or_auth_error(exc):
                log("=" * 70, "HDR")
                log(f"🚨 DEEPINFRA ACCOUNT CREDITS DEPLETED / AUTH LIMIT REACHED!", "WARN")
                log(f"   - Current prompt stopped at: #{global_idx}/200 ({s_id}, {lang.upper()}, {ver})", "INFO")
                log(f"   - Successfully completed & safely saved: {len(existing_records)}/200 records in checkpoint.", "OK")
                log(f"   - File: {CHECKPOINT_PATH}", "INFO")
                log(f"   - Next prompt to run will be: #{global_idx}", "INFO")
                log("=" * 70, "HDR")
                return False, f"CREDITS_EXHAUSTED_AT_{global_idx}"
            else:
                log(f"Unexpected error: {exc}. Retrying in 5 seconds...", "WARN")
                time.sleep(5)
                # Save whatever we have
                save_checkpoint(existing_records)
                return False, f"ERROR_{exc}"

    total_done = len(load_checkpoint())
    log(f"Batch completed! Total saved in checkpoint: {total_done}/200", "OK")
    return True, "BATCH_DONE"


def main():
    parser = argparse.ArgumentParser(description="DeepInfra Prompt-by-Prompt Inference for Llama-3.3-70B")
    parser.add_argument("--api_key", type=str, default=None, help="DeepInfra API Key")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of prompts to run in this invocation")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("DEEPINFRA_API_KEY", "")
    success, status = run_inference(api_key, limit=args.limit)
    if not success:
        sys.exit(2 if "CREDITS_EXHAUSTED" in status else 1)
    sys.exit(0)


if __name__ == "__main__":
    main()
