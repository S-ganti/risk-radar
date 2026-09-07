"""
Hedge effectiveness testing under Ind AS 109.

This is the most sellable calculation in the tool, for a reason worth stating
plainly: it is a *standard*, so the answer is objectively right or wrong, and it
is the test the client's own auditor will run. Nothing here is a Risk Radar
opinion.

Two methods:
  - dollar offset, cumulative and period-by-period, against the 80-125% band
  - regression of hedge changes on exposure changes: slope in [-1.25, -0.80],
    R^2 >= 0.80, and a slope significantly different from zero

Ind AS 109 replaced the bright-line 80-125% quantitative test with a principles
based assessment (economic relationship, credit risk not dominating, consistent
hedge ratio). The band is retained here because it remains the working
benchmark most Indian treasury teams and their auditors still apply, and because
it is what the counterparty bank will ask about. Both framings are reported.
"""
import math

from . import stats


def _diffs(xs):
    return [xs[i] - xs[i - 1] for i in range(1, len(xs))]


def dollar_offset(exposure, hedge, cumulative=True):
    """Dollar-offset ratio = -sum(change in hedge) / sum(change in exposure).

    An effective hedge moves opposite to the exposure, so the ratio is reported
    as a positive percentage.
    """
    if len(exposure) != len(hedge) or len(exposure) < 3:
        return {"error": "need equal-length series with at least 3 observations"}
    de, dh = _diffs(exposure), _diffs(hedge)
    rows = []
    for i, (e, h) in enumerate(zip(de, dh)):
        ratio = (-h / e * 100.0) if abs(e) > 1e-12 else None
        rows.append({"period": i + 1, "d_exposure": round(e, 4), "d_hedge": round(h, 4),
                     "ratio_pct": round(ratio, 2) if ratio is not None else None,
                     "in_band": (ratio is not None and 80.0 <= ratio <= 125.0)})
    se, sh = sum(de), sum(dh)
    cum = (-sh / se * 100.0) if abs(se) > 1e-12 else None
    scored = [r for r in rows if r["ratio_pct"] is not None]
    return {
        "method": "dollar-offset",
        "cumulative_ratio_pct": round(cum, 2) if cum is not None else None,
        "cumulative_in_band": (cum is not None and 80.0 <= cum <= 125.0),
        "periods": rows if not cumulative else rows,
        "periods_in_band": sum(1 for r in scored if r["in_band"]),
        "periods_scored": len(scored),
        "band": [80.0, 125.0],
    }


def regression(exposure, hedge):
    """Regress changes in hedge value on changes in exposure value.

    Effective when slope is near -1 (in [-1.25, -0.80]) and R^2 >= 0.80.
    """
    if len(exposure) != len(hedge) or len(exposure) < 4:
        return {"error": "need equal-length series with at least 4 observations"}
    x, y = _diffs(exposure), _diffs(hedge)
    n = len(x)
    mx, my = stats.mean(x), stats.mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    if sxx <= 0:
        return {"error": "exposure series does not vary — regression undefined"}
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    slope = sxy / sxx
    intercept = my - slope * mx
    resid = [b - (intercept + slope * a) for a, b in zip(x, y)]
    sse = sum(r * r for r in resid)
    sst = sum((b - my) ** 2 for b in y)
    r2 = 1 - sse / sst if sst > 0 else 0.0
    se_slope = math.sqrt(sse / (n - 2) / sxx) if n > 2 and sxx > 0 else None
    t = slope / se_slope if se_slope and se_slope > 0 else None
    slope_ok = -1.25 <= slope <= -0.80
    r2_ok = r2 >= 0.80
    return {
        "method": "regression",
        "slope": round(slope, 4), "intercept": round(intercept, 6),
        "r_squared": round(r2, 4),
        "std_error_slope": round(se_slope, 5) if se_slope else None,
        "t_statistic": round(t, 3) if t else None,
        "n": n,
        "slope_in_band": slope_ok, "r2_pass": r2_ok,
        "effective": slope_ok and r2_ok,
        "criteria": {"slope_band": [-1.25, -0.80], "min_r_squared": 0.80},
    }


