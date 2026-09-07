#!/usr/bin/env python3
"""
Smoke tests for the three MCP servers: every tool is called, its JSON is parsed,
and the result is checked for the shape a caller depends on.

Network-dependent regwatch tools are exercised but never asserted on content —
an unreachable feed must degrade to a stated error, not a false 'no change'.

Run: python tests/test_mcp_servers.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAILS = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILS.append(name)


def call(fn, *a, **kw):
    """FastMCP's decorator returns a FunctionTool; unwrap to the plain callable."""
    f = getattr(fn, "fn", None) or getattr(fn, "func", None) or fn
    return json.loads(f(*a, **kw))


def test_risk_engine():
    print("\nrisk-engine-mcp")
    from mcp_servers import risk_engine_mcp as m

    r = call(m.list_series)
    check("list_series returns series", r.get("count", 0) > 0, f"{r.get('count')} series")
    ids = [s["id"] for s in r["series"]]
    check("crude present", "crude" in ids)

    v = call(m.run_var, "crude", 0.99, 1)
    check("run_var historical produces a loss", v["historical"]["var"] > 0,
          f"{v['historical']['var']:.4f}")
    check("run_var returns all three estimators",
          all(v.get(k) for k in ("historical", "parametric", "monte_carlo")))
    check("run_var reports estimator spread", "spread" in v,
          v.get("spread", {}).get("note", "")[:38])

    bad = call(m.run_var, "nonexistent")
    check("run_var refuses unknown series", "error" in bad and "available" in bad)

    b = call(m.backtest_var, "crude", 0.99, 1000)
    check("backtest returns a verdict", "verdict" in b, b.get("verdict", "")[:40])
    thin = call(m.backtest_var, "crude", 0.99, 250)
    check("thin window is warned about", "warning" in thin)

    g = call(m.fit_garch, "crude", 21)
    check("garch fit converges", g["fit"]["converged"])
    check("garch is stationary", g["fit"]["persistence"] < 1,
          f"{g['fit']['persistence']:.4f}")
    check("garch forecast returned", g["forecast"]["sigma"] > 0)
    gm = call(m.fit_garch, "copper")
    check("garch refuses a short monthly series", "error" in gm,
          gm.get("error", "")[:45])

    t = call(m.fit_tail, "crude", 0.90)
    check("tail fit returns xi", "xi" in t, f"xi={t.get('xi')}")
    check("tail table produced", len(t.get("tail_table", [])) == 4)
    check("tail shape described", "tail_shape" in t)

    j = call(m.joint_stress, "crude,gold,usdinr", 0.99, 3, True)
    check("joint stress uses t copula", j.get("copula") == "student-t", str(j.get("df")))
    check("joint stress returns basket move", "equal_weighted_basket_move" in j)
    j1 = call(m.joint_stress, "crude")
    check("joint stress needs 2+ series", "error" in j1)

    exp = ",".join(str(x) for x in [100, 105, 103, 110, 108, 115, 112, 120])
    hed = ",".join(str(200 - x) for x in [100, 105, 103, 110, 108, 115, 112, 120])
    h = call(m.hedge_effectiveness, exp, hed)
    check("perfect hedge judged effective", h["verdict"] == "effective", h["verdict"])
    check("dollar offset ~100%",
          abs(h["dollar_offset"]["cumulative_ratio_pct"] - 100) < 0.01)
    hbad = call(m.hedge_effectiveness, "1,2,3", "1,2")
    check("mismatched lengths refused", "error" in hbad)

    br = call(m.basis_risk, "crude", "wti")
    check("basis risk aligns on common dates", br.get("aligned_on") == "common dates",
          f"{br.get('common_observations')} obs")
    # Brent and WTI are the same barrel with a freight and quality spread; if the
    # tool cannot see that, it is misaligned rather than insightful.
    check("brent vs wti correlation is high", (br.get("correlation") or 0) > 0.8,
          f"rho={br.get('correlation')}")
    check("basis vol reported", br.get("basis_vol_per_period") is not None)
    check("min-variance hedge ratio near 1",
          0.7 < (br.get("hedge_ratio_min_variance") or 0) < 1.3,
          str(br.get("hedge_ratio_min_variance")))

    c = call(m.company_cfar)
    check("cfar list returned", len(c.get("scored", [])) > 0,
          f"{len(c.get('scored', []))} scored")
    top = c["scored"][0]["company"]
    c1 = call(m.company_cfar, top)
    check("cfar detail has rupee figure", c1.get("cfar_cr") is not None)
    check("cfar detail ranks drivers", isinstance(c1.get("drivers"), list))
    cmiss = call(m.company_cfar, "not-a-company")
    check("cfar refuses unknown company", "error" in cmiss or cmiss.get("scored") is False)

    s = call(m.model_summary)
    check("model summary has method notes", len(s["meta"]["method_notes"]) >= 5)
    s1 = call(m.model_summary, "crude")
    check("per-series summary has garch and evt",
          "garch" in s1 and "evt" in s1)


