import json, sys
from collections import defaultdict, Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

data = json.load(open('results/checkpoints/checkpoint_llama31_8b.json', encoding='utf-8'))
print(f"Total records: {len(data)}")

dim_map = {'P': 'Power Distance', 'C': 'Collectivism', 'L': 'Long-term Orientation', 'I': 'Indulgence'}

# 1. Dimension x Language matrix
dim_stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'ok': 0, 'degen': 0, 'trunc': 0, 'toks': [], 'chars': []}))
for r in data:
    d = r['scenario_id'][0]
    l = r['lang']
    ok = r.get('script_ok', False) and not r.get('truncated', False)
    dim_stats[d][l]['total'] += 1
    if ok:
        dim_stats[d][l]['ok'] += 1
    if r.get('degeneration_loop'):
        dim_stats[d][l]['degen'] += 1
    if r.get('truncated'):
        dim_stats[d][l]['trunc'] += 1
    dim_stats[d][l]['toks'].append(r.get('n_tokens_generated', 0))
    dim_stats[d][l]['chars'].append(len(r.get('response', '')))

print("\n--- 1. DIMENSION x LANGUAGE MATRIX ---")
print(f"{'Dimension':<25} {'EN':<16} {'TE':<16} {'TA':<16} {'KN':<16} {'Total Usable'}")
print("-" * 95)
for d_code, d_name in dim_map.items():
    row_strs = []
    tot_ok, tot_all = 0, 0
    for l in ['en', 'te', 'ta', 'kn']:
        s = dim_stats[d_code][l]
        tot_ok += s['ok']
        tot_all += s['total']
        pct = s['ok'] / s['total'] * 100
        row_strs.append(f"{s['ok']}/{s['total']} ({pct:.0f}%)")
    print(f"{d_name:<25} {row_strs[0]:<16} {row_strs[1]:<16} {row_strs[2]:<16} {row_strs[3]:<16} {tot_ok}/{tot_all} ({tot_ok/tot_all*100:.1f}%)")

# 2. Generic vs Localized
ver_stats = defaultdict(lambda: Counter())
for r in data:
    v = r['version']
    ok = r.get('script_ok', False) and not r.get('truncated', False)
    ver_stats[v]['total'] += 1
    if ok:
        ver_stats[v]['ok'] += 1
    else:
        ver_stats[v]['fail'] += 1
    if r.get('truncated'):
        ver_stats[v]['trunc'] += 1
    if r.get('degeneration_loop'):
        ver_stats[v]['degen'] += 1

print("\n--- 2. VERSION BREAKDOWN ---")
for k, v in ver_stats.items():
    print(f"{k.upper()}: total={v['total']} | usable={v['ok']} ({v['ok']/v['total']*100:.1f}%) | truncated={v['trunc']} | degen_loop={v['degen']}")

# 3. Latency & Tokens
print("\n--- 3. LATENCY & TOKENS ---")
elapsed_by_lang = defaultdict(list)
toks_by_lang = defaultdict(list)
chars_by_lang = defaultdict(list)
for r in data:
    elapsed_by_lang[r['lang']].append(r.get('elapsed_s', 0))
    toks_by_lang[r['lang']].append(r.get('n_tokens_generated', 0))
    chars_by_lang[r['lang']].append(len(r.get('response', '')))

for l in ['en', 'te', 'ta', 'kn']:
    avg_t = sum(toks_by_lang[l]) / len(toks_by_lang[l])
    max_t = max(toks_by_lang[l])
    avg_c = sum(chars_by_lang[l]) / len(chars_by_lang[l])
    avg_s = sum(elapsed_by_lang[l]) / len(elapsed_by_lang[l])
    print(f"{l.upper():<4}: avg_toks={avg_t:.1f} | max_toks={max_t} | avg_chars={avg_c:.1f} | avg_elapsed={avg_s:.1f}s")

# 4. Catalog of Truncated & Degeneration Loops
print("\n--- 4. ANOMALIES BREAKDOWN ---")
anomalies = [r for r in data if not r.get('script_ok') or r.get('truncated') or r.get('degeneration_loop')]
print(f"Total Anomalous / Filtered records: {len(anomalies)}")

# Count overlaps: how many truncated were also degeneration loops?
trunc_and_degen = sum(1 for r in data if r.get('truncated') and r.get('degeneration_loop'))
trunc_only = sum(1 for r in data if r.get('truncated') and not r.get('degeneration_loop'))
degen_only = sum(1 for r in data if not r.get('truncated') and r.get('degeneration_loop'))
script_fails = sum(1 for r in data if not r.get('script_ok'))

print(f"Script failures (ratio < 70%): {script_fails}")
print(f"Truncated responses (hit token cap): {sum(1 for r in data if r.get('truncated'))}")
print(f"Degeneration loops detected: {sum(1 for r in data if r.get('degeneration_loop'))}")
print(f"Overlaps (Both Truncated & Degen Loop): {trunc_and_degen}")
print(f"Truncated without loop: {trunc_only}")
print(f"Degen loop without truncation: {degen_only}")

print("\nList of all 26 Truncated records (which are excluded from judge):")
trunc_records = [r for r in data if r.get('truncated')]
for i, r in enumerate(trunc_records, 1):
    resp = r.get('response', '').replace('\n', ' ')
    print(f"[{i:02d}] {r['scenario_id']} | {r['version']:<9} | {r['lang'].upper()} (reg={r.get('region')}): tokens={r.get('n_tokens_generated')} | attempts={r.get('attempts')} | degen={r.get('degeneration_loop')}")
    print(f"     Snippet end: \"...{resp[-100:]}\"")
