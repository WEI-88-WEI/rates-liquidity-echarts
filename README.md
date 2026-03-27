# rates-liquidity-echarts

Historical rates/liquidity dashboard built with static JSON data and ECharts.

## Data included
- SOFR
- TGCR
- BGCR
- DGS10 / DGS30
- USD 10Y / 30Y swap rate (static, repository-managed)
- 10Y / 30Y swap spread (derived from static swap rate minus Treasury)
- OFR repo market series: GCF Treasury rate/volume, Tri-Party Treasury rate/volume, DVP overnight rate/volume
- FRBNY 2023 long-end proxy series

## Run
Open `public/index.html` in a browser.

## Data model
- `data/combined.json` is the single file the page reads.
- `data/swap_static.json` is an optional helper file for maintaining static 10Y/30Y swap series.
- `scripts/fetch_data.py` no longer fetches remote data; it only merges static swap series into `combined.json` and recomputes swap spreads.

## Update data
If you edit `data/swap_static.json`, rebuild the combined file with:

```bash
python3 scripts/fetch_data.py
```

Then commit and push the updated JSON files.
