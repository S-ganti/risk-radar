"""
Dependence modelling: correlation matrices, Gaussian and Student-t copulas.

Why the t copula matters here rather than as a technical flourish: a Gaussian
copula has zero tail dependence, so it says that in the limit commodity shocks
become independent exactly when they stop being independent in practice. India's
import basket is the case in point — a rupee slide and a crude spike arrive
together, and that is precisely the joint move a Gaussian dependence structure
assigns a vanishing probability.

The degrees of freedom are estimated from the data (excess kurtosis of pooled
standardised returns) rather than assumed, and the empirical tail dependence is
reported next to the Gaussian-implied zero so the gap is visible.
"""
import math
import random

from . import stats


def align(series_map):
    """{id: [(date, return)]} -> (ids, rows) over dates common to every series."""
    ids = sorted(series_map)
    if not ids:
        return [], []
    common = None
    maps = {}
    for i in ids:
        m = dict(series_map[i])
        maps[i] = m
        common = set(m) if common is None else (common & set(m))
    dates = sorted(common or [])
    rows = [[maps[i][d] for i in ids] for d in dates]
    return ids, rows


def corr_matrix(series_map, min_obs=24):
    """Pairwise Pearson correlation on overlapping observations."""
    ids = sorted(series_map)
    maps = {i: dict(series_map[i]) for i in ids}
    n = len(ids)
    R = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    pairs, used = {}, 0
    for a in range(n):
        for b in range(a + 1, n):
            ia, ib = ids[a], ids[b]
            common = sorted(set(maps[ia]) & set(maps[ib]))[-60:]
            if len(common) >= min_obs:
                r = stats.pearson([maps[ia][d] for d in common],
                                  [maps[ib][d] for d in common])
                used += 1
            else:
                r = 0.0
            R[a][b] = R[b][a] = r
            pairs[f"{ia}|{ib}"] = round(r, 4)
    return {"ids": ids, "matrix": R, "pairs": pairs,
            "measured_pairs": used, "total_pairs": n * (n - 1) // 2}


def _jacobi_eigen(A, iters=100):
    """Eigen-decomposition of a symmetric matrix by cyclic Jacobi rotation."""
    n = len(A)
    a = [row[:] for row in A]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(iters):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < 1e-12:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-15:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [a[i][i] for i in range(n)], v


def nearest_psd(R, eps=1e-8):
    """Clip negative eigenvalues and renormalise to a correlation matrix.

    Pairwise-estimated matrices are routinely not positive semi-definite because
    each entry uses a different overlapping sample. Without this repair the
    Cholesky step fails and the joint simulation silently falls back to
    something weaker.
    """
    n = len(R)
    vals, vecs = _jacobi_eigen(R)
    floor = max(eps, 1e-6 * max(vals) if max(vals) > 0 else eps)
    if min(vals) >= floor:
        return R, False
    vals = [max(v, floor) for v in vals]
    B = [[sum(vecs[i][k] * vals[k] * vecs[j][k] for k in range(n))
          for j in range(n)] for i in range(n)]
    # Rescale to unit diagonal in one pass. Capture the diagonal FIRST: dividing
    # rows and then columns against a diagonal that the row pass has already
    # changed destroys the positive-definiteness the clipping just restored.
    d = [math.sqrt(B[i][i]) if B[i][i] > 0 else 1.0 for i in range(n)]
    B = [[B[i][j] / (d[i] * d[j]) for j in range(n)] for i in range(n)]
    for i in range(n):
        B[i][i] = 1.0
    return B, True


def cholesky(A):
    n = len(A)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = A[i][j] - sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                if s <= 1e-12:
                    return None
                L[i][j] = math.sqrt(s)
            else:
                L[i][j] = s / L[j][j]
    return L


def empirical_tail_dependence(x, y, q=0.95):
    """Lower-tail dependence: P(Y in its worst 1-q | X in its worst 1-q).

    A Gaussian copula implies this goes to zero as q rises. If the data says
    otherwise, a Gaussian joint stress is understating exactly the scenario the
    risk function exists to size.
    """
    n = min(len(x), len(y))
    if n < 100:
        return None
    qx, qy = stats.quantile(x, 1 - q), stats.quantile(y, 1 - q)
    nx = sum(1 for a in x if a <= qx)
    both = sum(1 for a, b in zip(x, y) if a <= qx and b <= qy)
    return round(both / nx, 4) if nx else None


def estimate_df(series_map, lo=4.5, hi=30.0):
    """Degrees of freedom from the pooled excess kurtosis of standardised
    returns: for a t distribution, excess kurtosis = 6/(df-4)."""
    pooled = []
    for _i, ser in series_map.items():
        v = [r for _d, r in ser]
        s = stats.stdev(v)
        if s > 0:
            m = stats.mean(v)
            pooled.extend((x - m) / s for x in v)
    if len(pooled) < 200:
        return {"df": 8.0, "method": "default (insufficient sample)", "excess_kurtosis": None}
    k = stats.excess_kurtosis(pooled)
    df = 4 + 6 / k if k > 0.2 else hi
    return {"df": round(min(max(df, lo), hi), 2),
            "method": "moment matching on pooled excess kurtosis",
            "excess_kurtosis": round(k, 3), "n_pooled": len(pooled)}


def simulate(R, vols, paths=20000, df=None, seed=4242):
    """Draw correlated shocks. df=None gives a Gaussian copula; a finite df gives
    a Student-t copula standardised to unit variance so the two are comparable.

    Returns a list of shock vectors in the same units as `vols`.
    """
    n = len(vols)
    Rp, repaired = nearest_psd(R)
    L = cholesky(Rp)
    if L is None:
        return None, {"error": "correlation matrix is not positive definite even "
                               "after repair"}
    rng = random.Random(seed)
    scale = math.sqrt((df - 2) / df) if df else 1.0
    out = []
    for _ in range(paths):
        zs = [rng.gauss(0.0, 1.0) for _ in range(n)]
        cz = [sum(L[i][k] * zs[k] for k in range(i + 1)) for i in range(n)]
        if df:
            w = rng.gammavariate(df / 2.0, 2.0)
            m = math.sqrt(w / df)
            cz = [c / m * scale for c in cz]
        out.append([cz[i] * vols[i] for i in range(n)])
    return out, {"paths": paths, "df": df, "psd_repaired": repaired,
                 "copula": "student-t" if df else "gaussian"}
