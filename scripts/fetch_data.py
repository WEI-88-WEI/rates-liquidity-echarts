import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT = DATA_DIR / 'combined.json'


def load_json(name):
    path = DATA_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def align_spread(a, b):
    mb = {x['date']: x['value'] for x in b}
    out = []
    for x in a:
        d = x['date']
        if d in mb:
            out.append({'date': d, 'value': x['value'] - mb[d]})
    return out


base = load_json('combined.json')
swap = load_json('swap_static.json')

base['USD_SWAP_10Y'] = swap.get('USD_SWAP_10Y', [])
base['USD_SWAP_30Y'] = swap.get('USD_SWAP_30Y', [])
base['SWAP_SPREAD_10Y'] = align_spread(base.get('USD_SWAP_10Y', []), base.get('DGS10', []))
base['SWAP_SPREAD_30Y'] = align_spread(base.get('USD_SWAP_30Y', []), base.get('DGS30', []))

OUT.write_text(json.dumps(base, ensure_ascii=False, indent=2))
print(f'wrote {OUT}')
for k in ['USD_SWAP_10Y', 'USD_SWAP_30Y', 'SWAP_SPREAD_10Y', 'SWAP_SPREAD_30Y']:
    print(k, len(base.get(k, [])))
