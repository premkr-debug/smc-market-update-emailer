"""Daily 'Market ki Halchal' email generator (live-text HTML email, no images needed for data).
Free stack: yfinance + GitHub Actions + GitHub Pages.   Test without internet:  python market_update.py --demo"""
import io, os, sys, shutil, pathlib, datetime as dt, zoneinfo
from jinja2 import Template

ROOT = pathlib.Path(__file__).parent
IST = zoneinfo.ZoneInfo("Asia/Kolkata")
NOW = dt.datetime.now(IST)
SITE = os.getenv("SITE_URL", "").rstrip("/")          # e.g. https://user.github.io/market-mailer
NAMES = {"HINDUNILVR": "HUL", "TATACONSUM": "TATA Cons. Prod", "HDFCLIFE": "HDFC Life",
         "INDIGO": "Interglobe Avi", "SHRIRAMFIN": "Shriram Finance", "ADANIENT": "Adani Enterpris",
         "MAXHEALTH": "Max Healthcare", "BAJFINANCE": "Bajaj Finance", "TATASTEEL": "Tata Steel",
         "JSWSTEEL": "JSW Steel", "BHARTIARTL": "Bharti Airtel", "HINDALCO": "Hindalco"}

def inr(x, d=2):
    s = f"{abs(x):.{d}f}"; i, _, f = s.partition(".")
    if len(i) > 3:
        head, tail, g = i[:-3], i[-3:], []
        while len(head) > 2: g.insert(0, head[-2:]); head = head[:-2]
        if head: g.insert(0, head)
        i = ",".join(g + [tail])
    return ("-" if x < 0 else "") + i + (f".{f}" if d else "")

def sgn(x, d=2): return ("+" if x >= 0 else "\u2212") + inr(abs(x), d)

def short(sym, company):
    if sym in NAMES: return NAMES[sym]
    n = company.replace(" Limited", "").replace(" Ltd.", "").replace(" Ltd", "")
    return n if len(n) <= 16 else n[:16].rstrip()

