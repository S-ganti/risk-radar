# Commodity tools for consultancy partners and directors

Research reviewed 12 November 2026. Priorities below are product recommendations, not measured user demand. Preserve the existing models, mapping and scenario features; build decision workflows around them.

| Priority | Feature | Partner/director question | Required inputs / limits |
|---|---|---|---|
| 1 | Exposure-ranked client opportunity list | Which clients need a conversation this week, and why? | Existing exposure mapping plus price change, quote age and explicit assumptions. Rank potential impact, not share-price performance. Client-specific procurement must be confirmed. |
| 1 | One-page decision brief | What decision is needed, who owns it, and what changes under each option? | Baseline versus stress, gross/net exposure, mitigation choices, source dates, confidence, owner and next action. Existing brief export is the starting point. |
| 1 | Scenario comparison | Should we hedge, reprice, hold inventory or diversify sourcing? | Side-by-side baseline/hedge/pricing/inventory effects, with consistent units and explicit procurement periods. Do not optimise invented client positions. |
| 2 | Hedge feasibility and basis-risk workbench | Is the instrument actually appropriate and executable? | Physical benchmark, contract size, currency, tenor, basis history, liquidity and margin cash requirements. Existing hedgeability matrix is a starting point; risk analytics are not accounting eligibility. |
| 2 | Forward curve and procurement calendar | Which budget periods face the greatest risk? | Licensed or explicitly available futures tenors/settlements, client volumes and delivery schedules. Do not infer a curve from a front-month quote. |
| 2 | Supply-chain chokepoint overlay | Which supplier, country or route can disrupt several clients? | Dependency graph plus sourced supplier concentration, route/port exposure and inventory cover. Differentiate known relationships from assumed ones. |
| 3 | Decision and model review register | Can we defend the recommendation later? | Versioned inputs/models, reviewer, assumptions, decision, date and realised outcome. Shared storage and authenticated approvals are prerequisites for team governance. |

## What the external products support

- [CME commodity tools](https://www.cmegroup.com/markets/commodities) combine hedging instruments with volume/open interest and implied-volatility tools. Product inference: add liquidity, basis and cash requirements to the existing exposure view, rather than another standalone risk score.
- [S&P Global risk and economics](https://www.spglobal.com/market-intelligence/en/solutions/global-risk-and-economics) covers scenario impacts spanning commodity prices, FX and geopolitics. Product inference: cross-risk comparisons and clear transmission channels are more useful to directors than isolated price alerts.
- [S&P Global supply-chain failure analysis](https://www.spglobal.com/market-intelligence/en/news-insights/research/2026/09/identifying-and-monitoring-single-points-of-failure-in-supply-chains-if-anything-can-go-wrong-it-will) connects supplier vulnerability with operational signals. Product inference: extend the dependency tree with sourced chokepoints when those datasets exist.
- [Platts benchmarks](https://energy.spglobal.com/pricebenchmarks) and [market-data delivery](https://www.spglobal.com/energy/en/products-solutions/market-data) distinguish assessed prices, forward curves and delivery products. A single exchange quote is not a complete physical commodity price.

## Public data implementation and constraints

The new quote register contains all 87 company records, all 97 commodity references and 3 macro benchmarks. The first successful run returned 85 equity quotes, 16 commodity futures benchmarks, 5 monthly commodity references and 3 macro quotes. Two stock symbols failed: Tata Motors and Gujarat Gas; corporate-action mapping needs review rather than silently substituting a successor entity.

Public Yahoo chart responses are treated as delayed or end-of-day; provider access is best-effort and may fail. Every row retains its actual observation time, symbol, source and units. Failed refreshes retain a visibly stale last-good quote. Unmapped physical markets remain unavailable. Optional quote fields include volume, daily range, 52-week range and market cap when the provider returns them; valuation ratios and company financials are not fabricated.

[NSE real-time subscriptions](https://www.nse.in/static/market-data/real-time-data-subscription) and [data usage policy](https://www.nseindia.com/static/market-data/nse-data-policy) establish why public access should not be described as an unrestricted real-time redistribution service. [World Bank Pink Sheet](https://www.worldbank.org/en/research/commodity-markets) is periodic, not live.

Local mode: `python scripts/serve.py --port 8768` supports an on-demand refresh with a five-minute cache. Static hosting reads the last published snapshot; the new hourly GitHub workflow only operates after changes are pushed and Actions is enabled. A static refresh button cannot start a privileged GitHub workflow. Provider refresh does not revalidate exposure assumptions, policies, financial statements or separately generated model outputs.

## Correctness finding

[Ind AS 109](https://www.mca.gov.in/Ministry/pdf/IndAS109_2020_10112020.pdf), section 6.4.1 and B6.4, requires an economic relationship, credit risk not dominating and an appropriate hedge ratio. Statistical thresholds alone do not establish accounting eligibility. The legacy quantitative diagnostics are retained but now explicitly report accounting status as not assessed.
