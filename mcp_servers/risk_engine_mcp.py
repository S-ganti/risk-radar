#!/usr/bin/env python3
"""
risk-engine-mcp — the model stack as callable tools.

The point of exposing these over MCP is not convenience. It is that the weekly
cycle agent must *compute* its numbers rather than assert them. Before this
existed, a cycle narrative could contain a plausible-sounding volatility or
loss figure with nothing behind it. Now every such figure is the return value of
a tool call, produced by the same engine that produced the number on the
dashboard, and the tool refuses when the data cannot support the calculation.

Install once:  pip install mcp
Run:           python mcp/risk_engine_mcp.py        (stdio)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# The SDK renamed FastMCP to MCPServer in 2.x. Support both so the servers run
# against whichever version is installed rather than pinning the user to one.
try:
    from mcp.server.mcpserver import MCPServer as _Server      # mcp >= 2.0
except ImportError:  # pragma: no cover
    try:
        from mcp.server.fastmcp import FastMCP as _Server      # mcp 1.x
    except ImportError:
        print("risk-engine-mcp needs the MCP SDK:  pip install mcp", file=sys.stderr)
        raise

from engine import cfar as cfar_mod          # noqa: E402
from engine import copula, evt, garch, hedge, stats, var  # noqa: E402

DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")

mcp = _Server("risk-engine")


# --------------------------------------------------------------- helpers --
def _load_raw(series_id):
    path = os.path.join(RAW, f"{series_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return [(d, float(v)) for d, v in json.load(f)]


def _returns(series_id):
    closes = _load_raw(series_id)
    if not closes:
        return None
    return [r for _d, r in stats.log_returns(closes)]


def _available():
    if not os.path.isdir(RAW):
        return []
    return sorted(f[:-5] for f in os.listdir(RAW) if f.endswith(".json"))


def _risk_json():
    try:
        with open(os.path.join(DATA, "risk.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _err(msg, **extra):
    return json.dumps({"error": msg, **extra}, indent=1)


# ----------------------------------------------------------------- tools --
@mcp.tool()
def list_series() -> str:
    """List the market series the engine can compute on, with their history
    length and last observation date."""
    out = []
    for sid in _available():
        closes = _load_raw(sid)
        if closes:
            out.append({"id": sid, "observations": len(closes),
                        "first": closes[0][0], "last": closes[-1][0],
                        "last_price": closes[-1][1]})
    return json.dumps({"series": out, "count": len(out),
                       "note": "Populated by scripts/pipeline.py. Commodities "
                               "without a free price series are absent by design "
                               "rather than filled with a proxy."}, indent=1)


@mcp.tool()
def run_var(series_id: str, confidence: float = 0.99, horizon_days: int = 1) -> str:
    """Value-at-Risk and Expected Shortfall for one market series.

    Returns all three estimators (historical simulation, normal parametric,
    Student-t Monte Carlo) plus their spread. When they disagree materially the
    tail shape is doing the work and the historical figure is the one to quote.
    """
    r = _returns(series_id)
    if r is None:
        return _err(f"no series '{series_id}'", available=_available())
    if not 0.5 < confidence < 1:
        return _err("confidence must be between 0.5 and 1")
    res = var.cross_check(r, alpha=confidence, horizon=max(1, horizon_days))
    return json.dumps({"series": series_id, "confidence": confidence,
                       "horizon_days": horizon_days, **res,
                       "units": "log-return loss, positive = loss"}, indent=1)


@mcp.tool()
def backtest_var(series_id: str, confidence: float = 0.99, window: int = 1000) -> str:
    """Rolling out-of-sample VaR backtest: Kupiec coverage, Christoffersen
    independence, and the joint test. This is the honest measure of whether a
    VaR number works, and it will tell you when the estimation window is too
    thin to support the confidence level rather than blaming the model."""
    r = _returns(series_id)
    if r is None:
        return _err(f"no series '{series_id}'", available=_available())
    return json.dumps({"series": series_id,
                       **var.backtest(r, alpha=confidence, window=window)}, indent=1)


@mcp.tool()
def fit_garch(series_id: str, forecast_days: int = 21) -> str:
    """Fit GARCH(1,1) by maximum likelihood and forecast volatility over the
    horizon. Unlike scaling today's estimate by sqrt(time), this mean-reverts
    toward the long-run level, which is what actually happens."""
    r = _returns(series_id)
    if r is None:
        return _err(f"no series '{series_id}'", available=_available())
    fit = garch.fit(r)
    if not fit:
        return _err(f"'{series_id}' has {len(r)} returns; GARCH(1,1) needs >= 250")
    return json.dumps({"series": series_id, "fit": fit,
                       "forecast": garch.forecast(fit, forecast_days)}, indent=1)


@mcp.tool()
def fit_tail(series_id: str, threshold_quantile: float = 0.90) -> str:
    """Fit a Generalised Pareto tail to real losses by peaks-over-threshold, and
    return the shape parameter, tail VaR/ES table and mean-excess diagnostic.

    Fitted to observed market returns. An earlier version of this tool fitted a
    GPD to a Monte Carlo simulator's own draws, which recovers the simulator's
    assumptions rather than the market's tails; that was removed, not caveated.
    """
    r = _returns(series_id)
    if r is None:
        return _err(f"no series '{series_id}'", available=_available())
    fit = evt.fit_pot(r, threshold_q=threshold_quantile)
    if "error" in fit:
        return json.dumps({"series": series_id, **fit}, indent=1)
    fit["tail_table"] = evt.tail_table(fit)
    return json.dumps({"series": series_id, **fit}, indent=1)


@mcp.tool()
def joint_stress(series_ids: str, confidence: float = 0.99,
                 horizon_months: int = 3, use_t_copula: bool = True) -> str:
    """Correlated multi-market stress. `series_ids` is comma-separated.

    Uses a Student-t copula by default: a Gaussian copula has zero tail
    dependence, so it assigns vanishing probability to exactly the joint move
    (rupee slide plus crude spike) an Indian import book is exposed to.
    """
    ids = [s.strip() for s in series_ids.split(",") if s.strip()]
    if len(ids) < 2:
        return _err("give at least two comma-separated series ids",
                    available=_available())
    missing = [i for i in ids if _load_raw(i) is None]
    if missing:
        return _err(f"unknown series: {', '.join(missing)}", available=_available())

    mret = {}
    for i in ids:
        closes = _load_raw(i)
        mr = stats.monthly_log_returns(closes)
        if len(mr) < 24:
            return _err(f"'{i}' has {len(mr)} monthly returns; need >= 24")
        mret[i] = mr
    cm = copula.corr_matrix(mret, min_obs=24)
    dfe = copula.estimate_df(mret)
    vols = []
    for i in cm["ids"]:
        v = [x for _d, x in mret[i]]
        vols.append(stats.stdev(v) * (max(1, horizon_months) ** 0.5))
    draws, meta = copula.simulate(cm["matrix"], vols, paths=20000,
                                  df=dfe["df"] if use_t_copula else None, seed=7)
    if draws is None:
        return _err(meta.get("error", "simulation failed"))
    worst = [max(d) for d in draws]           # worst single-market move per path
    basket = [sum(d) / len(d) for d in draws]  # equal-weighted basket move
    return json.dumps({
        "series": cm["ids"], "horizon_months": horizon_months,
        "correlations": cm["pairs"], "measured_pairs": cm["measured_pairs"],
        "copula": meta["copula"], "df": meta.get("df"),
        "psd_repaired": meta.get("psd_repaired"),
        "t_copula_estimation": dfe,
        "worst_single_market_move": {
            "p50": round(stats.quantile(worst, 0.50), 4),
            f"p{int(confidence*100)}": round(stats.quantile(worst, confidence), 4)},
        "equal_weighted_basket_move": {
            "p50": round(stats.quantile(basket, 0.50), 4),
            f"p{int(confidence*100)}": round(stats.quantile(basket, confidence), 4)},
        "units": "log return over the horizon",
    }, indent=1)


@mcp.tool()
def hedge_effectiveness(exposure_values: str, hedge_values: str) -> str:
    """Ind AS 109 hedge-effectiveness test on two comma-separated series of
    fair values (hedged item, hedging instrument), in the same currency and
    observed on the same dates.

    Runs both the dollar-offset and regression methods against the 80-125%
    working benchmark and returns a verdict. This is the test the client's own
    auditor will run, so the answer is objectively right or wrong.
    """
    try:
        exp = [float(x) for x in exposure_values.replace(" ", "").split(",") if x]
        hed = [float(x) for x in hedge_values.replace(" ", "").split(",") if x]
    except ValueError:
        return _err("both inputs must be comma-separated numbers")
    if len(exp) != len(hed):
        return _err(f"series lengths differ: {len(exp)} vs {len(hed)}")
    return json.dumps(hedge.assess(exp, hed), indent=1)


@mcp.tool()
def basis_risk(series_a: str, series_b: str) -> str:
    """Quantify the basis between an exposure and the instrument available to
    hedge it — MCX crude settling against WTI while the import basket is
    Dubai-linked, Newcastle 6,000 kcal coal against Indonesian 4,200 kcal.
    Returns correlation, R-squared, basis volatility and the minimum-variance
    hedge ratio. Accepts either two known series ids or comma-separated prices.
    """
    ca, cb = _load_raw(series_a.strip()), _load_raw(series_b.strip())
    if ca and cb:
        # Align on dates. Truncating two series from the right pairs prices from
        # different days whenever the calendars differ, which silently destroys
        # the correlation the caller asked about — Brent against WTI came back at
        # 0.10 instead of ~0.95 before this was fixed.
        ma, mb = dict(ca), dict(cb)
        common = sorted(set(ma) & set(mb))
        if len(common) < 30:
            return _err(f"only {len(common)} common dates between "
                        f"'{series_a}' and '{series_b}'")
        res = hedge.basis_risk([ma[d] for d in common], [mb[d] for d in common],
                               series_a.strip(), series_b.strip())
        res.update({"aligned_on": "common dates", "common_observations": len(common),
                    "first": common[0], "last": common[-1]})
        return json.dumps(res, indent=1)

    def _prices(spec):
        c = _load_raw(spec.strip())
        if c:
            return [v for _d, v in c], spec.strip()
        try:
            return [float(x) for x in spec.replace(" ", "").split(",") if x], "supplied"
        except ValueError:
            return None, spec

    a, la = _prices(series_a)
    b, lb = _prices(series_b)
    if a is None or b is None:
        return _err("give known series ids or comma-separated prices",
                    available=_available())
    n = min(len(a), len(b))
    res = hedge.basis_risk(a[-n:], b[-n:], la, lb)
    res["aligned_on"] = ("positional — supplied series are assumed to share "
                         "observation dates; confirm before quoting")
    return json.dumps(res, indent=1)


@mcp.tool()
def company_cfar(company_id: str = "") -> str:
    """Cash-Flow-at-Risk in INR crore for a company in the universe, with the
    input drivers ranked. Omit `company_id` to list everything scored.

    Reads the figures computed by scripts/compute_risk.py so the tool and the
    dashboard cannot disagree. Companies without verified financials, or whose
    revenue-side exposure exceeds their cost side, are reported as skipped with
    the reason rather than scored on assumptions.
    """
    rj = _risk_json()
    cf = rj.get("cfar") or {}
    if not cf:
        return _err("data/risk.json not found — run scripts/compute_risk.py")
    if not company_id:
        return json.dumps({
            "scored": [{"company": k, "name": v.get("name"),
                        "cfar_cr": v.get("cfar_cr"),
                        "pct_ebitda": v.get("cfar_pct_ebitda"),
                        "coverage_pct": v.get("input_coverage_pct"),
                        "gross_converter_flag": bool(v.get("pass_through_risk"))}
                       for k, v in sorted(cf.items(),
                                          key=lambda kv: -(kv[1].get("cfar_cr") or 0))],
            "skipped": rj.get("cfar_skipped", []),
            "generated": rj.get("generated"),
        }, indent=1)
    if company_id not in cf:
        skip = [s for s in rj.get("cfar_skipped", []) if s.get("company") == company_id]
        if skip:
            return json.dumps({"company": company_id, "scored": False, **skip[0]}, indent=1)
        return _err(f"'{company_id}' is not in the scored set",
                    scored=sorted(cf.keys()))
    return json.dumps(cf[company_id], indent=1)


@mcp.tool()
def model_summary(series_id: str = "") -> str:
    """The published model output for a series: GARCH fit, EVT tail, VaR
    cross-check and backtest verdicts. Omit `series_id` for the whole set plus
    the engine's method notes and what it refused to compute."""
    rj = _risk_json()
    if not rj:
        return _err("data/risk.json not found — run scripts/compute_risk.py")
    if series_id:
        s = (rj.get("series") or {}).get(series_id)
        if not s:
            return _err(f"no series '{series_id}'",
                        available=sorted((rj.get("series") or {}).keys()))
        return json.dumps(s, indent=1)
    return json.dumps({"generated": rj.get("generated"),
                       "engine_version": rj.get("engine_version"),
                       "joint": rj.get("joint"),
                       "meta": rj.get("meta")}, indent=1)


if __name__ == "__main__":
    mcp.run()
