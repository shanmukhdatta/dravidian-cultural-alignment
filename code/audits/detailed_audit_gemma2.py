import json, sys
from collections import defaultdict, Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

data = json.load(open('results/checkpoints/checkpoint_gemma2_9b.json', encoding='utf-8'))

dim_map = {'P': 'Power Distance', 'C': 'Collectivism', 'L': 'Long-term Orientation', 'I': 'Indulgence'}

print("==================================================================")
print("1. DIMENSION & LANGUAGE MATRIX (Clean usable records / Total)")
print("==================================================================")
dim_stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'ok': 0, 'chars': [], 'toks': []}))
for r in data:
    d_code = r['scenario_id'][0]
    l = r['lang']
    ok = r.get('script_ok', False) and not r.get('truncated', False)
    dim_stats[d_code][l]['total'] += 1
    if ok:
        dim_stats[d_code][l]['ok'] += 1
    dim_stats[d_code][l]['chars'].append(len(r.get('response', '')))
    dim_stats[d_code][l]['toks'].append(r.get('n_tokens_generated', 0))

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

print("\n==================================================================")
print("2. TOKEN & CHARACTER LENGTHS (Mean generated tokens / chars)")
print("==================================================================")
print(f"{'Language':<10} {'Avg Tokens':<15} {'Avg Chars':<15} {'Budget Limit':<15} {'Max Tokens Used'}")
print("-" * 75)
token_caps = {'en': 1500, 'te': 2950, 'ta': 2750, 'kn': 2300}
for l in ['en', 'te', 'ta', 'kn']:
    all_toks = [r.get('n_tokens_generated', 0) for r in data if r['lang'] == l]
    all_chars = [len(r.get('response', '')) for r in data if r['lang'] == l]
    max_t = max(all_toks) if all_toks else 0
    avg_t = sum(all_toks) / len(all_toks) if all_toks else 0
    avg_c = sum(all_chars) / len(all_chars) if all_chars else 0
    print(f"{l.upper():<10} {avg_t:<15.1f} {avg_c:<15.1f} {token_caps[l]:<15} {max_t}")

print("\n==================================================================")
print("3. COMPLETE CATALOG OF ALL 22 ABNORMALITIES / FAILURES")
print("==================================================================")
anomalies = [r for r in data if not r.get('script_ok') or r.get('truncated') or r.get('degeneration_loop')]
print(f"Total Anomalous Records: {len(anomalies)} / 200\n")

for i, r in enumerate(anomalies, 1):
    sid = r['scenario_id']
    dim = dim_map[sid[0]]
    ver = r['version']
    lang = r['lang'].upper()
    ratio = r.get('script_ratio', 1.0)
    hits = r.get('other_script_hits', [])
    degen = r.get('degeneration_loop', False)
    trunc = r.get('truncated', False)
    resp = r.get('response', '').strip().replace('\n', ' ')
    
    reasons = []
    if not r.get('script_ok'):
        reasons.append(f"Script Failure (Ratio: {ratio:.1%}, Threshold: 70%)")
    if hits:
        reasons.append(f"Contaminating Scripts: {', '.join(hits)}")
    if degen:
        reasons.append("Degeneration/Repetition Loop Detected")
    if trunc:
        reasons.append("Hit Max Token Cap / Truncated")
        
    print(f"[{i:02d}] {sid} ({dim}) | Version: {ver} | Language: {lang}")
    print(f"     Status  : { ' | '.join(reasons) }")
    print(f"     Snippet : \"{resp[:130]}...\"")
    print()
