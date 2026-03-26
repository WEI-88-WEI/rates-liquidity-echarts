# rates-liquidity-echarts

Historical rates/liquidity dashboard built with public data and ECharts.

## Data included
- SOFR
- TGCR
- TGCR Volume
- BGCR
- DGS10 / DGS30
- SOFR-Treasury proxy spreads (placeholder until richer swap source is wired)
- OFR repo market series: GCF Treasury rate/volume, Tri-Party Treasury rate/volume, DVP overnight rate/volume

## Run
Open `public/index.html` in a browser after generating `data/combined.json`.

## Update data
```bash
python3 scripts/fetch_data.py
```


> Note: data source wiring is included; if remote public sources throttle from this environment, the app still boots with empty series and can be refreshed locally.
