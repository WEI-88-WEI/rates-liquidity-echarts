# rates-liquidity-echarts

Historical rates/liquidity dashboard built with public data and ECharts.

## Data included
- SOFR
- TGCR
- TGCR Volume
- BGCR
- DGS10 / DGS30
- SOFR-Treasury proxy spreads (placeholder until richer swap source is wired)

## Run
Open `public/index.html` in a browser after generating `data/combined.json`.

## Update data
```bash
python3 scripts/fetch_data.py
```
