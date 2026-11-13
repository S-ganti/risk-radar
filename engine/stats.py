"""Return series, volatility estimators and descriptive statistics."""
import math
from statistics import NormalDist

_N = NormalDist()


def log_returns(closes):
    """[(date, price)] ascending -> [(date, log return)]."""
    out = []
    for i in range(1, len(closes)):
        p0, p1 = closes[i - 1][1], closes[i][1]
        if p0 > 0 and p1 > 0:
            out.append((closes[i][0], math.log(p1 / p0)))
    return out


def values(pairs):
    return [v for _d, v in pairs]


def monthly_closes(closes):
    out = {}
    for d, c in closes:            # ascending; last close of the month wins
        out[d[:7]] = c
    return sorted(out.items())


def monthly_log_returns(closes):
    m = monthly_closes(closes)
    return [(m[i][0], math.log(m[i][1] / m[i - 1][1]))
            for i in range(1, len(m)) if m[i - 1][1] > 0 and m[i][1] > 0]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs, ddof=1):
    n = len(xs)
    if n <= ddof:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - ddof))


def skewness(xs):
    n, s = len(xs), stdev(xs)
    if n < 3 or s == 0:
        return 0.0
    m = mean(xs)
    return (n / ((n - 1) * (n - 2))) * sum(((x - m) / s) ** 3 for x in xs)


def excess_kurtosis(xs):
    """Fisher (excess) kurtosis, bias-corrected."""
    n, s = len(xs), stdev(xs)
    if n < 4 or s == 0:
        return 0.0
    m = mean(xs)
    g2 = sum(((x - m) / s) ** 4 for x in xs) * n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
    return g2 - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))


def quantile(xs, p):
    """Linear-interpolated empirical quantile; p in [0,1]. Input need not be sorted."""
    if not xs:
        return None
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    h = (len(s) - 1) * min(max(p, 0.0), 1.0)
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def percentile_rank(series, value):
    if not series:
        return None
    return round(100.0 * sum(1 for s in series if s <= value) / len(series), 1)


def ewma_vol_series(returns, lam=0.94, seed=30):
    """RiskMetrics EWMA sigma_t, per-period units. Returns [] if too short."""
    if len(returns) < seed + 5:
        return []
    v = sum(r * r for r in returns[:seed]) / seed
    out = [math.sqrt(v)]
    for r in returns[seed:]:
        v = lam * v + (1 - lam) * r * r
        out.append(math.sqrt(v))
    return out


def rolling_std_series(returns, window=36):
    if len(returns) < window + 3:
        return []
    out = []
    for i in range(window, len(returns) + 1):
        w = returns[i - window:i]
        m = sum(w) / window
        out.append(math.sqrt(sum((r - m) ** 2 for r in w) / (window - 1)))
    return out


def pearson(xs, ys):
    n = min(len(xs), len(ys))
    if n < 3:
        return 0.0
    xs, ys = xs[:n], ys[:n]
    mx, my = mean(xs), mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs)
    dy = sum((b - my) ** 2 for b in ys)
    return num / math.sqrt(dx * dy) if dx > 0 and dy > 0 else 0.0


def aggregate_overlapping(returns, h):
    """Rolling h-period sums of log returns — the standard basis for multi-day
    historical simulation. Overlapping windows reuse data, so the effective
    sample is smaller than the count suggests; callers should say so."""
    if h <= 1:
        return list(returns)
    if len(returns) < h:
        return []
    run = sum(returns[:h])
    out = [run]
    for i in range(h, len(returns)):
        run += returns[i] - returns[i - h]
        out.append(run)
    return out


def z(p):
    """Standard-normal inverse CDF."""
    return _N.inv_cdf(p)


def phi(x):
    """Standard-normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def Phi(x):
    """Standard-normal CDF."""
    return _N.cdf(x)


def chi2_sf(x, df):
    """Upper-tail probability of a chi-square variate. Exact for df 1 and 2,
    which is all the coverage tests below need."""
    if x <= 0:
        return 1.0
    if df == 1:
        return 2 * (1 - Phi(math.sqrt(x)))
    if df == 2:
        return math.exp(-x / 2)
    # Wilson-Hilferty normal approximation for other dof.
    t = ((x / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    return 1 - Phi(t)
