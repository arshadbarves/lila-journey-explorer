"""Telemetry parquet -> sharded, lazily-loadable web data.
Scales by (1) streaming ONE day-folder at a time (memory bounded by the largest day), (2) being incremental (a day whose
file listing+sizes are unchanged is skipped), (3) emitting small shards + an index + pre-aggregated heat grids so the browser
never has to download or scan raw events.   Usage: python pipeline/build_data.py <player_data_dir> [out_dir=web] [--force]
Output: data/<Map>/index.json (match manifest) · <Day>_<k>.json (<=CHUNK matches each) · agg_<Day>.json (256^2 count grids)"""
import sys, os, json, glob, hashlib
import numpy as np, pandas as pd, pyarrow.parquet as pq
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
args = [a for a in sys.argv[1:] if not a.startswith("--")]; FORCE = "--force" in sys.argv
SRC = args[0]; OUT = args[1] if len(args) > 1 else "web"
MAPS = {"AmbroseValley": (900, -370, -473, "AmbroseValley_Minimap.png"),
        "GrandRift": (581, -290, -290, "GrandRift_Minimap.png"),
        "Lockdown": (1000, -500, -500, "Lockdown_Minimap.jpg")}
EV = {"Loot": 0, "Kill": 1, "Killed": 2, "BotKill": 3, "BotKilled": 4, "KilledByStorm": 5}
CODE = {**EV, "Position": -1, "BotPosition": -1}
LAYERS = {"traffic": (-1,), "kills": (1, 3), "deaths": (2, 4, 5), "loot": (0,), "storm": (5,)}
SZ, G, CHUNK = 1024, 256, 100

def process(day, tag, files, sf, fp):
    raw = pd.concat([pq.read_table(p).to_pandas().assign(file=f) for f, p in files], ignore_index=True)
    raw["event"] = raw["event"].map(lambda b: b.decode() if isinstance(b, bytes) else b)
    raw["t"] = raw["ts"].astype("int64")
    raw = raw.drop_duplicates(["file", "t", "event", "x", "y", "z"]).copy()
    raw["start"] = raw.groupby("match_id")["t"].transform("min"); raw["rt"] = raw["t"] - raw["start"]
    kinds = raw.groupby("file")["event"].agg(set); uid = raw.groupby("file")["user_id"].first()
    bot = {f: 1 if "BotPosition" in s else 0 if "Position" in s else int("-" not in uid[f]) for f, s in kinds.items()}
    raw["bot"] = raw["file"].map(bot); raw["c"] = raw["event"].map(CODE)
    state = {"fp": fp, "maps": {}}
    for m, (scale, ox, oz, _) in MAPS.items():
        for old in glob.glob(f"{OUT}/data/{m}/{tag}_*.json") + glob.glob(f"{OUT}/data/{m}/agg_{tag}.json"): os.remove(old)
        q = raw[raw.map_id == m]
        if q.empty: state["maps"][m] = []; continue
        q = q.assign(px=((q.x - ox) / scale * SZ).round(1), py=((1 - (q.z - oz) / scale) * SZ).round(1))
        cell = np.clip((q.py.values / SZ * G).astype(int), 0, G - 1) * G + np.clip((q.px.values / SZ * G).astype(int), 0, G - 1)
        agg = {}
        for L, codes in LAYERS.items():
            for a, k in ((0, "h"), (1, "b")):
                cnt = np.bincount(cell[(q.bot.values == a) & np.isin(q.c.values, codes)], minlength=G * G); nz = np.nonzero(cnt)[0]
                agg[f"{L}_{k}"] = np.column_stack([nz, cnt[nz]]).ravel().tolist()
        json.dump(agg, open(f"{OUT}/data/{m}/agg_{tag}.json", "w"), separators=(",", ":"))
        matches = []
        for mid, g in q.groupby("match_id"):
            pls, c = [], [0] * 12
            for (f, u), pg in g.groupby(["file", "user_id"]):
                pg = pg.sort_values("t"); mv = pg[pg.c == -1]; ev = pg[pg.c >= 0]; b = int(pg.bot.iloc[0])
                for code in ev.c: c[6 * b + int(code)] += 1
                pls.append({"id": u[:8] if "-" in u else u, "bot": b,
                            "p": [float(v) for r in mv[["rt", "px", "py"]].itertuples(index=False) for v in r],
                            "e": [float(v) for r in ev[["rt", "c", "px", "py"]].itertuples(index=False) for v in r]})
            pls.sort(key=lambda p: p["bot"])
            matches.append({"id": mid.split(".")[0], "t0": int(g.start.iloc[0]), "dur": int(g.rt.max()), "pl": pls,
                            "h": sum(1 for p in pls if not p["bot"]), "b": sum(p["bot"] for p in pls), "c": c})
        matches.sort(key=lambda x: x["t0"]); rows = []
        for k in range(0, len(matches), CHUNK):
            name = f"{tag}_{k // CHUNK}"
            json.dump({"matches": [{kk: x[kk] for kk in ("id", "t0", "dur", "pl")} for x in matches[k:k + CHUNK]]},
                      open(f"{OUT}/data/{m}/{name}.json", "w"), separators=(",", ":"))
            rows += [[x["id"], day, x["t0"], x["dur"], x["h"], x["b"], name, *x["c"]] for x in matches[k:k + CHUNK]]
        state["maps"][m] = rows
    json.dump(state, open(sf, "w"), separators=(",", ":"))

STATE = os.path.join(os.path.dirname(os.path.abspath(OUT)), ".pipeline_state")
os.makedirs(STATE, exist_ok=True); seen = set(); order = []
for m in MAPS: os.makedirs(f"{OUT}/data/{m}", exist_ok=True)
for d in sorted(glob.glob(f"{SRC}/February_*")):
    day = os.path.basename(d).replace("February_", "Feb "); tag = day.replace(" ", "_"); order.append((day, tag))
    files = [(f, os.path.join(d, f)) for f in sorted(os.listdir(d)) if not f.startswith(".") and f not in seen]
    seen.update(f for f, _ in files)
    sf = f"{STATE}/{tag}.json"; fp = hashlib.sha1("|".join(f"{f}:{os.path.getsize(p)}" for f, p in files).encode()).hexdigest()
    if not FORCE and os.path.exists(sf) and json.load(open(sf))["fp"] == fp: print(day, "unchanged -> skipped"); continue
    process(day, tag, files, sf, fp); print(day, "processed", len(files), "files")
for m, (_, _, _, img) in MAPS.items():
    rows, days = [], []
    for day, tag in order:
        r = json.load(open(f"{STATE}/{tag}.json"))["maps"].get(m, [])
        if r: days.append(day); rows += r
    json.dump({"days": days, "m": rows}, open(f"{OUT}/data/{m}/index.json", "w"), separators=(",", ":"))
    print(m, len(rows), "matches", len(glob.glob(f"{OUT}/data/{m}/Feb_*.json")), "shards")
    dst = f"{OUT}/maps/{m}.webp"
    if FORCE or not os.path.exists(dst):
        im = Image.open(f"{SRC}/minimaps/{img}")
        if im.mode == "RGBA": bg = Image.new("RGB", im.size, (14, 17, 22)); bg.paste(im, mask=im.split()[3]); im = bg
        im.convert("RGB").resize((SZ, SZ), Image.LANCZOS).save(dst, quality=82)
