# Insights (all numbers reproducible with `python analysis/insights.py`)

## 1. This is functionally a PvE game in the data: players almost never meet each other
**What caught my eye:** the Kill/Killed filters are nearly empty.
**Evidence:** 797 match records, only **6 PvP events (3 kills)** vs 2,376 bot kills. 401 of 443 human deaths (**91 %**) are by bots, 39 (9 %) by storm, ≈0 by humans. 744/797 matches contain a single human journey and no bots; only 52 matches have bot journeys at all.
**Actionable?** Yes (with a data check first: if this is a sampling artifact, ignore). Metrics: PvP encounter rate, time-to-first-contact, share of deaths by cause, lobby fill rate. Actions: confirm matchmaking/lobby sizes; if lobbies are genuinely sparse, add bot density/POI contest rather than tuning chokepoints for PvP; stop using PvP-based balance assumptions for sightlines and cover.
**Why a level designer cares:** every chokepoint and sightline is tuned for player-vs-player tension that currently isn't happening.

## 2. Fights and loot concentrate in a handful of cells while big areas go unused
**What caught my eye:** the Ambrose Valley kill-zone heatmap is a few red blobs around the centre plus 4 outposts.
**Evidence:** on Ambrose, **3 of 256 grid cells (1.2 % of area) hold 21 % of all bot kills**, and the 3 hottest loot cells hold **17 % of all loot** (top 5: 27 %). The top 10 % of visited cells carry **39 %** of human movement (Grand Rift 32 %, Lockdown 36 %). Only 129/256 (Ambrose), 110/256 (Grand Rift) and 98/256 (Lockdown) grid cells see any human traffic; 34 of Ambrose's 129 visited cells get <0.2 % each.
**Actionable?** Yes. Metrics: map-area utilisation, loot-per-cell Gini, time-to-first-loot, kills per km². Actions: move high-tier loot/objectives into cold regions (west and far-east edges of Ambrose), add rotation reasons through the quiet roads, and check whether the central cluster over-saturates early.
**Why:** unused map area is production cost that players never see, and a single hot centre makes every match feel identical.

## 3. The storm is a late-game event most players never reach
**What caught my eye:** only 39 storm-death markers across 5 days.
**Evidence:** earliest storm death at **655 s**, median **739 s**; yet the median journey is **362 s** and only **133/798 (16.7 %)** of human journeys last ≥655 s. Storm = **9 %** of human deaths (Ambrose 17, Lockdown 17, Grand Rift 5; the 5 Grand Rift deaths sit in just 5 cells). Bots kill humans at a median of ~270 s on Ambrose, long before the storm matters.
**Actionable?** Yes, with caveat: no extraction event exists, so non-death journeys could be extractions or quits. Metrics: % of journeys reaching storm onset, storm-death rate, extraction rate, session length. Actions: test an earlier/faster storm or shorter matches to create the extraction pressure the design intends; review the Grand Rift corners where storm victims end up.
**Why:** the storm is supposed to push players across the map; for ~83 % of journeys it never influences routing, so layout pacing is decided by bots, not by the storm.
