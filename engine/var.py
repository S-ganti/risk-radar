"""
Value-at-Risk and Expected Shortfall on real return series, plus the coverage
tests that say whether the numbers held up out of sample.

Sign convention: VaR and ES are reported as POSITIVE losses in return units
(0.031 = a 3.1% loss). A 99% VaR is the loss exceeded on 1% of periods.

Three estimators are provided deliberately. Historical simulation makes no
distributional assumption and is the number a treasury team can reconcile
against their own; parametric is the closed-form cross-check; Monte Carlo lets
the shape assumption be varied. When they disagree materially, that disagreement
is information about the tail, and callers should surface it rather than pick one.
"""
import math
import random

from . import stats


def historical(returns, alpha=0.99, horizon=1):
    """Historical-simulation VaR/ES at `alpha` over `horizon` periods."""
    r = stats.aggregate_overlapping(list(returns), horizon)
    if len(r) < 100:
        return None
    q = stats.quantile(r, 1 - alpha)          # left tail of the return distribution
    tail = [x for x in r if x <= q]
    if not tail:
        return None
    eff = len(r) / horizon                    # overlapping windows reuse data
    return {
        "method": "historical-simulation",
        "alpha": alpha, "horizon": horizon,
        "var": round(-q, 6),
        "es": round(-stats.mean(tail), 6),
        "n": len(r), "n_effective": round(eff, 1),
        "n_tail": len(tail),
        "overlapping": horizon > 1,
    }


def parametric(returns, alpha=0.99, horizon=1, sigma=None):
    """Normal-parametric VaR/ES. `sigma` overrides the sample estimate (pass an
    EWMA or GARCH forecast to make this conditional rather than unconditional)."""
    r = list(returns)
    if len(r) < 30:
        return None
    mu = stats.mean(r) * horizon
    sd = (sigma if sigma is not None else stats.stdev(r)) * math.sqrt(horizon)
    if sd <= 0:
        return None
    zq = stats.z(1 - alpha)
    var = -(mu + sd * zq)
    es = -(mu - sd * stats.phi(zq) / (1 - alpha))
    return {
        "method": "parametric-normal",
        "alpha": alpha, "horizon": horizon,
        "var": round(var, 6), "es": round(es, 6),
        "mu": round(mu, 6), "sigma": round(sd, 6),
        "sigma_source": "supplied" if sigma is not None else "sample",
        "n": len(r),
    }


def monte_carlo(returns, alpha=0.99, horizon=1, sigma=None, df=5,
                paths=20000, seed=12345):
    """Student-t Monte Carlo VaR/ES, moment-matched to the target volatility.

    df defaults to 5; pass df=None to fit it from the sample excess kurtosis.
    """
    r = list(returns)
    if len(r) < 30:
        return None
    mu = stats.mean(r)
    sd = sigma if sigma is not None else stats.stdev(r)
    if sd <= 0:
        return None
    if df is None:
        k = stats.excess_kurtosis(r)
        df = 4 + 6 / k if k > 0.2 else 30.0
    df = min(max(float(df), 4.5), 30.0)
    scale = math.sqrt((df - 2) / df)          # standardise t to unit variance
    rng = random.Random(seed)
    sims = []
    for _ in range(paths):
        acc = 0.0
        for _h in range(horizon):
            # t = Z / sqrt(W/df), W ~ chi2(df) via a gamma variate
            w = rng.gammavariate(df / 2.0, 2.0)
            t = rng.gauss(0.0, 1.0) / math.sqrt(w / df)
            acc += mu + sd * scale * t
        sims.append(acc)
    q = stats.quantile(sims, 1 - alpha)
    tail = [x for x in sims if x <= q]
    return {
        "method": "monte-carlo-t",
        "alpha": alpha, "horizon": horizon, "df": round(df, 1),
        "var": round(-q, 6),
        "es": round(-stats.mean(tail), 6) if tail else None,
        "paths": paths, "seed": seed,
        "sigma_source": "supplied" if sigma is not None else "sample",
    }


def cross_check(returns, alpha=0.99, horizon=1, sigma=None):
    """Run all three estimators and report their spread. A wide spread means the
    tail shape matters and the parametric number should not be quoted alone."""
    h = historical(returns, alpha, horizon)
    p = parametric(returns, alpha, horizon, sigma)
    m = monte_carlo(returns, alpha, horizon, sigma, df=None)
    got = [x["var"] for x in (h, p, m) if x and x.get("var") is not None]
    out = {"historical": h, "parametric": p, "monte_carlo": m}
    if len(got) >= 2:
        lo, hi = min(got), max(got)
        out["spread"] = {
            "min": round(lo, 6), "max": round(hi, 6),
            "ratio": round(hi / lo, 3) if lo > 0 else None,
            "note": ("estimators agree within 15%" if lo > 0 and hi / lo <= 1.15 else
                     "estimators disagree materially — tail shape is doing the work; "
                     "quote the historical number and show the range"),
        }
    return out


# ------------------------------------------------------------------ backtests --
def exceptions(returns, var_level):
    """Boolean exception sequence: True where the realised loss exceeded VaR."""
    return [(-r) > var_level for r in returns]


