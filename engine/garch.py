"""
GARCH(1,1) by maximum likelihood — pure Python, Nelder-Mead simplex.

This replaces the volatility *rating* that used to feed the Monte Carlo model.
EWMA (RiskMetrics) is the special case omega=0, alpha=1-lambda, beta=lambda with
no mean reversion; fitting the three parameters instead lets volatility revert to
a long-run level, which is what makes a multi-day forecast behave sensibly.

Parameters are optimised in an unconstrained space and mapped back through a
logistic transform, so stationarity (alpha + beta < 1) and positivity hold by
construction rather than by hoping the optimiser respects a boundary.
"""
import math

from . import stats


def _sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def _unpack(theta, var0):
    """R^3 -> (omega, alpha, beta) with omega>0 and alpha+beta<1 enforced."""
    persistence = _sigmoid(theta[0]) * 0.9995          # alpha + beta
    share = _sigmoid(theta[1])                          # alpha's share of it
    alpha = persistence * share
    beta = persistence - alpha
    omega = math.exp(theta[2]) * var0 * (1 - persistence)
    return omega, alpha, beta


def _neg_loglik(theta, r, var0):
    omega, alpha, beta = _unpack(theta, var0)
    if omega <= 0:
        return 1e12
    h = var0
    ll = 0.0
    for x in r:
        if h <= 1e-14:
            return 1e12
        ll += math.log(h) + x * x / h
        h = omega + alpha * x * x + beta * h
    return 0.5 * ll


def _nelder_mead(f, x0, iters=600, tol=1e-9):
    n = len(x0)
    pts = [list(x0)]
    for i in range(n):
        p = list(x0)
        p[i] += 0.5 if p[i] == 0 else 0.5 * abs(p[i])
        pts.append(p)
    vals = [f(p) for p in pts]
    for _ in range(iters):
        order = sorted(range(len(pts)), key=lambda i: vals[i])
        pts = [pts[i] for i in order]
        vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol:
            break
        centroid = [sum(p[i] for p in pts[:-1]) / n for i in range(n)]
        worst = pts[-1]
        refl = [centroid[i] + 1.0 * (centroid[i] - worst[i]) for i in range(n)]
        fr = f(refl)
        if vals[0] <= fr < vals[-2]:
            pts[-1], vals[-1] = refl, fr
            continue
        if fr < vals[0]:
            exp_ = [centroid[i] + 2.0 * (centroid[i] - worst[i]) for i in range(n)]
            fe = f(exp_)
            pts[-1], vals[-1] = (exp_, fe) if fe < fr else (refl, fr)
            continue
        con = [centroid[i] + 0.5 * (worst[i] - centroid[i]) for i in range(n)]
        fc = f(con)
        if fc < vals[-1]:
            pts[-1], vals[-1] = con, fc
            continue
        best = pts[0]
        for i in range(1, len(pts)):
            pts[i] = [best[j] + 0.5 * (pts[i][j] - best[j]) for j in range(n)]
            vals[i] = f(pts[i])
    i = min(range(len(pts)), key=lambda k: vals[k])
    return pts[i], vals[i]


def fit(returns, demean=True):
    """Fit GARCH(1,1) with normal innovations. Returns None if the sample is too
    short to identify three parameters (fewer than ~250 observations)."""
    r = [float(x) for x in returns]
    if len(r) < 250:
        return None
    mu = stats.mean(r) if demean else 0.0
    r = [x - mu for x in r]
    var0 = stats.stdev(r) ** 2
    if var0 <= 0:
        return None

    best, bestv = None, float("inf")
    for start in ([2.5, -1.5, 0.0], [3.5, -2.5, 0.5], [1.5, -0.5, -0.5]):
        th, v = _nelder_mead(lambda t: _neg_loglik(t, r, var0), start)
        if v < bestv:
            best, bestv = th, v
    omega, alpha, beta = _unpack(best, var0)
    persistence = alpha + beta
    uncond = omega / (1 - persistence) if persistence < 1 else None

    # conditional variance path and the one-step-ahead forecast
    h = var0
    for x in r:
        h = omega + alpha * x * x + beta * h
    k = 3
    n = len(r)
    return {
        "model": "GARCH(1,1)-normal",
        "omega": omega, "alpha": round(alpha, 6), "beta": round(beta, 6),
        "persistence": round(persistence, 6),
        "mu": round(mu, 8),
        "half_life_periods": (round(math.log(0.5) / math.log(persistence), 1)
                              if 0 < persistence < 1 else None),
        "sigma_uncond": round(math.sqrt(uncond), 6) if uncond else None,
        "sigma_next": round(math.sqrt(h), 6),
        "loglik": round(-bestv, 3),
        "aic": round(2 * k + 2 * bestv, 3),
        "bic": round(k * math.log(n) + 2 * bestv, 3),
        "n": n,
        "converged": bestv < 1e11,
        "note": ("Stationary; volatility mean-reverts to sigma_uncond."
                 if persistence < 0.999 else
                 "Persistence at the boundary — behaves like EWMA with no mean reversion."),
    }


def forecast(fit_result, horizon=21):
    """Multi-period volatility forecast. Aggregates the variance path, so it
    reverts toward the unconditional level instead of scaling by sqrt(h)."""
    if not fit_result:
        return None
    omega = fit_result["omega"]
    a, b = fit_result["alpha"], fit_result["beta"]
    h = fit_result["sigma_next"] ** 2
    total = 0.0
    for _ in range(horizon):
        total += h
        h = omega + (a + b) * h
    return {"horizon": horizon,
            "sigma": round(math.sqrt(total), 6),
            "sigma_per_period": round(math.sqrt(total / horizon), 6),
            "method": "GARCH(1,1) variance-path aggregation"}