def test_india_markets():
    print("\nindia-markets-mcp")
    from mcp_servers import india_markets_mcp as m

    s = call(m.get_spot)
    check("spot marks returned", len(s.get("spot", {})) > 3)
    check("stale manual marks identified", "stale_marks" in s,
          ",".join(s.get("stale_marks", [])))
    u = call(m.get_spot, "usdinr")
    check("usdinr spot has as-of and source", u.get("asof") and u.get("src"),
          f"{u.get('v')} @ {u.get('asof')}")

    g = call(m.get_series, "gold", 20)
    check("series returns requested tail", g["returned"] == 20)
    check("series summary computed", g["summary"]["volatility"] > 0)
    bad = call(m.get_series, "nope")
    check("unknown series refused with alternatives", "available" in bad)

    v = call(m.get_volatility, "crude")
    check("volatility carries method and n", v.get("method") and v.get("n"),
          v.get("method"))

    c = call(m.get_correlations, "crude", 0.3)
    check("correlations filtered by threshold",
          all(abs(r["correlation"]) >= 0.3 for r in c["pairs"]),
          f"{c['count']} pairs")

    r = call(m.get_regime)
    check("regime label present", r["regime"]["label"] in
          ("normal", "elevated", "stressed", "crisis"), r["regime"]["label"])
    check("regime components exposed", "components" in r["regime"])

    h = call(m.hedgeability)
    check("hedgeability lists commodities", h.get("count", 0) > 20,
          f"{h.get('count')} commodities")

    sh = call(m.score_history)
    check("score history has a span", sh["span"]["observations"] > 0,
          f"{sh['span']['observations']} obs {sh['span']['from']}->{sh['span']['to']}")
    check("validation readiness stated", "validation_ready" in sh,
          str(sh["validation_ready"]))
    check("moved/unmoved risks distinguished",
          any(v["moved"] for v in sh["risks"].values())
          and any(not v["moved"] for v in sh["risks"].values()))


def test_regwatch():
    print("\nregwatch-mcp  (network-dependent: content is not asserted)")
    from mcp_servers import regwatch_mcp as m

    s = call(m.list_sources)
    check("sources listed", len(s["sources"]) >= 4)
    check("official-source policy stated", "Official sources only" in s["policy"])

    e = call(m.check_elapsed_deadlines)
    check("elapsed-deadline check runs offline", "today" in e)
    check("watchlist deadlines evaluated", "watchlist_deadlines_elapsed" in e)
    check("next deadline identified", e.get("next_watchlist_deadline") is not None,
          json.dumps(e.get("next_watchlist_deadline")))
    check("no watchlist deadline is already elapsed",
          len(e["watchlist_deadlines_elapsed"]) == 0,
          json.dumps(e["watchlist_deadlines_elapsed"]))

    n = call(m.fetch_notifications, "rbi_notifications", 60)
    ok = ("items" in n) or ("error" in n and "unknown" not in n["error"])
    check("rbi feed returns items or a stated error", ok,
          f"{n.get('count', n.get('error', ''))}"[:60])
    if "error" in n:
        check("unreachable feed does not imply 'no change'", "note" in n)

    bad = call(m.fetch_notifications, "not_a_source")
    check("unknown source refused", "error" in bad and "available" in bad)

    d = call(m.diff_watchlist, 45)
    check("watchlist diff runs", "checked" in d and d["checked"] >= 5)
    check("diff refuses to conclude on its own",
          "human" in d["verdict"].lower() or "not proof" in d["verdict"].lower())
    check("candidates flagged as untrusted", "untrusted" in d["instruction"].lower())

    q = call(m.search_official, "hedging", 120)
    check("search returns a result set", "results" in q)
    check("search notes feeds are untrusted input", "untrusted" in q["note"].lower())


if __name__ == "__main__":
    for t in (test_risk_engine, test_india_markets, test_regwatch):
        try:
            t()
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR in {t.__name__}: {type(e).__name__}: {e}")
            FAILS.append(f"{t.__name__} raised {type(e).__name__}")
    print("\n" + "=" * 60)
    if FAILS:
        print(f"{len(FAILS)} FAILED: {', '.join(FAILS)}")
        raise SystemExit(1)
    print("All MCP server tests passed.")