def kupiec_pof(exc, alpha=0.99):
    """Unconditional-coverage LR test (Kupiec 1995). H0: exception rate = 1-alpha."""
    n = len(exc)
    x = sum(1 for e in exc if e)
    if n < 30:
        return None
    p = 1 - alpha
    pi = x / n
    if x == 0:
        lr = -2 * (n * math.log(1 - p))
    elif pi >= 1:
        lr = -2 * (n * math.log(p))
    else:
        lr = -2 * ((n - x) * math.log(1 - p) + x * math.log(p)
                   - (n - x) * math.log(1 - pi) - x * math.log(pi))
    pv = stats.chi2_sf(lr, 1)
    return {"test": "kupiec-pof", "n": n, "exceptions": x,
            "rate": round(pi, 4), "expected_rate": round(p, 4),
            "lr": round(lr, 3), "p_value": round(pv, 4),
            "reject_5pct": pv < 0.05}


def christoffersen_independence(exc):
    """Independence LR test. H0: exceptions are not clustered."""
    n = len(exc)
    if n < 30:
        return None
    n00 = n01 = n10 = n11 = 0
    for a, b in zip(exc[:-1], exc[1:]):
        if not a and not b:
            n00 += 1
        elif not a and b:
            n01 += 1
        elif a and not b:
            n10 += 1
        else:
            n11 += 1
    if (n00 + n01) == 0 or (n10 + n11) == 0 or (n01 + n11) == 0:
        return {"test": "christoffersen-independence", "n": n,
                "lr": None, "p_value": None, "reject_5pct": False,
                "note": "too few exceptions or transitions to evaluate independence"}
    pi01 = n01 / (n00 + n01)
    pi11 = n11 / (n10 + n11)
    pi = (n01 + n11) / n

    def _ll(p, k, m):
        if p <= 0 or p >= 1:
            return 0.0
        return k * math.log(p) + m * math.log(1 - p)

    lr = -2 * (_ll(pi, n01 + n11, n00 + n10)
               - (_ll(pi01, n01, n00) + _ll(pi11, n11, n10)))
    pv = stats.chi2_sf(max(lr, 0.0), 1)
    return {"test": "christoffersen-independence", "n": n,
            "n00": n00, "n01": n01, "n10": n10, "n11": n11,
            "lr": round(max(lr, 0.0), 3), "p_value": round(pv, 4),
            "reject_5pct": pv < 0.05}


def backtest(returns, alpha=0.99, window=250, horizon=1):
    """Rolling out-of-sample VaR backtest: fit on a trailing window, test on the
    next observation, then report Kupiec, Christoffersen and their joint test.

    This is the honest measure of whether the VaR number works. It needs
    `window` + 30 observations before it will return anything.
    """
    r = list(returns)
    if len(r) < window + 30:
        return {"error": f"need >= {window + 30} observations, have {len(r)}"}
    # A historical-simulation quantile is only as good as the number of tail
    # points supporting it. At 99% on a 250-day window the estimate rests on
    # 2-3 observations and reliably over-exceeds; the rule of thumb is at least
    # ~10 expected observations beyond the quantile inside the estimation window.
    expected_tail_obs = window * (1 - alpha)
    thin = expected_tail_obs < 10
    exc, used = [], 0
    for i in range(window, len(r)):
        hist = r[i - window:i]
        q = stats.quantile(hist, 1 - alpha)
        if q is None:
            continue
        exc.append((-r[i]) > -q)
        used += 1
    pof = kupiec_pof(exc, alpha)
    ind = christoffersen_independence(exc)
    out = {"alpha": alpha, "window": window, "horizon": horizon,
           "tested": used, "exceptions": sum(1 for e in exc if e),
           "kupiec": pof, "christoffersen": ind}
    if pof and ind and ind.get("lr") is not None:
        lr_cc = pof["lr"] + ind["lr"]
        pv = stats.chi2_sf(lr_cc, 2)
        out["conditional_coverage"] = {"test": "christoffersen-cc",
                                       "lr": round(lr_cc, 3),
                                       "p_value": round(pv, 4),
                                       "reject_5pct": pv < 0.05}
    out["estimation_window_tail_obs"] = round(expected_tail_obs, 1)
    if thin:
        out["warning"] = (
            f"The {alpha:.0%} quantile is estimated from about "
            f"{expected_tail_obs:.0f} observations in a {window}-period window. "
            f"That is too thin to be stable: historical simulation under-states "
            f"the loss here and will over-exceed. Use at least "
            f"{int(math.ceil(10 / (1 - alpha)))} periods for this confidence "
            f"level, or read the {alpha:.0%} number off a fitted tail (see evt.py) "
            f"rather than the empirical quantile.")
    if pof:
        if pof["reject_5pct"] and thin:
            out["verdict"] = ("rejected at 5%, but the estimation window is too "
                              "thin to support this confidence level — fix the "
                              "window before concluding the model is wrong")
        elif pof["reject_5pct"]:
            out["verdict"] = ("model rejected at 5% — exception rate is inconsistent "
                              "with the stated confidence level")
        else:
            out["verdict"] = "coverage consistent with the stated confidence level"
    return out
