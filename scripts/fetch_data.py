import csv, io, json, math, os, tempfile, re, time
from pathlib import Path

import requests
import xlrd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
OUT = DATA_DIR / 'combined.json'
START = '2025-01-01'
END = '2026-03-26'
HEADERS = {'User-Agent': 'Mozilla/5.0'}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get_with_retries(url, *, timeout=30, attempts=4, sleep=2, stream=False):
    last_err = None
    for i in range(attempts):
        try:
            r = SESSION.get(url, timeout=timeout, stream=stream)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_err = e
            if i == attempts - 1:
                raise
            time.sleep(sleep * (i + 1))
    raise last_err


def treasury_year(year):
    u = f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv'
    return get_with_retries(u, timeout=30).text


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


def fred_csv_series(series_id, start=START, end=END):
    u = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}&coed={end}'
    text = get_with_retries(u, timeout=60).text
    rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    for row in rows:
        d = row.get('DATE')
        v = row.get(series_id)
        if not d or v in (None, '', '.'):
            continue
        out.append({'date': d, 'value': float(v)})
    return out


def align_spread(a, b):
    mb = {x['date']: x['value'] for x in b}
    out = []
    for x in a:
        d = x['date']
        if d in mb:
            out.append({'date': d, 'value': x['value'] - mb[d]})
    return out


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
    return get_with_retries(u, timeout=90).json()['timeseries']


def dataset_series(dataset, mnemonic, start=START, end=END):
    data = dataset[mnemonic]['timeseries']['aggregation']
    out = []
    for d, v in data:
        if d < start or d > end or v is None:
            continue
        out.append({'date': d, 'value': float(v)})
    return out


def norm_excel_date(v):
    if isinstance(v, (int, float)):
        y, m, d, _, _, _ = xlrd.xldate_as_tuple(v, 0)
        return f'{y:04d}-{m:02d}-{d:02d}'
    month_map = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    parts = str(v).split()
    return f"{parts[2]}-{month_map[parts[0][:3]]}-{parts[1].zfill(2)}"


def frb_longend_proxy_2023():
    files = [
        'https://www.newyorkfed.org/medialibrary/media/markets/DFA/tsy_data_2023_q1.xls',
        'https://www.newyorkfed.org/medialibrary/media/markets/DFA/tsy_data_2023_q2.xls',
        'https://www.newyorkfed.org/medialibrary/media/markets/DFA/tsy_data_2023_q3.xls',
        'https://www.newyorkfed.org/medialibrary/media/markets/DFA/tsy_data_2023_q4.xls',
    ]
    def is_longend(desc):
        m = re.search(r'(\d{2})\s*$', desc.strip())
        if not m:
            return False
        return 2000 + int(m.group(1)) >= 2040
    by = {}
    for u in files:
        try:
            r = get_with_retries(u, timeout=40)
        except requests.RequestException:
            continue
        if 'excel' not in (r.headers.get('content-type') or '').lower():
            continue
        fd, path = tempfile.mkstemp(suffix='.xls')
        os.write(fd, r.content)
        os.close(fd)
        try:
            book = xlrd.open_workbook(path)
            sh = book.sheet_by_name('tsy data')
            for i in range(4, sh.nrows):
                desc = str(sh.cell_value(i, 5)).strip()
                if not is_longend(desc):
                    continue
                d = norm_excel_date(sh.cell_value(i, 0))
                cat = str(sh.cell_value(i, 2)).strip()
                amt = float(sh.cell_value(i, 3))
                rec = by.setdefault(d, {'Purchase': 0.0, 'Sale': 0.0, 'Gross': 0.0, 'Net': 0.0})
                rec[cat] += amt
                rec['Gross'] += amt
                rec['Net'] += amt if cat == 'Purchase' else -amt
        finally:
            os.remove(path)
    purchases, sales, gross, net = [], [], [], []
    for d in sorted(by):
        rec = by[d]
        purchases.append({'date': d, 'value': rec['Purchase']})
        sales.append({'date': d, 'value': rec['Sale']})
        gross.append({'date': d, 'value': rec['Gross']})
        net.append({'date': d, 'value': rec['Net']})
    return purchases, sales, gross, net


