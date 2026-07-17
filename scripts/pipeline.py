#!/usr/bin/env python3
"""
Risk Radar data pipeline (P1) — zero-dependency (Python 3.10+ stdlib only).

Fetches free market data, computes real risk statistics, and writes
data/latest.json (consumed by index.html with the embedded snapshot as fallback)
plus data/history.json (real per-risk score history, appended per run-date).

Sources (all free, no API keys):
  - frankfurter.dev          ECB daily reference FX rates, ~5y history (USD base)
  - open.er-api.com          spot FX (fresh intraday print)
  - api.gold-api.com         spot gold USD/oz
  - fred.stlouisfed.org      keyless fredgraph.csv:
        daily  (EIA):  Brent DCOILBRENTEU, WTI DCOILWTICO, Henry Hub DHHNGSP
        monthly (IMF PCPS): copper, aluminum, wheat, sugar, coffee, cocoa,
                            iron ore, Australian thermal coal, palm oil, rubber
  - prices.lbma.org.uk       daily LBMA gold PM fix (JSON, full history)
  - EUA / CBAM reference     manual marks with as-of dates (see MANUAL_MARKS) —
                             no reliable keyless API exists; update with cycles.
MCX bhavcopy is a TODO (WAF/session handling) — INR commodity prints currently
derive as USD price x USD/INR where needed.

Run:  python scripts/pipeline.py
"""
import csv
import io
import json
import math
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
UA = {"User-Agent": "Mozilla/5.0 (risk-radar-pipeline; +https://github.com/S-ganti/risk-radar)"}
TODAY = date.today()
HISTORY_YEARS = 5.3

# --- Manual marks: no free keyless feed exists; update with each cycle. -----
MANUAL_MARKS = {
    "eua": {"v": 79.05, "cur": "EUR", "asof": "2026-07-16",
            "src": "tradingeconomics.com/commodity/carbon (manual mark)"},
    "cbam_ref": {"v": 75.28, "cur": "EUR", "q": "Q2 2026", "published": "2026-07-06",
                 "src": "EC official CBAM certificate price via cbamguide.com (manual mark)"},
}

# Market series -> dashboard commodity ids. freq D = daily, M = monthly.
SOURCES = {
    "crude":   {"kind": "fred", "id": "DCOILBRENTEU", "freq": "D", "label": "Brent (EIA via FRED)"},
    "wti":     {"kind": "fred", "id": "DCOILWTICO",   "freq": "D", "label": "WTI (EIA via FRED)"},
    "natgas":  {"kind": "fred", "id": "DHHNGSP",      "freq": "D", "label": "Henry Hub (EIA via FRED)"},
    "gold":    {"kind": "lbma", "id": "gold_pm",      "freq": "D", "label": "LBMA gold PM fix"},
    "copper":  {"kind": "fred", "id": "PCOPPUSDM",    "freq": "M", "label": "Copper (IMF PCPS via FRED)"},
    "alum":    {"kind": "fred", "id": "PALUMUSDM",    "freq": "M", "label": "Aluminum (IMF PCPS via FRED)"},
    "wheat":   {"kind": "fred", "id": "PWHEAMTUSDM",  "freq": "M", "label": "Wheat (IMF PCPS via FRED)"},
    "sugar":   {"kind": "fred", "id": "PSUGAISAUSDM", "freq": "M", "label": "Sugar (IMF PCPS via FRED)"},
    "coffee":  {"kind": "fred", "id": "PCOFFOTMUSDM", "freq": "M", "label": "Coffee (IMF PCPS via FRED)"},
    "cocoa":   {"kind": "fred", "id": "PCOCOUSDM",    "freq": "M", "label": "Cocoa (IMF PCPS via FRED)"},
    "ironore": {"kind": "fred", "id": "PIORECRUSDM",  "freq": "M", "label": "Iron ore (IMF PCPS via FRED)"},
    "coal":    {"kind": "fred", "id": "PCOALAUUSDM",  "freq": "M", "label": "Australian thermal coal (IMF PCPS via FRED)"},
    "palm":    {"kind": "fred", "id": "PPOILUSDM",    "freq": "M", "label": "Palm oil (IMF PCPS via FRED)"},
    "natrub":  {"kind": "fred", "id": "PRUBBUSDM",    "freq": "M", "label": "Rubber (IMF PCPS via FRED)"},
}

