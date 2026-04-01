# MEMORY.md

## Preferences

- User wants x-list-digest outputs to follow the reference style from `x-info/skills/x-list-digest/data/2026-03-20/00:02:42~09:10:19.md`.
- `全部列表总结` must be real synthesis, not excerpt stitching.
- `全部列表总结` should use exactly 3 bullets with fixed openings:
  1. `交易主线还是围着高波动里的被动应对展开：`
  2. `宏观和结构性压力仍然在：`
  3. `机会侧还是有东西可做，但更偏执行型：`
- Each summary bullet should contain only 1-2 hard facts: prices, events, numbers, flows, project names, or explicit actions.
- Do not use filler/meta lines like `今天信息密度最高的列表` / `跨列表主线` / `噪音主要集中在`.
- Do not paste long raw tweet wording into `全部列表总结`; rewrite into compressed Chinese prose first.
- Prefer fewer, sharper items; filter aggressively.
- Drop obvious noise from alias sections too: personal updates, blogger recommendations, generic motivation, sports metaphors, emotional venting, and broad hot-take lists.
- User explicitly disliked excerpt-style summaries and wants future sessions to preserve this format preference.

## Projects

- The user now uses `fwalert` for phone alerts.
- For the `price-alerts` project, keep the fwalert trigger URL out of GitHub and store it locally via environment variables only.
- Create a new repo/project named `price-alerts` (English naming) for the user's price notification work.

- `preps-arbitrage` is a new multi-platform arbitrage dashboard project.
- Future target venues: `trade.xyz`, `ostium`, `lighter`, `edgex`, `asterdex`, `extended`, `pacifica`.
- Phase 1 should only integrate `trade.xyz`, `ostium`, and `lighter` first; do not rush all venues at once.
- Project should be implemented primarily in Python and should use a dedicated virtual environment on the server.
- Core reference repo is `https://github.com/DING-88-DING/trade.xyz-ostium`, which already contains early `trade.xyz` + `ostium` logic and should be reused/refactored where helpful.
- Core logic: compare 1M-volume-level symbols pairwise across venues, assume spread converges to 0, subtract fees on both venues, and alert only when net profit remains positive.
- Product form should be a scalable arbitrage panel/dashboard for multiple venues, not just the old two-venue presentation.
- In new sessions, remember that the user may continue defining requirements for `preps-arbitrage`, and the assistant should retain the project goal and current phase.
