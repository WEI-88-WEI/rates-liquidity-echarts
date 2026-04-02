# rates-liquidity-echarts

A static historical rates/liquidity dashboard built with ECharts and repository-managed JSON data.

## What this repo is

This project serves a browser-based dashboard from static files in the repository.

- Frontend page: `public/index.html`
- Main dataset: `data/combined.json`
- Optional static swap source: `data/swap_static.json`
- Helper script: `scripts/fetch_data.py`

The dashboard does **not** depend on a live backend.

## Deployment

This repository no longer uses a GitHub Actions workflow for Pages deployment.

GitHub Pages is configured in **branch mode** (`main` / root), while the dashboard source file lives in `public/index.html`.

That means:

- there is no scheduled Actions deployment anymore
- there is no workflow-based Pages publish step anymore
- if you want the live site to reflect repository changes, make sure the published branch/root layout matches what GitHub Pages is serving

## Included data

The dashboard currently includes historical/static series such as:

- SOFR
- TGCR
- BGCR
- DGS10 / DGS30
- USD 10Y / 30Y swap rate (repository-managed static series)
- 10Y / 30Y swap spread (derived from swap rate minus Treasury)
- OFR repo market series:
  - GCF Treasury rate / volume
  - Tri-Party Treasury rate / volume
  - DVP overnight rate / volume
- FRBNY 2023 long-end proxy series

## Local use

You can inspect the dashboard locally by opening:

- `public/index.html`

in a browser.

If your browser blocks local file access for JSON, serve the repo with a tiny local HTTP server instead:

```bash
python3 -m http.server 8000
```

Then open the appropriate path in your browser.

## Data model

### `data/combined.json`

This is the single JSON file read by the dashboard.

### `data/swap_static.json`

This file is used to maintain static 10Y/30Y USD swap series inside the repo.

### `scripts/fetch_data.py`

Despite the name, this script does **not** fetch remote data anymore.

It only:

- loads `data/combined.json`
- loads `data/swap_static.json`
- writes `USD_SWAP_10Y`
- writes `USD_SWAP_30Y`
- recomputes `SWAP_SPREAD_10Y`
- recomputes `SWAP_SPREAD_30Y`
- saves the updated result back into `data/combined.json`

## Updating data

If you update static swap series, rebuild the combined file with:

```bash
python3 scripts/fetch_data.py
```

Then commit and push the changed JSON files.

## Notes

- This repo is currently maintained as a **static-data** dashboard.
- There is no live data refresh pipeline in the repository at the moment.
- If deployment strategy changes again later, update this README to match the actual Pages source and publish flow.