# Risk -> daily market series driving its computed velocity; cap maps a
# "very fast" 20-day move to 100. FX uses a tighter cap than commodities.
# Risks without a free daily series (regulation/geopolitics/rates) keep their
# curated velocity in the page and are tagged as such.
VELOCITY_MAP = {
    "oil":    {"series": "crude",  "cap": 15.0},
    "gold":   {"series": "gold",   "cap": 15.0},
    "usdinr": {"series": "usdinr", "cap": 4.0},
}

# Minimal risk metadata for score history (kept in sync with RISKS in
# index.html until P3 single-sources it into data/). compo() formula mirror:
# 0.30*sev/5*100 + 0.20*vel + 0.25*exp + 0.15*con + 0.10*confN
RISKS_META = {
    "rbi-fx":  {"sev": 5, "conf": 90, "vel": 85, "exp": 78, "con": 70},
    "cbam":    {"sev": 4, "conf": 90, "vel": 45, "exp": 72, "con": 74},
    "oil":     {"sev": 4, "conf": 60, "vel": 70, "exp": 66, "con": 58},
    "usdinr":  {"sev": 4, "conf": 90, "vel": 80, "exp": 82, "con": 64},
    "china":   {"sev": 4, "conf": 60, "vel": 55, "exp": 60, "con": 88},
    "coal":    {"sev": 3, "conf": 60, "vel": 40, "exp": 55, "con": 80},
    "gold":    {"sev": 3, "conf": 90, "vel": 60, "exp": 48, "con": 72},
    "rates":   {"sev": 3, "conf": 60, "vel": 50, "exp": 58, "con": 50},
}

REGIME_DAILY = ["crude", "natgas", "gold", "usdinr"]  # 5y vol-percentile inputs


def http_get(url, timeout=45, retries=2):
    last = None
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 — degrade gracefully per-source
            last = e
    print(f"  ! fetch failed: {url} ({last})", file=sys.stderr)
    return None


def get_json(url, **kw):
    raw = http_get(url, **kw)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


# ----------------------------------------------------------------- fetchers --
def fetch_fx_history():
    """~5y of ECB daily reference rates, USD base -> {ccy: [(date, rate)]}. """
    start = (TODAY - timedelta(days=int(HISTORY_YEARS * 365))).isoformat()
    url = f"https://api.frankfurter.dev/v1/{start}..{TODAY.isoformat()}?base=USD&symbols=INR,EUR,GBP,JPY,CHF"
    j = get_json(url, timeout=60)
    if not j or "rates" not in j:
        return {}
    out = {}
    for d in sorted(j["rates"]):
        for ccy, v in j["rates"][d].items():
            out.setdefault(ccy, []).append((d, float(v)))
    print(f"  fx history: {len(out.get('INR', []))} INR days (frankfurter/ECB)")
    return out


def fetch_fx_spot():
    j = get_json("https://open.er-api.com/v6/latest/USD")
    if j and j.get("rates", {}).get("INR"):
        return {"rates": j["rates"], "asof": TODAY.isoformat(), "src": "open.er-api.com"}
    return None


def fetch_gold_spot():
    j = get_json("https://api.gold-api.com/price/XAU")
    if j and j.get("price"):
        return {"v": round(float(j["price"]), 1), "asof": TODAY.isoformat(), "src": "gold-api.com"}
    return None


def fetch_fred(series_id):
    """Keyless CSV: fredgraph.csv?id=SERIES -> [(date, close)] ascending."""
    raw = http_get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}")
    if not raw:
        return []
    cutoff = (TODAY - timedelta(days=int(HISTORY_YEARS * 365))).isoformat()
    rows = []
    text = raw.decode("utf-8", "replace")
    for rec in csv.reader(io.StringIO(text)):
        if len(rec) != 2 or rec[0] in ("DATE", "observation_date"):
            continue
        d, v = rec
        if d >= cutoff and v not in (".", ""):
            try:
                rows.append((d, float(v)))
            except ValueError:
                continue
    return rows


