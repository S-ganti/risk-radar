"""
Cash-Flow-at-Risk: from commodity shocks to rupees of EBITDA.

This is the translation layer between the model lab and the conversation a CFO
actually has. "Aluminium vol is at the 50th percentile" is not a finding. "There
is a 5% chance this costs you more than 340 crore of FY27 EBITDA, which is 11% of
last year's" is one.

Mechanics: draw correlated shocks across the input basket (t copula by default,
so joint tail moves are not assumed away), apply each company's cost-base
weights, damp by the sector pass-through and hedge assumptions, and read the
distribution of the EBITDA hit.

The output is a model number built on estimated cost shares. It is labelled as
one everywhere it surfaces.
"""
from . import copula, stats


def simulate_company(weights, vols, R, cost_base_cr, ebitda_cr=None,
                     horizon_months=12, pass_through=0.5, hedge_ratio=0.0,
                     df=8.0, paths=20000, seed=99, alpha=0.95):
    """
    weights        {commodity_id: share of cost base}, shares in [0,1]
    vols           {commodity_id: monthly volatility}
    R              correlation matrix over sorted(weights) ids
    cost_base_cr   INR crore of annual input cost exposed
    ebitda_cr      INR crore of annual EBITDA, for the denominator
    pass_through   share of a cost rise the company CANNOT pass on (retained)
    hedge_ratio    share of the exposure already hedged
    """
    ids = sorted(weights)
    if not ids or cost_base_cr in (None, 0):
        return {"error": "need a cost base and at least one weighted input"}
    missing = [i for i in ids if i not in vols]
    if missing:
        return {"error": f"no volatility available for {', '.join(missing)}"}

    h = max(1, int(horizon_months))
    sc = h ** 0.5                                   # scale monthly vol to horizon
    v = [vols[i] * sc for i in ids]
    draws, meta = copula.simulate(R, v, paths=paths, df=df, seed=seed)
    if draws is None:
        return {"error": meta.get("error", "simulation failed")}

    w = [weights[i] for i in ids]
    retained = max(0.0, min(1.0, pass_through))
    unhedged = max(0.0, min(1.0, 1.0 - hedge_ratio))

    # Cost shock as a share of the cost base, then the EBITDA hit in crore.
    hits = []
    for shock in draws:
        basket = sum(w[i] * shock[i] for i in range(len(ids)))
        hits.append(basket * cost_base_cr * retained * unhedged)

    hits.sort()
    tail_q = stats.quantile(hits, alpha)            # right tail = worst cost outcome
    tail = [x for x in hits if x >= tail_q]
    out = {
        "confidence": alpha,
        "horizon_months": h,
        "cfar_cr": round(tail_q, 1),
        "expected_shortfall_cr": round(stats.mean(tail), 1) if tail else None,
        "median_cr": round(stats.quantile(hits, 0.5), 1),
        "best_5pct_cr": round(stats.quantile(hits, 0.05), 1),
        "cost_base_cr": cost_base_cr,
        "inputs_modelled": ids,
        "weights_sum": round(sum(w), 4),
        "assumptions": {"retained_cost_share": retained,
                        "hedge_ratio": hedge_ratio,
                        "copula": meta.get("copula"), "df": meta.get("df"),
                        "paths": meta.get("paths"),
                        "psd_repaired": meta.get("psd_repaired")},
    }
    if ebitda_cr:
        out["ebitda_cr"] = ebitda_cr
        out["cfar_pct_ebitda"] = round(tail_q / ebitda_cr * 100, 1)
        out["statement"] = (
            f"{int(round((1-alpha)*100))}% chance the input basket costs more than "
            f"Rs {round(tail_q):,} crore of EBITDA over {h} months — "
            f"{round(tail_q / ebitda_cr * 100, 1)}% of the year's EBITDA."
        ).replace(",", ",")
    else:
        out["statement"] = (
            f"{int(round((1-alpha)*100))}% chance the input basket costs more than "
            f"Rs {round(tail_q):,} crore over {h} months. No verified EBITDA "
            f"denominator on file, so this is not expressed as a share of earnings."
        )
    out["caveat"] = ("Cost-base shares are estimates from segment disclosure and "
                     "annual-report commentary, not the client's ledger. Confirming "
                     "them is the first day of the engagement, not a prerequisite "
                     "for the conversation.")
    return out


def contribution(weights, vols, R, cost_base_cr, **kw):
    """Marginal contribution of each input to CFaR, by leave-one-out.

    Answers "which input is actually driving the number" — the question that
    turns a CFaR figure into a procurement or hedging action.
    """
    base = simulate_company(weights, vols, R, cost_base_cr, **kw)
    if "error" in base:
        return base
    ids = sorted(weights)
    rows = []
    for drop in ids:
        w2 = {k: v for k, v in weights.items() if k != drop}
        if not w2:
            continue
        idx = [i for i, x in enumerate(ids) if x != drop]
        R2 = [[R[a][b] for b in idx] for a in idx]
        alt = simulate_company(w2, vols, R2, cost_base_cr, **kw)
        if "error" in alt:
            continue
        rows.append({"input": drop,
                     "weight": round(weights[drop], 4),
                     "cfar_without_cr": alt["cfar_cr"],
                     "contribution_cr": round(base["cfar_cr"] - alt["cfar_cr"], 1)})
    rows.sort(key=lambda r: -r["contribution_cr"])
    return {"cfar_cr": base["cfar_cr"], "drivers": rows,
            "note": "Leave-one-out contributions do not sum to total CFaR because "
                    "the inputs are correlated; rank them, do not add them."}
