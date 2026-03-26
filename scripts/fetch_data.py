import csv, io, json, math, os, tempfile
from pathlib import Path

import requests
import xlrd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT = DATA_DIR / 'combined.json'
START = '2025-01-01'
END = '2026-03-26'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


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


def merge_years(col):
    merged = []
    for y in [2025, 2026]:
        merged.extend(parse_treasury(treasury_year(y), col))
    merged.sort(key=lambda x: x['date'])
    return merged


def rolling_std_of_changes(series, win):
    vals = [x['value'] for x in series]
    dates = [x['date'] for x in series]
    out = []
    diffs = [None]
    for i in range(1, len(vals)):
        diffs.append(vals[i] - vals[i - 1])
    for i in range(len(vals)):
        if i < win or diffs[i] is None:
            continue
        w = [x for x in diffs[i - win + 1:i + 1] if x is not None]
        if len(w) < win:
            continue
        mean = sum(w) / len(w)
        var = sum((x - mean) ** 2 for x in w) / len(w)
        out.append({'date': dates[i], 'value': math.sqrt(var)})
    return out


def dataset_timeseries(name):
    u = f'https://data.financialresearch.gov/v1/series/dataset?dataset={name}'
    r = requests.get(u, timeout=90, headers=HEADERS)
    r.raise_for_status()
    return r.json()['timeseries']


def dataset_series(dataset, mnemonic, start=START, end=END):
    data = dataset[mnemonic]['timeseries']['aggregation']
    out = []
    for d, v in data:
        if d < start or d > end or v is None:
            continue
        out.append({'date': d, 'value': float(v)})
    return out


fnyr = dataset_timeseries('fnyr')
repo = dataset_timeseries('repo')

series = {}
# NY Fed secured rates + percentiles + underlying volume from OFR mirror dataset
fnyr_map = {
    'SOFR': 'FNYR-SOFR-A',
    'SOFR_P1': 'FNYR-SOFR_1Pctl-A',
    'SOFR_P25': 'FNYR-SOFR_25Pctl-A',
    'SOFR_P75': 'FNYR-SOFR_75Pctl-A',
    'SOFR_P99': 'FNYR-SOFR_99Pctl-A',
    'SOFR_UV': 'FNYR-SOFR_UV-A',
    'TGCR': 'FNYR-TGCR-A',
    'TGCR_P1': 'FNYR-TGCR_1Pctl-A',
    'TGCR_P25': 'FNYR-TGCR_25Pctl-A',
    'TGCR_P75': 'FNYR-TGCR_75Pctl-A',
    'TGCR_P99': 'FNYR-TGCR_99Pctl-A',
    'TGCR_UV': 'FNYR-TGCR_UV-A',
    'BGCR': 'FNYR-BGCR-A',
    'BGCR_P1': 'FNYR-BGCR_1Pctl-A',
    'BGCR_P25': 'FNYR-BGCR_25Pctl-A',
    'BGCR_P75': 'FNYR-BGCR_75Pctl-A',
    'BGCR_P99': 'FNYR-BGCR_99Pctl-A',
    'BGCR_UV': 'FNYR-BGCR_UV-A',
}
for out_name, mnemonic in fnyr_map.items():
    series[out_name] = dataset_series(fnyr, mnemonic)

# Backward-compatible single-point aliases removed; use full UV history instead
series['SOFRVOLUME'] = series['SOFR_UV']
series['TGCRVOLUME'] = series['TGCR_UV']
series['BGCRVOLUME'] = series['BGCR_UV']

series['DGS10'] = merge_years('10 Yr')
series['DGS30'] = merge_years('30 Yr')

repo_mnemonics = {
    'REPO_GCF_AR_T': 'REPO-GCF_AR_T-F',
    'REPO_GCF_TV_T': 'REPO-GCF_TV_T-F',
    'REPO_TRI_AR_T': 'REPO-TRI_AR_T-F',
    'REPO_TRI_TV_T': 'REPO-TRI_TV_T-F',
    'REPO_DVP_AR_OO': 'REPO-DVP_AR_OO-F',
    'REPO_DVP_TV_OO': 'REPO-DVP_TV_OO-F',
}
for out_name, mnemonic in repo_mnemonics.items():
    series[out_name] = dataset_series(repo, mnemonic)

series['SOFR_20d_vol'] = rolling_std_of_changes(series['SOFR'], 20)
series['TGCR_20d_vol'] = rolling_std_of_changes(series['TGCR'], 20)
series['BGCR_20d_vol'] = rolling_std_of_changes(series['BGCR'], 20)
series['REPO_GCF_AR_T_20d_vol'] = rolling_std_of_changes(series['REPO_GCF_AR_T'], 20)
series['REPO_TRI_AR_T_20d_vol'] = rolling_std_of_changes(series['REPO_TRI_AR_T'], 20)
series['REPO_DVP_AR_OO_20d_vol'] = rolling_std_of_changes(series['REPO_DVP_AR_OO'], 20)

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
for k, v in series.items():
    print(k, len(v))