def fetch_lbma_gold():
    """LBMA PM fix full history JSON -> [(date, usd)] ascending."""
    j = get_json("https://prices.lbma.org.uk/json/gold_pm.json", timeout=60)
    if not j:
        return []
    cutoff = (TODAY - timedelta(days=int(HISTORY_YEARS * 365))).isoformat()
    rows = []
    for rec in j:
        d, v = rec.get("d", ""), rec.get("v") or []
        if d >= cutoff and v and v[0]:
            rows.append((d, float(v[0])))
    rows.sort()
    return rows


def fetch_mcx_bhavcopy():
    """TODO (P1.1): MCX EOD bhavcopy needs session/WAF handling; INR commodity
    prints currently derive as USD x USDINR. Kept as an explicit stub so the
    gap is visible in code review rather than silently absent."""
    return None


# ------------------------------------------------------------------- maths --
def log_returns(closes):
    out = []
    for i in range(1, len(closes)):
        p0, p1 = closes[i - 1][1], closes[i][1]
        if p0 > 0 and p1 > 0:
            out.append(math.log(p1 / p0))
    return out


def ewma_vol_series(returns, lam=0.94, seed=30):
    """RiskMetrics EWMA sigma_t series (per-period units)."""
    if len(returns) < seed + 5:
        return []
    var = sum(r * r for r in returns[:seed]) / seed
    sig = [math.sqrt(var)]
    for r in returns[seed:]:
        var = lam * var + (1 - lam) * r * r
        sig.append(math.sqrt(var))
    return sig


def rolling_std_series(returns, window=36):
    """Rolling std of monthly returns (for monthly-frequency series)."""
    if len(returns) < window + 3:
        return []
    out = []
    for i in range(window, len(returns) + 1):
        w = returns[i - window:i]
        m = sum(w) / window
        out.append(math.sqrt(sum((r - m) ** 2 for r in w) / (window - 1)))
    return out


def percentile_rank(series, value):
    if not series:
        return None
    return round(100.0 * sum(1 for s in series if s <= value) / len(series), 1)


def monthly_closes(closes):
    out = {}
    for d, c in closes:  # rows ascending; last close of month wins
        out[d[:7]] = c
    return sorted(out.items())


def monthly_log_returns(closes):
    m = monthly_closes(closes)
    return [(m[i][0], math.log(m[i][1] / m[i - 1][1]))
            for i in range(1, len(m)) if m[i - 1][1] > 0 and m[i][1] > 0]


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs)
    dy = sum((b - my) ** 2 for b in ys)
    return num / math.sqrt(dx * dy) if dx > 0 and dy > 0 else 0.0


def move_pct(closes, periods):
    if len(closes) <= periods:
        return None
    return (closes[-1][1] / closes[-1 - periods][1] - 1) * 100.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# -------------------------------------------------------------------- main --
