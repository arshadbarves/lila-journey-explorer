# LILA BLACK · Player Journey Explorer
A browser tool for Level Designers to explore player journeys, combat, loot and storm deaths on the three LILA BLACK maps.

**Live URL:** _<paste your deployed URL here>_ · Docs: [INTERVIEW_PREP.md](INTERVIEW_PREP.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [INSIGHTS.md](INSIGHTS.md)

**Walkthrough video:** _<paste link>_ (script: see the demo section of [INTERVIEW_PREP.md](INTERVIEW_PREP.md))

## Design
Styled after lilagames.com: near-black `#0c0c0d` base, editorial bold type with wide-tracked wordmark, uppercase micro-labels, pill controls and a white pill call-to-action. The header, and PNG exports, use `web/brand/logo.svg`, a placeholder LILA wordmark. To use the official logo, replace that file (keep the name, or edit the `<img class="lg">` src in `index.html` for a PNG).

## Tech stack
- **Pipeline:** Python 3.12 · pandas · pyarrow · numpy · Pillow
- **Frontend:** vanilla JavaScript + HTML5 Canvas (single `index.html`, no framework, no build step)
- **Tests / CI:** pytest · GitHub Actions · **Hosting:** any static host (Vercel, Netlify, GitHub Pages)
- **Env vars:** none

## Features (walkthrough)
- **Journeys on the correct minimap**: world→minimap mapping per README; zoom (scroll) / pan (drag) / reset.
- **Humans vs bots**: cyan solid line + ● dot vs grey dashed line + ■ dot (classified from the event stream).
- **Events as distinct markers**: loot ◆, kill ●, killed ✕, killed-by-storm ◎ (toggle each in the View panel; hover for details).
- **Filters**: map, date and match in the top bar (searchable match list sorted by "most action"); humans/bots and event types in the floating panel.
- **Clean by design**: the panel shows journey controls *or* heatmap controls, never both; the timeline appears only when it applies.
- **Playback**: play/pause (Space), scrub, 1–60× speed. With "All matches" selected it replays every match on a shared match clock.
- **Shareable links**: every filter, the timeline position and the heatmap mode live in the URL hash. “Copy link” gives a designer a link to the exact view.
- **Export PNG**: saves the current view with a caption, for design reviews and tickets.
- **Compare dates (diff heatmap)**: pick a second date; orange = more activity in the selection, blue = more in the compared date. Grids are normalised by share, so different sample sizes compare fairly.
- **Heatmaps**: traffic, kill zones, death zones, loot, storm deaths; opacity slider; honours filters and the timeline.

## Setup & run locally
```bash
pip install pandas pyarrow pillow            # only needed to rebuild data
python pipeline/build_data.py path/to/player_data web   # incremental: only new/changed days are processed (--force = rebuild all)
python -m http.server -d web 8000            # open http://localhost:8000
```
No env vars. `python analysis/insights.py` reproduces the numbers in INSIGHTS.md.

## Deploy (static)
- **Vercel:** import the repo and deploy (`vercel.json` points to `web/`; no build step).
- **Netlify:** import the repo (`netlify.toml` sets publish = `web`; no build step). (Or drag the `web/` folder into Netlify Drop.)

## Tests & CI
`pip install pytest && pytest -q tests` checks the generated data contract (coordinate mapping, in-bounds pixels, time-ordered, valid event codes, no duplicate combat events). GitHub Actions (`.github/workflows/ci.yml`) runs the tests plus a JS syntax check on every push/PR and **deploys `web/` to GitHub Pages** on `main` (repo Settings → Pages → Source: GitHub Actions).

## Scaling in one paragraph
The pipeline streams one day at a time and is incremental; the web data is sharded (`web/data/<Map>/<Day>_<k>.json`), with a small per-map manifest (`index.json`) and pre-aggregated heat grids (`agg_<Day>.json`). The browser lazy-loads only what the current selection needs, virtualises the match list, draws at most 120 sampled journeys in aggregate view, and computes heatmaps from the aggregates, so cost stays flat as data grows. Details and the 100–1000× plan: [SCALING.md](SCALING.md).

## Layout
`pipeline/` parquet → JSON/WebP · `web/` static app + generated data · `analysis/` insight stats
