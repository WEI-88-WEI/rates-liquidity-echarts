import csv, json, math, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT = DATA_DIR / 'combined.json'

SERIES = {
    'SOFR': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=SOFR',
    'TGCR': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=TGCR',
    'TGCRVOLUME': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=TGCRVOLUME',
    'BGCR': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=BGCR',
    'DGS10': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10',
    'DGS30': 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS30',
}

def fetch_csv(url):
    last = None
    for i in range(4):
        try:
            res = subprocess.run([
                'curl','-L','--fail','--silent','--show-error',
                '--max-time','45',
                '--http1.1',
                '-A','Mozilla/5.0',
                url
            ], capture_output=True, text=True, check=True)
            return res.stdout
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise last

def parse_fred(text, name):
    rows = list(csv.DictReader(text.splitlines()))
    out = []
    for row in rows:
        date_key = row.get('DATE') or row.get('observation_date')
        v = row.get(name)
        if not v or v == '.':
            continue
        try:
            out.append({'date': row.get('DATE') or row.get('observation_date'), 'value': float(v)})
        except Exception:
            pass
    return out

def rolling_std_of_changes(series, win):
    vals = [x['value'] for x in series]
    dates = [x['date'] for x in series]
    out = []
    diffs = [None]
    for i in range(1, len(vals)):
        diffs.append(vals[i]-vals[i-1])
    for i in range(len(vals)):
        if i < win or diffs[i] is None:
            continue
        w = [x for x in diffs[i-win+1:i+1] if x is not None]
        if len(w) < win:
            continue
        mean = sum(w)/len(w)
        var = sum((x-mean)**2 for x in w)/len(w)
        out.append({'date': dates[i], 'value': math.sqrt(var)})
    return out

def spread(a, b):
    bm = {x['date']: x['value'] for x in b}
    out = []
    for x in a:
        y = bm.get(x['date'])
        if y is not None:
            out.append({'date': x['date'], 'value': x['value'] - y})
    return out

series = {}
for name, url in SERIES.items():
    text = fetch_csv(url)
    series[name] = parse_fred(text, name)

series['SOFR_minus_DGS10_proxy'] = spread(series['SOFR'], series['DGS10'])
series['SOFR_minus_DGS30_proxy'] = spread(series['SOFR'], series['DGS30'])
series['SOFR_20d_vol'] = rolling_std_of_changes(series['SOFR'], 20)
series['TGCR_20d_vol'] = rolling_std_of_changes(series['TGCR'], 20)
series['BGCR_20d_vol'] = rolling_std_of_changes(series['BGCR'], 20)

OUT.write_text(json.dumps(series, ensure_ascii=False))
print(f'wrote {OUT}')
