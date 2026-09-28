import json
from collections import Counter, defaultdict

def summarize_model(filepath, model_name):
    data = json.load(open(filepath, encoding='utf-8'))
    total = len(data)
    
    # Check completeness
    scenarios = set(r['scenario_id'] for r in data)
    langs = Counter(r['lang'] for r in data)
    vers = Counter(r['version'] for r in data)
    
    # Fidelity & Anomalies
    script_stats = defaultdict(lambda: {'ok': 0, 'fail': 0, 'ratios': [], 'hits': Counter()})
    degen_by_lang = Counter()
    trunc_by_lang = Counter()
    attempts_by_lang = defaultdict(Counter)
    
    for r in data:
        l = r['lang']
        ok = r.get('script_ok', False)
        if ok:
            script_stats[l]['ok'] += 1
        else:
            script_stats[l]['fail'] += 1
        script_stats[l]['ratios'].append(r.get('script_ratio', 1.0))
        for h in r.get('other_script_hits', []):
            script_stats[l]['hits'][h] += 1
            
        if r.get('degeneration_loop'):
            degen_by_lang[l] += 1
        if r.get('truncated'):
            trunc_by_lang[l] += 1
        attempts_by_lang[l][r.get('attempts', 1)] += 1
        
    usable = [r for r in data if r.get('script_ok') and not r.get('truncated')]
    
    print(f"==================================================================")
    print(f" AUDIT REPORT: {model_name} ({filepath})")
    print(f"==================================================================")
    print(f"Total Records           : {total} / 200 expected (All 20 scenarios present: {len(scenarios) == 20})")
    print(f"Conditions Distribution : EN={langs['en']} (80 expected), TE={langs['te']} (40), TA={langs['ta']} (40), KN={langs['kn']} (40)")
    print(f"Usable for Judge (clean): {len(usable)} / {total} ({len(usable)/total*100:.1f}%)")
    print()
    print("Language-by-Language Script Fidelity & Hallucination Breakdown:")
    print(f"{'Lang':<6} {'Total':<7} {'Script OK':<12} {'Fail Script':<13} {'Avg Ratio':<11} {'Truncated':<11} {'Degen Loop':<12} {'Contaminating Hits'}")
    print("-" * 95)
    for l in ['en', 'te', 'ta', 'kn']:
        st = script_stats[l]
        avg_r = sum(st['ratios']) / len(st['ratios']) if st['ratios'] else 0
        hits_str = ", ".join(f"{k}:{v}" for k, v in st['hits'].items()) if st['hits'] else "None"
        print(f"{l.upper():<6} {len(st['ratios']):<7} {st['ok']:<12} {st['fail']:<13} {avg_r:<11.3f} {trunc_by_lang[l]:<11} {degen_by_lang[l]:<12} {hits_str}")
    print()
    print("Retry Attempts:")
    for l in ['en', 'te', 'ta', 'kn']:
        print(f"  {l.upper()}: {dict(attempts_by_lang[l])}")
    print()

if __name__ == '__main__':
    summarize_model('results/checkpoints/checkpoint_gemma2_9b.json', 'Gemma-2-9B-IT')
    summarize_model('results/checkpoints/checkpoint_llama31_8b.json', 'Llama-3.1-8B-Instruct')
