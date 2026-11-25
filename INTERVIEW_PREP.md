# Interview prep: how this was built (and how to talk about it)

## 30-second pitch
"I built a static web tool for Level Designers. A Python pipeline turns the parquet telemetry into small per-map JSON files and 1024px minimaps. A single-file vanilla JS app draws journeys, events, a replay timeline and heatmaps on canvas. No backend, so it deploys anywhere for free. The interesting work was in the data: timestamps, bot detection, duplicates and coordinate mapping."

## Build order (what I actually did)
1. **Read the brief and README**, then profiled the data before designing anything: 89,104 rows, 1,242 unique files, 796 matches, 339 users.
2. **Found the data traps** (these are your best interview stories):
   - `ts` is labelled milliseconds but is really **Unix seconds**. Proof: values ≈ 1.77e9 give Feb 2026 as seconds; positions step by 5 units; matches last 13–890 units (≈ 7 min avg). Read as ms, a match would last 0.4 s.
   - README says bots = numeric IDs, but **users 1429/1402/1379** emit human `Position`/`Loot` events. I classify by event stream (`BotPosition` ⇒ bot).
   - **1,505 duplicate rows**, including one whole file in two day folders.
   - README says minimaps are 1024², but real files are 4320², 2160×2158, 9000².
   - Most matches have only **1 human**; only 52 matches have bot journeys; only 3 PvP kills.
3. **Pipeline** (`pipeline/build_data.py`): decode bytes → dedupe → match-relative time → classify actor → world→pixel conversion → emit flat-array JSON + WebP minimaps.
4. **Validated the mapping visually**: plotted every point over each minimap. Paths follow roads/river on Ambrose, the cave layout on Grand Rift, and avoid the water on Lockdown. Also checked all points fall in 0–1 UV.
5. **Frontend** in one HTML file: canvas renderer, filters, timeline, heatmap, zoom/pan, tooltips.
6. **Smoke-tested** in headless Chromium (Playwright): no console errors, stats match my Python analysis.
7. **Insights** from `analysis/insights.py`, so every number is reproducible.
8. **UI polish**: studio-grey theme; hid markers under aggregate heatmaps after seeing they drowned the heat.

## Coordinate mapping (be ready to whiteboard this)
`u=(x−ox)/scale`, `v=(z−oz)/scale`, `px=u·1024`, `py=(1−v)·1024`. Use **x and z** (y = height). Flip Y because images have a top-left origin but world Z grows "up". Map params: Ambrose 900/(−370,−473), Grand Rift 581/(−290,−290), Lockdown 1000/(−500,−500). Because UV is normalised, resizing the image never breaks the mapping.