def live_data():
    import pandas as pd, requests, yfinance as yf
    try:
        r = requests.get("https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        r.raise_for_status(); df = pd.read_csv(io.StringIO(r.text))
    except Exception as e:
        print("NSE list fetch failed, using local nifty50.csv:", e); df = pd.read_csv(ROOT / "nifty50.csv")
    syms = df["Symbol"].str.strip().tolist(); comp = dict(zip(syms, df["Company Name"]))

    def last2(tk):
        c = yf.download(tk, period="10d", interval="1d", auto_adjust=False, progress=False)["Close"].dropna(how="all")
        return c.index[-1].date(), c.iloc[-1], c.iloc[-2]
    d, last, prev = last2([s + ".NS" for s in syms])
    if d != NOW.date() and os.getenv("FORCE") != "1":
        print(f"Latest data is {d}, today is {NOW.date()} -> holiday/no data, skipping."); sys.exit(0)
    rows = []
    for s in syms:
        l, p = last.get(s + ".NS"), prev.get(s + ".NS")
        if pd.isna(l) or pd.isna(p): continue
        rows.append(dict(name=short(s, comp[s]), l=float(l), c=float(l - p), p=float((l - p) / p * 100)))
    _, il, ip = last2(["^BSESN", "^NSEI"])
    idx = [(n, float(il[t]), float(il[t] - ip[t]), float((il[t] / ip[t] - 1) * 100)) for n, t in (("SENSEX", "^BSESN"), ("NIFTY", "^NSEI"))]
    _, fl, fp = last2(["INR=X", "GC=F", "SI=F"]); usd = float(fl["INR=X"]); parts = []
    if os.getenv("ENABLE_COMMODITIES") == "1":   # approximate! verify vs MCX before enabling
        gp, sp = float(os.getenv("GOLD_PREMIUM") or 0), float(os.getenv("SILVER_PREMIUM") or 0)
        g = fl["GC=F"] * usd / 31.1035 * 10 * (1 + gp); s = fl["SI=F"] * usd / 31.1035 * 1000 * (1 + sp)
        parts += [f"GOLD - {inr(g)} ({(fl['GC=F']/fp['GC=F']-1)*100:+.2f}%)", f"SILVER - {inr(s)} ({(fl['SI=F']/fp['SI=F']-1)*100:+.2f}%)"]
    parts.append(f"USD/INR - {usd:.3f} ({(usd/fp['INR=X']-1)*100:+.2f}%)")
    return d, rows, idx, " | ".join(parts)

def demo_data():
    g = [("HUL",2141.80,122.70,6.08),("TATA Cons. Prod",1185.80,52.80,4.66),("HDFC Life",601.3,26.35,4.58),("Nestle",1358.50,52.60,4.03),
         ("Interglobe Avi",5720.00,197.00,3.57),("Trent",3319.60,111.60,3.48),("HDFC Bank",846.2,28.40,3.47),("ICICI Bank",1640.00,54.50,3.44),
         ("Bajaj Finance",1131.35,35.85,3.27),("Grasim",3162.00,86.80,2.82)]
    l = [("Tata Steel",159.3,-3.70,-2.27),("Max Healthcare",1076.30,-13.25,-1.22),("Hindalco",889.9,-10.55,-1.17),("JSW Steel",1302.50,-9.40,-0.72),
         ("Shriram Finance",989.95,-5.95,-0.60),("Bharti Airtel",2117.50,-11.00,-0.52),("ONGC",222,-0.85,-0.38),("Adani Enterpris",2668.50,-9.40,-0.35)]
    rows = [dict(name=n, l=a, c=b, p=c) for n, a, b, c in g + l]
    return NOW.date(), rows, [("SENSEX",83938.28,1502.29,1.82),("NIFTY",25819.25,469.60,1.85)], \
           "GOLD - 1,20,725.00 (\u22121.31%) | SILVER - 1,42,527.00 (\u22122.00%) | USD/INR - 92.259 (\u22120.71%)"

def main():
    d, rows, idx, footer = demo_data() if "--demo" in sys.argv else live_data()
    fmt = lambda r: dict(name=r["name"], price=inr(r["l"]), chg=sgn(r["c"]), pct=f"{r['p']:+.2f}%".replace("-", "\u2212"))
    gainers = [fmt(r) for r in sorted([r for r in rows if r["c"] > 0], key=lambda r: -r["p"])[:10]]
    losers = [fmt(r) for r in sorted([r for r in rows if r["c"] < 0], key=lambda r: r["p"])[:10]]
    indices = [dict(name=n, price=inr(p), chg=sgn(c), pct=f"{pc:+.2f}%".replace("-", "\u2212"), up=c >= 0) for n, p, c, pc in idx]

    out = ROOT / "docs"; out.mkdir(exist_ok=True)
    if (ROOT / "assets").exists(): shutil.copytree(ROOT / "assets", out / "assets", dirs_exist_ok=True)
    base = (SITE + "/assets/") if SITE else "assets/"
    img = lambda n: (base + n) if (ROOT / "assets" / n).exists() else None
    s0 = indices[0]; s1 = indices[1]
    subject = f"Market ki Halchal | {d.strftime('%d %b %Y')} | Sensex {s0['price']} ({s0['pct']})"
    html = Template((ROOT / "email_template.html").read_text(encoding="utf-8"), autoescape=True).render(
        logo=img("logo.png"), bull=img("bull.png"), bear=img("bear.png"),
        date_str=d.strftime("%d %B %Y").upper(), date_short=d.strftime("%d %b %Y"), time_str=NOW.strftime("%I:%M %p"),
        preheader=f"Sensex {s0['price']} ({s0['pct']}) | Nifty {s1['price']} ({s1['pct']})",
        indices=indices, gainers=gainers, losers=losers, footer=footer)
    (out / f"email-{d.isoformat()}.html").write_text(html, encoding="utf-8")
    (out / "email.html").write_text(html, encoding="utf-8")
    (out / "email-source.txt").write_text(html, encoding="utf-8")      # open this, Ctrl+A, Ctrl+C -> paste in WebEngage
    (out / "subject.txt").write_text(subject, encoding="utf-8")
    print("Created docs/email.html | Subject:", subject)

if __name__ == "__main__":
    main()
