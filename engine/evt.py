"""
Extreme value theory — peaks-over-threshold with a Generalised Pareto tail.

The previous implementation fitted a GPD to the Monte Carlo simulator's own
draws, which recovers the simulator's assumptions rather than the market's tails.
It was removed rather than caveated. This is the honest replacement: the fit runs
on the observed loss tail of a real return series.

Estimation uses probability-weighted moments as the primary method — it is far
more stable than method-of-moments in small samples, which matters because a
tail by definition has few observations — with method-of-moments reported
alongside as a stability check. A mean-excess diagnostic is returned so the
threshold choice can be inspected rather than trusted.
"""
import math

from . import stats

MIN_EXCEEDANCES = 30


def _pwm(exc):
    """Probability-weighted-moment estimator (Hosking & Wallis)."""
    x = sorted(exc)
    n = len(x)
    a0 = sum(x) / n
    a1 = sum((1.0 - (i + 1 - 0.35) / n) * xi for i, xi in enumerate(x)) / n
    den = a0 - 2 * a1
    if abs(den) < 1e-12:
        return None
    xi = 2.0 - a0 / den
    sigma = 2.0 * a0 * a1 / den
    if sigma <= 0:
        return None
    return xi, sigma


def _mom(exc):
    """Method of moments."""
    m = stats.mean(exc)
    v = stats.stdev(exc, ddof=0) ** 2
    if v <= 0:
        return None
    xi = 0.5 * (1 - m * m / v)
    sigma = 0.5 * m * (m * m / v + 1)
    if sigma <= 0:
        return None
    return xi, sigma


def mean_excess(losses, points=12):
    """Mean-excess function. A GPD tail is linear in the threshold above the
    point where the approximation starts to hold, so this is how the threshold
    is justified rather than assumed."""
    s = sorted(losses)
    n = len(s)
    if n < 50:
        return []
    out = []
    for p in [0.70 + 0.025 * i for i in range(points)]:
        u = stats.quantile(s, p)
        ex = [x - u for x in s if x > u]
        if len(ex) >= 10:
            out.append({"threshold_q": round(p, 3), "u": round(u, 6),
                        "n_exceed": len(ex), "mean_excess": round(stats.mean(ex), 6)})
    return out


def fit_pot(returns, threshold_q=0.90, side="loss"):
    """Fit a GPD to exceedances over a high quantile of the loss distribution.

    `side="loss"` models the left tail of returns (losses as positive numbers),
    which is the tail a risk function cares about.
    """
    r = [float(x) for x in returns]
    if len(r) < 250:
        return {"error": f"need >= 250 observations for a tail fit, have {len(r)}"}
    losses = [-x for x in r] if side == "loss" else list(r)
    u = stats.quantile(losses, threshold_q)
    exc = [x - u for x in losses if x > u]
    if len(exc) < MIN_EXCEEDANCES:
        return {"error": f"only {len(exc)} exceedances above the {threshold_q:.0%} "
                         f"threshold; need >= {MIN_EXCEEDANCES}. Lower the threshold "
                         f"or gather more history."}
    pwm, mom = _pwm(exc), _mom(exc)
    if not pwm:
        return {"error": "PWM estimator degenerate on this sample"}
    xi, sigma = pwm
    n, nu = len(losses), len(exc)
    out = {
        "model": "GPD peaks-over-threshold",
        "side": side,
        "threshold_q": threshold_q,
        "u": round(u, 6),
        "n": n, "n_exceedances": nu,
        "exceedance_rate": round(nu / n, 4),
        "xi": round(xi, 4), "sigma": round(sigma, 6),
        "estimator": "probability-weighted moments",
        "xi_mom": round(mom[0], 4) if mom else None,
        "sigma_mom": round(mom[1], 6) if mom else None,
        "mean_excess": mean_excess(losses),
    }
    out["tail_shape"] = (
        "heavy-tailed (xi > 0): losses beyond the threshold decay as a power law, "
        "so the worst case is materially worse than a normal model implies" if xi > 0.05
        else "short-tailed (xi < 0): the loss distribution has a finite upper bound"
        if xi < -0.05 else "near-exponential (xi ~ 0)")
    if mom and abs(mom[0] - xi) > 0.25:
        out["warning"] = ("PWM and method-of-moments disagree on the shape parameter "
                          "(%.2f vs %.2f) — the tail estimate is not stable at this "
                          "sample size; treat quantiles beyond the data with caution."
                          % (xi, mom[0]))
    if xi >= 0.5:
        out.setdefault("warning", "")
        out["warning"] += (" xi >= 0.5 implies infinite variance; the ES figure is "
                           "not reliable at this shape.")
    return out


def tail_quantile(fit, p):
    """VaR at confidence p from a fitted GPD tail (p above the threshold)."""
    if not fit or "error" in fit:
        return None
    xi, sigma, u = fit["xi"], fit["sigma"], fit["u"]
    zeta = fit["n_exceedances"] / fit["n"]
    if p <= 1 - zeta:
        return None                      # below the threshold: use the empirical CDF
    if abs(xi) < 1e-8:
        return u + sigma * math.log(zeta / (1 - p))
    return u + (sigma / xi) * (((1 - p) / zeta) ** (-xi) - 1)


def tail_es(fit, p):
    """Expected shortfall beyond the GPD quantile at confidence p."""
    if not fit or "error" in fit:
        return None
    xi = fit["xi"]
    if xi >= 1:
        return None                      # mean does not exist
    q = tail_quantile(fit, p)
    if q is None:
        return None
    return (q + fit["sigma"] - xi * fit["u"]) / (1 - xi)


def tail_table(fit, levels=(0.95, 0.99, 0.995, 0.999)):
    """VaR and ES across confidence levels, with the empirical value alongside
    where the sample can support it."""
    if not fit or "error" in fit:
        return []
    rows = []
    for p in levels:
        q, e = tail_quantile(fit, p), tail_es(fit, p)
        rows.append({
            "confidence": p,
            "var": round(q, 6) if q is not None else None,
            "es": round(e, 6) if e is not None else None,
            "extrapolated": p > 1 - 1.0 / fit["n"],
        })
    return rows
