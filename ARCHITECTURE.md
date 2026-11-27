# Architecture

**Stack:** Python (pandas, pyarrow, Pillow) offline pipeline → sharded static JSON + WebP minimaps → single-file vanilla JS app on `<canvas>`. No backend, no build step, no env vars; deploys to any static host.
*Why:* the data is small (~88k rows) and read-only, so precomputing in Python keeps parquet/bytes/dedupe logic out of the browser and makes the tool instant, free to host and shareable with designers. Scaling beyond this: see [SCALING.md](SCALING.md).

## Data flow
`player_data/*/*.nakama-0` (parquet) → `pipeline/build_data.py` → `web/data/<Map>/{index.json, <Day>_<k>.json, agg_<Day>.json}` + `web/maps/*.webp` → `web/index.html`
1. Stream one day-folder at a time; decode `event` bytes → str; dedupe exact duplicate rows; derive match-relative time; classify human/bot; convert world → minimap pixels.
2. Emit per map: a manifest (one small row per match), shards of ≤100 matches (`players[] → {p:[t,x,y…], e:[t,code,x,y…]}`), and pre-aggregated 256² count grids per heat layer.
3. The browser loads the manifest, lazily fetches only needed shards/aggregates, filters (map/date/match/actor/event), draws paths + markers up to the timeline cursor, and renders heatmaps by blurring count grids (single match: from raw points).

## Coordinate mapping
README formula: `u=(x−origin_x)/scale`, `v=(z−origin_z)/scale`, `px=u·1024`, `py=(1−v)·1024` (image Y is flipped). Only `x` and `z` are used (`y` is elevation). Applied once in the pipeline, so the client works in 1024-px minimap space; zoom/pan is a canvas transform.
**Verified** by (a) every point falling in 0≤u,v≤1, (b) overlaying all points: paths follow roads/river (Ambrose), cave layout (Grand Rift), and avoid the water (Lockdown), (c) a unit test on a worked example.
**Gotcha:** the README says minimaps are 1024², but files are 4320², 2160×2158 and 9000². UV is normalised, so I resample each to 1024² (Grand Rift is 0.09 % non-square; ignored).

## Assumptions / data quirks
| Finding | Handling |
|---|---|
| `ts` is labelled ms but is **Unix seconds** (≈1.77e9 = Feb 2026; 5-unit sampling; matches last 13–890). README calls it match-relative. | Match time = `ts − min(ts)` per match, in seconds. |
| Users `1429`, `1402`, `1379` have numeric IDs (README: bots) but emit human `Position`/`Loot` events. | Human/bot from the **event stream** (`BotPosition` ⇒ bot); UUID pattern only as fallback. |
| 1,505 duplicate rows (89,104 → 87,599), incl. one file in two day folders; 1,237 are `Loot` (maybe multi-pickups). | Dedupe on the full row; first folder wins. Loot counts may be slightly low. |
| 744/797 matches have 1 human and no bots; 52 have bot journeys; 3 PvP kills in total. One match straddles two day folders (797 vs 796 records). | Documented; aggregate views carry the value. |
| Day folders ≈ UTC day of match start. No extraction event exists. | Folder name = date filter; extraction not inferred. |
| Event position = the logging player's position (killer for `Kill/BotKill`, victim for `Killed/BotKilled`). | Not merged across files; filterable by Humans/Bots. |

## Trade-offs
| Decision | Alternative | Why / cost |
|---|---|---|
| Static sharded JSON + pre-aggregates | Backend + DuckDB/parquet API | CDN-friendly, zero ops. Ad-hoc queries need new pipeline output. |
| Vanilla JS + canvas, one file | React/Vite, Leaflet, WebGL | Fastest to ship; handles tens of thousands of points. Less modular if it grows. |
| Heatmap from count grids (population) / raw points (one match) | Pre-baked PNGs | Respects date/actor/compare filters at constant cost. Population heat ignores the timeline. |
| 1024-px WebP minimaps (~70 KB) | Full-res tiles | Matches README space; fast. No fine-detail zoom. |
| ≤120 sampled journeys in aggregate view | Draw everything | Smooth at any size; stats/heatmaps still use 100 % of data. |
