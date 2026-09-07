#!/usr/bin/env python3
"""
Real model calculations over the price history the daily pipeline fetches.

Writes data/risk.json:
  series   per-market GARCH(1,1) fit, GPD tail fit, VaR/ES cross-check, and a
           rolling out-of-sample coverage backtest
  joint    correlation matrix, t-copula degrees of freedom, tail dependence
  cfar     per-company Cash-Flow-at-Risk in INR crore, with input coverage
  meta     what was computed, what was refused, and why

Nothing here is estimated from a rating. Where the data cannot support a
calculation the entry carries an `error` string and the dashboard shows the
reason instead of a number.

Run after pipeline.py (which populates data/raw/):
    python scripts/pipeline.py && python scripts/compute_risk.py
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import cfar, copula, evt, garch, stats, var  # noqa: E402

DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
INDEX = os.path.join(ROOT, "index.html")

# Sector pass-through: the share of an input-cost rise the company CANNOT pass
# on. Mirrors SECRETAIN in index.html; kept in sync deliberately rather than
# parsed, because a silent drift here would change every rupee figure.
SECRETAIN = {"autos": 0.5, "steel": 0.3, "metals": 0.4, "paints": 0.6,
             "jewellery": 0.65, "pharma": 0.7, "fmcg": 0.45, "cement": 0.55,
             "power": 0.2, "energy": 0.3, "infra": 0.5, "banks": 0.1, "it": 0.15}
SECTOR_KEYWORDS = [
    ("banks", ("bank", "financ", "insur", "nbfc")), ("it", ("it services", "software")),
    ("steel", ("steel",)), ("metals", ("metal", "alumin", "mining", "zinc", "copper")),
    ("jewellery", ("jewell", "watches")), ("pharma", ("pharma", "healthcare", "hospital")),
    ("cement", ("cement",)), ("power", ("power", "utilit")), ("energy", ("energy", "oil", "gas", "petchem")),
    ("autos", ("auto", "motor", "vehicle", "tyre", "tire")), ("paints", ("paint",)),
    ("fmcg", ("fmcg", "consumer", "food", "bever", "tobacco", "retail")),
    ("infra", ("infra", "construc", "engineering", "logistic", "port", "airline", "aviation")),
]


def _extract_literal(src, key, opener):
    """Pull a JS object/array literal out of index.html by brace matching.

    index.html is the single source of truth for the dependency graph; copying
    it into a second file would let the two drift, and the drift would be
    invisible.
    """
    m = re.search(r"\b" + re.escape(key) + r"\s*:\s*" + re.escape(opener), src)
    if not m:
        return None
    start = m.end() - 1
    closer = "}" if opener == "{" else "]"
    depth, i, in_str, esc = 0, start, False, False
    while i < len(src):
        ch = src[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(src[start:i + 1])
                except json.JSONDecodeError as e:
                    print(f"  ! could not parse {key}: {e}", file=sys.stderr)
                    return None
        i += 1
    return None


def load_universe():
    with open(INDEX, encoding="utf-8", errors="replace") as f:
        src = f.read()
    deps = _extract_literal(src, "deps", "{") or {}
    prod = _extract_literal(src, "prod", "{") or {}
    companies = _extract_literal(src, "companies", "[") or []
    sectors = {c["id"]: c.get("sector", "") for c in companies if isinstance(c, dict)}
    names = {c["id"]: c.get("name", c["id"]) for c in companies if isinstance(c, dict)}
    return deps, prod, sectors, names


# A single input above this share of the cost base means the business is a
# converter - a refiner, smelter or miller - whose output price tracks that
# input. A gross input-cost shock badly overstates such a company's exposure,
# because the real exposure is a processing spread. Reliance is the case in
# point: crude is half its cost base and refined product is its revenue.
CONVERTER_THRESHOLD = 0.35


def net_weights(dep, prod):
    """Cost-side weights net of revenue-side exposure to the same commodity.

    Hindalco buys 20% aluminium-linked inputs and sells 45% aluminium: it is a
    net producer, so an aluminium rally helps it. Scoring the gross cost side
    alone gets the sign of the exposure wrong.
    """
    net, offsets = {}, {}
    for c, w in (dep or {}).items():
        p = (prod or {}).get(c, 0.0)
        n = w - p
        if p:
            offsets[c] = {"cost_share": w, "revenue_share": p,
                          "net": round(n, 4),
                          "position": "net long (beneficiary)" if n < 0 else "net short (buyer)"}
        if n > 0.001:
            net[c] = n
    return net, offsets


def sector_key(desc):
    d = (desc or "").lower()
    for key, words in SECTOR_KEYWORDS:
        if any(w in d for w in words):
            return key
    return None


def load_series():
    """data/raw/<id>.json written by pipeline.py: [(date, close)] ascending."""
    out = {}
    if not os.path.isdir(RAW):
        return out
    for fn in sorted(os.listdir(RAW)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(RAW, fn), encoding="utf-8") as f:
                rows = json.load(f)
            if isinstance(rows, list) and len(rows) >= 40:
                out[fn[:-5]] = [(d, float(v)) for d, v in rows]
        except Exception as e:  # noqa: BLE001
            print(f"  ! skipped {fn}: {e}", file=sys.stderr)
    return out


def analyse_series(cid, closes, freq_daily):
    rets = [r for _d, r in stats.log_returns(closes)]
    n = len(rets)
    out = {"id": cid, "n_returns": n, "asof": closes[-1][0],
           "frequency": "daily" if freq_daily else "monthly",
           "last_price": closes[-1][1]}
    if n < 40:
        out["error"] = f"only {n} returns — nothing can be estimated"
        return out

    ann = 252 ** 0.5 if freq_daily else 12 ** 0.5
    ew = stats.ewma_vol_series(rets) if freq_daily else stats.rolling_std_series(rets)
    if ew:
        out["ewma_sigma"] = round(ew[-1], 6)
        out["ewma_sigma_annual"] = round(ew[-1] * ann, 4)
        out["vol_percentile_5y"] = stats.percentile_rank(ew, ew[-1])

    out["skewness"] = round(stats.skewness(rets), 3)
    out["excess_kurtosis"] = round(stats.excess_kurtosis(rets), 3)
    out["normality_note"] = (
        "Excess kurtosis above 1 means a normal VaR understates the tail; the "
        "historical and EVT figures are the ones to quote."
        if stats.excess_kurtosis(rets) > 1 else
        "Return distribution is close enough to normal that the three VaR "
        "estimators should broadly agree.")

    g = garch.fit(rets)
    if g:
        out["garch"] = g
        h = 21 if freq_daily else 1
        out["garch_forecast"] = garch.forecast(g, h)
    else:
        out["garch"] = {"error": f"need >= 250 observations to identify GARCH(1,1), have {n}"}

    sigma = g["sigma_next"] if g else (ew[-1] if ew else None)
    out["var"] = {}
    horizons = [1, 10, 21] if freq_daily else [1]
    for a in (0.95, 0.99):
        for h in horizons:
            key = f"{int(a*100)}_{h}"
            cc = var.cross_check(rets, alpha=a, horizon=h,
                                 sigma=sigma if h == 1 else None)
            out["var"][key] = cc

    if freq_daily and n >= 1030:
        out["backtest_99"] = var.backtest(rets, 0.99, window=1000)
    if freq_daily and n >= 280:
        out["backtest_95"] = var.backtest(rets, 0.95, window=250)

    tail = evt.fit_pot(rets, 0.90, side="loss")
    if "error" not in tail:
        tail.pop("mean_excess", None)      # kept out of the published payload for size
        tail["tail_table"] = evt.tail_table(tail)
    out["evt"] = tail
    return out


def main():
    print("Loading price history…")
    series = load_series()
    if not series:
        print("No data/raw series found — run scripts/pipeline.py first.", file=sys.stderr)
        return 1
    try:
        with open(os.path.join(DATA, "latest.json"), encoding="utf-8") as f:
            latest = json.load(f)
    except FileNotFoundError:
        latest = {}
    freqs = {k: (v.get("freq") == "D") for k, v in (latest.get("vols") or {}).items()}

    print(f"Analysing {len(series)} series…")
    out_series, refused = {}, []
    for cid, closes in sorted(series.items()):
        daily = freqs.get(cid, len(closes) > 400)
        res = analyse_series(cid, closes, daily)
        out_series[cid] = res
        flag = ""
        if res.get("garch", {}).get("error"):
            flag += " garch:no"
        if res.get("evt", {}).get("error"):
            flag += " evt:no"
            refused.append(f"{cid}: {res['evt']['error']}")
        print(f"  {cid:9s} n={res['n_returns']:5d}"
              f" sigma={res.get('ewma_sigma', float('nan')):.4f}"
              f" xi={res.get('evt', {}).get('xi', '—')}{flag}")

    # ---- joint dependence on monthly returns (uniform across daily and monthly) --
    print("Estimating joint dependence…")
    mret = {cid: stats.monthly_log_returns(cl) for cid, cl in series.items()}
    mret = {k: v for k, v in mret.items() if len(v) >= 24}
    cm = copula.corr_matrix(mret, min_obs=24)
    dfe = copula.estimate_df(mret)
    ids, rows = copula.align(mret)
    tail_dep = {}
    if rows and len(rows) >= 100:
        cols = {ids[i]: [r[i] for r in rows] for i in range(len(ids))}
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                td = copula.empirical_tail_dependence(cols[ids[i]], cols[ids[j]], q=0.90)
                if td:
                    tail_dep[f"{ids[i]}|{ids[j]}"] = td
    top_td = sorted(tail_dep.items(), key=lambda kv: -kv[1])[:12]
    _, meta = copula.simulate(cm["matrix"], [1.0] * len(cm["ids"]), paths=10,
                              df=dfe["df"], seed=1)
    joint = {
        "ids": cm["ids"], "pairs": cm["pairs"],
        "measured_pairs": cm["measured_pairs"], "total_pairs": cm["total_pairs"],
        "t_copula": dfe,
        "psd_repaired": bool(meta.get("psd_repaired")),
        "aligned_months": len(rows),
        "top_tail_dependence": [{"pair": k, "lambda": v} for k, v in top_td],
        "note": ("A Gaussian copula implies zero tail dependence. Measured joint "
                 "exceedance rates above zero are the reason the t copula with "
                 f"df={dfe['df']} is used for joint stress."),
    }

    # ---- per-company Cash-Flow-at-Risk -----------------------------------------
    print("Computing Cash-Flow-at-Risk…")
    deps, prod, sectors, names = load_universe()
    try:
        with open(os.path.join(DATA, "financials.json"), encoding="utf-8") as f:
            fin = json.load(f)
    except FileNotFoundError:
        fin = {}

    HORIZON_M = 3   # one quarter: the planning and board-reporting cycle, and
                    # short enough that a conditional volatility forecast is
                    # still informative rather than mean-reverted away.

    def horizon_vol(cid, months):
        """Volatility over `months`, mean-reverting where GARCH could be fitted.

        Scaling today's EWMA estimate by sqrt(time) assumes current conditions
        persist for the whole horizon. In an elevated regime that produces
        headline numbers no CFO will accept - Brent's EWMA sigma is 4%/day right
        now, which sqrt-scales to a 64% annual vol. The GARCH term structure
        reverts toward the long-run level instead, which is what actually happens.
        """
        res = out_series.get(cid) or {}
        if res.get("frequency") == "daily":
            g = res.get("garch")
            if g and "error" not in g:
                fc = garch.forecast(g, int(months * 21))
                if fc:
                    return fc["sigma"], "garch-term-structure"
            s = res.get("ewma_sigma")
            return (s * (months * 21) ** 0.5, "ewma-sqrt-time") if s else (None, None)
        s = res.get("ewma_sigma")
        return (s * months ** 0.5, "rolling36m-sqrt-time") if s else (None, None)

    hv, hv_method = {}, {}
    for cid in out_series:
        v, meth = horizon_vol(cid, HORIZON_M)
        if v:
            hv[cid], hv_method[cid] = v, meth

    idx = {c: i for i, c in enumerate(cm["ids"])}
    cfar_out, skipped = {}, []
    for coid, gross in sorted(deps.items()):
        f = fin.get(coid)
        if not f or not f.get("rev_cr") or not f.get("ebitda_cr"):
            skipped.append({"company": coid,
                            "reason": "no verified FY26 revenue and EBITDA on file"})
            continue
        weights, offsets = net_weights(gross, prod.get(coid))
        if not weights:
            skipped.append({"company": coid, "name": names.get(coid, coid),
                            "reason": "net long every mapped input — revenue-side "
                                      "exposure exceeds the cost side, so an input "
                                      "price rise is a benefit, not a risk",
                            "offsets": offsets})
            continue
        covered = {k: v for k, v in weights.items() if k in hv and k in idx}
        if not covered:
            skipped.append({"company": coid, "name": names.get(coid, coid),
                            "reason": "no net input in the cost base has a free price series"})
            continue
        ids_c = sorted(covered)
        R = [[cm["matrix"][idx[a]][idx[b]] for b in ids_c] for a in ids_c]
        cost_base = f["rev_cr"] - f["ebitda_cr"]
        sec = sector_key(sectors.get(coid, ""))
        retain = SECRETAIN.get(sec, 0.5)
        res = cfar.simulate_company(
            covered, hv, R, cost_base_cr=cost_base, ebitda_cr=f["ebitda_cr"],
            horizon_months=1, pass_through=retain, hedge_ratio=0.0,
            df=dfe["df"], paths=12000, seed=abs(hash(coid)) % 10 ** 6)
        # horizon_months=1 because hv already carries the full-horizon volatility
        if "error" in res:
            skipped.append({"company": coid, "reason": res["error"]})
            continue
        res["horizon_months"] = HORIZON_M
        total_w = sum(gross.values()) or 1.0
        top_share = max(covered.values())
        res.update({
            "company": coid, "name": names.get(coid, coid),
            "sector_key": sec, "fy": f.get("fy"),
            "gross_weights": gross, "producer_offsets": offsets,
            "vol_method": {c: hv_method.get(c) for c in ids_c},
            "input_coverage_pct": round(100 * sum(covered.values()) / total_w, 1),
            "inputs_unpriced": sorted(set(weights) - set(covered)),
        })
        if offsets:
            res["netting_note"] = (
                "Cost-side weights are shown net of revenue-side exposure to the "
                "same commodity, so a company that sells what it buys is not "
                "scored as if a price rise only hurt it.")
        if top_share >= CONVERTER_THRESHOLD:
            res["pass_through_risk"] = True
            res["pass_through_note"] = (
                f"A single input is {top_share*100:.0f}% of this cost base, which "
                f"means the business converts it rather than merely consuming it, "
                f"and its selling price will track that input. The figure below is "
                f"a GROSS input-cost exposure. The economic exposure is a "
                f"processing spread and needs the output-price linkage, which is "
                f"not in the dependency data — do not quote this number as an "
                f"earnings-at-risk figure for this company.")
        if res["input_coverage_pct"] < 100:
            res["coverage_note"] = (
                f"{res['input_coverage_pct']}% of the mapped cost base has a free "
                f"price series. The figure covers that share only and understates "
                f"total input risk; unpriced inputs are listed.")
        drv = cfar.contribution(covered, hv, R, cost_base, ebitda_cr=f["ebitda_cr"],
                                horizon_months=1, pass_through=retain,
                                df=dfe["df"], paths=6000)
        res["drivers"] = drv.get("drivers", [])[:5]
        cfar_out[coid] = res
        flag = " [GROSS - converter]" if res.get("pass_through_risk") else ""
        print(f"  {coid:14s} CFaR Rs {res['cfar_cr']:>7,.0f} cr "
              f"({res.get('cfar_pct_ebitda')}% of EBITDA) "
              f"coverage {res['input_coverage_pct']}%{flag}")

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine_version": "1.0.0",
        "series": out_series,
        "joint": joint,
        "cfar": cfar_out,
        "cfar_skipped": skipped,
        "meta": {
            "series_analysed": len(out_series),
            "companies_scored": len(cfar_out),
            "companies_skipped": len(skipped),
            "refused": refused,
            "method_notes": [
                "GARCH(1,1) fitted by maximum likelihood (Nelder-Mead) on log returns; "
                "stationarity enforced by parameterisation, not by clipping.",
                "VaR/ES reported three ways — historical simulation, normal parametric "
                "and Student-t Monte Carlo. Disagreement between them is reported "
                "rather than resolved: it is information about the tail.",
                "Historical simulation at 99% needs about 1,000 observations to be "
                "stable; where the window is thinner the backtest says so and the "
                "verdict does not blame the model.",
                "GPD peaks-over-threshold fitted by probability-weighted moments to "
                "losses beyond the 90th percentile, with method-of-moments as a "
                "stability check. Fitted to market returns, never to simulator output.",
                "Joint stress uses a Student-t copula whose degrees of freedom are "
                "estimated from pooled excess kurtosis, because a Gaussian copula "
                "assigns vanishing probability to the joint moves this book is "
                "exposed to.",
                "CFaR: a correlated 3-month basket shock (t copula) against the FY26 cost base "
                "(revenue - EBITDA), damped by sector pass-through, at a zero default "
                "hedge ratio. Horizon volatility comes from the GARCH term structure "
                "where one could be fitted, so it mean-reverts instead of assuming "
                "today's conditions hold all year.",
                "Cost weights are net of revenue-side exposure to the same commodity, so a "
                "net producer is not scored as if a price rise only hurt it. Where one "
                "input exceeds 35% of the cost base the company is a converter and the "
                "figure is flagged as a gross input cost, not an earnings-at-risk number.",
                "Cost-base shares are estimates from segment disclosure, labelled as "
                "estimates. Confirming them against the client ledger is day one of "
                "an engagement, not a prerequisite for the conversation.",
            ],
        },
    }
    path = os.path.join(DATA, "risk.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    size = os.path.getsize(path) / 1024
    print(f"\nWrote data/risk.json — {len(out_series)} series, "
          f"{len(cfar_out)} companies scored, {len(skipped)} skipped, {size:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
