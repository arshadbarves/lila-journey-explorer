"""Reproduces the numbers quoted in INSIGHTS.md from web/data/*.json (pixel space 1024x1024)."""
import json, glob, numpy as np, collections
def load(m):
    return [x for f in sorted(glob.glob(f"web/data/{m}/Feb_*.json")) for x in json.load(open(f))["matches"]]
N = 16
names = ["Loot","Kill","Killed","BotKill","BotKilled","Storm"]
for m in ["AmbroseValley","GrandRift","Lockdown"]:
    D = load(m)
    hum = [p for x in D for p in x["pl"] if not p["bot"]]
    ev = collections.Counter(); st=[]; ev_xy = collections.defaultdict(list); pos=np.zeros((N,N))
    for x in D:
        for p in x["pl"]:
            if not p["bot"]:
                a=p["p"]
                for k in range(0,len(a),3): pos[min(int(a[k+2]/1024*N),N-1), min(int(a[k+1]/1024*N),N-1)] += 1
            e=p["e"]
            for k in range(0,len(e),4):
                c=int(e[k+1]); ev[names[c]]+=1; ev_xy[c].append((e[k+2],e[k+3]))
                if c==5: st.append((e[k], x["dur"]))
    nm=len(D); hf=len(hum)
    print(f"\n=== {m}: {nm} matches, {hf} human journeys, mean dur {np.mean([x['dur'] for x in D]):.0f}s")
    print({k: v for k,v in ev.items()}, f"| loot/human-journey {ev['Loot']/hf:.1f}")
    print(f"human journeys with a death: {sum(1 for p in hum if any(p['e'][k+1] in (2,4,5) for k in range(0,len(p['e']),4)))}/{hf}")
    print("mean journey length (s):", round(np.mean([p['p'][-3] for p in hum if p['p']]),0))
    if st: print("storm deaths: n=%d, mean t=%.0fs, mean frac of match=%.2f" % (len(st), np.mean([s[0] for s in st]), np.mean([s[0]/max(s[1],1) for s in st])))
    nz = (pos>0).sum(); tot=N*N
    share = pos/pos.sum(); cold = ((share<0.002)&(share>=0)).sum()
    print(f"grid {N}x{N}: cells with any human traffic {nz}/{tot}; cells <0.2% of traffic {cold}; top-5 cells hold {np.sort(share.ravel())[-5:].sum():.0%} of traffic")
    for c,label in [(0,"loot"),(3,"botkill"),(4,"botkilled"),(5,"storm")]:
        pts=np.array(ev_xy[c]) if ev_xy[c] else np.zeros((0,2))
        if len(pts)==0: continue
        g=np.zeros((N,N)); 
        for x_,y_ in pts: g[min(int(y_/1024*N),N-1), min(int(x_/1024*N),N-1)] += 1
        idx=np.dstack(np.unravel_index(np.argsort(-g.ravel()),g.shape))[0][:3]
        print(f"  {label}: top-3 cells (row,col) {[tuple(int(v) for v in i) for i in idx]} hold {np.sort(g.ravel())[-3:].sum()/g.sum():.0%}; top-5 hold {np.sort(g.ravel())[-5:].sum()/g.sum():.0%}")
    tk=[p['e'][k] for p in hum for k in range(0,len(p['e']),4) if p['e'][k+1]==3]
    td=[p['e'][k] for p in hum for k in range(0,len(p['e']),4) if p['e'][k+1]==4]
    if td: print(f"  human killed by bots: n={len(td)} median t={np.median(td):.0f}s; human bot-kills: n={len(tk)} median t={np.median(tk):.0f}s")
al=[(m,x) for m in ["AmbroseValley","GrandRift","Lockdown"] for x in load(m)]
print("\nmatches with >=1 human:", sum(1 for _,x in al if any(not p['bot'] for p in x['pl'])), "with bots files:", sum(1 for _,x in al if any(p['bot'] for p in x['pl'])), "of", len(al))
pvp=sum(1 for _,x in al for p in x['pl'] for k in range(0,len(p['e']),4) if p['e'][k+1] in (1,2)); print("pvp events:", pvp)

print("\n=== extras")
st_all=[]; humj=0; lens=[]; hb_killed=0; hum_deaths=0
for m,x in al:
    for p in x['pl']:
        if p['bot']: continue
        humj+=1; lens.append(p['p'][-3] if p['p'] else 0)
        for k in range(0,len(p['e']),4):
            c=int(p['e'][k+1])
            if c==5: st_all.append(p['e'][k])
            if c in (2,4,5): hum_deaths+=1
            if c==4: hb_killed+=1
print(f"human journeys {humj}; storm deaths {len(st_all)} (min {min(st_all):.0f}s, median {np.median(st_all):.0f}s, max {max(st_all):.0f}s)")
print(f"journeys lasting >= earliest storm death: {sum(1 for l in lens if l>=min(st_all))} ({sum(1 for l in lens if l>=min(st_all))/humj:.1%}); median journey {np.median(lens):.0f}s; p90 {np.percentile(lens,90):.0f}s")
print(f"human deaths: {hum_deaths}; by bots {hb_killed} ({hb_killed/hum_deaths:.0%}); by storm {len(st_all)} ({len(st_all)/hum_deaths:.0%})")
for m in ["AmbroseValley","GrandRift","Lockdown"]:
    g=np.zeros((N,N))
    for x in load(m):
        for p in x["pl"]:
            if p["bot"]: continue
            a=p["p"]
            for k in range(0,len(a),3): g[min(int(a[k+2]/1024*N),N-1), min(int(a[k+1]/1024*N),N-1)]+=1
    occ=np.sort(g[g>0])[::-1]; top=max(1,int(round(len(occ)*0.1)))
    print(f"{m}: occupied cells {len(occ)}; top10% of occupied cells ({top}) hold {occ[:top].sum()/occ.sum():.0%} of human position samples; {int((occ<occ.sum()*0.002).sum())} occupied cells each <0.2%")