## Key technical decisions and the "why"
| Question | Answer |
|---|---|
| Why no backend? | 89k rows = 3.4 MB JSON. A server adds ops and latency for no gain. Trade-off: re-run the pipeline when data changes. |
| Why vanilla JS, not React? | Single view, one shared state object, fastest to ship; canvas does the heavy lifting. Would move to React/Vite if it grows to many views/teams. |
| Why canvas, not SVG/Leaflet? | Tens of thousands of points; canvas stays smooth, SVG would choke. |
| How is the heatmap made? | Each point adds a Gaussian kernel to a 256² float grid; I normalise at the 97th percentile (so outliers don't wash it out), map value→blue-to-red colour with alpha, then scale it over the map. Recomputed on filter/time change and cached by key. |
| How does replay work? | All timestamps are match-relative seconds. The slider sets cursor `t`; I draw path points with `time ≤ t`, show events up to `t`, and interpolate each player's dot between 5 s samples (binary search). |
| How are bots vs humans shown? | Colour + line style + dot shape (not colour alone, for accessibility). |
| Why pixels in the JSON, not world coords? | One source of truth for the mapping, simpler client. Cost: world coordinates are lost in the web data (raw data still has them). |
| Data-size/perf choices? | Flat numeric arrays (`[t,x,y,…]`) instead of objects; per-map lazy loading; 1 decimal precision. |

## Likely questions, short answers
- **What was hardest?** Finding that `ts` isn't what the README says, and deciding bot vs human when the ID rule and event rule disagree.
- **How did you verify correctness?** Visual overlay on all maps, UV bounds check, cross-checking UI stats against a pandas-style script, headless browser run.
- **What assumptions did you make?** Listed in ARCHITECTURE.md (timestamps, event-based bot rule, dedupe incl. loot, folder = date, no extraction event).
- **What would you do with more time?** Shareable URLs for filters, per-player paths coloured by outcome, extraction/quit detection, a cold-zone ("unused area") overlay, unit tests for the pipeline, higher-res zoom tiles, and automated deploy from CI.
- **Weaknesses I'd admit:** 
  - Loot duplicates may be legit multi-pickups, so loot counts could be ~10 % low.
  - The traffic heatmap saturates in busy areas (97th-percentile cap is a choice).
  - Most matches are single-human, so "match replay" is mostly one journey; the aggregate mode is where the value is.
  - No automated tests. The pipeline was checked by inspection and the UI by a smoke test.
  - Large aggregate replays recompute the heatmap every 3 s of match time and may stutter on slow machines.
- **Using AI?** The brief allowed it. I used Claude for coding speed but I owned the data investigation, the decisions and the verification. Be ready to explain any line of `build_data.py`.

## Numbers to remember
89,104 rows → 87,599 after dedupe · 1,242 files · 796 matches · 339 users · Ambrose 566 / Lockdown 171 / Grand Rift 59 matches · 6 PvP events · 91 % of human deaths by bots · storm deaths 39 (first at 655 s) · only 16.7 % of journeys reach 655 s · top 3 Ambrose cells = 21 % of bot kills.

## 2-minute demo script
Open Ambrose → show the top-action match, press Play (10×) → toggle humans/bots → hover a kill marker → switch to All matches → Kill zones heatmap → Loot → switch to Lockdown → Storm deaths → explain Insight 3.

## Studio-grade additions (be ready to explain)
- **URL state**: app state is serialised into `location.hash` (`history.replaceState`), parsed on load. Why hash: static hosting needs no server routing. Restores map/date/match/filters/heat/time.
- **Diff heatmap**: two splatted grids, each divided by its own total (share of activity), subtracted; sign picks orange/blue. Answers "did a change or a day shift behaviour?" the way A/B build comparisons do in studios.
- **Tests**: found a real nuance: loot rows that differ only by elevation collapse to the same 2D pixel, so the duplicate test applies to combat events only.
- **CI/CD**: test job (pytest + `node --check`) gates a GitHub Pages deploy.
- **Studio pipeline vs mine**: they run telemetry → data lake (Parquet) → scheduled warehouse jobs → dashboards/in-editor heatmaps. Mine is the same shape at prototype scale: `build_data.py` is the batch job, `web/data` is the serving layer.
- **Not built (say so honestly)**: per-player drill-down, saved named views, multi-build diff, API/warehouse backend.

## Scalability (likely follow-up: "what if the data were 1000x bigger?")
- **Principle:** make cost depend on what is *on screen*, not on what is *in the dataset*. Population questions → pre-aggregated grids; detail questions → lazy shards + sampling.
- **Pipeline:** per-day streaming (bounded memory), incremental by file-list fingerprint, partitioned output `<Map>/<Day>`. At scale: scheduled jobs, parallel per day, warehouse (BigQuery/DuckDB) instead of local pandas.
- **Frontend:** manifest-first loading, lazy shard fetch with a stale-selection guard (token), windowed list, deterministic sampling (≤120 matches), cached shards/aggregates.
- **Measured:** first load 484 KB (was 2.3 MB+); full-population heatmap 274 KB; match list 13 DOM nodes for 568 items; tests prove aggregates == per-match counts and the manifest == shard contents.
- **Honest limits:** aggregate grids are fixed at 256² (no zoom pyramid yet); population heat ignores the timeline; manifest is one file per map (page/shard it beyond ~100k matches); one match straddling two folders becomes two records.
