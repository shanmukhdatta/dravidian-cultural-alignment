"""
Prompt-by-Prompt NVIDIA NIM Inference Runner for Llama-3.1-Nemotron-70B-Instruct
================================================================================
Free inference using NVIDIA NIM developer tier with multi-key auto-rotation.

Features:
1. Canonical 200-condition Dravidian scenario bank (EN, TE, TA, KN).
2. Atomic checkpoint saving to results/checkpoints/checkpoint_llama-3.1-nemotron-70b-instruct.json
   immediately after EACH prompt.
3. Multi-key failover: automatically rotates to the next key if credits run out.
4. Script fidelity check (Telugu, Tamil, Kannada Unicode ranges) & loop detection.
5. Automatic resume: Skips already completed prompts on restart.
"""

import os
import sys
import json
import time
import argparse
import datetime
from pathlib import Path

# Force unbuffered UTF-8 output
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

from openai import OpenAI, AuthenticationError, RateLimitError

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
CODE_DIR = BASE_DIR.parent
sys.path.append(str(CODE_DIR))

# Import script fidelity checker
from script_fidelity_checker import check_fidelity, detect_degeneration_loop

SCENARIOS_PATH = REPO_ROOT / "data" / "all_scenarios.json"
RESULTS_DIR = REPO_ROOT / "results" / "checkpoints"
CHECKPOINT_PATH = RESULTS_DIR / "checkpoint_llama-3.1-nemotron-70b-instruct.json"

MODEL_ID = "nvidia/llama-3.1-nemotron-70b-instruct"
MODEL_NAME = "llama-3.1-nemotron-70b-instruct"

TOKENS_BY_LANG = {"en": 1200, "te": 2200, "ta": 2000, "kn": 1800}
LOCALIZED_KEY = {"te": "telugu", "ta": "tamil", "kn": "kannada"}


def log(msg, level="INFO"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag = {"INFO": "   ", "OK": "✓  ", "WARN": "!  ", "ERR": "ERR", "HDR": ">>>"}
    print(f"[{ts}] [{tag.get(level, '   ')}] {msg}", flush=True)


def build_prompt_list(bank):
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


def is_quota_error(exc):
    msg = str(exc).lower()
    if isinstance(exc, AuthenticationError):
        return True
    if hasattr(exc, "status_code") and exc.status_code in (401, 402, 403):
        return True
    indicators = ["insufficient", "credit", "balance", "quota exceeded", "402", "unauthorized", "payment required"]
    return any(ind in msg for ind in indicators)


def run_inference(api_keys, limit=None):
    if isinstance(api_keys, str):
        api_keys = [api_keys]

    if not api_keys:
        log("No NVIDIA NIM API key provided. Set the NVIDIA_API_KEY environment variable or pass --api_key", "ERR")
        sys.exit(1)

    active_key_idx = 0

    def get_client(idx):
        return OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_keys[idx].strip(),
            timeout=180.0
        )

    client = get_client(active_key_idx)
    log(f"Using NVIDIA NIM Key #{active_key_idx + 1}/{len(api_keys)}: ...{api_keys[active_key_idx][-8:]}")

    with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
        bank = json.load(f)

    all_prompts = build_prompt_list(bank)
    existing_records = load_checkpoint()

    # Index completed prompts
    completed_keys = set()
    for r in existing_records:
        if r.get("response", "").strip():
            k = (r["scenario_id"], r["version"], r["lang"], r.get("region"))
            completed_keys.add(k)

    log(f"Total scenario prompts: {len(all_prompts)}")
    log(f"Already completed in checkpoint: {len(completed_keys)}/{len(all_prompts)}")

    if len(completed_keys) >= len(all_prompts):
        log("🎉 All 200 prompts are ALREADY complete!", "OK")
        return True

    prompts_to_run = []
    for idx, p in enumerate(all_prompts, 1):
        k = (p["scenario_id"], p["version"], p["lang"], p.get("region"))
        if k not in completed_keys:
            prompts_to_run.append((idx, p))

    if limit:
        prompts_to_run = prompts_to_run[:limit]

    log(f"Prompts remaining to process: {len(prompts_to_run)}")
    log("=" * 70)

    for step_num, (global_idx, p_data) in enumerate(prompts_to_run, 1):
        s_id = p_data["scenario_id"]
        dim = p_data["dimension"]
        ver = p_data["version"]
        lang = p_data["lang"]
        reg = p_data["region"]
        user_prompt = p_data["prompt"]

        max_tokens = TOKENS_BY_LANG.get(lang, 1800)

        log(f"[{global_idx}/200] Inferencing {s_id} | {dim} | {lang.upper()} | {ver} (region={reg})...")

        messages = [
            {"role": "system", "content": "You are a helpful advisor giving practical life advice."},
            {"role": "user", "content": user_prompt}
        ]

        attempt_success = False
        while not attempt_success:
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
                attempt_success = True
                # Pacing: ensure we remain strictly within the 40 RPM limit
                time.sleep(2.0)

            except Exception as exc:
                elapsed = round(time.time() - t0, 2)
                err_str = str(exc).lower()
                log(f"Error on prompt #{global_idx}: {exc}", "ERR")

                # Handle rate limit (429) specifically: back off and retry same key
                if isinstance(exc, RateLimitError) or "429" in err_str or "rate limit" in err_str:
                    log("Rate limit (429) encountered. Backing off for 15 seconds...", "WARN")
                    time.sleep(15)
                    continue

                if is_quota_error(exc):
                    if active_key_idx + 1 < len(api_keys):
                        active_key_idx += 1
                        log(f"⚡ Rotating to next API key #{active_key_idx + 1}: ...{api_keys[active_key_idx][-8:]}", "WARN")
                        client = get_client(active_key_idx)
                        time.sleep(3)
                        continue
                    else:
                        log("=" * 70, "HDR")
                        log("🚨 ALL NVIDIA NIM API KEYS EXHAUSTED OR UNAVAILABLE!", "WARN")
                        log(f"   - Saved up to prompt #{global_idx - 1} ({len(existing_records)}/200 total)", "OK")
                        log(f"   - Checkpoint: {CHECKPOINT_PATH}", "INFO")
                        log("=" * 70, "HDR")
                        save_checkpoint(existing_records)
                        return False
                else:
                    log("Transient error. Retrying in 5s...", "WARN")
                    time.sleep(5)
                    save_checkpoint(existing_records)
                    # continue to retry same prompt

    log(f"Finished! Total records saved: {len(load_checkpoint())}/200", "OK")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NVIDIA NIM Prompt-by-Prompt Inference for Llama-3.1-Nemotron-70B-Instruct")
    parser.add_argument("--api_key", type=str, default=None, help="NVIDIA API Key(s), comma-separated for rotation")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of prompts to run")
    args = parser.parse_args()

    keys = []
    if args.api_key:
        keys = [k.strip() for k in args.api_key.split(",") if k.strip()]
    elif os.environ.get("NVIDIA_API_KEY"):
        keys = [k.strip() for k in os.environ["NVIDIA_API_KEY"].split(",") if k.strip()]

    if not keys:
        log("No API key provided! Please set the NVIDIA_API_KEY environment variable or pass --api_key <key>", "ERR")
        sys.exit(1)

    run_inference(keys, limit=args.limit)
