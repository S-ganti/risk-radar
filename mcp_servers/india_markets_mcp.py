#!/usr/bin/env python3
"""
india-markets-mcp — market data and the hedgeability layer as callable tools.

The hedgeability lookup is the one that matters. Bloomberg will tell an agent
the LME aluminium price; it will not tell it that MCX crude settles against WTI
while the client's import basket is Dubai-linked, or that a jet-fuel hedge for
an Indian carrier has no onshore contract and therefore carries a currency leg
that sits under the April 2026 NDF prohibition. That classification is checkable
against published exchange contract specifications, which makes it the most
defensible thing in the whole system.

Install once:  pip install mcp
Run:           python mcp_servers/india_markets_mcp.py     (stdio)
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
        print("india-markets-mcp needs the MCP SDK:  pip install mcp", file=sys.stderr)
        raise

from engine import stats  # noqa: E402

DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
mcp = _Server("india-markets")


def _load(name):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _err(msg, **extra):
    return json.dumps({"error": msg, **extra}, indent=1)


def _raw(series_id):
    p = os.path.join(RAW, f"{series_id}.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return [(d, float(v)) for d, v in json.load(f)]


@mcp.tool()
def get_spot(symbol: str = "") -> str:
    """Latest spot marks with their source and as-of date. Omit `symbol` for all.

    Every mark carries the date it was observed and where it came from. Marks
    the pipeline cannot fetch (EUA, the CBAM reference price) are manual and say
    so — check their age before quoting them.
    """
    latest = _load("latest.json")
    if not latest:
        return _err("data/latest.json not found — run scripts/pipeline.py")
    spot = latest.get("spot", {})
    if symbol:
        s = spot.get(symbol.lower())
        if not s:
            return _err(f"no spot mark '{symbol}'", available=sorted(spot))
        return json.dumps({"symbol": symbol.lower(), **s}, indent=1)
    return json.dumps({"generated": latest.get("generated"), "spot": spot,
                       "stale_marks": [k for k, v in spot.items()
                                       if "manual" in str(v.get("src", "")).lower()],
                       "note": "Marks flagged in stale_marks are entered by hand "
                               "because no free keyless feed exists; verify the "
                               "as-of date before use."}, indent=1)


@mcp.tool()
def get_series(series_id: str, last_n: int = 60) -> str:
    """Price history for one market series, most recent `last_n` observations."""
    rows = _raw(series_id)
    if rows is None:
        avail = sorted(f[:-5] for f in os.listdir(RAW)) if os.path.isdir(RAW) else []
        return _err(f"no series '{series_id}'", available=avail)
    tail = rows[-max(1, last_n):]
    rets = [r for _d, r in stats.log_returns(rows)]
    return json.dumps({
        "series": series_id, "observations_total": len(rows),
        "first": rows[0][0], "last": rows[-1][0], "last_price": rows[-1][1],
        "returned": len(tail), "data": [{"date": d, "close": v} for d, v in tail],
        "summary": {"mean_return": round(stats.mean(rets), 6),
                    "volatility": round(stats.stdev(rets), 6),
                    "skewness": round(stats.skewness(rets), 3),
                    "excess_kurtosis": round(stats.excess_kurtosis(rets), 3)},
    }, indent=1)


@mcp.tool()
def get_volatility(series_id: str = "") -> str:
    """Computed volatilities with method, sample size and 5-year percentile.
    Omit `series_id` for the whole set."""
    latest = _load("latest.json")
    if not latest:
        return _err("data/latest.json not found — run scripts/pipeline.py")
    vols = latest.get("vols", {})
    if series_id:
        v = vols.get(series_id)
        if not v:
            return _err(f"no volatility for '{series_id}'", available=sorted(vols))
        return json.dumps({"series": series_id, **v}, indent=1)
    return json.dumps({"generated": latest.get("generated"), "vols": vols,
                       "count": len(vols)}, indent=1)


@mcp.tool()
def get_correlations(series_id: str = "", min_abs: float = 0.0) -> str:
    """Measured correlations from overlapping monthly log returns.

    Pairs without enough overlapping history are absent rather than defaulted:
    a correlation the data cannot support is worse than no correlation.
    """
    latest = _load("latest.json")
    if not latest:
        return _err("data/latest.json not found — run scripts/pipeline.py")
    corr = latest.get("corr", {})
    rows = []
    for k, v in corr.items():
        a, b = k.split("|")
        if series_id and series_id not in (a, b):
            continue
        if abs(v) < min_abs:
            continue
        rows.append({"pair": k, "correlation": v})
    rows.sort(key=lambda r: -abs(r["correlation"]))
    return json.dumps({"filter": series_id or None, "min_abs": min_abs,
                       "pairs": rows, "count": len(rows),
                       "method": "Pearson on up to 60 overlapping monthly log "
                                 "returns, minimum 24"}, indent=1)


@mcp.tool()
def get_regime() -> str:
    """Current market regime and the observables behind it — realised-volatility
    percentile, rupee momentum, and breadth of commodity moves."""
    latest = _load("latest.json")
    if not latest:
        return _err("data/latest.json not found — run scripts/pipeline.py")
    return json.dumps({"generated": latest.get("generated"),
                       "regime": latest.get("regime"),
                       "inr_momentum": latest.get("inr"),
                       "breadth_pct": latest.get("breadth"),
                       "velocity": latest.get("velocity"),
                       "note": "Regime is computed from market observables, not "
                               "from the dashboard's own risk scores."}, indent=1)


@mcp.tool()
def hedgeability(commodity_id: str = "", bucket: str = "") -> str:
    """Can an Indian client hedge this input, and with what?

    Returns venue, benchmark contract, currency, whether an onshore MCX/NCDEX
    contract exists, and the resulting bucket: onshore INR / offshore USD only /
    proxy only / OTC / no hedge exists. Filter by `bucket` to list a class.

    This is checkable against published exchange contract specifications — it is
    a fact about the world rather than a model output, which is what makes it
    the most defensible layer in the tool.
    """
    com = _load("commodities.json")
    if not com:
        return _err("data/commodities.json not found")
    items = com.get("commodities", com) if isinstance(com, dict) else com
    if isinstance(items, dict):
        rows = [{"id": k, **(v if isinstance(v, dict) else {"value": v})}
                for k, v in items.items()]
    else:
        rows = list(items)

    def _hedge_fields(r):
        out = {"id": r.get("id"), "name": r.get("name") or r.get("label")}
        for key in ("family", "hedgeability", "hedge_bucket", "bucket", "venue",
                    "benchmark", "currency", "onshore", "mcx", "india_contract",
                    "how_it_trades", "settlement", "liquidity", "basis", "notes"):
            if key in r:
                out[key] = r[key]
        return out

    if commodity_id:
        hit = next((r for r in rows if r.get("id") == commodity_id), None)
        if not hit:
            return _err(f"no commodity '{commodity_id}'",
                        available=sorted(r.get("id", "") for r in rows)[:60])
        return json.dumps(_hedge_fields(hit), indent=1)

    out = [_hedge_fields(r) for r in rows]
    if bucket:
        b = bucket.lower()
        out = [r for r in out
               if b in json.dumps({k: v for k, v in r.items()
                                   if k not in ("id", "name")}).lower()]
    return json.dumps({"filter_bucket": bucket or None, "count": len(out),
                       "commodities": out[:120],
                       "note": "Bucket classification is derived from published "
                               "contract specifications. An offshore-only hedge "
                               "carries a currency leg, and that leg sits under the "
                               "1 April 2026 RBI NDF prohibition."}, indent=1)


@mcp.tool()
def score_history(risk_id: str = "") -> str:
    """Real composite-score history, one point per pipeline run.

    This is the series any validation claim has to rest on. Risks whose inputs
    are curated rather than market-driven show a single distinct value across the
    whole window — they have not moved, which is why they cannot be validated.
    """
    latest = _load("latest.json")
    hist = (latest or {}).get("history") or _load("history.json")
    if not hist:
        return _err("no score history found")
    dates, scores = hist.get("dates", []), hist.get("scores", {})
    if risk_id:
        s = scores.get(risk_id)
        if not s:
            return _err(f"no history for '{risk_id}'", available=sorted(scores))
        return json.dumps({"risk": risk_id, "dates": dates, "scores": s,
                           "distinct_values": len(set(s)),
                           "moved": len(set(s)) > 1}, indent=1)
    summary = {k: {"n": len(v), "distinct": len(set(v)),
                   "first": v[0] if v else None, "last": v[-1] if v else None,
                   "moved": len(set(v)) > 1}
               for k, v in scores.items()}
    n_days = len(dates)
    return json.dumps({
        "span": {"from": dates[0] if dates else None,
                 "to": dates[-1] if dates else None, "observations": n_days},
        "risks": summary,
        "validation_ready": n_days >= 84,
        "validation_note": (
            f"{n_days} observations. A twelve-week window (84) is the minimum "
            f"before any calibration or discrimination metric means anything, and "
            f"only for the risks whose scores actually move."),
    }, indent=1)


if __name__ == "__main__":
    mcp.run()
