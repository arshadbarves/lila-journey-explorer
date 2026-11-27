"""Data-contract tests for the generated sharded web data. Run: pytest -q tests"""
import glob, json, pytest
SCALE = {"AmbroseValley": (900, -370, -473), "GrandRift": (581, -290, -290), "Lockdown": (1000, -500, -500)}
LAYERS = {"kills": (1, 3), "deaths": (2, 4, 5), "loot": (0,), "storm": (5,)}
SHARDS = sorted(glob.glob("web/data/*/Feb_*.json"))
INDEX = {m: json.load(open(f"web/data/{m}/index.json")) for m in SCALE}

def world_to_px(m, x, z):
    s, ox, oz = SCALE[m]
    return (x - ox) / s * 1024, (1 - (z - oz) / s) * 1024

def test_mapping_known_point():
    px, py = world_to_px("AmbroseValley", -301.45, -355.55)
    assert (round(px), round(py)) == (78, 890)

def test_origin_and_far_corner():
    assert world_to_px("Lockdown", -500, -500) == (0, 1024)
    assert world_to_px("Lockdown", 500, 500) == (1024, 0)

@pytest.mark.parametrize("f", SHARDS)
def test_shard_invariants(f):
    assert len(json.load(open(f))["matches"]) <= 100
    for m in json.load(open(f))["matches"]:
        assert m["dur"] >= 0
        for p in m["pl"]:
            a, e = p["p"], p["e"]
            assert p["bot"] in (0, 1) and len(a) % 3 == 0 and len(e) % 4 == 0
            assert a[0::3] == sorted(a[0::3]) and e[0::4] == sorted(e[0::4])
            assert all(0 <= v <= 1024 for v in a[1::3] + a[2::3] + e[2::4] + e[3::4])
            assert set(e[1::4]) <= {0, 1, 2, 3, 4, 5}
            ev = [r for r in zip(e[0::4], e[1::4], e[2::4], e[3::4]) if r[1] != 0]; assert len(ev) == len(set(ev))

@pytest.mark.parametrize("m", SCALE)
def test_index_matches_shards(m):
    ids = set()
    for f in glob.glob(f"web/data/{m}/Feb_*.json"): ids |= {x["id"] for x in json.load(open(f))["matches"]}
    assert ids == {r[0] for r in INDEX[m]["m"]}

@pytest.mark.parametrize("m", SCALE)
def test_aggregates_equal_manifest_counts(m):
    for day in INDEX[m]["days"]:
        agg = json.load(open(f"web/data/{m}/agg_{day.replace(' ', '_')}.json")); rows = [r for r in INDEX[m]["m"] if r[1] == day]
        for layer, codes in LAYERS.items():
            for k, off in (("h", 0), ("b", 6)):
                assert sum(agg[f"{layer}_{k}"][1::2]) == sum(r[7 + off + c] for r in rows for c in codes), (day, layer, k)
