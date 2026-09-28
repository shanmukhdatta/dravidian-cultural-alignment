import json, sys
from collections import Counter, defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def audit(filepath):
    print(f"==================================================")
    print(f"AUDITING: {filepath}")
    print(f"==================================================")
    data = json.load(open(filepath, encoding='utf-8'))
    print(f"Total records: {len(data)} (Expected: 200 per model)")

    # Breakdown by language and version
    lang_counts = Counter(r['lang'] for r in data)
    print("Language distribution:", dict(lang_counts))
    # Note: EN has 80 (20 generic-en + 60 localized-en-te/ta/kn), TE has 40 (20 generic + 20 localized), TA has 40, KN has 40 = 200 total!

    ver_counts = Counter(r['version'] for r in data)
    print("Version distribution:", dict(ver_counts))

    scenarios = sorted(list(set(r['scenario_id'] for r in data)))
    print(f"Scenario IDs present ({len(scenarios)}/20):", scenarios)

    script_ok_by_lang = defaultdict(lambda: {'ok': 0, 'fail': 0, 'ratios': [], 'other_hits': Counter()})
    degen_count = 0
    truncated_count = 0
    attempts_dist = Counter()
    empty_count = 0
    anomalies = []

    for idx, r in enumerate(data):
        l = r['lang']
        ok = r.get('script_ok', False)
        ratio = r.get('script_ratio', 1.0)
        degen = r.get('degeneration_loop', False)
        trunc = r.get('truncated', False)
        resp = r.get('response', '').strip()
        attempts = r.get('attempts', 1)

        if ok:
            script_ok_by_lang[l]['ok'] += 1
        else:
            script_ok_by_lang[l]['fail'] += 1
        
        script_ok_by_lang[l]['ratios'].append(ratio)
        for hit in r.get('other_script_hits', []):
            script_ok_by_lang[l]['other_hits'][hit] += 1
        
        if degen:
            degen_count += 1
        if trunc:
            truncated_count += 1
        if not resp:
            empty_count += 1
        attempts_dist[attempts] += 1

        if (not ok) or degen or trunc or (not resp):
            anomalies.append({
                "index": idx,
                "scenario_id": r["scenario_id"],
                "version": r["version"],
                "lang": r["lang"],
                "region": r.get("region"),
                "script_ok": ok,
                "script_ratio": ratio,
                "degen": degen,
                "truncated": trunc,
                "length_chars": len(resp),
                "other_hits": r.get("other_script_hits", []),
                "snippet": resp[:120].replace("\n", " ")
            })

    print("\n--- Script Fidelity by Language ---")
    for l, s in sorted(script_ok_by_lang.items()):
        ratios = s['ratios']
        avg_r = sum(ratios) / len(ratios) if ratios else 0
        min_r = min(ratios) if ratios else 0
        print(f"  {l.upper():<4}: OK={s['ok']:2d} / {len(ratios):2d} | Avg Script Ratio={avg_r:.3f}, Min={min_r:.3f} | Contaminating scripts: {dict(s['other_hits'])}")

    print("\n--- Quality Anomalies ---")
    print(f"  Empty responses     : {empty_count}")
    print(f"  Truncated responses : {truncated_count}")
    print(f"  Degeneration loops  : {degen_count}")
    print(f"  Attempts breakdown  : {dict(attempts_dist)}")
    print(f"  Total Anomalous     : {len(anomalies)} / {len(data)} ({len(data) - len(anomalies)} usable for judge)")

    if anomalies:
        print("\n--- Detailed List of Anomalies ---")
        for a in anomalies:
            reasons = []
            if not a['script_ok']:
                reasons.append(f"Script Fail (ratio={a['script_ratio']:.2f}, hits={a['other_hits']})")
            if a['degen']:
                reasons.append("Degeneration Loop")
            if a['truncated']:
                reasons.append("Truncated")
            if a['length_chars'] == 0:
                reasons.append("Empty")
            print(f"  [#{a['index']+1:03d}] {a['scenario_id']} {a['version']:<9} {a['lang'].upper()} (reg={a['region']}): {'; '.join(reasons)}")
            print(f"         Snippet: \"{a['snippet']}...\"")

if __name__ == '__main__':
    audit('results/checkpoints/checkpoint_gemma2_9b.json')
    print("\n\n")
    audit('results/checkpoints/checkpoint_llama31_8b.json')
