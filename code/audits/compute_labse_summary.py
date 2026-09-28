import json
import numpy as np
from collections import defaultdict

data = json.load(open('data/embed_distances.json', encoding='utf-8'))
print('Total records:', len(data))

by_model = defaultdict(list)
for r in data:
    by_model[r['model']].append(r)

print('\n--- OVERALL RANKINGS (6 MODELS) ---')
stats = []
for m, recs in by_model.items():
    drifts = [r['drift'] for r in recs]
    coss = [r['cosine_sim'] for r in recs]
    stats.append({
        'model': m,
        'n': len(recs),
        'mean_cos': float(np.mean(coss)),
        'mean_drift': float(np.mean(drifts)),
        'std_drift': float(np.std(drifts))
    })

stats.sort(key=lambda x: x['mean_drift'])
for rank, s in enumerate(stats, 1):
    print(f"{rank}. {s['model']:<32} N={s['n']:<3} MeanCos={s['mean_cos']:.4f} MeanDrift={s['mean_drift']:.4f} Std={s['std_drift']:.4f}")

print('\n--- BY LANG PAIR ---')
by_m_lp = defaultdict(list)
for r in data:
    by_m_lp[(r['model'], r['lang_pair'])].append(r['drift'])

for s in stats:
    m = s['model']
    te = by_m_lp.get((m, 'en→te'), [])
    ta = by_m_lp.get((m, 'en→ta'), [])
    kn = by_m_lp.get((m, 'en→kn'), [])
    print(f"{m:<32} TE={np.mean(te):.4f} (n={len(te)}) | TA={np.mean(ta):.4f} (n={len(ta)}) | KN={np.mean(kn):.4f} (n={len(kn)})")

print('\n--- BY DIMENSION ---')
by_m_dim = defaultdict(list)
for r in data:
    by_m_dim[(r['model'], r['dimension'])].append(r['drift'])

for s in stats:
    m = s['model']
    c = by_m_dim.get((m, 'Collectivism'), [])
    ind = by_m_dim.get((m, 'Indulgence'), [])
    l = by_m_dim.get((m, 'Long-term Orientation'), [])
    p = by_m_dim.get((m, 'Power Distance'), [])
    print(f"{m:<32} C={np.mean(c):.4f} | I={np.mean(ind):.4f} | L={np.mean(l):.4f} | P={np.mean(p):.4f}")

print('\n--- H3: GENERIC VS LOCALIZED ---')
by_m_ver = defaultdict(list)
for r in data:
    by_m_ver[(r['model'], r['version'])].append(r['drift'])

for s in stats:
    m = s['model']
    g = by_m_ver.get((m, 'generic'), [])
    loc = by_m_ver.get((m, 'localized'), [])
    diff = np.mean(loc) - np.mean(g)
    print(f"{m:<32} Gen={np.mean(g):.4f} (n={len(g)}) | Loc={np.mean(loc):.4f} (n={len(loc)}) | Diff={diff:+.4f}")
