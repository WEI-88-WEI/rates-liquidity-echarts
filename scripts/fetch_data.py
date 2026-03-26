import csv, io, json, math, requests
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT = DATA_DIR / 'combined.json'
START = '2025-01-01'
END = '2026-03-26'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def nyfed_series(name):
    u = f'https://markets.newyorkfed.org/api/rates/secured/{name}/search.json?startDate={START}&endDate={END}&type=rate'
    r = requests.get(u, timeout=30, headers=HEADERS)
    r.raise_for_status()
    rows = r.json()['refRates']
    out = []
    for x in rows:
        out.append({'date': x['effectiveDate'], 'value': float(x['percentRate'])})
    out.sort(key=lambda x: x['date'])
    return out


def nyfed_last_volume(name):
    u = f'https://markets.newyorkfed.org/api/rates/secured/{name}/last/1.json'
    r = requests.get(u, timeout=30, headers=HEADERS)
    r.raise_for_status()
    rows = r.json()['refRates']
    out = []
    for x in rows:
        if 'volumeInBillions' in x:
            out.append({'date': x['effectiveDate'], 'value': float(x['volumeInBillions'])})
    return out


def treasury_year(year):
    u = f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv'
    r = requests.get(u, timeout=30, headers=HEADERS)
    r.raise_for_status()
    return r.text


def parse_treasury(text, col):
    rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    for row in rows:
        v = row.get(col)
        if not v:
            continue
        mm, dd, yyyy = row['Date'].split('/')
        out.append({'date': f'{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}', 'value': float(v)})
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


def merge_years(col):
    merged = []
    for y in [2025, 2026]:
        merged.extend(parse_treasury(treasury_year(y), col))
    merged.sort(key=lambda x: x['date'])
    return merged

series = {}
series['SOFR'] = nyfed_series('sofr')
series['TGCR'] = nyfed_series('tgcr')
series['BGCR'] = nyfed_series('bgcr')
series['SOFRVOLUME'] = nyfed_last_volume('sofr')
series['TGCRVOLUME'] = nyfed_last_volume('tgcr')
series['BGCRVOLUME'] = nyfed_last_volume('bgcr')
series['DGS10'] = merge_years('10 Yr')
series['DGS30'] = merge_years('30 Yr')
series['SOFR_20d_vol'] = rolling_std_of_changes(series['SOFR'], 20)
series['TGCR_20d_vol'] = rolling_std_of_changes(series['TGCR'], 20)
series['BGCR_20d_vol'] = rolling_std_of_changes(series['BGCR'], 20)
series['SOFR_minus_DGS10_proxy'] = []
series['SOFR_minus_DGS30_proxy'] = []

m10 = {x['date']: x['value'] for x in series['DGS10']}
m30 = {x['date']: x['value'] for x in series['DGS30']}
for x in series['SOFR']:
    d = x['date']
    if d in m10:
        series['SOFR_minus_DGS10_proxy'].append({'date': d, 'value': x['value'] - m10[d]})
    if d in m30:
        series['SOFR_minus_DGS30_proxy'].append({'date': d, 'value': x['value'] - m30[d]})

OUT.write_text(json.dumps(series, ensure_ascii=False, indent=2))
print(f'wrote {OUT}')
for k,v in series.items():
    print(k, len(v))
