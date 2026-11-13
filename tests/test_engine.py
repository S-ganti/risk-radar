#!/usr/bin/env python3
"""
Engine tests: each one checks a property the maths must satisfy, against data
whose right answer is known by construction. Run: python tests/test_engine.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import cfar, copula, evt, garch, hedge, stats, var  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILS.append(name)


def normal_series(n, sd=0.01, seed=1):
    rng = random.Random(seed)
    return [rng.gauss(0, sd) for _ in range(n)]


def test_stats():
    print("\nstats")
    xs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    check("quantile median", abs(stats.quantile(xs, 0.5) - 5.5) < 1e-9)
    check("quantile min/max", stats.quantile(xs, 0) == 1 and stats.quantile(xs, 1) == 10)
    check("z(0.99) ~ 2.326", abs(stats.z(0.99) - 2.3263) < 1e-3,
          f"{stats.z(0.99):.4f}")
    check("Phi(0) = 0.5", abs(stats.Phi(0) - 0.5) < 1e-12)
    n = normal_series(6000, 1.0, seed=7)
    check("excess kurtosis of normal ~ 0", abs(stats.excess_kurtosis(n)) < 0.2,
          f"{stats.excess_kurtosis(n):.3f}")
    # a t(5) sample must show clearly positive excess kurtosis
    rng = random.Random(3)
    t5 = [rng.gauss(0, 1) / math.sqrt(rng.gammavariate(2.5, 2.0) / 5) for _ in range(6000)]
    check("excess kurtosis of t(5) > 1", stats.excess_kurtosis(t5) > 1.0,
          f"{stats.excess_kurtosis(t5):.2f}")
    check("pearson of identical series = 1", abs(stats.pearson(xs, xs) - 1) < 1e-12)
    check("pearson of opposite series = -1",
          abs(stats.pearson(xs, [-x for x in xs]) + 1) < 1e-12)
    agg = stats.aggregate_overlapping([1, 1, 1, 1, 1], 3)
    check("overlapping aggregation", agg == [3, 3, 3], str(agg))
    check("chi2_sf(3.84, 1) ~ 0.05", abs(stats.chi2_sf(3.841, 1) - 0.05) < 0.002,
          f"{stats.chi2_sf(3.841,1):.4f}")
    check("chi2_sf(5.99, 2) ~ 0.05", abs(stats.chi2_sf(5.991, 2) - 0.05) < 0.002,
          f"{stats.chi2_sf(5.991,2):.4f}")


def test_var():
    print("\nvar / es")
    sd = 0.02
    r = normal_series(4000, sd, seed=11)
    p = var.parametric(r, 0.99)
    h = var.historical(r, 0.99)
    check("parametric VaR99 ~ 2.326 sigma", abs(p["var"] - 2.3263 * sd) < 0.0015,
          f"{p['var']:.4f} vs {2.3263*sd:.4f}")
    check("historical ~ parametric on normal data",
          abs(h["var"] - p["var"]) / p["var"] < 0.12,
          f"hist {h['var']:.4f} vs param {p['var']:.4f}")
    check("ES > VaR always", p["es"] > p["var"] and h["es"] > h["var"])
    check("VaR99 > VaR95", var.parametric(r, 0.99)["var"] > var.parametric(r, 0.95)["var"])
    h10 = var.historical(r, 0.99, horizon=10)
    check("10-day VaR > 1-day VaR", h10["var"] > h["var"],
          f"{h10['var']:.4f} vs {h['var']:.4f}")
    check("10-day VaR roughly sqrt(10) scaled",
          1.5 < h10["var"] / h["var"] < 5.5, f"ratio {h10['var']/h['var']:.2f}")
    mc = var.monte_carlo(r, 0.99, sigma=sd, df=5, paths=20000)
    check("t-MC VaR exceeds normal parametric", mc["var"] > p["var"] * 0.95,
          f"mc {mc['var']:.4f} param {p['var']:.4f}")
    check("short series returns None", var.historical([0.01] * 10, 0.99) is None)

    # Kupiec: a correctly specified VaR should not be rejected
    exc = [False] * 990 + [True] * 10
    random.Random(5).shuffle(exc)
    k = var.kupiec_pof(exc, 0.99)
    check("kupiec accepts correct coverage", not k["reject_5pct"],
          f"rate {k['rate']:.4f} p={k['p_value']:.3f}")
    bad = [False] * 900 + [True] * 100
    random.Random(5).shuffle(bad)
    check("kupiec rejects 10x over-exceedance",
          var.kupiec_pof(bad, 0.99)["reject_5pct"])
    clustered = ([False] * 490 + [True] * 10) * 2
    ci = var.christoffersen_independence(clustered)
    check("christoffersen flags clustering", ci["reject_5pct"] or ci["lr"] > 3.0,
          f"lr={ci['lr']}")
    # Machinery check against a VaR known to be correct by construction.
    true_var = -stats.z(0.01) * sd
    k_true = var.kupiec_pof([(-x) > true_var for x in r], 0.99)
    check("kupiec accepts a VaR that is right by construction",
          not k_true["reject_5pct"], f"rate {k_true['rate']:.4f}")

    # Historical simulation at 99% on 250 days rests on 2-3 tail points and is
    # known to over-exceed. The engine must SAY so rather than pass silently.
    thin = var.backtest(r, 0.99, window=250)
    check("thin estimation window is flagged", "warning" in thin,
          f"{thin['exceptions']}/{thin['tested']} tail_obs={thin['estimation_window_tail_obs']}")
    check("thin-window verdict does not blame the model",
          "thin" in thin.get("verdict", ""), thin.get("verdict", "")[:40])
    wide = var.backtest(r, 0.99, window=1000)
    check("adequate window passes coverage", not wide["kupiec"]["reject_5pct"],
          f"{wide['exceptions']}/{wide['tested']} rate={wide['kupiec']['rate']:.4f}")
    check("adequate window is not flagged", "warning" not in wide)
    at95 = var.backtest(r, 0.95, window=250)
    check("95% on 250 days is adequate and passes",
          not at95["kupiec"]["reject_5pct"] and "warning" not in at95,
          f"rate={at95['kupiec']['rate']:.4f}")


def test_garch():
    print("\ngarch")
    # simulate a known GARCH(1,1) and check the fit recovers it
    omega, alpha, beta = 1e-6, 0.08, 0.90
    rng = random.Random(23)
    h = omega / (1 - alpha - beta)
    r = []
    for _ in range(6000):
        e = rng.gauss(0, 1) * math.sqrt(h)
        r.append(e)
        h = omega + alpha * e * e + beta * h
    f = garch.fit(r)
    check("fit returns a result", f is not None)
    check("alpha recovered", abs(f["alpha"] - alpha) < 0.05,
          f"{f['alpha']:.4f} vs {alpha}")
    check("beta recovered", abs(f["beta"] - beta) < 0.06,
          f"{f['beta']:.4f} vs {beta}")
    check("persistence < 1 (stationary)", f["persistence"] < 1.0,
          f"{f['persistence']:.4f}")
    true_uncond = math.sqrt(omega / (1 - alpha - beta))
    check("unconditional vol recovered",
          abs(f["sigma_uncond"] - true_uncond) / true_uncond < 0.35,
          f"{f['sigma_uncond']:.5f} vs {true_uncond:.5f}")
    check("half-life positive", f["half_life_periods"] > 0)
    fc = garch.forecast(f, 21)
    check("21d forecast > 1d sigma", fc["sigma"] > f["sigma_next"])
    check("short series returns None", garch.fit(normal_series(100)) is None)


def test_evt():
    print("\nevt")
    # exceedances of an exponential tail have xi = 0
    rng = random.Random(31)
    r = [-rng.expovariate(50) if rng.random() < 0.5 else rng.expovariate(50)
         for _ in range(4000)]
    f = evt.fit_pot(r, 0.90)
    check("exponential tail gives xi near 0", abs(f["xi"]) < 0.25, f"xi={f['xi']}")

    # a Pareto(2) tail is heavy: xi should be clearly positive
    heavy = []
    for _ in range(4000):
        u = rng.random()
        x = (1 - u) ** (-1 / 2.0) - 1        # Pareto tail, xi = 0.5
        heavy.append(-x / 100 if rng.random() < 0.5 else x / 100)
    fh = evt.fit_pot(heavy, 0.90)
    check("pareto tail gives xi > 0.2", fh["xi"] > 0.2, f"xi={fh['xi']}")
    check("heavier tail has larger xi than exponential", fh["xi"] > f["xi"],
          f"{fh['xi']} > {f['xi']}")
    q99, q995 = evt.tail_quantile(fh, 0.99), evt.tail_quantile(fh, 0.995)
    check("tail quantiles increase with confidence", q995 > q99,
          f"{q995:.5f} > {q99:.5f}")
    check("ES exceeds VaR at same level", evt.tail_es(fh, 0.99) > q99)
    check("mean-excess diagnostic produced", len(fh["mean_excess"]) >= 5)
    check("short series refuses to fit", "error" in evt.fit_pot(normal_series(100)))
    tbl = evt.tail_table(fh)
    check("tail table has 4 levels", len(tbl) == 4)


def test_copula():
    print("\ncopula")
    rng = random.Random(41)
    n = 1500
    a, b, c = [], [], []
    for _ in range(n):
        z1, z2 = rng.gauss(0, 1), rng.gauss(0, 1)
        a.append(z1 * 0.02)
        b.append((0.8 * z1 + 0.6 * z2) * 0.02)      # corr ~0.8 with a
        c.append(rng.gauss(0, 1) * 0.02)            # independent
    dates = [f"2020-{1+i//28:02d}-{1+i%28:02d}" for i in range(n)]
    sm = {"a": list(zip(dates, a)), "b": list(zip(dates, b)), "c": list(zip(dates, c))}
    cm = copula.corr_matrix(sm, min_obs=24)
    i_a, i_b, i_c = cm["ids"].index("a"), cm["ids"].index("b"), cm["ids"].index("c")
    check("correlated pair recovered ~0.8",
          abs(cm["matrix"][i_a][i_b] - 0.8) < 0.15, f"{cm['matrix'][i_a][i_b]:.3f}")
    check("independent pair near 0", abs(cm["matrix"][i_a][i_c]) < 0.2,
          f"{cm['matrix'][i_a][i_c]:.3f}")

    bad = [[1.0, 0.99, -0.99], [0.99, 1.0, 0.99], [-0.99, 0.99, 1.0]]
    fixed, repaired = copula.nearest_psd(bad)
    check("non-PSD matrix repaired", repaired)
    check("repaired matrix is choleskyable", copula.cholesky(fixed) is not None)
    check("repaired diagonal is 1", all(abs(fixed[i][i] - 1) < 1e-6 for i in range(3)))

    R = [[1.0, 0.8], [0.8, 1.0]]
    g, _ = copula.simulate(R, [0.05, 0.05], paths=6000, df=None, seed=2)
    t, _ = copula.simulate(R, [0.05, 0.05], paths=6000, df=5, seed=2)
    gx = [p[0] for p in g]
    tx = [p[0] for p in t]
    check("gaussian marginal vol ~ target", abs(stats.stdev(gx) - 0.05) < 0.006,
          f"{stats.stdev(gx):.4f}")
    check("t marginal vol ~ target (standardised)",
          abs(stats.stdev(tx) - 0.05) < 0.012, f"{stats.stdev(tx):.4f}")
    check("t copula fatter tailed than gaussian",
          stats.excess_kurtosis(tx) > stats.excess_kurtosis(gx),
          f"t {stats.excess_kurtosis(tx):.2f} vs g {stats.excess_kurtosis(gx):.2f}")
    gtd = copula.empirical_tail_dependence([p[0] for p in g], [p[1] for p in g])
    ttd = copula.empirical_tail_dependence([p[0] for p in t], [p[1] for p in t])
    check("t copula shows more tail dependence than gaussian", ttd >= gtd,
          f"t {ttd} vs g {gtd}")
    est = copula.estimate_df(sm)
    check("df estimator returns a number in range", 4.5 <= est["df"] <= 30,
          f"df={est['df']}")


def test_hedge():
    print("\nhedge (Ind AS 109)")
    exposure = [100, 105, 103, 110, 108, 115, 112, 120]
    perfect = [100 - (e - 100) for e in exposure]        # exact offset
    a = hedge.assess(exposure, perfect)
    check("perfect hedge: dollar offset 100%",
          abs(a["dollar_offset"]["cumulative_ratio_pct"] - 100) < 0.01,
          f"{a['dollar_offset']['cumulative_ratio_pct']}")
    check("perfect hedge: slope -1", abs(a["regression"]["slope"] + 1) < 1e-9,
          f"{a['regression']['slope']}")
    check("perfect hedge: R2 = 1", abs(a["regression"]["r_squared"] - 1) < 1e-9)
    check("perfect hedge: verdict effective", a["verdict"] == "effective")

    rng = random.Random(77)
    noisy = [100 - (e - 100) * 0.9 + rng.gauss(0, 4) for e in exposure]
    b = hedge.assess(exposure, noisy)
    check("noisy hedge produces a verdict", b["verdict"] in
          ("effective", "ineffective", "mixed"), b["verdict"])

    unrelated = [100 + rng.gauss(0, 5) for _ in exposure]
    c = hedge.assess(exposure, unrelated)
    check("unrelated instrument is not effective", c["verdict"] != "effective",
          c["verdict"])

    over = [100 - (e - 100) * 2.0 for e in exposure]     # 200% ratio
    d = hedge.assess(exposure, over)
    check("over-hedge falls outside the band",
          not d["dollar_offset"]["cumulative_in_band"],
          f"{d['dollar_offset']['cumulative_ratio_pct']}%")

    pa = [100 * (1.01 ** i) for i in range(60)]
    pb = [100 * (1.009 ** i) for i in range(60)]
    br = hedge.basis_risk(pa, pb, "Dubai-linked import", "MCX crude (WTI-settled)")
    check("basis risk computes a hedge ratio",
          br.get("hedge_ratio_min_variance") is not None)
    check("basis vol reported", br.get("basis_vol_per_period") is not None)


def test_cfar():
    print("\ncfar")
    weights = {"crude": 0.4, "alum": 0.3}
    vols = {"crude": 0.08, "alum": 0.06}
    R = [[1.0, 0.4], [0.4, 1.0]]          # ids sort to [alum, crude]
    out = cfar.simulate_company(weights, vols, R, cost_base_cr=10000,
                                ebitda_cr=2000, horizon_months=12,
                                pass_through=0.5, hedge_ratio=0.0, paths=8000)
    check("cfar returns a rupee figure", out.get("cfar_cr") is not None,
          f"{out.get('cfar_cr')} cr")
    check("cfar is positive (a cost increase)", out["cfar_cr"] > 0)
    check("ES exceeds CFaR", out["expected_shortfall_cr"] > out["cfar_cr"])
    check("percent of EBITDA computed", out.get("cfar_pct_ebitda") is not None)
    check("statement mentions crore", "crore" in out["statement"])

    hedged = cfar.simulate_company(weights, vols, R, 10000, 2000,
                                   hedge_ratio=0.5, paths=8000)
    check("hedging halves the exposure",
          abs(hedged["cfar_cr"] - out["cfar_cr"] / 2) / out["cfar_cr"] < 0.05,
          f"{hedged['cfar_cr']} vs {out['cfar_cr']}")

    longer = cfar.simulate_company(weights, vols, R, 10000, 2000,
                                   horizon_months=24, paths=8000)
    check("longer horizon increases CFaR", longer["cfar_cr"] > out["cfar_cr"],
          f"24m {longer['cfar_cr']} > 12m {out['cfar_cr']}")

    contrib = cfar.contribution(weights, vols, R, 10000, ebitda_cr=2000, paths=4000)
    check("contribution ranks the drivers", len(contrib["drivers"]) == 2)
    check("largest weight is the top driver",
          contrib["drivers"][0]["input"] == "crude",
          contrib["drivers"][0]["input"])
    check("missing vol is refused",
          "error" in cfar.simulate_company({"x": 1.0}, vols, [[1.0]], 100))


if __name__ == "__main__":
    for t in (test_stats, test_var, test_garch, test_evt,
              test_copula, test_hedge, test_cfar):
        t()
    print("\n" + ("=" * 60))
    if FAILS:
        print(f"{len(FAILS)} FAILED: {', '.join(FAILS)}")
        raise SystemExit(1)
    print("All engine tests passed.")
