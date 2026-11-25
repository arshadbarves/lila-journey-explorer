# Scaling design (huge / many datasets)
| Concern | What scales it | Cost model |
|---|---|---|
| Pipeline memory | Streams **one day-folder at a time**; per-day output; cross-folder duplicate files skipped by name | Memory ∝ largest day, not the dataset |
| Re-runs | **Incremental**: a day whose file list+sizes are unchanged is skipped (`--force` rebuilds); cache in `.pipeline_state/` (not deployed) | New day = O(new day) |
| Initial page load | Manifest + lazy shards (measured: **484 KB** vs 2.3 MB+ before for Ambrose) | O(manifest), ~80 B/match |
| Match list UI | **Virtualised** list (13 DOM rows for 568 matches) + search | O(visible rows) |
| Heatmaps over everything | Server-side **pre-aggregated grids**; client sums + blurs a 256² grid (measured: **274 KB** for all 567 matches) | O(grid), independent of event count |
| Journey rendering | **Level of detail**: ≤120 deterministically sampled matches drawn as raw journeys; stats come from the manifest; heatmaps use the full population | Bounded draw cost |
| Many maps/days/builds | Layout is partitioned `<Map>/<Day>`; add a build/season level, per-map manifests stay small | Partition pruning |
**Next steps at 100–1000× scale:** replace the local batch with scheduled warehouse jobs (parquet → DuckDB/BigQuery), run per-day jobs in parallel, shard the manifest per map/day (paged), serve shards/aggregates from object storage + CDN (immutable, gzip/brotli, content-hashed names), add finer aggregate pyramids (zoom-level grids, time buckets) and an API for ad-hoc queries.