def assess(exposure, hedge, hedge_ratio=None):
    """Full Ind AS 109 assessment: both methods plus a plain verdict.

    `exposure` and `hedge` are fair values (or cash flows) of the hedged item and
    the hedging instrument at each observation date, in the same currency.
    """
    do = dollar_offset(exposure, hedge)
    rg = regression(exposure, hedge)
    if "error" in do:
        return {"error": do["error"]}
    out = {"dollar_offset": do, "regression": rg,
           "hedge_ratio_designated": hedge_ratio}

    do_ok = bool(do.get("cumulative_in_band"))
    rg_ok = bool(rg.get("effective")) if "error" not in rg else None
    passes = [v for v in (do_ok, rg_ok) if v is not None]

    if all(passes) and passes:
        verdict, detail = "effective", "Both methods sit inside the working benchmarks."
    elif not any(passes):
        verdict, detail = "ineffective", "Neither method meets the working benchmarks."
    else:
        verdict, detail = ("mixed",
                           "The methods disagree — this is usually basis risk between the "
                           "hedged item and the instrument. Document which method is "
                           "designated in the hedge documentation and why.")
    out["verdict"] = verdict
    out["detail"] = detail

    notes = [
        "Ind AS 109 replaced the bright-line 80-125% test with a principles-based "
        "assessment: an economic relationship must exist, credit risk must not "
        "dominate the value changes, and the hedge ratio must match what the entity "
        "actually uses. The band is reported because it remains the practical "
        "benchmark auditors and counterparty banks apply.",
        "Effectiveness is assessed prospectively. A passing historical test is "
        "evidence for the economic relationship, not a substitute for it.",
    ]
    if rg.get("r_squared") is not None and rg["r_squared"] < 0.80:
        notes.append("Low R-squared with an acceptable dollar-offset ratio is the "
                     "classic proxy-hedge signature: the instrument tracks the "
                     "exposure on average but not period by period. Quantify the "
                     "basis before designating.")
    out["notes"] = notes
    return out


def basis_risk(series_a, series_b, label_a="exposure", label_b="instrument"):
    """Quantify the basis between what a client is exposed to and what they can
    actually trade — MCX crude settling against WTI while the import basket is
    Dubai-linked, Newcastle 6,000 kcal coal against Indonesian 4,200 kcal, and so
    on. Correlation alone hides the level drift that breaks effectiveness."""
    n = min(len(series_a), len(series_b))
    if n < 30:
        return {"error": "need at least 30 aligned observations"}
    a, b = series_a[:n], series_b[:n]
    ra = [math.log(a[i] / a[i - 1]) for i in range(1, n) if a[i - 1] > 0 and a[i] > 0]
    rb = [math.log(b[i] / b[i - 1]) for i in range(1, n) if b[i - 1] > 0 and b[i] > 0]
    m = min(len(ra), len(rb))
    ra, rb = ra[:m], rb[:m]
    rho = stats.pearson(ra, rb)
    spread = [x - y for x, y in zip(ra, rb)]
    return {
        "label_a": label_a, "label_b": label_b, "n": m,
        "correlation": round(rho, 4),
        "r_squared": round(rho * rho, 4),
        "basis_vol_per_period": round(stats.stdev(spread), 6),
        "vol_a": round(stats.stdev(ra), 6), "vol_b": round(stats.stdev(rb), 6),
        "hedge_ratio_min_variance": (round(rho * stats.stdev(ra) / stats.stdev(rb), 4)
                                     if stats.stdev(rb) > 0 else None),
        "note": ("R-squared below 0.80 means a regression-based effectiveness test "
                 "on this pair fails before any execution decision is made."
                 if rho * rho < 0.80 else
                 "Tracking is tight enough that a regression test would pass on this "
                 "sample; the residual basis still needs sizing."),
    }
