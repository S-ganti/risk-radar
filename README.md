# Commodity & treasury risk radar — India

Self-contained dashboard built from public official sources. Open: https://s-ganti.github.io/risk-radar/

**87 companies · 97 commodity markets across 10 families · 5 model families · daily live-data pipeline.**

Current research cycle: **2026-W28** (7 Jul 2026). Market data refreshes daily via GitHub Actions (`scripts/pipeline.py`, 18:30 IST → `data/latest.json`).

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
data/commodities.json          commodity reference sheet (fetched same-origin)
data/latest.json               daily market data, vols, correlations, regime
data/history.json              real per-run score history — accumulates in git
data/financials.json           FY26 revenue/EBITDA denominators, from filings
scripts/build_commodities.py   source of truth for the reference sheet
scripts/pipeline.py            daily market-data pipeline (stdlib only)
scripts/migrations/            one-shot patches, kept as the record of what changed
BRAINSTORM.md                  ranked feature roadmap for a risk-advisory partner
PARTNER-REVIEW.md              correctness audit and architecture review
```

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