fnyr = dataset_timeseries('fnyr')
repo = dataset_timeseries('repo')

series = {}
fnyr_map = {
    'SOFR': 'FNYR-SOFR-A', 'SOFR_P1': 'FNYR-SOFR_1Pctl-A', 'SOFR_P25': 'FNYR-SOFR_25Pctl-A', 'SOFR_P75': 'FNYR-SOFR_75Pctl-A', 'SOFR_P99': 'FNYR-SOFR_99Pctl-A', 'SOFR_UV': 'FNYR-SOFR_UV-A',
    'TGCR': 'FNYR-TGCR-A', 'TGCR_P1': 'FNYR-TGCR_1Pctl-A', 'TGCR_P25': 'FNYR-TGCR_25Pctl-A', 'TGCR_P75': 'FNYR-TGCR_75Pctl-A', 'TGCR_P99': 'FNYR-TGCR_99Pctl-A', 'TGCR_UV': 'FNYR-TGCR_UV-A',
    'BGCR': 'FNYR-BGCR-A', 'BGCR_P1': 'FNYR-BGCR_1Pctl-A', 'BGCR_P25': 'FNYR-BGCR_25Pctl-A', 'BGCR_P75': 'FNYR-BGCR_75Pctl-A', 'BGCR_P99': 'FNYR-BGCR_99Pctl-A', 'BGCR_UV': 'FNYR-BGCR_UV-A',
}
for out_name, mnemonic in fnyr_map.items():
    series[out_name] = dataset_series(fnyr, mnemonic)
series['SOFRVOLUME'] = series['SOFR_UV']
series['TGCRVOLUME'] = series['TGCR_UV']
series['BGCRVOLUME'] = series['BGCR_UV']
series['DGS10'] = merge_years('10 Yr')
series['DGS30'] = merge_years('30 Yr')

repo_mnemonics = {
    'REPO_GCF_AR_T': 'REPO-GCF_AR_T-F', 'REPO_GCF_TV_T': 'REPO-GCF_TV_T-F',
    'REPO_TRI_AR_T': 'REPO-TRI_AR_T-F', 'REPO_TRI_TV_T': 'REPO-TRI_TV_T-F',
    'REPO_DVP_AR_OO': 'REPO-DVP_AR_OO-F', 'REPO_DVP_TV_OO': 'REPO-DVP_TV_OO-F',
}
for out_name, mnemonic in repo_mnemonics.items():
    series[out_name] = dataset_series(repo, mnemonic)

p, s, g, n = frb_longend_proxy_2023()
series['FRBNY_LONGEND_PURCHASES_2023'] = p
series['FRBNY_LONGEND_SALES_2023'] = s
series['FRBNY_LONGEND_GROSS_2023'] = g
series['FRBNY_LONGEND_NET_2023'] = n

series['SOFR_20d_vol'] = rolling_std_of_changes(series['SOFR'], 20)
series['TGCR_20d_vol'] = rolling_std_of_changes(series['TGCR'], 20)
series['BGCR_20d_vol'] = rolling_std_of_changes(series['BGCR'], 20)
series['REPO_GCF_AR_T_20d_vol'] = rolling_std_of_changes(series['REPO_GCF_AR_T'], 20)
series['REPO_TRI_AR_T_20d_vol'] = rolling_std_of_changes(series['REPO_TRI_AR_T'], 20)
series['REPO_DVP_AR_OO_20d_vol'] = rolling_std_of_changes(series['REPO_DVP_AR_OO'], 20)

series['USD_SWAP_10Y'] = fred_csv_series('ICERATES1100USD10Y')
series['USD_SWAP_30Y'] = fred_csv_series('ICERATES1100USD30Y')
series['SWAP_SPREAD_10Y'] = align_spread(series['USD_SWAP_10Y'], series['DGS10'])
series['SWAP_SPREAD_30Y'] = align_spread(series['USD_SWAP_30Y'], series['DGS30'])
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
