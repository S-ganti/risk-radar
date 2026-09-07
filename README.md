# Commodity & treasury risk radar — India

Self-contained dashboard built from public official sources. Open: https://s-ganti.github.io/risk-radar/

**87 companies · 97 commodity markets across 10 families · 5 model families computed from real price history · 3 MCP servers · daily live-data pipeline.**

Current research cycle: **2026-W28** (7 Jul 2026). Market data and model output refresh daily via GitHub Actions (18:30 IST → `data/latest.json`, `data/risk.json`).

## What it answers

Most commodity tools tell you what a price did. This one is built around the question an India-focused commodity & treasury risk practice actually gets paid to answer:

> Which named client should be called this week, about which exposure, before which deadline — and **can they do anything about it?**

That last clause is the **Hedgeability Matrix**. For every commodity in the reference sheet we record whether a listed contract exists, on which venue and in which currency, and whether there is an onshore Indian contract. Crossed with each company's cost base, that splits input spend into:

| Bucket | What it means for the client |
|---|---|
| Onshore INR contract | MCX / NCDEX listed — hedge in rupees, no FX leg, lightest permission burden |
| Offshore USD/EUR only | RBI Master Direction permission plus a currency leg, itself constrained by the April 2026 NDF prohibition |
| Proxy hedge only | Correlated contract, material basis — Ind AS 109 effectiveness at 80–125% is hard to hold |
| OTC / index-linked | Formula pricing or bilateral swap; counterparty credit sits with the client |
| No hedge exists | Contractual and operational levers only |

Ranking the universe by *unhedgeable* share surfaces a different set of names than ranking by exposure size, and points at a different kind of engagement — supply-chain mapping rather than a hedge programme.

## Layout

```
index.html                     the whole dashboard, single file, no build step
engine/                        risk maths, pure stdlib — VaR/ES, GARCH, EVT,
                               copulas, Ind AS 109 effectiveness, CFaR
mcp_servers/                   three MCP servers over the same engine
data/commodities.json          commodity reference sheet (fetched same-origin)
data/latest.json               daily market data, vols, correlations, regime
data/risk.json                 computed model output — GARCH fits, GPD tails,
                               VaR/ES cross-checks with backtests, company CFaR
data/history.json              real per-run score history — accumulates in git
data/financials.json           FY26 revenue/EBITDA denominators, from filings
scripts/pipeline.py            daily market-data fetch (stdlib only)
scripts/compute_risk.py        runs the engine over the fetched history
scripts/backfill_history.py    one-shot recovery of history the old cap discarded
tests/                         engine property tests and MCP smoke tests
BRAINSTORM.md                  ranked feature roadmap for a risk-advisory partner
PARTNER-REVIEW.md              correctness audit and architecture review (Jul)
REVIEW-2026-09.md              September review: what was wrong, and the build
```

## Models

Every number below is computed from observed prices by `engine/`, which is pure
standard library on purpose: the nightly job cannot break on a dependency
resolution, and the MCP servers, the CI pipeline and the dashboard all run the
*same* code, so a tool call and the page cannot disagree.

| Layer | What runs |
|---|---|
| Volatility | EWMA(0.94) and GARCH(1,1) fitted by maximum likelihood; the term structure mean-reverts instead of scaling by √t |
| VaR / ES | Historical simulation, normal parametric and Student-t Monte Carlo, reported together — disagreement between them is information about the tail, not something to resolve silently |
| Validation | Rolling out-of-sample backtest with Kupiec coverage and Christoffersen independence. It also states when the estimation window is too thin to support the confidence level, rather than blaming the model |
| Tails | Generalised Pareto peaks-over-threshold fitted by probability-weighted moments to **real** losses, with a mean-excess diagnostic |
| Dependence | Measured correlations with PSD repair, and a Student-t copula whose degrees of freedom are estimated from the data — a Gaussian copula assigns vanishing probability to exactly the joint move an Indian import book carries |
| Earnings impact | Cash-Flow-at-Risk in ₹ crore against FY26 cost base, net of revenue-side exposure to the same commodity |
| Hedge accounting | Ind AS 109 dollar-offset and regression effectiveness against the 80–125% band |

Where the data cannot support a calculation the engine returns a stated reason
instead of a number. A company that sells what it buys is not scored as if a
price rise only hurt it; a company where one input exceeds 35% of the cost base
is flagged as a converter whose real exposure is a processing spread.

## MCP servers

```bash
pip install mcp        # SDK 1.x and 2.x both supported
```

Registered in `.mcp.json`; all three speak stdio.

- **`risk-engine`** — `run_var`, `backtest_var`, `fit_garch`, `fit_tail`, `joint_stress`, `hedge_effectiveness`, `basis_risk`, `company_cfar`, `model_summary`
- **`india-markets`** — `get_spot`, `get_series`, `get_volatility`, `get_correlations`, `get_regime`, `hedgeability`, `score_history`
- **`regwatch`** — `diff_watchlist`, `check_elapsed_deadlines`, `fetch_notifications`, `search_official`, `list_sources`

The point of the MCP layer is not convenience. It is that the weekly cycle agent
must **compute** its figures rather than assert them, and `regwatch` exists
because of a specific failure: the RBI moved the FCNR(B) window forward by a
month in August 2026 and the dashboard counted down to the old date for three
weeks. Prices refreshed nightly the whole time. A stale price is an annoyance; a
stale *rule* is a wrong answer delivered with confidence.

The reference sheet is fetched at runtime; the scoring data the risk models consume is embedded, so **the models never depend on the network**.

## Commodity reference sheet

Structure follows the [Commodities 101](https://commodities101.morgandowney.com/) fact-sheet breakdown — family, symbol, how-it-trades (venue, benchmark, lot, price terms, settlement, curve, liquidity), producers / consumers / importers, main uses, price drivers, key stats — with the India hedgeability layer added.

Supply concentration is **computed** from producer shares via a Herfindahl band rather than hand-set, with documented overrides where world shares misstate India's sourcing (Australia is 52% of seaborne coking coal but ~85% of India's imports; China is 44% of copper *refining* where mine shares are fragmented).

48 of the 97 markets carry full profiles; the rest carry structural facts and trading terms only, and are labelled as such in the UI.

## What was deliberately removed

A risk tool cannot survive being caught generating its own evidence. These were cut rather than caveated:

- **Counterparty risk table** — invented counterparties whose fabricated limit utilisations were being pushed into the real cockpit escalation queue
- **Backtest on synthetic outcomes** — the mock was constructed so the ensemble won, and the tool cited that as evidence for multi-model weighting. Replaced with a Validation tab that reports the real history accumulating in `data/history.json` and states plainly that no validation is possible yet
- **Structured-judgment model family** — claimed a seeded AHP pairwise matrix and a Delphi panel that did not exist, while drawing its ratings from the same inputs as the objective model. Carried 15% of ensemble weight and added no independent information
- **GPD/EVT fitted to Monte-Carlo output** — circular; fitting an extreme-value distribution to the simulator's own draws recovers the simulator's assumptions, not the market's tails
- **Alpha Vantage key entry** — asked the viewer to paste a personal API key into the browser to repair the correlation matrix the pipeline now computes
- **"Probability of breach"** on a logistic whose coefficients were never fitted to outcomes — kept as a ranked pressure index, relabelled everywhere

## Caveats

Cost-base shares are estimates from segment disclosure and annual-report commentary, and are labelled as estimates. They are good enough to rank and to scope; confirming them against a client's own ledger is the first day of the engagement, not a prerequisite for the conversation.