def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    series, freq, labels = {}, {}, {}

    print("Fetching FX history…")
    fx_hist = fetch_fx_history()
    if fx_hist.get("INR"):
        series["usdinr"], freq["usdinr"], labels["usdinr"] = fx_hist["INR"], "D", "USD/INR (ECB via frankfurter)"

    print("Fetching commodity series…")
    for cid, s in SOURCES.items():
        rows = fetch_lbma_gold() if s["kind"] == "lbma" else fetch_fred(s["id"])
        need = 250 if s["freq"] == "D" else 40
        if len(rows) >= need:
            series[cid], freq[cid], labels[cid] = rows, s["freq"], s["label"]
            print(f"  {cid:8s} {s['freq']} {len(rows):5d} rows  last {rows[-1][0]} = {rows[-1][1]}")
        else:
            print(f"  {cid:8s} skipped ({len(rows)} rows) — {s['label']}")

    fx_spot = fetch_fx_spot()
    gold_spot = fetch_gold_spot()
    fetch_mcx_bhavcopy()  # stub, see docstring

    # ---- per-series stats ----
    vols, latest_moves = {}, {}
    for cid, closes in series.items():
        if freq[cid] == "D":
            rets = log_returns(closes)
            sigs = ewma_vol_series(rets)
            if not sigs:
                continue
            daily = sigs[-1]
            vols[cid] = {"freq": "D", "monthly": round(daily * math.sqrt(21), 4),
                         "annual": round(daily * math.sqrt(252), 4),
                         "pct5y": percentile_rank(sigs, daily),
                         "asof": closes[-1][0], "n": len(rets), "src": labels[cid],
                         "method": "EWMA(0.94) daily"}
            mv = move_pct(closes, 20)
            latest_moves[cid] = None if mv is None else round(mv, 2)
        else:
            mrets = [r for _, r in monthly_log_returns(closes)]
            stds = rolling_std_series(mrets)
            if not stds:
                continue
            vols[cid] = {"freq": "M", "monthly": round(stds[-1], 4),
                         "annual": round(stds[-1] * math.sqrt(12), 4),
                         "pct5y": percentile_rank(stds, stds[-1]),
                         "asof": closes[-1][0], "n": len(mrets), "src": labels[cid],
                         "method": "rolling 36m std of monthly returns"}
            mv = move_pct(closes, 1)  # last month-over-month move
            latest_moves[cid] = None if mv is None else round(mv, 2)

    # ---- monthly correlation matrix (uniform across D and M series) ----
    mrets_map = {cid: dict(monthly_log_returns(cl)) for cid, cl in series.items()}
    corr = {}
    ids = sorted(mrets_map)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            months = sorted(set(mrets_map[a]) & set(mrets_map[b]))[-60:]
            if len(months) >= 24:
                r = pearson([mrets_map[a][m] for m in months], [mrets_map[b][m] for m in months])
                corr[f"{a}|{b}"] = round(r, 2)

    # ---- INR momentum / breadth / regime ----
    inr = {"mom20": None, "mom60": None}
    if "usdinr" in series:
        inr = {"mom20": round(move_pct(series["usdinr"], 20) or 0, 2),
               "mom60": round(move_pct(series["usdinr"], 60) or 0, 2)}
    valid_moves = {c: m for c, m in latest_moves.items() if m is not None}
    moved = [c for c, m in valid_moves.items() if abs(m) > 5.0]
    breadth = round(100.0 * len(moved) / len(valid_moves), 1) if valid_moves else 0.0
    core_pcts = [vols[c]["pct5y"] for c in REGIME_DAILY if c in vols and vols[c]["pct5y"] is not None]
    avg_vol_pct = sum(core_pcts) / len(core_pcts) if core_pcts else 50.0
    inr_component = clamp((inr["mom20"] or 0) / 3.0, 0, 1) * 100  # +3% in 20d = max stress
    regime_score = 0.5 * avg_vol_pct + 0.3 * inr_component + 0.2 * breadth
    regime = ("crisis" if regime_score >= 75 else
              "stressed" if regime_score >= 60 else
              "elevated" if regime_score >= 45 else "normal")

    # ---- computed per-risk velocity (market-driven where a daily series exists) ----
    velocity = {}
    for rid, m in VELOCITY_MAP.items():
        mv = latest_moves.get(m["series"])
        if mv is not None and freq.get(m["series"]) == "D":
            velocity[rid] = round(clamp(abs(mv) / m["cap"], 0, 1) * 100)

    # ---- score history (real): mirror of the page's compo() ----
    hist_path = os.path.join(DATA_DIR, "history.json")
    try:
        with open(hist_path, encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = {"dates": [], "scores": {}}
    dkey = TODAY.isoformat()
    if dkey not in history["dates"]:
        history["dates"].append(dkey)
        for rid, meta in RISKS_META.items():
            vel = velocity.get(rid, meta["vel"])
            compo = round(0.30 * meta["sev"] / 5 * 100 + 0.20 * vel +
                          0.25 * meta["exp"] + 0.15 * meta["con"] + 0.10 * meta["conf"])
            history["scores"].setdefault(rid, []).append(compo)
        history["dates"] = history["dates"][-26:]
        for rid in history["scores"]:
            history["scores"][rid] = history["scores"][rid][-26:]

    # ---- spot block ----
    spot = {}
    if fx_spot:
        spot["usdinr"] = {"v": round(fx_spot["rates"]["INR"], 2), "asof": fx_spot["asof"], "src": fx_spot["src"]}
        for k, ccy in (("eurinr", "EUR"), ("gbpinr", "GBP"), ("jpyinr", "JPY"), ("chfinr", "CHF")):
            if fx_spot["rates"].get(ccy):
                spot[k] = {"v": round(fx_spot["rates"]["INR"] / fx_spot["rates"][ccy], 2),
                           "asof": fx_spot["asof"], "src": fx_spot["src"]}
    elif "usdinr" in series:
        spot["usdinr"] = {"v": round(series["usdinr"][-1][1], 2), "asof": series["usdinr"][-1][0],
                          "src": "frankfurter.dev (ECB, EOD)"}
    if gold_spot:
        spot["gold"] = gold_spot
    elif "gold" in series:
        spot["gold"] = {"v": round(series["gold"][-1][1], 1), "asof": series["gold"][-1][0], "src": labels["gold"]}
    if "crude" in series:
        spot["brent"] = {"v": round(series["crude"][-1][1], 2), "asof": series["crude"][-1][0], "src": labels["crude"]}
    spot["eua"] = MANUAL_MARKS["eua"]
    spot["cbam_ref"] = MANUAL_MARKS["cbam_ref"]
    if spot.get("gold") and spot.get("usdinr"):
        spot["gold_inr_10g"] = {"v": round(spot["gold"]["v"] * spot["usdinr"]["v"] * 10 / 31.1035),
                                "asof": spot["gold"]["asof"], "src": "derived: XAUUSD x USDINR (MCX feed TODO)"}

    latest = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "spot": spot,
        "vols": vols,
        "moves": latest_moves,
        "corr": corr,
        "inr": inr,
        "breadth": breadth,
        "regime": {"label": regime, "score": round(regime_score, 1),
                   "components": {"avg_vol_pct5y": round(avg_vol_pct, 1),
                                  "inr_mom20_component": round(inr_component, 1),
                                  "breadth": breadth}},
        "velocity": velocity,
        "history": history,
        "notes": [
            "Daily series (Brent, WTI, Henry Hub, LBMA gold, USDINR): EWMA vol lambda=0.94; monthly = daily*sqrt(21).",
            "Monthly series (IMF PCPS): rolling 36-month std of monthly log returns.",
            "Correlations: Pearson on up to 60 overlapping monthly log returns (min 24), uniform across all series.",
            "Regime = 0.5*avg 5y vol percentile (Brent, Henry Hub, gold, USDINR) + 0.3*INR 20d momentum (3%=max) + 0.2*breadth(|move|>5%); thresholds 45/60/75.",
            "Velocity computed from |20d move| where a daily series exists (oil, gold, USDINR); other risks keep curated velocity, tagged in the UI.",
            "Exposure/concentration remain curated in P1 (computed from cost-base data in P2).",
            "natgas is US Henry Hub — Asian LNG is oil-indexed; steel/metcoal/API/TiO2/lithium have no free series (rating-based).",
            "MCX bhavcopy: TODO (WAF/session); gold INR derived as XAUUSD x USDINR meanwhile.",
        ],
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(latest, f, indent=1)
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=1)
    for cid, closes in series.items():  # refetchable; data/raw is gitignored
        with open(os.path.join(RAW_DIR, f"{cid}.json"), "w", encoding="utf-8") as f:
            json.dump(closes, f)

    print(f"\nWrote data/latest.json — {len(series)} series ({sum(1 for c in freq.values() if c=='D')} daily), "
          f"{len(corr)} corr pairs, regime={regime} (score {regime_score:.0f}), velocity={velocity}")


if __name__ == "__main__":
    main()
